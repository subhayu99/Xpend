from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func, desc
from app.db.session import get_session
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.transaction import Transaction
from app.models.category import Category
from app.services.recurring_detection import RecurringDetectionService
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import calendar

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


@router.get("/spending-by-category", response_model=List[Dict[str, Any]])
def get_spending_by_category(
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get spending breakdown by category for a specific month"""
    if not month:
        month = datetime.now().month
    if not year:
        year = datetime.now().year

    start_date = datetime(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = datetime(year, month, last_day, 23, 59, 59)

    # Get categories for this user
    categories = db.exec(
        select(Category).where(Category.user_id == current_user.id)
    ).all()
    category_map = {str(c.id): {"name": c.name, "icon": c.icon, "color": c.color} for c in categories}

    # Aggregate spending by category
    results = db.exec(
        select(Transaction.category_id, func.sum(Transaction.amount).label("total"))
        .where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == 'expense',
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        )
        .group_by(Transaction.category_id)
        .order_by(func.sum(Transaction.amount).asc())
    ).all()

    data = []
    for r in results:
        cat_id = str(r[0]) if r[0] else None
        cat_info = category_map.get(cat_id, {"name": "Uncategorized", "icon": None, "color": "#808080"})
        data.append({
            "category_id": cat_id,
            "category_name": cat_info["name"],
            "icon": cat_info["icon"],
            "color": cat_info["color"] or "#808080",
            "amount": abs(r[1]) if r[1] else 0
        })

    return data


@router.get("/monthly-trends", response_model=List[Dict[str, Any]])
def get_monthly_trends(
    months: int = Query(default=6, ge=1, le=24),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get monthly income vs expenses for the last N months"""
    data = []
    today = datetime.now()

    for i in range(months - 1, -1, -1):
        # Calculate month and year for i months ago
        target_date = today - timedelta(days=30 * i)
        month = target_date.month
        year = target_date.year

        start_date = datetime(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = datetime(year, month, last_day, 23, 59, 59)

        # Get income
        income_result = db.exec(
            select(func.coalesce(func.sum(Transaction.amount), 0.0)).where(
                Transaction.user_id == current_user.id,
                Transaction.transaction_type == 'income',
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date
            )
        ).first()
        income = float(income_result) if income_result else 0.0

        # Get expenses
        expense_result = db.exec(
            select(func.coalesce(func.sum(Transaction.amount), 0.0)).where(
                Transaction.user_id == current_user.id,
                Transaction.transaction_type == 'expense',
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date
            )
        ).first()
        expenses = abs(float(expense_result)) if expense_result else 0.0

        month_name = start_date.strftime("%b %Y")
        data.append({
            "month": month_name,
            "income": income,
            "expenses": expenses,
            "savings": income - expenses
        })

    return data


@router.get("/daily-spending", response_model=List[Dict[str, Any]])
def get_daily_spending(
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get daily spending for a specific month"""
    if not month:
        month = datetime.now().month
    if not year:
        year = datetime.now().year

    last_day = calendar.monthrange(year, month)[1]
    data = []

    for day in range(1, last_day + 1):
        date = datetime(year, month, day)

        result = db.exec(
            select(func.coalesce(func.sum(Transaction.amount), 0.0)).where(
                Transaction.user_id == current_user.id,
                Transaction.transaction_type == 'expense',
                func.date(Transaction.transaction_date) == date.date()
            )
        ).first()

        amount = abs(float(result)) if result else 0.0
        data.append({
            "day": day,
            "date": date.strftime("%Y-%m-%d"),
            "amount": amount
        })

    return data


@router.get("/summary", response_model=Dict[str, Any])
def get_summary(
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get summary statistics for a specific month"""
    if not month:
        month = datetime.now().month
    if not year:
        year = datetime.now().year

    start_date = datetime(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = datetime(year, month, last_day, 23, 59, 59)

    # Total income
    income_result = db.exec(
        select(func.coalesce(func.sum(Transaction.amount), 0.0)).where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == 'income',
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        )
    ).first()
    total_income = float(income_result) if income_result else 0.0

    # Total expenses
    expense_result = db.exec(
        select(func.coalesce(func.sum(Transaction.amount), 0.0)).where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == 'expense',
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        )
    ).first()
    total_expenses = abs(float(expense_result)) if expense_result else 0.0

    # Transaction count
    tx_count = db.exec(
        select(func.count(Transaction.id)).where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        )
    ).first() or 0

    # Average transaction
    avg_result = db.exec(
        select(func.avg(Transaction.amount)).where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == 'expense',
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        )
    ).first()
    avg_expense = abs(float(avg_result)) if avg_result else 0.0

    # Largest expense
    max_result = db.exec(
        select(func.min(Transaction.amount)).where(  # min because expenses are negative
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == 'expense',
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        )
    ).first()
    largest_expense = abs(float(max_result)) if max_result else 0.0

    return {
        "month": month,
        "year": year,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_savings": total_income - total_expenses,
        "transaction_count": tx_count,
        "avg_expense": round(avg_expense, 2),
        "largest_expense": largest_expense
    }
