from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid

class CategoryBase(BaseModel):
    """Base category schema"""
    name: str = Field(min_length=1, max_length=100)
    type: str = Field(default="expense", pattern="^(income|expense)$")
    icon: Optional[str] = Field(default=None, max_length=50)
    color: Optional[str] = Field(default=None, max_length=20)

class CategoryCreate(CategoryBase):
    """Category creation schema"""
    pass

class CategoryUpdate(BaseModel):
    """Category update schema"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    type: Optional[str] = Field(default=None, pattern="^(income|expense)$")
    icon: Optional[str] = None
    color: Optional[str] = None

class CategoryResponse(CategoryBase):
    """Category response schema"""
    id: uuid.UUID
    user_id: uuid.UUID
    is_default: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
