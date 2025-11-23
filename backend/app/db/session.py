from sqlmodel import SQLModel, create_engine, Session
from app.core.config import settings
# Import models to register them with SQLModel metadata
from app.models.user import User
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.template import StatementTemplate
from app.models.transfer import Transfer

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.ENVIRONMENT == "development"
)

def init_db():
    """Create all tables"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependency for getting DB session"""
    with Session(engine) as session:
        yield session
