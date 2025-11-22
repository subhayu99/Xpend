from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
from app.schemas.transaction import TransactionResponse

class DashboardSummary(BaseModel):
    total_balance: float
    monthly_income: float
    monthly_expense: float
    savings_rate: float

class CategorySpend(BaseModel):
    category_name: str
    amount: float
    color: str | None = None

class MonthlyTrend(BaseModel):
    month: str  # YYYY-MM
    income: float
    expense: float

class DashboardData(BaseModel):
    summary: DashboardSummary
    category_spend: List[CategorySpend]
    monthly_trend: List[MonthlyTrend]
    recent_transactions: List[TransactionResponse]
