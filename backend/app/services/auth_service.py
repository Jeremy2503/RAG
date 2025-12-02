"""
Authentication Service
Handles user authentication, registration, and token management.
"""

from typing import Optional
from datetime import timedelta
from fastapi import HTTPException, status
import logging

from app.models.user import User, UserCreate, UserLogin, TokenResponse, UserResponse
from app.repositories.mongodb_repo import MongoDBRepository
from app.utils.jwt_handler import JWTHandler
from app.utils.validators import validate_password_strength
from app.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """
    Authentication service implementing business logic for user management.
    """
    
    def __init__(self, db_repo: MongoDBRepository):
        """
        Initialize authentication service.
        
        Args:
            db_repo: MongoDB repository instance
        """
        self.db_repo = db_repo
        self.jwt_handler = JWTHandler()
    
    async def register_user(self, user_create: UserCreate) -> User:
        """
        Register a new user.
        
        Args:
            user_create: User registration data
            
        Returns:
            Created user object
            
        Raises:
            HTTPException: If email already exists or validation fails
        """
        # Check if user already exists
        existing_user = await self.db_repo.get_user_by_email(user_create.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Validate password strength
        validate_password_strength(user_create.password)
        
        # Hash password
        hashed_password = self.jwt_handler.hash_password(user_create.password)
        
        # Create user
        try:
            user = await self.db_repo.create_user(user_create, hashed_password)
            logger.info(f"User registered successfully: {user.email}")
            return user
            
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register user"
            )
    
    async def authenticate_user(self, user_login: UserLogin) -> TokenResponse:
        """
        Authenticate a user and generate tokens.
        
        Args:
            user_login: Login credentials
            
        Returns:
            Token response with access and refresh tokens
            
        Raises:
            HTTPException: If credentials are invalid
        """
        # Get user by email
        user = await self.db_repo.get_user_by_email(user_login.email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Verify password
        if not self.jwt_handler.verify_password(user_login.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Update last login
        await self.db_repo.update_last_login(user.id)
        
        # Generate tokens
        token_data = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value
        }
        
        access_token = self.jwt_handler.create_access_token(token_data)
        refresh_token = self.jwt_handler.create_refresh_token(token_data)
        
        # Create user response
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
        logger.info(f"User authenticated successfully: {user.email}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            user=user_response
        )
    
    async def get_current_user(self, token: str) -> User:
        """
        Get current user from access token.
        
        Args:
            token: JWT access token
            
        Returns:
            Current user object
            
        Raises:
            HTTPException: If token is invalid or user not found
        """
        # Verify token
        token_data = self.jwt_handler.verify_token(token, token_type="access")
        
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Get user from database
        user = await self.db_repo.get_user_by_id(token_data.user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        return user
    
    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: JWT refresh token
            
        Returns:
            New token response
            
        Raises:
            HTTPException: If refresh token is invalid
        """
        # Verify refresh token
        token_data = self.jwt_handler.verify_token(refresh_token, token_type="refresh")
        
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Get user
        user = await self.db_repo.get_user_by_id(token_data.user_id)
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Generate new tokens
        new_token_data = {
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value
        }
        
        access_token = self.jwt_handler.create_access_token(new_token_data)
        new_refresh_token = self.jwt_handler.create_refresh_token(new_token_data)
        
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            user=user_response
        )
    
    def verify_admin(self, user: User) -> bool:
        """
        Verify that user has admin role.
        
        Args:
            user: User object to check
            
        Returns:
            True if user is admin
            
        Raises:
            HTTPException: If user is not admin
        """
        if user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return True

