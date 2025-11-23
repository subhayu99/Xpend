from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.transaction import Transaction
    from app.models.category import Category
    from app.models.budget import Budget
    from app.models.merchant import Merchant

class User(SQLModel, table=True):
    """User model"""
    __tablename__ = "users"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    name: Optional[str] = Field(default=None, max_length=100)
    timezone: str = Field(default="Asia/Kolkata", max_length=50)
    currency: str = Field(default="INR", max_length=3)
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    accounts: list["Account"] = Relationship(back_populates="user")
    transactions: list["Transaction"] = Relationship(back_populates="user")
    categories: list["Category"] = Relationship(back_populates="user")
    merchants: list["Merchant"] = Relationship(back_populates="user")
