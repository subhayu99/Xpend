from sqlmodel import Session, select
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, Token
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.config import settings
from datetime import timedelta
import uuid

class AuthService:
    """Authentication service"""
    
    @staticmethod
    def register_user(db: Session, user_data: UserCreate) -> User:
        """Register a new user"""
        # Check if user exists
        existing_user = db.exec(
            select(User).where(User.email == user_data.email)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        user = User(
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            name=user_data.name,
            timezone=user_data.timezone,
            currency=user_data.currency,
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def authenticate_user(db: Session, credentials: UserLogin) -> Token:
        """Authenticate user and return tokens"""
        # Find user
        user = db.exec(
            select(User).where(User.email == credentials.email)
        ).first()
        
        if not user or not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        # Create tokens
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> Token:
        """Refresh access token using refresh token"""
        payload = decode_token(refresh_token)
        
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Verify user exists and is active
        user = db.get(User, uuid.UUID(user_id))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,  # Return same refresh token
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    @staticmethod
    def get_current_user(db: Session, token: str) -> User:
        """Get current user from access token"""
        payload = decode_token(token)
        
        if not payload or payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        user = db.get(User, uuid.UUID(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
