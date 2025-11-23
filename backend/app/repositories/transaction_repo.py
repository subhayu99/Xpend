from sqlmodel import Session, select
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from typing import List, Optional
import uuid

class TransactionRepository:
    """Repository for transaction operations"""
    
    @staticmethod
    def create(db: Session, user_id: uuid.UUID, transaction_data: TransactionCreate) -> Transaction:
        """Create a new transaction with hash generation"""
        from app.utils.hashing import hash_transaction
        from sqlmodel import select
        
        # Find next available index for this transaction signature
        index = 0
        while True:
            tx_hash = hash_transaction(
                date=transaction_data.transaction_date,
                amount=transaction_data.amount,
                description=transaction_data.description,
                account_id=transaction_data.account_id,
                index=index
            )
            # Check if hash exists
            existing = db.exec(
                select(Transaction).where(Transaction.transaction_hash == tx_hash)
            ).first()
            
            if not existing:
                break
            index += 1
            
        transaction = Transaction(
            user_id=user_id,
            transaction_hash=tx_hash,
            **transaction_data.model_dump()
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction
    
    @staticmethod
    def create_multi(db: Session, user_id: uuid.UUID, transactions_data: List[TransactionCreate]) -> List[Transaction]:
        """
        Create multiple transactions with duplicate detection.
        Uses hashing and occurrence counting to handle identical transactions.
        """
        from app.utils.hashing import hash_transaction
        from sqlmodel import func
        
        # 1. Group incoming transactions by signature
        # Key: (date, amount, description, account_id) -> List[TransactionCreate]
        grouped_txs = {}
        
        for tx_data in transactions_data:
            # Normalize date for grouping (YYYY-MM-DD)
            date_str = tx_data.transaction_date.strftime("%Y-%m-%d")
            key = (date_str, tx_data.amount, tx_data.description.strip().lower(), tx_data.account_id)
            
            if key not in grouped_txs:
                grouped_txs[key] = []
            grouped_txs[key].append(tx_data)
            
        new_transactions = []
        
        # 2. Process each group
        for key, tx_list in grouped_txs.items():
            date_str, amount, desc, account_id = key
            
            # Query DB for existing count of this specific signature
            # We count how many transactions exist with same date, amount, desc, account
            # Note: We match loosely on date (day level)
            
            # Construct start and end of day for query
            # Actually, let's just use the hash check which is more robust if we trust our logic
            # But to generate the correct index, we need to know how many exist.
            
            # Optimization: Instead of querying count, let's fetch ALL existing hashes for this account
            # and check against them. But that might be heavy if account has 10k txs.
            # Let's query count for this specific signature.
            
            # Parse date back to datetime for query
            # This query might be slow if done for every group. 
            # Better approach: Fetch all transactions for the relevant dates?
            # For now, let's do the count query, it's safer.
            
            # Wait, we can just try to insert with index 0, 1, 2... and check if hash exists.
            # But we need to check against DB.
            
            # Let's try indices 0 to N+M (where N is existing, M is new)
            # We don't know N.
            # We can query existing hashes for this user/account?
            
            # Let's use the count approach.
            existing_count = db.exec(
                select(func.count(Transaction.id)).where(
                    Transaction.account_id == account_id,
                    Transaction.amount == amount,
                    func.lower(Transaction.description) == desc,
                    func.date(Transaction.transaction_date) == date_str
                )
            ).one()
            
            # 3. Assign indices and create objects
            current_index = existing_count
            
            for tx_data in tx_list:
                # Generate hash
                tx_hash = hash_transaction(
                    date=tx_data.transaction_date,
                    amount=tx_data.amount,
                    description=tx_data.description,
                    account_id=tx_data.account_id,
                    index=current_index
                )
                
                # Check if this hash already exists (double safety, e.g. if we re-upload same file)
                # If we rely on existing_count, re-uploading the same file:
                # File has 2 txs. DB has 2 txs. existing_count = 2.
                # We start at index 2. Hash(..., 2) is generated.
                # Does Hash(..., 2) exist? No. So we insert duplicates!
                # ERROR in logic: existing_count includes the ones we are trying to re-upload!
                
                # CORRECT LOGIC:
                # We need to check if the specific HASH exists.
                # But we don't know which index corresponds to "this" transaction in the file vs "that" one in DB.
                # They are identical.
                # So, if we have 2 in file, and 2 in DB.
                # We generate hashes for indices 0, 1.
                # Check if Hash(0) exists? Yes. Skip.
                # Check if Hash(1) exists? Yes. Skip.
                # This works!
                
                # So we should ALWAYS start index at 0 and go up to (existing_count + new_count).
                # And for each, check if hash exists. If yes, skip. If no, insert.
                # But wait, if we have 2 new ones, and 2 existing.
                # We iterate 0..3?
                # No. We have 2 incoming. We want to check if they are *new*.
                # If DB has 2 (indices 0, 1).
                # We process incoming 1. Try index 0. Exists? Yes. Try index 1. Exists? Yes. Try index 2. New!
                # We process incoming 2. Try index 3. New!
                
                # So for the group of K incoming transactions:
                # We iterate from i = 0 upwards.
                # We find the first K indices that do NOT exist in DB.
                # Assign those to the K incoming transactions.
                
                # Wait, if we do that, we will ALWAYS add them as new transactions!
                # Example: DB has 2 (Coffee). File has 2 (Coffee).
                # We want to SKIP them because they are the SAME 2 coffees.
                # We DON'T want to add 2 MORE coffees.
                
                # How to distinguish "Same 2 coffees" vs "2 New coffees"?
                # WE CAN'T without external ID.
                # Assumption: If I upload a file, and it contains transactions that "look like" existing ones,
                # are they duplicates or new?
                # Standard convention: They are duplicates.
                # If I really bought 4 coffees, and uploaded File A (2 coffees) then File B (4 coffees),
                # File B contains the 2 old + 2 new.
                # We should match 2 old, and add 2 new.
                
                # So:
                # 1. Calculate hashes for indices 0, 1, 2, ...
                # 2. Check which ones exist.
                # 3. If Hash(0) exists, we assume the first tx in our list IS that transaction.
                # 4. If Hash(1) exists, the second tx is that one.
                # 5. If Hash(2) does not exist, the third tx is NEW.
                
                # So we just iterate through our list of K incoming txs.
                # For the j-th transaction in our list (0..K-1), what index should it have?
                # It should map to the j-th occurrence in the "global history" of this transaction signature?
                # No, that implies strict ordering.
                
                # Let's assume the file contains a snapshot.
                # If DB has 2. File has 2.
                # We check Hash(0), Hash(1). Both exist. We skip both.
                
                # If DB has 2. File has 3.
                # We check Hash(0), Hash(1). Exist. Skip.
                # We check Hash(2). Doesn't exist. Insert.
                
                # If DB has 2. File has 1.
                # We check Hash(0). Exists. Skip.
                
                # This logic holds up!
                # We just need to iterate 0 to K-1 (where K is count in file).
                # AND we need to check if we need to "continue" numbering if we are adding MORE than existing.
                # No, if file has 3 and DB has 2.
                # Hash(0) exists. Hash(1) exists. Hash(2) is new.
                # So we just assign index = loop_index?
                # Yes!
                
                # BUT what if I uploaded File A (2 coffees). DB has Hash(0), Hash(1).
                # Then I buy a 3rd coffee.
                # I upload File B (contains ONLY the 3rd coffee).
                # My logic: File B has 1 coffee. I assign index 0.
                # Hash(0) exists! So I skip it.
                # ERROR! I lost the 3rd coffee!
                
                # This is the hard part.
                # If the file is partial (incremental), we fail.
                # If the file is cumulative (full history), we succeed.
                
                # Most bank statements are monthly.
                # Month 1: 2 coffees. Upload. DB: Hash(0), Hash(1).
                # Month 2: 2 coffees. Upload.
                # These are NEW coffees (different date). So hashes are different. Safe.
                
                # The issue is only for SAME DAY, SAME AMOUNT, SAME DESC.
                # If I buy 2 coffees on Monday. Upload.
                # Then I buy 3rd coffee on Monday. Upload file with JUST that 3rd coffee.
                # It will be skipped.
                
                # However, usually you download a statement for a date range.
                # If you download "Monday", you get all 3.
                # Then we process 3. Hash(0), Hash(1) exist. Hash(2) new. Added. Safe.
                
                # Conclusion: This logic works for CUMULATIVE statements for the overlapping period.
                # It fails for DISJOINT partial statements of the same day.
                # This is an acceptable trade-off.
                
                # Implementation:
                # For each group of K transactions in the file:
                # We assume they correspond to indices 0..K-1 of that signature for that day.
                # But wait... if I already have 2 in DB.
                # And I upload a file with 3 (the 2 old + 1 new).
                # I check indices 0, 1, 2.
                # 0 exists -> Skip.
                # 1 exists -> Skip.
                # 2 missing -> Insert.
                # Correct.
                
                # What if I upload a file with ONLY the 3rd one?
                # I check index 0.
                # 0 exists -> Skip.
                # ERROR.
                
                # To fix this, we would need to know "this is the 3rd one". We don't.
                # The user's suggestion of "ledger" implies we count globally.
                # If we count globally, we ALWAYS add new ones.
                # DB has 2. New file has 1. We assign index 2 (since 2 exist). Add it.
                # Result: DB has 3.
                # If we re-upload the file with 1.
                # DB has 3. We assign index 3. Add it.
                # Result: DB has 4. DUPLICATE!
                
                # So we must choose:
                # A) Prevent duplicates (Safe for re-uploads, fails for partial same-day updates)
                # B) Allow partial updates (Safe for partials, duplicates on re-uploads)
                
                # Option A is much safer. Re-uploading is common. Partial same-day updates are rare.
                # So I will stick to Option A:
                # Indices are assigned based on the order IN THE CURRENT FILE.
                
                pass
            
            # We need to query which hashes exist for this group
            # We can generate all K hashes and check existence in one query
            
            hashes_to_check = []
            for i, tx_data in enumerate(tx_list):
                h = hash_transaction(
                    date=tx_data.transaction_date,
                    amount=tx_data.amount,
                    description=tx_data.description,
                    account_id=tx_data.account_id,
                    index=i
                )
                hashes_to_check.append(h)
                
            # Query DB for these hashes
            existing_hashes = db.exec(
                select(Transaction.transaction_hash).where(
                    Transaction.transaction_hash.in_(hashes_to_check)
                )
            ).all()
            existing_hashes_set = set(existing_hashes)
            
            # Filter
            for i, tx_data in enumerate(tx_list):
                h = hashes_to_check[i]
                if h not in existing_hashes_set:
                    # Create new transaction
                    new_tx = Transaction(
                        user_id=user_id,
                        transaction_hash=h,
                        **tx_data.model_dump()
                    )
                    new_transactions.append(new_tx)
        
        if new_transactions:
            db.add_all(new_transactions)
            db.commit()
            for tx in new_transactions:
                db.refresh(tx)
                
        return new_transactions
    
    @staticmethod
    def get_by_id(db: Session, transaction_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Transaction]:
        """Get transaction by ID for a specific user"""
        return db.exec(
            select(Transaction).where(
                Transaction.id == transaction_id,
                Transaction.user_id == user_id
            )
        ).first()
    
    @staticmethod
    def get_all(
        db: Session, 
        user_id: uuid.UUID, 
        skip: int = 0, 
        limit: int = 100,
        account_id: Optional[uuid.UUID] = None,
        category_id: Optional[uuid.UUID] = None,
        transaction_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Transaction]:
        """Get all transactions for a user with pagination and advanced filtering"""
        from datetime import datetime
        
        query = select(Transaction).where(Transaction.user_id == user_id)
        
        # Account filter
        if account_id:
            query = query.where(Transaction.account_id == account_id)
        
        # Category filter
        if category_id:
            query = query.where(Transaction.category_id == category_id)
        
        # Transaction type filter
        if transaction_type:
            query = query.where(Transaction.transaction_type == transaction_type)
        
        # Date range filter
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                query = query.where(Transaction.transaction_date >= start_dt)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                query = query.where(Transaction.transaction_date <= end_dt)
            except ValueError:
                pass
        
        # Search filter (description or merchant name)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (Transaction.description.ilike(search_pattern)) |
                (Transaction.merchant_name.ilike(search_pattern))
            )
            
        query = query.order_by(Transaction.transaction_date.desc())
        query = query.offset(skip).limit(limit)
        
        return db.exec(query).all()
    
    @staticmethod
    def update(db: Session, transaction: Transaction, update_data: TransactionUpdate) -> Transaction:
        """Update a transaction"""
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(transaction, field, value)
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction
    
    @staticmethod
    def delete(db: Session, transaction: Transaction) -> None:
        """Delete a transaction"""
        db.delete(transaction)
        db.commit()

    @staticmethod
    def apply_merchant_mapping(
        db: Session,
        user_id: uuid.UUID,
        transaction: Transaction
    ) -> Transaction:
        """
        Apply merchant normalization and auto-categorization to a transaction.
        Uses the MerchantRepository to find matching mappings.
        """
        from app.repositories.merchant_repo import MerchantRepository
        from app.utils.merchant_normalizer import MerchantNormalizer

        if not transaction.description:
            return transaction

        # First, try to find an existing merchant mapping
        match = MerchantRepository.find_match(db, user_id, transaction.description)

        if match:
            merchant, score, pattern = match
            transaction.merchant_name = merchant.normalized_name

            # Apply category if not already set and merchant has a default category
            if not transaction.category_id and merchant.category_id:
                transaction.category_id = merchant.category_id

            # Increment usage count
            MerchantRepository.increment_usage(db, merchant)
        else:
            # Use basic normalization if no mapping found
            normalized = MerchantNormalizer.normalize(transaction.description)
            if normalized:
                transaction.merchant_name = normalized

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        return transaction

    @staticmethod
    def apply_merchant_mappings_bulk(
        db: Session,
        user_id: uuid.UUID,
        transactions: List[Transaction]
    ) -> int:
        """
        Apply merchant normalization and auto-categorization to multiple transactions.
        Returns the number of transactions updated.
        """
        from app.repositories.merchant_repo import MerchantRepository
        from app.utils.merchant_normalizer import MerchantNormalizer

        updated_count = 0

        for transaction in transactions:
            if not transaction.description:
                continue

            # Try to find an existing merchant mapping
            match = MerchantRepository.find_match(db, user_id, transaction.description)

            if match:
                merchant, score, pattern = match
                transaction.merchant_name = merchant.normalized_name

                # Apply category if not already set
                if not transaction.category_id and merchant.category_id:
                    transaction.category_id = merchant.category_id

                updated_count += 1
            else:
                # Use basic normalization
                normalized = MerchantNormalizer.normalize(transaction.description)
                if normalized and normalized != transaction.merchant_name:
                    transaction.merchant_name = normalized
                    updated_count += 1

            db.add(transaction)

        if updated_count > 0:
            db.commit()

        return updated_count

    @staticmethod
    def get_uncategorized_grouped_by_merchant(
        db: Session,
        user_id: uuid.UUID,
        include_transactions: bool = False,
        limit: int = 100
    ) -> List[dict]:
        """
        Get uncategorized transactions grouped by merchant_name.
        Returns groups sorted by transaction count (descending).
        """
        from sqlmodel import func
        from app.models.account import Account

        # Query to get groups with aggregates
        query = (
            select(
                Transaction.merchant_name,
                func.count(Transaction.id).label('transaction_count'),
                func.sum(Transaction.amount).label('total_amount'),
                func.min(Transaction.transaction_date).label('first_date'),
                func.max(Transaction.transaction_date).label('last_date')
            )
            .where(
                Transaction.user_id == user_id,
                Transaction.category_id.is_(None),
                Transaction.merchant_name.isnot(None)
            )
            .group_by(Transaction.merchant_name)
            .order_by(func.count(Transaction.id).desc())
            .limit(limit)
        )

        results = db.exec(query).all()
        groups = []

        for row in results:
            group = {
                'merchant_name': row.merchant_name,
                'transaction_count': row.transaction_count,
                'total_amount': float(row.total_amount) if row.total_amount else 0.0,
                'first_date': row.first_date,
                'last_date': row.last_date,
                'transactions': [],
                'sample_descriptions': []
            }

            if include_transactions:
                # Fetch all transactions for this merchant
                txs = db.exec(
                    select(Transaction)
                    .where(
                        Transaction.user_id == user_id,
                        Transaction.merchant_name == row.merchant_name,
                        Transaction.category_id.is_(None)
                    )
                    .order_by(Transaction.transaction_date.desc())
                ).all()

                # Get account names for transactions
                account_ids = list(set(tx.account_id for tx in txs))
                accounts = {a.id: a.name for a in db.exec(
                    select(Account).where(Account.id.in_(account_ids))
                ).all()}

                group['transactions'] = [
                    {
                        'id': tx.id,
                        'transaction_date': tx.transaction_date,
                        'amount': tx.amount,
                        'description': tx.description,
                        'account_id': tx.account_id,
                        'account_name': accounts.get(tx.account_id)
                    }
                    for tx in txs
                ]

                # Get unique descriptions as samples
                unique_descs = list(set(tx.description for tx in txs if tx.description))[:5]
                group['sample_descriptions'] = unique_descs
            else:
                # Just get sample descriptions without full transaction data
                sample_txs = db.exec(
                    select(Transaction.description)
                    .where(
                        Transaction.user_id == user_id,
                        Transaction.merchant_name == row.merchant_name,
                        Transaction.category_id.is_(None)
                    )
                    .distinct()
                    .limit(5)
                ).all()
                group['sample_descriptions'] = [d for d in sample_txs if d]

            groups.append(group)

        return groups

    @staticmethod
    def categorize_by_merchant_name(
        db: Session,
        user_id: uuid.UUID,
        merchant_name: str,
        category_id: uuid.UUID
    ) -> int:
        """
        Assign a category to all uncategorized transactions with a specific merchant_name.
        Returns the number of transactions updated.
        """
        # Get all matching transactions
        transactions = db.exec(
            select(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.merchant_name == merchant_name,
                Transaction.category_id.is_(None)
            )
        ).all()

        for tx in transactions:
            tx.category_id = category_id
            db.add(tx)

        if transactions:
            db.commit()

        return len(transactions)

    @staticmethod
    def get_transactions_without_merchant_by_account(
        db: Session,
        user_id: uuid.UUID,
        account_id: uuid.UUID
    ) -> List[Transaction]:
        """
        Get all transactions for a specific account that don't have a merchant_name.
        """
        return db.exec(
            select(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.account_id == account_id,
                Transaction.merchant_name.is_(None)
            )
        ).all()

    @staticmethod
    def get_unextracted_counts_by_account(
        db: Session,
        user_id: uuid.UUID
    ) -> List[dict]:
        """
        Get count of transactions without merchant_name grouped by account.
        Returns list of {account_id, account_name, bank_name, count}.
        """
        from sqlmodel import func
        from app.models.account import Account

        # Query to get counts per account
        query = (
            select(
                Transaction.account_id,
                Account.name.label('account_name'),
                Account.bank_name,
                func.count(Transaction.id).label('count')
            )
            .join(Account, Transaction.account_id == Account.id)
            .where(
                Transaction.user_id == user_id,
                Transaction.merchant_name.is_(None)
            )
            .group_by(Transaction.account_id, Account.name, Account.bank_name)
            .order_by(func.count(Transaction.id).desc())
        )

        results = db.exec(query).all()
        return [
            {
                'account_id': row.account_id,
                'account_name': row.account_name,
                'bank_name': row.bank_name,
                'count': row.count
            }
            for row in results
        ]

    @staticmethod
    def bulk_update_merchant_names(
        db: Session,
        updates: dict  # {transaction_id: merchant_name}
    ) -> int:
        """
        Bulk update merchant_name for multiple transactions.
        Returns count of updated transactions.
        """
        if not updates:
            return 0

        count = 0
        for tx_id, merchant_name in updates.items():
            tx = db.get(Transaction, tx_id)
            if tx and not tx.merchant_name:  # Only update if not already set
                tx.merchant_name = merchant_name
                db.add(tx)
                count += 1

        if count > 0:
            db.commit()

        return count
