from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from app.db.session import get_session
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.account import Account
from typing import Optional
from datetime import datetime
import calendar
import io
import csv

router = APIRouter(prefix="/export", tags=["Export"])


@router.get("/transactions/csv")
def export_transactions_csv(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    account_id: Optional[str] = None,
    category_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Export transactions to CSV file"""
    # Build query
    query = select(Transaction).where(Transaction.user_id == current_user.id)

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

    if account_id:
        query = query.where(Transaction.account_id == account_id)

    if category_id:
        query = query.where(Transaction.category_id == category_id)

    query = query.order_by(Transaction.transaction_date.desc())

    transactions = db.exec(query).all()

    # Get category and account names
    categories = db.exec(select(Category).where(Category.user_id == current_user.id)).all()
    category_map = {str(c.id): c.name for c in categories}

    accounts = db.exec(select(Account).where(Account.user_id == current_user.id)).all()
    account_map = {str(a.id): a.name for a in accounts}

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        'Date', 'Description', 'Merchant', 'Amount', 'Type',
        'Category', 'Account', 'Reference'
    ])

    # Data rows
    for tx in transactions:
        writer.writerow([
            tx.transaction_date.strftime('%Y-%m-%d'),
            tx.description,
            tx.merchant_name or '',
            tx.amount,
            tx.transaction_type.value if tx.transaction_type else '',
            category_map.get(str(tx.category_id), '') if tx.category_id else '',
            account_map.get(str(tx.account_id), ''),
            tx.external_id or ''
        ])

    output.seek(0)

    filename = f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/monthly-report/csv")
def export_monthly_report_csv(
    month: int = Query(default=None),
    year: int = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Export monthly summary report to CSV"""
    if not month:
        month = datetime.now().month
    if not year:
        year = datetime.now().year

    start_date = datetime(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = datetime(year, month, last_day, 23, 59, 59)

    # Get transactions for this month
    transactions = db.exec(
        select(Transaction).where(
            Transaction.user_id == current_user.id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date
        ).order_by(Transaction.transaction_date.desc())
    ).all()

    # Get categories
    categories = db.exec(select(Category).where(Category.user_id == current_user.id)).all()
    category_map = {str(c.id): c.name for c in categories}

    # Get accounts
    accounts = db.exec(select(Account).where(Account.user_id == current_user.id)).all()
    account_map = {str(a.id): a.name for a in accounts}

    # Calculate totals
    total_income = sum(tx.amount for tx in transactions if tx.transaction_type and tx.transaction_type.value == 'income')
    total_expenses = sum(abs(tx.amount) for tx in transactions if tx.transaction_type and tx.transaction_type.value == 'expense')

    # Category breakdown
    category_totals = {}
    for tx in transactions:
        if tx.transaction_type and tx.transaction_type.value == 'expense' and tx.category_id:
            cat_name = category_map.get(str(tx.category_id), 'Uncategorized')
            category_totals[cat_name] = category_totals.get(cat_name, 0) + abs(tx.amount)

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Summary section
    month_name = datetime(year, month, 1).strftime('%B %Y')
    writer.writerow(['Monthly Report', month_name])
    writer.writerow([])
    writer.writerow(['Summary'])
    writer.writerow(['Total Income', total_income])
    writer.writerow(['Total Expenses', total_expenses])
    writer.writerow(['Net Savings', total_income - total_expenses])
    writer.writerow(['Transaction Count', len(transactions)])
    writer.writerow([])

    # Category breakdown
    writer.writerow(['Spending by Category'])
    writer.writerow(['Category', 'Amount'])
    for cat, amount in sorted(category_totals.items(), key=lambda x: -x[1]):
        writer.writerow([cat, amount])
    writer.writerow([])

    # Transaction details
    writer.writerow(['Transaction Details'])
    writer.writerow([
        'Date', 'Description', 'Merchant', 'Amount', 'Type',
        'Category', 'Account'
    ])

    for tx in transactions:
        writer.writerow([
            tx.transaction_date.strftime('%Y-%m-%d'),
            tx.description,
            tx.merchant_name or '',
            tx.amount,
            tx.transaction_type.value if tx.transaction_type else '',
            category_map.get(str(tx.category_id), '') if tx.category_id else '',
            account_map.get(str(tx.account_id), '')
        ])

    output.seek(0)

    filename = f"monthly_report_{year}_{month:02d}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
