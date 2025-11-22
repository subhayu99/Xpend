from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.db.session import get_session
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, TokenRefresh
from app.services.auth_service import AuthService
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

from app.repositories.category_repo import CategoryRepository

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_session)
):
    """Register a new user"""
    user = AuthService.register_user(db, user_data)
    # Seed default categories
    CategoryRepository.seed_defaults(db, user.id)
    return user

@router.post("/login", response_model=Token)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_session)
):
    """Login and get access token"""
    return AuthService.authenticate_user(db, credentials)

@router.post("/refresh", response_model=Token)
def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_session)
):
    """Refresh access token"""
    return AuthService.refresh_access_token(db, token_data.refresh_token)

@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user info"""
    return current_user
