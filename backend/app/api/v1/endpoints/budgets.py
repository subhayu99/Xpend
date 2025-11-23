from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func
from app.db.session import get_session
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse, BudgetProgress
from app.repositories.budget_repo import BudgetRepository
from typing import List
import uuid
from datetime import datetime
import calendar

router = APIRouter(prefix="/budgets", tags=["Budgets"])

@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget_in: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Create a new budget"""
    # Check if budget already exists for this category/period
    existing = BudgetRepository.get_by_category(
        db, 
        current_user.id, 
        budget_in.category_id,
        budget_in.month or datetime.now().month,
        budget_in.year or datetime.now().year
    )
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Budget already exists for this category and period"
        )
    
    budget = Budget(
        user_id=current_user.id,
        **budget_in.dict()
    )
    
    # Default to current month/year if not provided
    if not budget.month:
        budget.month = datetime.now().month
    if not budget.year:
        budget.year = datetime.now().year
        
    return BudgetRepository.create(db, budget)

@router.get("", response_model=List[BudgetProgress])
def get_budgets(
    month: int = None,
    year: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get all budgets with progress for a specific month"""
    if not month:
        month = datetime.now().month
    if not year:
        year = datetime.now().year
        
    budgets = BudgetRepository.get_all(db, current_user.id, month, year)
    
    result = []
    for budget in budgets:
        # Calculate spent amount for this category in this month
        start_date = datetime(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = datetime(year, month, last_day, 23, 59, 59)
        
        # Sum expenses (negative amounts) for this category
        # Note: Expenses are stored as negative, so we sum them and take abs
        # Or if stored as positive/negative based on type, we need to check logic.
        # In AddTransactionModal, expenses are negative.
        
        query = select(func.sum(Transaction.amount)).where(
            Transaction.user_id == current_user.id,
            Transaction.category_id == budget.category_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
            Transaction.transaction_type == 'expense'
        )
        
        spent = db.exec(query).one() or 0
        spent = abs(spent) # Convert to positive for display
        
        result.append(BudgetProgress(
            **budget.dict(),
            spent=spent,
            remaining=budget.amount - spent,
            percentage=min((spent / budget.amount) * 100, 100) if budget.amount > 0 else 0
        ))
        
    return result

@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: uuid.UUID,
    budget_in: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Update a budget"""
    budget = db.get(Budget, budget_id)
    if not budget or budget.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Budget not found")
        
    if budget_in.amount is not None:
        budget.amount = budget_in.amount
    if budget_in.is_active is not None:
        budget.is_active = budget_in.is_active
        
    return BudgetRepository.update(db, budget)

@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Delete a budget"""
    budget = db.get(Budget, budget_id)
    if not budget or budget.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Budget not found")
        
    BudgetRepository.delete(db, budget)
    return None
