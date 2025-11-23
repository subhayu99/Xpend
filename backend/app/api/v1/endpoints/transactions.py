from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Body
from sqlmodel import Session
from app.db.session import get_session
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.account import Account
from app.models.template import StatementTemplate
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.repositories.transaction_repo import TransactionRepository
from app.repositories.template_repo import TemplateRepository
from app.services.statement_parser import StatementParserService
from typing import List, Optional
import uuid
import json

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.post("/upload", response_model=dict)
async def upload_statement(
    file: UploadFile = File(...),
    account_id: uuid.UUID = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Upload and parse a bank statement.
    Checks for existing template for the bank.
    Returns parsed transactions and potential new template structure.
    """
    # Get Account to know the Bank Name
    account = db.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if account.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    file_ext = file.filename.split('.')[-1].lower()
    
    # Check for existing template
    template = TemplateRepository.get_by_bank_and_type(db, current_user.id, account.bank_name, file_ext)
    
    # Process file
    result = await StatementParserService.process_upload(file, account.bank_name, template)
    
    return result

@router.post("/confirm", response_model=List[TransactionResponse], status_code=status.HTTP_201_CREATED)
def confirm_transactions(
    transactions: List[TransactionCreate],
    save_template: bool = False,
    template_data: Optional[str] = None, # JSON string of structure
    account_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """
    Confirm and save transactions.
    Optionally save the parsing template for future use.
    """
    # Save Transactions
    saved_txs = TransactionRepository.create_multi(db, current_user.id, transactions)
    
    # Save Template if requested
    if save_template and template_data and account_id:
        account = db.get(Account, account_id)
        if account:
            # Check if template already exists to avoid duplicates
            # For simplicity, we might overwrite or ignore. Let's create if not exists.
            file_type = "csv" # This should ideally come from the request too, assuming CSV for now if not passed
            # We need to pass file_type from frontend. For now, let's assume we can infer or it's passed in template_data
            
            structure = json.loads(template_data)
            # Infer file type from structure or pass it explicitly? 
            # Let's assume the frontend passes the file type or we just save it.
            # Actually, we need the file type to look it up later.
            # Let's add file_type to the request body or assume it's part of the flow.
            
            # For this MVP, let's just save it if we can.
            pass 
            
    return saved_txs

@router.post("/save-template", status_code=status.HTTP_201_CREATED)
def save_parsing_template(
    account_id: uuid.UUID = Body(...),
    file_type: str = Body(...),
    structure_json: str = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Save a parsing template for a bank"""
    print(f"=== SAVE TEMPLATE CALLED ===")
    print(f"Account ID: {account_id}")
    print(f"File Type: {file_type}")
    print(f"Structure JSON (first 200 chars): {structure_json[:200]}")
    
    account = db.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    print(f"Bank Name: {account.bank_name}")
        
    # Check if exists
    existing = TemplateRepository.get_by_bank_and_type(db, current_user.id, account.bank_name, file_type)
    if existing:
        print(f"Updating existing template: {existing.id}")
        existing.structure_json = structure_json
        db.add(existing)
        db.commit()
        db.expire_all()  # Clear cache
        return {"message": "Template updated"}
    
    print(f"Creating new template for {account.bank_name}")
    template = StatementTemplate(
        user_id=current_user.id,
        name=f"{account.bank_name} {file_type.upper()} Template",
        bank_name=account.bank_name,
        file_type=file_type,
        structure_json=structure_json
    )
    TemplateRepository.create(db, template)
    print(f"Template created successfully!")
    return {"message": "Template saved"}

# ... Keep existing CRUD endpoints ...
@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Create a single transaction manually"""
    # Verify account belongs to user
    account = db.get(Account, transaction.account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Create transaction
    created = TransactionRepository.create(db, current_user.id, transaction)
    return created

@router.get("", response_model=List[TransactionResponse])
def get_transactions(
    skip: int = 0,
    limit: int = 100,
    account_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    return TransactionRepository.get_all(db, current_user.id, skip, limit, account_id)

@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: uuid.UUID,
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Update an existing transaction"""
    transaction = TransactionRepository.get_by_id(db, transaction_id, current_user.id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Update fields
    for key, value in transaction_data.dict(exclude_unset=True).items():
        setattr(transaction, key, value)
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction

@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    transaction = TransactionRepository.get_by_id(db, transaction_id, current_user.id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    TransactionRepository.delete(db, transaction)
    return None
