from sqlmodel import Session, select
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate
from typing import List, Optional
import uuid

class CategoryRepository:
    """Repository for category operations"""
    
    @staticmethod
    def create(db: Session, user_id: uuid.UUID, category_data: CategoryCreate) -> Category:
        """Create a new category"""
        category = Category(
            user_id=user_id,
            **category_data.model_dump()
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    
    @staticmethod
    def get_all(db: Session, user_id: uuid.UUID, type: Optional[str] = None) -> List[Category]:
        """Get all categories for a user (including defaults)"""
        # We might want to include system defaults here too if we had a separate table or flag
        # For now, just user's categories
        query = select(Category).where(Category.user_id == user_id)
        
        if type:
            query = query.where(Category.type == type)
            
        query = query.order_by(Category.name)
        return db.exec(query).all()
    
    @staticmethod
    def get_by_id(db: Session, category_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Category]:
        """Get category by ID"""
        return db.exec(
            select(Category).where(
                Category.id == category_id,
                Category.user_id == user_id
            )
        ).first()
    
    @staticmethod
    def update(db: Session, category: Category, update_data: CategoryUpdate) -> Category:
        """Update a category"""
        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(category, field, value)
        
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    
    @staticmethod
    def delete(db: Session, category: Category) -> None:
        """Delete a category"""
        db.delete(category)
        db.commit()
        
    @staticmethod
    def seed_defaults(db: Session, user_id: uuid.UUID) -> None:
        """Seed default categories for a new user"""
        defaults = [
            {"name": "Salary", "type": "income", "icon": "💰", "color": "#4CAF50"},
            {"name": "Food & Dining", "type": "expense", "icon": "🍔", "color": "#F44336"},
            {"name": "Transportation", "type": "expense", "icon": "🚗", "color": "#2196F3"},
            {"name": "Shopping", "type": "expense", "icon": "🛍️", "color": "#9C27B0"},
            {"name": "Bills & Utilities", "type": "expense", "icon": "💡", "color": "#FF9800"},
            {"name": "Entertainment", "type": "expense", "icon": "🎬", "color": "#673AB7"},
            {"name": "Health", "type": "expense", "icon": "🏥", "color": "#E91E63"},
            {"name": "Travel", "type": "expense", "icon": "✈️", "color": "#00BCD4"},
            {"name": "Education", "type": "expense", "icon": "📚", "color": "#3F51B5"},
            {"name": "Investment", "type": "expense", "icon": "📈", "color": "#009688"},
        ]
        
        for data in defaults:
            cat = Category(
                user_id=user_id,
                is_default=True,
                **data
            )
            db.add(cat)
        db.commit()
