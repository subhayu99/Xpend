from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
import uuid
from typing import Optional

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    name: Optional[str] = None
    timezone: str = "Asia/Kolkata"
    currency: str = "INR"

class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(min_length=8, max_length=100)

class UserUpdate(BaseModel):
    """User update schema"""
    name: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None

class UserResponse(UserBase):
    """User response schema"""
    id: uuid.UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str

class Token(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenRefresh(BaseModel):
    """Token refresh schema"""
    refresh_token: str
