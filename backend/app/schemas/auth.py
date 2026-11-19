from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr = Field(..., description="User's valid email address")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    password: str = Field(..., min_length=6, max_length=128, description="User password")


class UserLogin(BaseModel):
    """Schema for JSON-based login."""
    email_or_username: str = Field(..., description="Email or username for authentication")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    """Schema for user profile data."""
    id: UUID
    email: str
    username: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    token_type: str = "bearer"
    user: Optional[UserResponse] = None


class TokenData(BaseModel):
    """Schema for decoded JWT token payload."""
    user_id: Optional[str] = None
    username: Optional[str] = None
