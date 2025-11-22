from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.db.session import get_session
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.account import AccountCreate, AccountUpdate, AccountResponse
from app.repositories.account_repo import AccountRepository
from typing import List
import uuid

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    account_data: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Create a new account"""
    account = AccountRepository.create(db, current_user.id, account_data)
    
    # Create response with calculated balance
    account_dict = account.model_dump()
    account_dict['current_balance'] = AccountRepository.calculate_balance(db, account.id)
    
    return AccountResponse(**account_dict)

@router.get("", response_model=List[AccountResponse])
def get_accounts(
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get all accounts for current user"""
    accounts = AccountRepository.get_all(db, current_user.id, include_inactive)
    
    # Add current balance to each account
    response = []
    for account in accounts:
        account_dict = account.model_dump()
        account_dict['current_balance'] = AccountRepository.calculate_balance(db, account.id)
        response.append(AccountResponse(**account_dict))
    
    return response

@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get a specific account"""
    account = AccountRepository.get_by_id(db, account_id, current_user.id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    account_dict = account.model_dump()
    account_dict['current_balance'] = AccountRepository.calculate_balance(db, account.id)
    
    return AccountResponse(**account_dict)

@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: uuid.UUID,
    update_data: AccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Update an account"""
    account = AccountRepository.get_by_id(db, account_id, current_user.id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    account = AccountRepository.update(db, account, update_data)
    
    account_dict = account.model_dump()
    account_dict['current_balance'] = AccountRepository.calculate_balance(db, account.id)
    
    return AccountResponse(**account_dict)

@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Delete an account (soft delete)"""
    account = AccountRepository.get_by_id(db, account_id, current_user.id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    AccountRepository.delete(db, account)
    return None
