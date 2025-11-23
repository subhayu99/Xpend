from pydantic import BaseModel, EmailStr
from typing import Optional

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None

class UserProfile(BaseModel):
    name: str
    email: EmailStr
    currency: str
    timezone: str
    
    class Config:
        from_attributes = True

class AISettingsUpdate(BaseModel):
    api_key: Optional[str] = None
    model: Optional[str] = None

class AISettings(BaseModel):
    provider: str = "gemini"
    model: str = "gemini-pro"
    has_custom_key: bool = False
