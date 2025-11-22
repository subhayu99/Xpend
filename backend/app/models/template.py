from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, Dict, Any
import uuid
import json

class StatementTemplate(SQLModel, table=True):
    """Model to store bank statement parsing templates"""
    __tablename__ = "statement_templates"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=100, description="e.g., HDFC Savings CSV")
    bank_name: str = Field(max_length=100, index=True)
    file_type: str = Field(max_length=20)  # csv, xls, xlsx, pdf
    
    # JSON string storing the configuration
    # CSV/Excel: { "header_row": 1, "date_col": "Date", "amount_col": "Amount", "desc_col": "Narration", "date_format": "%d/%m/%Y" }
    # PDF: { "strategy": "regex", "patterns": {...} } or { "strategy": "ai_layout", ... }
    structure_json: str = Field(description="JSON configuration for parsing")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def structure(self) -> Dict[str, Any]:
        return json.loads(self.structure_json)
    
    @structure.setter
    def structure(self, value: Dict[str, Any]):
        self.structure_json = json.dumps(value)
