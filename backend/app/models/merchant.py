from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.category import Category

class Merchant(SQLModel, table=True):
    """
    Merchant model for storing merchant mappings.
    Maps messy merchant names from bank statements to normalized names.
    """
    __tablename__ = "merchants"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)

    # Normalized merchant name (clean version)
    normalized_name: str = Field(max_length=255, index=True)

    # Patterns that match this merchant (stored as JSON array)
    # e.g., ["SWIGGY*", "Swiggy*", "SWIGGY DELHI"]
    patterns: List[str] = Field(default=[], sa_column=Column(JSON))

    # Default category for this merchant
    category_id: Optional[uuid.UUID] = Field(default=None, foreign_key="categories.id", index=True)

    # Fuzzy matching threshold (0.0 to 1.0)
    fuzzy_threshold: float = Field(default=0.85)

    # Whether this mapping is shared globally (community contribution)
    is_public: bool = Field(default=False)

    # Usage tracking
    usage_count: int = Field(default=0)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: "User" = Relationship(back_populates="merchants")
    category: Optional["Category"] = Relationship()
