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


class TransactionSummary(BaseModel):
    """Summary of a transaction for grouping display"""
    id: uuid.UUID
    transaction_date: datetime
    amount: float
    description: str
    account_id: uuid.UUID
    account_name: Optional[str] = None


class MerchantGroup(BaseModel):
    """A group of transactions with the same merchant name (uncategorized)"""
    merchant_name: str
    transaction_count: int
    total_amount: float
    first_date: datetime
    last_date: datetime
    transactions: List[TransactionSummary] = []
    sample_descriptions: List[str] = []


class UncategorizedGroupsResponse(BaseModel):
    """Response for uncategorized transactions grouped by merchant"""
    groups: List[MerchantGroup]
    total_groups: int
    total_transactions: int


class BulkCategorizeRequest(BaseModel):
    """Request to categorize multiple merchants at once"""
    merchant_name: str
    category_id: uuid.UUID
    create_mapping: bool = True  # Create a merchant mapping for future transactions
    patterns: List[str] = []  # Additional patterns to match


class BulkCategorizeResponse(BaseModel):
    """Response for bulk categorization"""
    transactions_updated: int
    merchant_created: bool = False
    merchant_id: Optional[uuid.UUID] = None


class UnextractedAccountInfo(BaseModel):
    """Info about an account with unextracted transactions"""
    account_id: uuid.UUID
    account_name: str
    bank_name: Optional[str] = None
    count: int


class UnextractedAccountsResponse(BaseModel):
    """Response for accounts with unextracted merchants"""
    accounts: List[UnextractedAccountInfo]
    total_unextracted: int


class ExtractMerchantsResponse(BaseModel):
    """Response for merchant extraction"""
    transactions_updated: int
    regex_used: Optional[str] = None
    bank_name: Optional[str] = None
