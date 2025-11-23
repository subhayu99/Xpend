from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
import uuid

class Budget(SQLModel, table=True):
    """Model for category budgets"""
    __tablename__ = "budgets"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    category_id: uuid.UUID = Field(foreign_key="categories.id", index=True)
    
    amount: float = Field(description="Budget amount for the period")
    period: str = Field(default="monthly", description="Budget period: monthly, quarterly, yearly")
    
    # For monthly budgets, track which month/year
    month: Optional[int] = Field(default=None, description="Month (1-12) for monthly budgets")
    year: Optional[int] = Field(default=None, description="Year for budgets")
    
    is_active: bool = Field(default=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
