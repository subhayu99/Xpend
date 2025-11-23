from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from app.db.session import get_session
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.category import Category
from app.schemas.merchant import (
    MerchantCreate,
    MerchantUpdate,
    MerchantResponse,
    MerchantListResponse,
    UnmappedMerchantsResponse,
    MerchantSuggestionsResponse,
    MerchantSuggestion,
    CategoryInfo,
    UncategorizedGroupsResponse,
    MerchantGroup,
    TransactionSummary,
    BulkCategorizeRequest,
    BulkCategorizeResponse,
    UnextractedAccountInfo,
    UnextractedAccountsResponse,
    ExtractMerchantsResponse,
)
from app.repositories.merchant_repo import MerchantRepository
from app.repositories.transaction_repo import TransactionRepository
from app.repositories.account_repo import AccountRepository
from app.utils.merchant_normalizer import MerchantNormalizer
from typing import Optional
import uuid

router = APIRouter(prefix="/merchants", tags=["Merchants"])


def _build_merchant_response(merchant, db: Session) -> MerchantResponse:
    """Build merchant response with category info"""
    category_info = None
    if merchant.category_id:
        category = db.get(Category, merchant.category_id)
        if category:
            category_info = CategoryInfo(id=category.id, name=category.name)

    return MerchantResponse(
        id=merchant.id,
        user_id=merchant.user_id,
        normalized_name=merchant.normalized_name,
        patterns=merchant.patterns,
        category_id=merchant.category_id,
        fuzzy_threshold=merchant.fuzzy_threshold,
        is_public=merchant.is_public,
        usage_count=merchant.usage_count,
        category=category_info,
        created_at=merchant.created_at,
        updated_at=merchant.updated_at
    )


