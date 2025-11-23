from sqlmodel import Session, select, func
from app.models.merchant import Merchant
from app.models.transaction import Transaction
from app.models.category import Category
from app.schemas.merchant import MerchantCreate, MerchantUpdate, UnmappedMerchantInfo
from typing import List, Optional, Tuple
from datetime import datetime
import uuid
import re

try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False


class MerchantRepository:
    """Repository for merchant operations with fuzzy matching"""

    @staticmethod
    def create(db: Session, user_id: uuid.UUID, merchant_data: MerchantCreate) -> Merchant:
        """Create a new merchant mapping"""
        merchant = Merchant(
            user_id=user_id,
            **merchant_data.model_dump()
        )
        db.add(merchant)
        db.commit()
        db.refresh(merchant)
        return merchant

    @staticmethod
    def get_by_id(db: Session, merchant_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Merchant]:
        """Get merchant by ID for a specific user"""
        return db.exec(
            select(Merchant).where(
                Merchant.id == merchant_id,
                Merchant.user_id == user_id
            )
        ).first()

    @staticmethod
    def get_all(
        db: Session,
        user_id: uuid.UUID,
        page: int = 1,
        limit: int = 50,
        search: Optional[str] = None
    ) -> Tuple[List[Merchant], int]:
        """Get all merchants for a user with pagination"""
        query = select(Merchant).where(Merchant.user_id == user_id)

        if search:
            query = query.where(Merchant.normalized_name.ilike(f"%{search}%"))

        # Get total count
        count_query = select(func.count(Merchant.id)).where(Merchant.user_id == user_id)
        if search:
            count_query = count_query.where(Merchant.normalized_name.ilike(f"%{search}%"))
        total = db.exec(count_query).first() or 0

        # Apply pagination
        query = query.order_by(Merchant.normalized_name).offset((page - 1) * limit).limit(limit)

        merchants = db.exec(query).all()
        return list(merchants), total

    @staticmethod
    def get_by_normalized_name(db: Session, user_id: uuid.UUID, name: str) -> Optional[Merchant]:
        """Get merchant by normalized name"""
        return db.exec(
            select(Merchant).where(
                Merchant.user_id == user_id,
                Merchant.normalized_name.ilike(name)
            )
        ).first()

    @staticmethod
    def update(db: Session, merchant: Merchant, update_data: MerchantUpdate) -> Merchant:
        """Update a merchant mapping"""
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(merchant, field, value)

        merchant.updated_at = datetime.utcnow()
        db.add(merchant)
        db.commit()
        db.refresh(merchant)
        return merchant

    @staticmethod
    def delete(db: Session, merchant: Merchant) -> None:
        """Delete a merchant mapping"""
        db.delete(merchant)
        db.commit()

    @staticmethod
    def increment_usage(db: Session, merchant: Merchant) -> None:
        """Increment usage count for a merchant"""
        merchant.usage_count += 1
        db.add(merchant)
        db.commit()

    @staticmethod
    def find_match(
        db: Session,
        user_id: uuid.UUID,
        description: str,
        default_threshold: float = 0.85
    ) -> Optional[Tuple[Merchant, float, Optional[str]]]:
        """
        Find a matching merchant for a transaction description.
        Returns (merchant, match_score, matched_pattern) or None.

        Matching priority:
        1. Exact pattern match
        2. Fuzzy match against normalized names
        3. Fuzzy match against patterns
        """
        if not description:
            return None

        description_upper = description.upper().strip()

        # Get all merchants for this user
        merchants = db.exec(
            select(Merchant).where(Merchant.user_id == user_id)
        ).all()

        if not merchants:
            return None

        best_match: Optional[Tuple[Merchant, float, Optional[str]]] = None
        best_score = 0.0

        for merchant in merchants:
            threshold = merchant.fuzzy_threshold or default_threshold

            # Check exact pattern matches first
            for pattern in merchant.patterns:
                pattern_upper = pattern.upper()

                # Check if pattern is a regex (contains * or other special chars)
                if '*' in pattern or '?' in pattern:
                    # Convert glob pattern to regex
                    regex_pattern = pattern_upper.replace('*', '.*').replace('?', '.')
                    if re.match(regex_pattern, description_upper):
                        return (merchant, 1.0, pattern)
                elif pattern_upper in description_upper:
                    # Simple substring match
                    return (merchant, 1.0, pattern)

            # Fuzzy matching using rapidfuzz
            if RAPIDFUZZ_AVAILABLE:
                # Match against normalized name
                name_score = fuzz.token_set_ratio(
                    merchant.normalized_name.upper(),
                    description_upper
                ) / 100.0

                if name_score >= threshold and name_score > best_score:
                    best_score = name_score
                    best_match = (merchant, name_score, None)

                # Also try matching against patterns
                for pattern in merchant.patterns:
                    pattern_clean = pattern.replace('*', '').replace('?', '').upper()
                    pattern_score = fuzz.token_set_ratio(pattern_clean, description_upper) / 100.0

                    if pattern_score >= threshold and pattern_score > best_score:
                        best_score = pattern_score
                        best_match = (merchant, pattern_score, pattern)

        return best_match

    @staticmethod
    def get_unmapped_merchants(
        db: Session,
        user_id: uuid.UUID,
        limit: int = 50
    ) -> List[UnmappedMerchantInfo]:
        """
        Get transactions that don't have a merchant mapping applied.
        Groups by description patterns and returns summary info.
        """
        from app.utils.merchant_normalizer import MerchantNormalizer

        # Get all transactions without merchant_name set
        transactions = db.exec(
            select(Transaction).where(
                Transaction.user_id == user_id,
                (Transaction.merchant_name.is_(None)) | (Transaction.merchant_name == '')
            )
        ).all()

        if not transactions:
            return []

        # Group by normalized description
        grouped = {}
        for tx in transactions:
            normalized = MerchantNormalizer.normalize(tx.description)
            if normalized:
                if normalized not in grouped:
                    grouped[normalized] = {
                        'count': 0,
                        'total': 0.0,
                        'first_seen': tx.transaction_date,
                        'last_seen': tx.transaction_date,
                        'samples': []
                    }
                grouped[normalized]['count'] += 1
                grouped[normalized]['total'] += float(tx.amount) if tx.amount else 0.0
                if tx.transaction_date < grouped[normalized]['first_seen']:
                    grouped[normalized]['first_seen'] = tx.transaction_date
                if tx.transaction_date > grouped[normalized]['last_seen']:
                    grouped[normalized]['last_seen'] = tx.transaction_date
                if len(grouped[normalized]['samples']) < 3:
                    grouped[normalized]['samples'].append(tx.description)

        # Filter out already mapped merchants
        existing_merchants = db.exec(
            select(Merchant.normalized_name).where(Merchant.user_id == user_id)
        ).all()
        existing_names = {name.upper() for name in existing_merchants}

        unmapped = []
        for name, data in sorted(grouped.items(), key=lambda x: -x[1]['count'])[:limit]:
            if name.upper() not in existing_names:
                unmapped.append(UnmappedMerchantInfo(
                    raw_name=name,
                    transaction_count=data['count'],
                    total_amount=data['total'],
                    first_seen=data['first_seen'],
                    last_seen=data['last_seen'],
                    sample_descriptions=data['samples']
                ))

        return unmapped

    @staticmethod
    def apply_mapping_to_transactions(
        db: Session,
        user_id: uuid.UUID,
        merchant: Merchant,
        update_category: bool = True
    ) -> int:
        """
        Apply a merchant mapping to existing transactions.
        Returns the number of transactions updated.
        """
        count = 0

        # Get all transactions for this user (including those without merchant_name)
        transactions = db.exec(
            select(Transaction).where(Transaction.user_id == user_id)
        ).all()

        for txn in transactions:
            # Check if description matches patterns
            match = MerchantRepository._matches_patterns(txn.description, merchant.patterns)

            # Also check if already has this merchant name (skip if so)
            if txn.merchant_name and txn.merchant_name.upper() == merchant.normalized_name.upper():
                continue  # Already mapped to this merchant

            if match:
                txn.merchant_name = merchant.normalized_name
                if update_category and merchant.category_id and not txn.category_id:
                    txn.category_id = merchant.category_id
                txn.updated_at = datetime.utcnow()
                db.add(txn)
                count += 1

        if count > 0:
            db.commit()

        return count

    @staticmethod
    def _matches_patterns(description: str, patterns: List[str]) -> bool:
        """Check if description matches any of the patterns"""
        if not description or not patterns:
            return False

        description_upper = description.upper()

        for pattern in patterns:
            pattern_upper = pattern.upper()

            if '*' in pattern or '?' in pattern:
                regex_pattern = pattern_upper.replace('*', '.*').replace('?', '.')
                if re.match(regex_pattern, description_upper):
                    return True
            elif pattern_upper in description_upper:
                return True

        return False
