from fastapi import APIRouter, HTTPException, status, Depends, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import timedelta
from app.schemas.auth import UserRegister, UserLogin, TokenResponse
from app.services.auth_service import verify_password, get_password_hash, create_access_token
from app.services.db_service import get_user_by_email, get_user_by_cpf, create_user
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def register(request: Request, user_data: UserRegister):
    """Register a new user"""
    # Check if email already exists
    existing_user = get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if CPF already exists
    existing_cpf = get_user_by_cpf(user_data.cpf)
    if existing_cpf:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF already registered"
        )
    
    # Hash password
    password_hash = get_password_hash(user_data.password)
    
    # Create user
    try:
        user = create_user(
            name=user_data.name,
            email=user_data.email,
            cpf=user_data.cpf,
            password_hash=password_hash
        )
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user. Please try again."
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user["id"])},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "cpf": user["cpf"]
        }
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def login(request: Request, credentials: UserLogin):
    """Login user"""
    # Get user by email
    user = get_user_by_email(credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user["id"])},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "cpf": user["cpf"]
        }
    )

