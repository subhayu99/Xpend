from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

class BudgetBase(BaseModel):
    category_id: uuid.UUID
    amount: float
    period: str = "monthly"
    month: Optional[int] = None
    year: Optional[int] = None
    is_active: bool = True

class BudgetCreate(BudgetBase):
    pass

class BudgetUpdate(BaseModel):
    amount: Optional[float] = None
    is_active: Optional[bool] = None

class BudgetResponse(BudgetBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class BudgetProgress(BudgetResponse):
    spent: float
    remaining: float
    percentage: float
