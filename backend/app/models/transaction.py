from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from enum import Enum
import uuid

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.account import Account
    from app.models.category import Category

class TransactionType(str, Enum):
    """Transaction type enum"""
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"

class Transaction(SQLModel, table=True):
    """Transaction model"""
    __tablename__ = "transactions"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    account_id: uuid.UUID = Field(foreign_key="accounts.id", index=True)
    category_id: Optional[uuid.UUID] = Field(default=None, foreign_key="categories.id", index=True)
    
    amount: float = Field(description="Transaction amount")
    description: str = Field(max_length=255, description="Original description from bank statement")
    merchant_name: Optional[str] = Field(default=None, max_length=100, description="Cleaned merchant name")
    transaction_date: datetime = Field(index=True)
    transaction_type: TransactionType = Field(default=TransactionType.EXPENSE)
    
    # Metadata for tracking source
    source_file: Optional[str] = Field(default=None, max_length=255)
    external_id: Optional[str] = Field(default=None, max_length=100, description="ID from the bank if available")
    transaction_hash: Optional[str] = Field(default=None, max_length=64, index=True, description="Hash to prevent duplicates")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: "User" = Relationship(back_populates="transactions")
    account: "Account" = Relationship(back_populates="transactions")
    category: Optional["Category"] = Relationship(back_populates="transactions")
