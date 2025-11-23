from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
import uuid


class MerchantBase(BaseModel):
    """Base merchant schema"""
    normalized_name: str = Field(min_length=1, max_length=255)
    patterns: List[str] = Field(default=[])
    category_id: Optional[uuid.UUID] = None
    fuzzy_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    is_public: bool = False


class MerchantCreate(MerchantBase):
    """Schema for creating a merchant mapping"""
    pass


class MerchantUpdate(BaseModel):
    """Schema for updating a merchant mapping"""
    normalized_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    patterns: Optional[List[str]] = None
    category_id: Optional[uuid.UUID] = None
    fuzzy_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    is_public: Optional[bool] = None


class CategoryInfo(BaseModel):
    """Category info in merchant response"""
    id: uuid.UUID
    name: str


class MerchantResponse(MerchantBase):
    """Merchant response schema"""
    id: uuid.UUID
    user_id: uuid.UUID
    usage_count: int
    category: Optional[CategoryInfo] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MerchantListResponse(BaseModel):
    """Paginated merchant list response"""
    items: List[MerchantResponse]
    total: int
    page: int
    limit: int


class UnmappedMerchantInfo(BaseModel):
    """Info about an unmapped merchant"""
    raw_name: str
    transaction_count: int
    total_amount: float
    first_seen: datetime
    last_seen: datetime
    sample_descriptions: List[str] = []


class UnmappedMerchantsResponse(BaseModel):
    """Response for unmapped merchants endpoint"""
    items: List[UnmappedMerchantInfo]
    total: int


class MerchantSuggestion(BaseModel):
    """AI-suggested category for a merchant"""
    category_name: str
    category_id: Optional[uuid.UUID] = None
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: Optional[str] = None


class MerchantSuggestionsResponse(BaseModel):
    """Response for merchant category suggestions"""
    merchant_name: str
    suggestions: List[MerchantSuggestion]


class MerchantMatch(BaseModel):
    """Result of fuzzy matching a merchant"""
    merchant_id: uuid.UUID
    normalized_name: str
    category_id: Optional[uuid.UUID]
    match_score: float
    matched_pattern: Optional[str] = None
