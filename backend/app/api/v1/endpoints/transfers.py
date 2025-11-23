from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.db.session import get_session
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.transfer import Transfer
from app.models.transaction import Transaction
from app.services.transfer_detection import TransferDetectionService
from typing import List
import uuid
from pydantic import BaseModel

router = APIRouter(prefix="/transfers", tags=["Transfers"])

class TransferCreate(BaseModel):
    debit_transaction_id: str
    credit_transaction_id: str
    confidence_score: float = None

@router.get("/detect", response_model=List[dict])
def detect_potential_transfers(
    days_window: int = 2,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Detect potential self-transfers between user's accounts"""
    return TransferDetectionService.detect_potential_transfers(
        db, 
        current_user.id,
        days_window=days_window
    )

@router.post("", response_model=dict)
def create_transfer(
    transfer_data: TransferCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Link two transactions as a transfer"""
    try:
        transfer = TransferDetectionService.create_transfer(
            db,
            current_user.id,
            uuid.UUID(transfer_data.debit_transaction_id),
            uuid.UUID(transfer_data.credit_transaction_id),
            confidence_score=transfer_data.confidence_score,
            is_confirmed=True
        )
        return {"message": "Transfer created", "id": str(transfer.id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{transfer_id}")
def delete_transfer(
    transfer_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Unlink a transfer"""
    try:
        TransferDetectionService.delete_transfer(db, transfer_id, current_user.id)
        return {"message": "Transfer deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("", response_model=List[dict])
def get_all_transfers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get all confirmed transfers for user"""
    from sqlmodel import select
    transfers = db.exec(
        select(Transfer).where(Transfer.user_id == current_user.id)
    ).all()
    
    result = []
    for transfer in transfers:
        debit_tx = db.get(Transaction, transfer.debit_transaction_id)
        credit_tx = db.get(Transaction, transfer.credit_transaction_id)
        
        result.append({
            'id': str(transfer.id),
            'amount': transfer.amount,
            'transfer_date': transfer.transfer_date.isoformat(),
            'confidence_score': transfer.confidence_score,
            'is_confirmed': transfer.is_confirmed,
            'debit_transaction': {
                'id': str(debit_tx.id),
                'description': debit_tx.description,
                'account_id': str(debit_tx.account_id)
            } if debit_tx else None,
            'credit_transaction': {
                'id': str(credit_tx.id),
                'description': credit_tx.description,
                'account_id': str(credit_tx.account_id)
            } if credit_tx else None
        })
    
    return result
