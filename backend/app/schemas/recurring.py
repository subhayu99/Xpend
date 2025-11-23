from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class RecurringStatus(str, Enum):
    SUGGESTED = "suggested"
    CONFIRMED = "confirmed"
    DISMISSED = "dismissed"


class RecurringInterval(str, Enum):
    WEEKLY = "Weekly"
    BI_WEEKLY = "Bi-weekly"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    YEARLY = "Yearly"


class RecurringRuleCreate(BaseModel):
    """Create a recurring rule from a suggestion"""
    merchant_name: str
    expected_amount: float
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    is_variable_amount: bool = False
    interval: RecurringInterval
    avg_days: float
    confidence: float = 0.0
    last_transaction_date: Optional[datetime] = None
    next_expected_date: Optional[datetime] = None
    transaction_count: int = 0
    category_id: Optional[uuid.UUID] = None
    status: RecurringStatus = RecurringStatus.SUGGESTED


class RecurringRuleUpdate(BaseModel):
    """Update a recurring rule"""
    status: Optional[RecurringStatus] = None
    category_id: Optional[uuid.UUID] = None
    notify_before_days: Optional[int] = None
    is_notification_enabled: Optional[bool] = None
    expected_amount: Optional[float] = None
    interval: Optional[RecurringInterval] = None


class RecurringRuleResponse(BaseModel):
    """Response for a recurring rule"""
    id: uuid.UUID
    user_id: uuid.UUID
    merchant_name: str
    expected_amount: float
    amount_min: Optional[float]
    amount_max: Optional[float]
    is_variable_amount: bool
    interval: RecurringInterval
    avg_days: float
    status: RecurringStatus
    confidence: float
    last_transaction_date: Optional[datetime]
    next_expected_date: Optional[datetime]
    transaction_count: int
    category_id: Optional[uuid.UUID]
    notify_before_days: int
    is_notification_enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecurringSuggestion(BaseModel):
    """AI-detected recurring pattern (not yet saved)"""
    merchant: str
    amount: float
    amount_min: float
    amount_max: float
    is_variable_amount: bool
    interval: str
    confidence: float
    avg_days: float
    std_days: float
    last_date: str
    next_date: str
    transaction_count: int
    transaction_ids: List[str] = []
    transactions: List[Dict[str, Any]] = []
    example_tx_id: str
    status: str = "suggested"
    # Whether this suggestion already has a saved rule
    existing_rule_id: Optional[uuid.UUID] = None
    existing_rule_status: Optional[RecurringStatus] = None


class RecurringListResponse(BaseModel):
    """Response for recurring list endpoint"""
    suggestions: List[RecurringSuggestion]
    confirmed: List[RecurringRuleResponse]
    dismissed_count: int


class ConfirmRecurringRequest(BaseModel):
    """Request to confirm a recurring suggestion"""
    merchant_name: str
    expected_amount: float
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    is_variable_amount: bool = False
    interval: RecurringInterval
    avg_days: float
    confidence: float = 0.0
    last_transaction_date: Optional[str] = None
    next_expected_date: Optional[str] = None
    transaction_count: int = 0
    category_id: Optional[uuid.UUID] = None


class DismissRecurringRequest(BaseModel):
    """Request to dismiss a recurring suggestion"""
    merchant_name: str
