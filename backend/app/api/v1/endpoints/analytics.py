from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func, desc
from app.db.session import get_session
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.transaction import Transaction
from app.services.recurring_detection import RecurringDetectionService
from typing import List, Dict, Any

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/recurring", response_model=List[Dict[str, Any]])
def get_recurring_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Detect potential recurring transactions (subscriptions, bills)"""
    return RecurringDetectionService.detect_recurring(db, current_user.id)

@router.get("/top-merchants", response_model=List[Dict[str, Any]])
def get_top_merchants(
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get top merchants by spending"""
    # Aggregate by merchant name
    results = db.exec(
        select(Transaction.merchant_name, func.sum(Transaction.amount).label("total"))
        .where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == 'expense',
            Transaction.merchant_name != None
        )
        .group_by(Transaction.merchant_name)
        .order_by(desc("total")) # Expenses are negative, so sum is negative. We want largest absolute value.
        # Actually, if expenses are negative, sum is negative. 
        # To get "top spending", we want the most negative values (smallest numbers).
        # So order by total ASC (e.g. -5000 before -100)
        .order_by(func.sum(Transaction.amount).asc())
        .limit(limit)
    ).all()
    
    return [
        {"merchant": r[0], "amount": abs(r[1])} 
        for r in results
    ]
