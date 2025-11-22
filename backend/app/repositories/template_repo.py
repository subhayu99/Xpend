from sqlmodel import Session, select
from app.models.template import StatementTemplate
from typing import Optional
import uuid

class TemplateRepository:
    """Repository for statement templates"""
    
    @staticmethod
    def get_by_bank_and_type(db: Session, user_id: uuid.UUID, bank_name: str, file_type: str) -> Optional[StatementTemplate]:
        return db.exec(
            select(StatementTemplate).where(
                StatementTemplate.user_id == user_id,
                StatementTemplate.bank_name == bank_name,
                StatementTemplate.file_type == file_type
            )
        ).first()
    
    @staticmethod
    def create(db: Session, template: StatementTemplate) -> StatementTemplate:
        db.add(template)
        db.commit()
        db.refresh(template)
        # Clear cache so next query will fetch fresh data
        db.expire_all()
        return template
