from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import register_user, authenticate_user
from app.utils.security import get_current_user

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Registers a new user account, hashes password, and returns a JWT access token."""
    user, token = await register_user(db, user_in)
    return Token(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Authenticates credentials (via JSON body or OAuth2 form) and returns a JWT access token."""
    content_type = request.headers.get("content-type", "")
    identifier = ""
    password = ""

    if "application/json" in content_type:
        try:
            body = await request.json()
            identifier = body.get("email_or_username") or body.get("username") or body.get("email") or ""
            password = body.get("password") or ""
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )
    else:
        # Fallback to form data for OAuth2 swagger client
        form_data = await request.form()
        identifier = str(form_data.get("username") or form_data.get("email_or_username") or form_data.get("email") or "")
        password = str(form_data.get("password") or "")

    if not identifier or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username/email and password are required"
        )

    user, token = await authenticate_user(db, identifier, password)
    return Token(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """Returns profile details for the currently authenticated user."""
    return current_user
