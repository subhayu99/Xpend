from sqlmodel import SQLModel, Field, Relationship
from datetime import date, datetime
from typing import Optional, TYPE_CHECKING
from enum import Enum
import uuid

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.transaction import Transaction

class AccountType(str, Enum):
    """Account type enum"""
    SAVINGS = "savings"
    CURRENT = "current"
    CREDIT_CARD = "credit_card"
    WALLET = "wallet"

class Account(SQLModel, table=True):
    """Account model"""
    __tablename__ = "accounts"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=100)
    bank_name: Optional[str] = Field(default=None, max_length=100)
    account_type: AccountType = Field(default=AccountType.SAVINGS)
    last_4_digits: Optional[str] = Field(default=None, max_length=4)
    opening_balance: float = Field(default=0.0)
    opening_balance_date: Optional[date] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: "User" = Relationship(back_populates="accounts")
    transactions: list["Transaction"] = Relationship(back_populates="account")
