from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid
from app.models.transaction import TransactionType

class TransactionBase(BaseModel):
    """Base transaction schema"""
    amount: float
    description: str = Field(min_length=1, max_length=255)
    merchant_name: Optional[str] = Field(default=None, max_length=100)
    transaction_date: datetime
    transaction_type: TransactionType = TransactionType.EXPENSE
    category_id: Optional[uuid.UUID] = None
    account_id: uuid.UUID

class TransactionCreate(TransactionBase):
    """Transaction creation schema"""
    pass

class TransactionUpdate(BaseModel):
    """Transaction update schema"""
    amount: Optional[float] = None
    description: Optional[str] = Field(default=None, min_length=1, max_length=255)
    merchant_name: Optional[str] = None
    transaction_date: Optional[datetime] = None
    transaction_type: Optional[TransactionType] = None
    category_id: Optional[uuid.UUID] = None
    account_id: Optional[uuid.UUID] = None

class TransactionResponse(TransactionBase):
    """Transaction response schema"""
    id: uuid.UUID
    user_id: uuid.UUID
    source_file: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TransactionListResponse(BaseModel):
    """Paginated transaction list response"""
    items: list[TransactionResponse]
    total: int
    page: int
    limit: int
