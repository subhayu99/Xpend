from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.db.session import get_session
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.repositories.category_repo import CategoryRepository
from typing import List, Optional
import uuid

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Create a new category"""
    return CategoryRepository.create(db, current_user.id, category_data)

@router.get("", response_model=List[CategoryResponse])
def get_categories(
    type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get all categories for current user"""
    return CategoryRepository.get_all(db, current_user.id, type)

@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get a specific category"""
    category = CategoryRepository.get_by_id(db, category_id, current_user.id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return category

@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: uuid.UUID,
    update_data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Update a category"""
    category = CategoryRepository.get_by_id(db, category_id, current_user.id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return CategoryRepository.update(db, category, update_data)

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Delete a category"""
    category = CategoryRepository.get_by_id(db, category_id, current_user.id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    CategoryRepository.delete(db, category)
    return None

@router.post("/seed-defaults", status_code=status.HTTP_201_CREATED)
def seed_default_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Seed default categories for the current user"""
    # Check if user already has categories
    existing = CategoryRepository.get_all(db, current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has categories"
        )
        
    CategoryRepository.seed_defaults(db, current_user.id)
    return {"message": "Default categories seeded"}
