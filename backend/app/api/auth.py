"""
Authentication Endpoints
Handles user registration, login, and token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, Any

from app.models.user import UserCreate, UserLogin, TokenResponse, UserResponse, User
from app.services.auth_service import AuthService
from app.repositories.mongodb_repo import get_mongodb_repo, MongoDBRepository

router = APIRouter()
security = HTTPBearer()


# Dependency to get auth service
async def get_auth_service(
    db_repo: MongoDBRepository = Depends(get_mongodb_repo)
) -> AuthService:
    """Get authentication service instance."""
    return AuthService(db_repo)


# Dependency to get current user from token
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP bearer token credentials
        auth_service: Authentication service
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    return await auth_service.get_current_user(token)


# Dependency to verify admin access
async def verify_admin(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """
    Verify that current user is an admin.
    
    Args:
        current_user: Current user
        auth_service: Authentication service
        
    Returns:
        Current user if admin
        
    Raises:
        HTTPException: If user is not admin
    """
    auth_service.verify_admin(current_user)
    return current_user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """
    Register a new user.
    
    Args:
        user_create: User registration data
        auth_service: Authentication service
        
    Returns:
        Created user information
    """
    user = await auth_service.register_user(user_create)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    user_login: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """
    Authenticate user and return JWT tokens.
    
    Args:
        user_login: Login credentials
        auth_service: Authentication service
        
    Returns:
        Access and refresh tokens with user information
    """
    return await auth_service.authenticate_user(user_login)


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""
    refresh_token: str

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """
    Refresh access token using refresh token.
    
    Args:
        request: Request containing refresh token
        auth_service: Authentication service
        
    Returns:
        New access and refresh tokens
    """
    return await auth_service.refresh_access_token(request.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User information
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.get("/verify-admin")
async def verify_admin_access(
    admin_user: User = Depends(verify_admin)
) -> Dict[str, Any]:
    """
    Verify admin access.
    
    Args:
        admin_user: Verified admin user
        
    Returns:
        Confirmation message
    """
    return {
        "message": "Admin access verified",
        "user": {
            "email": admin_user.email,
            "role": admin_user.role.value
        }
    }

