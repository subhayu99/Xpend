from sqlmodel import Session, select, func
from app.models.account import Account
from app.models.transaction import Transaction, TransactionType
from app.schemas.account import AccountCreate, AccountUpdate
from typing import List, Optional
import uuid

class AccountRepository:
    """Repository for account operations"""
    
    @staticmethod
    def create(db: Session, user_id: uuid.UUID, account_data: AccountCreate) -> Account:
        """Create a new account"""
        account = Account(
            user_id=user_id,
            **account_data.model_dump()
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        return account
    
    @staticmethod
    def get_by_id(db: Session, account_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Account]:
        """Get account by ID for a specific user"""
        return db.exec(
            select(Account).where(
                Account.id == account_id,
                Account.user_id == user_id
            )
        ).first()
    
    @staticmethod
    def get_all(db: Session, user_id: uuid.UUID, include_inactive: bool = False) -> List[Account]:
        """Get all accounts for a user"""
        query = select(Account).where(Account.user_id == user_id)
        
        if not include_inactive:
            query = query.where(Account.is_active == True)
        
        return db.exec(query).all()
    
    @staticmethod
    def update(db: Session, account: Account, update_data: AccountUpdate) -> Account:
        """Update an account"""
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(account, field, value)
        
        db.add(account)
        db.commit()
        db.refresh(account)
        return account
    
    @staticmethod
    def delete(db: Session, account: Account) -> None:
        """Soft delete an account"""
        account.is_active = False
        db.add(account)
        db.commit()
    
    @staticmethod
    def calculate_balance(db: Session, account_id: uuid.UUID) -> float:
        """
        Calculate current balance for an account.
        Formula: Opening Balance + Sum(INCOME) - Sum(EXPENSE)
        Note: TRANSFER transactions are treated as EXPENSE (outgoing) from this account
        """
        account = db.get(Account, account_id)
        if not account:
            return 0.0

        opening_balance = account.opening_balance or 0.0

        # Sum all INCOME transactions for this account
        income_result = db.exec(
            select(func.coalesce(func.sum(Transaction.amount), 0.0)).where(
                Transaction.account_id == account_id,
                Transaction.transaction_type == TransactionType.INCOME
            )
        ).first()
        total_income = float(income_result) if income_result else 0.0

        # Sum all EXPENSE transactions for this account
        expense_result = db.exec(
            select(func.coalesce(func.sum(Transaction.amount), 0.0)).where(
                Transaction.account_id == account_id,
                Transaction.transaction_type == TransactionType.EXPENSE
            )
        ).first()
        total_expense = float(expense_result) if expense_result else 0.0

        # Sum all TRANSFER transactions (outgoing from this account)
        transfer_result = db.exec(
            select(func.coalesce(func.sum(Transaction.amount), 0.0)).where(
                Transaction.account_id == account_id,
                Transaction.transaction_type == TransactionType.TRANSFER
            )
        ).first()
        total_transfers = float(transfer_result) if transfer_result else 0.0

        # Current Balance = Opening Balance + Income + Expenses + Transfers
        # Note: Expenses and Transfers are already stored as NEGATIVE values
        current_balance = opening_balance + total_income + total_expense + total_transfers

        return round(current_balance, 2)

    @staticmethod
    def get_balance_breakdown(db: Session, account_id: uuid.UUID) -> dict:
        """
        Get detailed balance breakdown for an account.
        Useful for debugging and detailed account views.
        """
        account = db.get(Account, account_id)
        if not account:
            return {}

        opening_balance = account.opening_balance or 0.0

        # Sum all INCOME transactions
        income_result = db.exec(
            select(func.coalesce(func.sum(Transaction.amount), 0.0)).where(
                Transaction.account_id == account_id,
                Transaction.transaction_type == TransactionType.INCOME
            )
        ).first()
        total_income = float(income_result) if income_result else 0.0

        # Sum all EXPENSE transactions
        expense_result = db.exec(
            select(func.coalesce(func.sum(Transaction.amount), 0.0)).where(
                Transaction.account_id == account_id,
                Transaction.transaction_type == TransactionType.EXPENSE
            )
        ).first()
        total_expense = float(expense_result) if expense_result else 0.0

        # Sum all TRANSFER transactions
        transfer_result = db.exec(
            select(func.coalesce(func.sum(Transaction.amount), 0.0)).where(
                Transaction.account_id == account_id,
                Transaction.transaction_type == TransactionType.TRANSFER
            )
        ).first()
        total_transfers = float(transfer_result) if transfer_result else 0.0

        # Count transactions
        transaction_count = db.exec(
            select(func.count(Transaction.id)).where(
                Transaction.account_id == account_id
            )
        ).first() or 0

        # Note: Expenses and Transfers are already stored as NEGATIVE values
        current_balance = opening_balance + total_income + total_expense + total_transfers

        return {
            "opening_balance": round(opening_balance, 2),
            "total_income": round(total_income, 2),
            "total_expense": round(total_expense, 2),
            "total_transfers": round(total_transfers, 2),
            "current_balance": round(current_balance, 2),
            "transaction_count": transaction_count
        }
