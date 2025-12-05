from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func, desc, extract
from typing import List
from datetime import datetime, timedelta
from app.db.session import get_session
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.category import Category
from app.schemas.dashboard import DashboardData, DashboardSummary, CategorySpend, MonthlyTrend
from app.repositories.account_repo import AccountRepository

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("", response_model=DashboardData)
def get_dashboard_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Get aggregated data for the dashboard:
    - Total Balance
    - Monthly Income/Expense (Current Month)
    - Category Breakdown (Current Month)
    - Recent Transactions
    """
    
    # 1. Total Balance
    accounts = AccountRepository.get_all(db, current_user.id)
    total_balance = sum(AccountRepository.calculate_balance(db, acc.id) for acc in accounts)
    
    # 2. Current Month Date Range
    today = datetime.utcnow()
    start_of_month = datetime(today.year, today.month, 1)
    if today.month == 12:
        start_of_next_month = datetime(today.year + 1, 1, 1)
    else:
        start_of_next_month = datetime(today.year, today.month + 1, 1)
        
    # 3. Monthly Income & Expense
    # Filter transactions for current user and current month
    # We need to join with Account to filter by user_id
    base_query = select(Transaction).join(Account).where(
        Account.user_id == current_user.id,
        Transaction.transaction_date >= start_of_month,
        Transaction.transaction_date < start_of_next_month
    )
    
    income_query = base_query.where(Transaction.transaction_type == "income")
    expense_query = base_query.where(Transaction.transaction_type == "expense")
    
    monthly_income = db.exec(select(func.sum(Transaction.amount)).where(
        Transaction.id.in_(select(Transaction.id).join(Account).where(
            Account.user_id == current_user.id,
            Transaction.transaction_date >= start_of_month,
            Transaction.transaction_date < start_of_next_month,
            Transaction.transaction_type == "income"
        ))
    )).one() or 0.0
    
    monthly_expense = db.exec(select(func.sum(Transaction.amount)).where(
        Transaction.id.in_(select(Transaction.id).join(Account).where(
            Account.user_id == current_user.id,
            Transaction.transaction_date >= start_of_month,
            Transaction.transaction_date < start_of_next_month,
            Transaction.transaction_type == "expense"
        ))
    )).one() or 0.0
    
    # Ensure positive values for display logic if needed, but usually expense is stored as positive or negative depending on design.
    # Based on parser, expense is negative. Let's convert to positive for display if it's negative.
    # Checking parser logic: "amount = float(credit) - float(debit)". So expense is negative.
    # Let's return absolute values for dashboard summary usually.
    
    monthly_income = abs(monthly_income)
    monthly_expense = abs(monthly_expense)
    
    savings_rate = 0.0
    if monthly_income > 0:
        savings_rate = ((monthly_income - monthly_expense) / monthly_income) * 100
        
    summary = DashboardSummary(
        total_balance=total_balance,
        monthly_income=monthly_income,
        monthly_expense=monthly_expense,
        savings_rate=savings_rate
    )
    
    # 4. Category Spend (Current Month)
    # Group by category
    category_stats = db.exec(
        select(Category.id, Category.name, Category.color, func.sum(Transaction.amount))
        .join(Category, isouter=True)
        .join(Account)
        .where(
            Account.user_id == current_user.id,
            Transaction.transaction_date >= start_of_month,
            Transaction.transaction_date < start_of_next_month,
            Transaction.transaction_type == "expense"
        )
        .group_by(Category.id, Category.name, Category.color)
    ).all()
    
    category_spend = []
    for cat_id, name, color, amount in category_stats:
        category_spend.append(CategorySpend(
            category_id=cat_id,
            category_name=name or "Uncategorized",
            amount=abs(amount or 0.0),
            color=color
        ))
    
    # Sort by amount desc
    category_spend.sort(key=lambda x: x.amount, reverse=True)
        
    # 5. Monthly Trend (Last 6 months)
    monthly_trend = []
    
    # Generate last 6 month keys
    month_keys = []
    for i in range(5, -1, -1):
        # Manual year/month math to be precise
        year = today.year
        month = today.month - i
        while month <= 0:
            month += 12
            year -= 1
        month_keys.append(f"{year}-{month:02d}")
        
    # Fetch transactions for this range
    start_year = int(month_keys[0].split('-')[0])
    start_month = int(month_keys[0].split('-')[1])
    trend_start_date = datetime(start_year, start_month, 1)
    
    trend_txs = db.exec(
        select(Transaction)
        .join(Account)
        .where(
            Account.user_id == current_user.id,
            Transaction.transaction_date >= trend_start_date
        )
    ).all()
    
    trend_map = {k: {"income": 0.0, "expense": 0.0} for k in month_keys}
    
    for tx in trend_txs:
        month_key = tx.transaction_date.strftime("%Y-%m")
        if month_key in trend_map:
             if tx.transaction_type == "income":
                trend_map[month_key]["income"] += abs(tx.amount)
             else:
                trend_map[month_key]["expense"] += abs(tx.amount)
                
    monthly_trend = [
        MonthlyTrend(month=m, income=trend_map[m]["income"], expense=trend_map[m]["expense"])
        for m in month_keys
    ]
    
    
    # 6. Recent Transactions
    recent_txs = db.exec(
        select(Transaction)
        .join(Account)
        .where(Account.user_id == current_user.id)
        .order_by(desc(Transaction.transaction_date))
        .limit(5)
    ).all()
    
    return DashboardData(
        summary=summary,
        category_spend=category_spend,
        monthly_trend=monthly_trend,
        recent_transactions=recent_txs
    )
