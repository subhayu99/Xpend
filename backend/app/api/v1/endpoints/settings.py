from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlmodel import Session, select
from app.db.session import get_session
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.budget import Budget
from app.models.transfer import Transfer
from app.schemas.settings import UserProfile, UserProfileUpdate
from typing import Dict, Any
import json
from datetime import datetime

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("/profile", response_model=UserProfile)
def get_profile(
    current_user: User = Depends(get_current_user),
):
    """Get user profile settings"""
    return current_user

@router.put("/profile", response_model=UserProfile)
def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Update user profile"""
    if profile_data.name is not None:
        current_user.name = profile_data.name
    if profile_data.currency is not None:
        current_user.currency = profile_data.currency
    if profile_data.timezone is not None:
        current_user.timezone = profile_data.timezone
        
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/export/json")
def export_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Export all user data as JSON"""
    # Fetch all data
    accounts = db.exec(select(Account).where(Account.user_id == current_user.id)).all()
    transactions = db.exec(select(Transaction).where(Transaction.user_id == current_user.id)).all()
    categories = db.exec(select(Category).where(Category.user_id == current_user.id)).all()
    budgets = db.exec(select(Budget).where(Budget.user_id == current_user.id)).all()
    transfers = db.exec(select(Transfer).where(Transfer.user_id == current_user.id)).all()
    
    data = {
        "version": "1.0",
        "export_date": datetime.now().isoformat(),
        "user": {
            "email": current_user.email,
            "name": current_user.name,
            "currency": current_user.currency,
            "timezone": current_user.timezone
        },
        "accounts": [acc.dict() for acc in accounts],
        "categories": [cat.dict() for cat in categories],
        "transactions": [tx.dict() for tx in transactions],
        "budgets": [b.dict() for b in budgets],
        "transfers": [t.dict() for t in transfers]
    }
    
    # Convert UUIDs and dates to strings
    # Pydantic .dict() might keep them as objects. We need to ensure JSON serializability.
    # FastAPI will handle JSON response, but if we want to return a file download, we need to serialize manually.
    
    from fastapi.responses import Response
    
    # Custom encoder for UUID and Date
    class CustomEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (datetime, datetime.date)):
                return obj.isoformat()
            if isinstance(obj, uuid.UUID):
                return str(obj)
            return super().default(obj)
            
    import uuid
    import datetime as dt
    
    def json_serializer(obj):
        if isinstance(obj, (dt.datetime, dt.date)):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        raise TypeError(f"Type {type(obj)} not serializable")

    json_str = json.dumps(data, default=json_serializer, indent=2)
    
    return Response(
        content=json_str,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=finance_backup_{datetime.now().strftime('%Y%m%d')}.json"
        }
    )
