from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
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


class RecurringRule(SQLModel, table=True):
    """
    User-verified recurring transaction rules.
    Stores both AI-suggested and user-confirmed recurring patterns.
    """
    __tablename__ = "recurring_rules"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)

    # Merchant identification
    merchant_name: str = Field(index=True)

    # Amount info
    expected_amount: float
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    is_variable_amount: bool = False

    # Interval info
    interval: RecurringInterval
    avg_days: float

    # Status
    status: RecurringStatus = Field(default=RecurringStatus.SUGGESTED)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    # Tracking
    last_transaction_date: Optional[datetime] = None
    next_expected_date: Optional[datetime] = None
    transaction_count: int = Field(default=0)

    # Optional category assignment
    category_id: Optional[uuid.UUID] = Field(default=None, foreign_key="categories.id")

    # Notifications
    notify_before_days: int = Field(default=3)  # Notify X days before expected
    is_notification_enabled: bool = Field(default=True)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
