from sqlmodel import Session, select
from app.models.account import Account
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
        """Calculate current balance for an account"""
        # Will implement when we have transactions
        # For now, return opening balance
        account = db.get(Account, account_id)
        return account.opening_balance if account else 0.0
