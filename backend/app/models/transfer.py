from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
import uuid

class Transfer(SQLModel, table=True):
    """Model to track self-transfers between user's accounts"""
    __tablename__ = "transfers"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    
    # The two linked transactions
    debit_transaction_id: uuid.UUID = Field(foreign_key="transactions.id", index=True)
    credit_transaction_id: uuid.UUID = Field(foreign_key="transactions.id", index=True)
    
    amount: float = Field(description="Transfer amount")
    transfer_date: datetime = Field(description="Date of transfer")
    
    # Confidence score for auto-detected transfers
    confidence_score: Optional[float] = Field(default=None, description="0-1 score for auto-detection")
    is_confirmed: bool = Field(default=False, description="User confirmed this transfer")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
