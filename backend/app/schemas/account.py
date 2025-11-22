from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
import uuid
from app.models.account import AccountType

class AccountBase(BaseModel):
    """Base account schema"""
    name: str = Field(min_length=1, max_length=100)
    bank_name: Optional[str] = Field(default=None, max_length=100)
    account_type: AccountType = AccountType.SAVINGS
    last_4_digits: Optional[str] = Field(default=None, min_length=4, max_length=4)
    opening_balance: float = 0.0
    opening_balance_date: Optional[date] = None

class AccountCreate(AccountBase):
    """Account creation schema"""
    pass

class AccountUpdate(BaseModel):
    """Account update schema"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    bank_name: Optional[str] = None
    account_type: Optional[AccountType] = None
    last_4_digits: Optional[str] = Field(default=None, min_length=4, max_length=4)
    opening_balance: Optional[float] = None
    opening_balance_date: Optional[date] = None
    is_active: Optional[bool] = None

class AccountResponse(AccountBase):
    """Account response schema"""
    id: uuid.UUID
    user_id: uuid.UUID
    current_balance: float  # Calculated field
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
