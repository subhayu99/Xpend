from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session
from app.db.session import get_session
from app.models.user import User
from app.services.auth_service import AuthService

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_session)
) -> User:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    return AuthService.get_current_user(db, token)
