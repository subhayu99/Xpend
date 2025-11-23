from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlmodel import Session, select, func, desc
from app.db.session import get_session
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.recurring import RecurringRule, RecurringStatus, RecurringInterval
from app.services.recurring_detection import RecurringDetectionService
from app.schemas.recurring import (
    RecurringSuggestion,
    RecurringRuleResponse,
    RecurringListResponse,
    ConfirmRecurringRequest,
    DismissRecurringRequest,
)
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import calendar

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/recurring")
def get_recurring_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> RecurringListResponse:
    """
    Get recurring transactions with user verification status.
    Returns AI suggestions merged with user-confirmed/dismissed rules.
    """
    # Get AI-detected suggestions
    suggestions = RecurringDetectionService.detect_recurring(db, current_user.id)

    # Get user's saved recurring rules
    saved_rules = db.exec(
        select(RecurringRule).where(RecurringRule.user_id == current_user.id)
    ).all()

    # Create lookup by merchant name
    rules_by_merchant = {r.merchant_name: r for r in saved_rules}

    # Merge suggestions with saved rules
    merged_suggestions = []
    for s in suggestions:
        merchant = s['merchant']
        existing_rule = rules_by_merchant.get(merchant)

        suggestion = RecurringSuggestion(
            merchant=merchant,
            amount=s['amount'],
            amount_min=s['amount_min'],
            amount_max=s['amount_max'],
            is_variable_amount=s['is_variable_amount'],
            interval=s['interval'],
            confidence=s['confidence'],
            avg_days=s['avg_days'],
            std_days=s['std_days'],
            last_date=s['last_date'],
            next_date=s['next_date'],
            transaction_count=s['transaction_count'],
            transaction_ids=s.get('transaction_ids', []),
            transactions=s.get('transactions', []),
            example_tx_id=s['example_tx_id'],
            status=existing_rule.status if existing_rule else 'suggested',
            existing_rule_id=existing_rule.id if existing_rule else None,
            existing_rule_status=existing_rule.status if existing_rule else None,
        )

        # Only include suggestions that aren't dismissed
        if not existing_rule or existing_rule.status != RecurringStatus.DISMISSED:
            merged_suggestions.append(suggestion)

    # Get confirmed rules (might include ones not in current suggestions)
    confirmed_rules = [
        RecurringRuleResponse.model_validate(r)
        for r in saved_rules
        if r.status == RecurringStatus.CONFIRMED
    ]

    # Count dismissed
    dismissed_count = sum(1 for r in saved_rules if r.status == RecurringStatus.DISMISSED)

    return RecurringListResponse(
        suggestions=merged_suggestions,
        confirmed=confirmed_rules,
        dismissed_count=dismissed_count,
    )


@router.post("/recurring/confirm")
def confirm_recurring(
    request: ConfirmRecurringRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> RecurringRuleResponse:
    """Confirm a recurring suggestion as a valid recurring expense"""
    # Check if rule already exists
    existing = db.exec(
        select(RecurringRule).where(
            RecurringRule.user_id == current_user.id,
            RecurringRule.merchant_name == request.merchant_name
        )
    ).first()

    if existing:
        # Update existing rule
        existing.status = RecurringStatus.CONFIRMED
        existing.expected_amount = request.expected_amount
        existing.amount_min = request.amount_min
        existing.amount_max = request.amount_max
        existing.is_variable_amount = request.is_variable_amount
        existing.interval = request.interval
        existing.avg_days = request.avg_days
        existing.confidence = request.confidence
        existing.transaction_count = request.transaction_count
        if request.last_transaction_date:
            existing.last_transaction_date = datetime.fromisoformat(request.last_transaction_date)
        if request.next_expected_date:
            existing.next_expected_date = datetime.fromisoformat(request.next_expected_date)
        if request.category_id:
            existing.category_id = request.category_id
        existing.updated_at = datetime.utcnow()
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return RecurringRuleResponse.model_validate(existing)

    # Create new rule
    rule = RecurringRule(
        user_id=current_user.id,
        merchant_name=request.merchant_name,
        expected_amount=request.expected_amount,
        amount_min=request.amount_min,
        amount_max=request.amount_max,
        is_variable_amount=request.is_variable_amount,
        interval=request.interval,
        avg_days=request.avg_days,
        confidence=request.confidence,
        transaction_count=request.transaction_count,
        status=RecurringStatus.CONFIRMED,
        category_id=request.category_id,
    )

    if request.last_transaction_date:
        rule.last_transaction_date = datetime.fromisoformat(request.last_transaction_date)
    if request.next_expected_date:
        rule.next_expected_date = datetime.fromisoformat(request.next_expected_date)

    db.add(rule)
    db.commit()
    db.refresh(rule)

    return RecurringRuleResponse.model_validate(rule)


@router.post("/recurring/dismiss")
def dismiss_recurring(
    request: DismissRecurringRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Dismiss a recurring suggestion (mark as not recurring)"""
    # Check if rule already exists
    existing = db.exec(
        select(RecurringRule).where(
            RecurringRule.user_id == current_user.id,
            RecurringRule.merchant_name == request.merchant_name
        )
    ).first()

    if existing:
        existing.status = RecurringStatus.DISMISSED
        existing.updated_at = datetime.utcnow()
        db.add(existing)
    else:
        # Create a dismissed rule to remember the user's choice
        rule = RecurringRule(
            user_id=current_user.id,
            merchant_name=request.merchant_name,
            expected_amount=0,
            interval=RecurringInterval.MONTHLY,  # Default, doesn't matter for dismissed
            avg_days=30,
            status=RecurringStatus.DISMISSED,
        )
        db.add(rule)

    db.commit()

    return {"message": f"Dismissed recurring suggestion for '{request.merchant_name}'"}


@router.delete("/recurring/{rule_id}")
def delete_recurring_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Delete a recurring rule (resets to suggestion state)"""
    import uuid as uuid_module
    try:
        rule_uuid = uuid_module.UUID(rule_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid rule ID")

    rule = db.exec(
        select(RecurringRule).where(
            RecurringRule.id == rule_uuid,
            RecurringRule.user_id == current_user.id
        )
    ).first()

    if not rule:
        raise HTTPException(status_code=404, detail="Recurring rule not found")

    merchant_name = rule.merchant_name
    db.delete(rule)
    db.commit()

    return {"message": f"Deleted recurring rule for '{merchant_name}'"}

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