@router.post("", response_model=MerchantResponse, status_code=status.HTTP_201_CREATED)
def create_merchant(
    merchant_data: MerchantCreate,
    apply_to_existing: bool = Query(default=True, description="Apply mapping to existing transactions"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Create a new merchant mapping"""
    # Check if merchant with this name already exists
    existing = MerchantRepository.get_by_normalized_name(
        db, current_user.id, merchant_data.normalized_name
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Merchant '{merchant_data.normalized_name}' already exists"
        )

    merchant = MerchantRepository.create(db, current_user.id, merchant_data)

    # Apply to existing transactions if requested
    if apply_to_existing:
        updated_count = MerchantRepository.apply_mapping_to_transactions(
            db, current_user.id, merchant
        )

    return _build_merchant_response(merchant, db)


@router.get("", response_model=MerchantListResponse)
def get_merchants(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get all merchant mappings for current user"""
    merchants, total = MerchantRepository.get_all(
        db, current_user.id, page, limit, search
    )

    items = [_build_merchant_response(m, db) for m in merchants]

    return MerchantListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit
    )


@router.get("/unmapped", response_model=UnmappedMerchantsResponse)
def get_unmapped_merchants(
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get merchants from transactions that don't have mappings yet"""
    unmapped = MerchantRepository.get_unmapped_merchants(db, current_user.id, limit)

    return UnmappedMerchantsResponse(
        items=unmapped,
        total=len(unmapped)
    )


@router.get("/normalize")
def normalize_merchant_name(
    description: str = Query(..., description="Transaction description to normalize"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Normalize a merchant name from transaction description"""
    normalized = MerchantNormalizer.normalize(description)

    # Check if we have an existing mapping
    match = MerchantRepository.find_match(db, current_user.id, description)

    return {
        "original": description,
        "normalized": normalized,
        "existing_match": {
            "merchant_id": str(match[0].id),
            "normalized_name": match[0].normalized_name,
            "category_id": str(match[0].category_id) if match[0].category_id else None,
            "match_score": match[1],
            "matched_pattern": match[2]
        } if match else None
    }


@router.get("/suggestions", response_model=MerchantSuggestionsResponse)
async def get_category_suggestions(
    merchant_name: str = Query(..., description="Merchant name to get suggestions for"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get AI-powered category suggestions for a merchant"""
    from app.services.gemini_service import GeminiService
    from sqlmodel import select

    # Get user's categories
    categories = db.exec(
        select(Category).where(Category.user_id == current_user.id)
    ).all()

    category_names = [c.name for c in categories]

    # Use Gemini to suggest category
    try:
        gemini = GeminiService()
        suggestion = await gemini.suggest_category(merchant_name, category_names)

        suggestions = []
        if suggestion:
            # Find matching category
            matching_cat = next(
                (c for c in categories if c.name.lower() == suggestion.lower()),
                None
            )
            suggestions.append(MerchantSuggestion(
                category_name=suggestion,
                category_id=matching_cat.id if matching_cat else None,
                confidence=0.85,
                reasoning=f"Based on merchant name analysis"
            ))

        return MerchantSuggestionsResponse(
            merchant_name=merchant_name,
            suggestions=suggestions
        )
    except Exception as e:
        # Return empty suggestions if AI fails
        return MerchantSuggestionsResponse(
            merchant_name=merchant_name,
            suggestions=[]
        )


@router.get("/{merchant_id}", response_model=MerchantResponse)
def get_merchant(
    merchant_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get a specific merchant mapping"""
    merchant = MerchantRepository.get_by_id(db, merchant_id, current_user.id)

    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )

    return _build_merchant_response(merchant, db)


@router.put("/{merchant_id}", response_model=MerchantResponse)
def update_merchant(
    merchant_id: uuid.UUID,
    update_data: MerchantUpdate,
    apply_to_existing: bool = Query(default=False, description="Apply updated mapping to existing transactions"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Update a merchant mapping"""
    merchant = MerchantRepository.get_by_id(db, merchant_id, current_user.id)

    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )

    # Check for duplicate name if updating normalized_name
    if update_data.normalized_name and update_data.normalized_name != merchant.normalized_name:
        existing = MerchantRepository.get_by_normalized_name(
            db, current_user.id, update_data.normalized_name
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Merchant '{update_data.normalized_name}' already exists"
            )

    merchant = MerchantRepository.update(db, merchant, update_data)

    # Apply to existing transactions if requested
    if apply_to_existing:
        MerchantRepository.apply_mapping_to_transactions(
            db, current_user.id, merchant
        )

    return _build_merchant_response(merchant, db)


@router.delete("/{merchant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_merchant(
    merchant_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Delete a merchant mapping"""
    merchant = MerchantRepository.get_by_id(db, merchant_id, current_user.id)

    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )

    MerchantRepository.delete(db, merchant)
    return None


@router.post("/{merchant_id}/apply")
def apply_merchant_mapping(
    merchant_id: uuid.UUID,
    update_category: bool = Query(default=True, description="Also update category for matched transactions"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Apply a merchant mapping to all matching transactions"""
    merchant = MerchantRepository.get_by_id(db, merchant_id, current_user.id)

    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )

    updated_count = MerchantRepository.apply_mapping_to_transactions(
        db, current_user.id, merchant, update_category
    )

    return {
        "message": f"Applied mapping to {updated_count} transactions",
        "transactions_updated": updated_count
    }


@router.get("/uncategorized/groups", response_model=UncategorizedGroupsResponse)
def get_uncategorized_groups(
    include_transactions: bool = Query(default=False, description="Include full transaction details"),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Get uncategorized transactions grouped by merchant name.
    This endpoint helps users see all transactions that need categorization,
    grouped by the extracted merchant name for easy bulk categorization.
    """
    groups_data = TransactionRepository.get_uncategorized_grouped_by_merchant(
        db, current_user.id, include_transactions, limit
    )

    # Convert to response models
    groups = []
    total_transactions = 0

    for g in groups_data:
        transactions = []
        if include_transactions and g['transactions']:
            transactions = [
                TransactionSummary(
                    id=tx['id'],
                    transaction_date=tx['transaction_date'],
                    amount=tx['amount'],
                    description=tx['description'],
                    account_id=tx['account_id'],
                    account_name=tx.get('account_name')
                )
                for tx in g['transactions']
            ]

        groups.append(MerchantGroup(
            merchant_name=g['merchant_name'],
            transaction_count=g['transaction_count'],
            total_amount=g['total_amount'],
            first_date=g['first_date'],
            last_date=g['last_date'],
            transactions=transactions,
            sample_descriptions=g['sample_descriptions']
        ))
        total_transactions += g['transaction_count']

    return UncategorizedGroupsResponse(
        groups=groups,
        total_groups=len(groups),
        total_transactions=total_transactions
    )


@router.post("/uncategorized/categorize", response_model=BulkCategorizeResponse)
def bulk_categorize_merchant(
    request: BulkCategorizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Categorize all uncategorized transactions with a specific merchant name.
    Optionally creates a merchant mapping for future automatic categorization.
    """
    # Validate category exists
    category = db.get(Category, request.category_id)
    if not category or category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Categorize existing transactions
    updated_count = TransactionRepository.categorize_by_merchant_name(
        db, current_user.id, request.merchant_name, request.category_id
    )

    merchant_created = False
    merchant_id = None

    # Create merchant mapping if requested
    if request.create_mapping:
        # Check if mapping already exists
        existing = MerchantRepository.get_by_normalized_name(
            db, current_user.id, request.merchant_name
        )

        if not existing:
            # Create new merchant mapping
            merchant_data = MerchantCreate(
                normalized_name=request.merchant_name,
                patterns=request.patterns if request.patterns else [request.merchant_name],
                category_id=request.category_id,
                fuzzy_threshold=0.85
            )
            merchant = MerchantRepository.create(db, current_user.id, merchant_data)
            merchant_created = True
            merchant_id = merchant.id
        else:
            # Update existing mapping's category
            existing.category_id = request.category_id
            if request.patterns:
                existing.patterns = list(set(existing.patterns + request.patterns))
            db.add(existing)
            db.commit()
            merchant_id = existing.id

    return BulkCategorizeResponse(
        transactions_updated=updated_count,
        merchant_created=merchant_created,
        merchant_id=merchant_id
    )


@router.get("/extract/accounts", response_model=UnextractedAccountsResponse)
def get_accounts_with_unextracted_merchants(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Get list of accounts that have transactions without extracted merchant names.
    Useful for showing which accounts need merchant re-extraction.
    """
    accounts_data = TransactionRepository.get_unextracted_counts_by_account(
        db, current_user.id
    )

    accounts = [
        UnextractedAccountInfo(
            account_id=a['account_id'],
            account_name=a['account_name'],
            bank_name=a['bank_name'],
            count=a['count']
        )
        for a in accounts_data
    ]

    total = sum(a['count'] for a in accounts_data)

    return UnextractedAccountsResponse(
        accounts=accounts,
        total_unextracted=total
    )


@router.post("/extract/{account_id}", response_model=ExtractMerchantsResponse)
def extract_merchants_for_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Re-run merchant extraction for all transactions in an account that don't have merchant names.
    Uses AI to generate a regex pattern specific to this bank's transaction format.
    """
    from app.services.gemini_service import gemini_service

    # Verify account belongs to user
    account = AccountRepository.get_by_id(db, account_id, current_user.id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Get transactions without merchant names
    transactions = TransactionRepository.get_transactions_without_merchant_by_account(
        db, current_user.id, account_id
    )

    if not transactions:
        return ExtractMerchantsResponse(
            transactions_updated=0,
            regex_used=None,
            bank_name=account.bank_name
        )

    # Collect unique descriptions
    descriptions = list(set(tx.description for tx in transactions if tx.description))

    if not descriptions:
        return ExtractMerchantsResponse(
            transactions_updated=0,
            regex_used=None,
            bank_name=account.bank_name
        )

    # Ask Gemini for a regex pattern specific to this bank
    bank_name = account.bank_name or account.name
    regex_result = gemini_service.get_merchant_extraction_regex(descriptions, bank_name)

    if not regex_result or 'regex' not in regex_result:
        # Fallback to normalizer
        updates = {}
        for tx in transactions:
            if tx.description:
                merchant = MerchantNormalizer.normalize(tx.description)
                if merchant:
                    updates[tx.id] = merchant

        updated_count = TransactionRepository.bulk_update_merchant_names(db, updates)
        return ExtractMerchantsResponse(
            transactions_updated=updated_count,
            regex_used=None,
            bank_name=bank_name
        )

    # Apply the regex
    regex_pattern = regex_result['regex']
    all_descriptions = [tx.description for tx in transactions]
    merchant_map = gemini_service.extract_merchants_batch(all_descriptions, regex_pattern)

    # Build updates dict mapping transaction_id -> merchant_name
    updates = {}
    for tx in transactions:
        if tx.description and tx.description in merchant_map:
            updates[tx.id] = merchant_map[tx.description]

    # Apply updates
    updated_count = TransactionRepository.bulk_update_merchant_names(db, updates)

    return ExtractMerchantsResponse(
        transactions_updated=updated_count,
        regex_used=regex_pattern,
        bank_name=bank_name
    )
