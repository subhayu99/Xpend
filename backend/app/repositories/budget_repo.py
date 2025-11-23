from sqlmodel import Session, select
from app.models.budget import Budget
from typing import List, Optional
import uuid
from datetime import datetime

class BudgetRepository:
    """Repository for budget operations"""
    
    @staticmethod
    def create(db: Session, budget: Budget) -> Budget:
        db.add(budget)
        db.commit()
        db.refresh(budget)
        return budget
    
    @staticmethod
    def get_all(
        db: Session, 
        user_id: uuid.UUID, 
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> List[Budget]:
        query = select(Budget).where(Budget.user_id == user_id)
        
        if month:
            query = query.where(Budget.month == month)
        if year:
            query = query.where(Budget.year == year)
            
        return db.exec(query).all()
    
    @staticmethod
    def get_by_category(
        db: Session, 
        user_id: uuid.UUID, 
        category_id: uuid.UUID,
        month: int,
        year: int
    ) -> Optional[Budget]:
        query = select(Budget).where(
            Budget.user_id == user_id,
            Budget.category_id == category_id,
            Budget.month == month,
            Budget.year == year
        )
        return db.exec(query).first()
    
    @staticmethod
    def update(db: Session, budget: Budget) -> Budget:
        budget.updated_at = datetime.utcnow()
        db.add(budget)
        db.commit()
        db.refresh(budget)
        return budget
    
    @staticmethod
    def delete(db: Session, budget: Budget):
        db.delete(budget)
        db.commit()
