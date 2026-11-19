from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from fastapi import HTTPException, status
from uuid import UUID
from typing import Optional, Tuple

from app.models.user import User
from app.schemas.auth import UserCreate
from app.utils.security import hash_password, verify_password, create_access_token


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Retrieves a user by their email address."""
    query = select(User).where(User.email == email.lower().strip())
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Retrieves a user by their username."""
    query = select(User).where(User.username == username.strip())
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """Retrieves a user by their unique UUID."""
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def register_user(db: AsyncSession, user_in: UserCreate) -> Tuple[User, str]:
    """Registers a new user, hashes their password, and creates an access token."""
    # Check if email is already registered
    existing_email = await get_user_by_email(db, user_in.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    # Check if username is already taken
    existing_username = await get_user_by_username(db, user_in.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken"
        )

    hashed_pw = hash_password(user_in.password)
    user = User(
        email=user_in.email.lower().strip(),
        username=user_in.username.strip(),
        hashed_password=hashed_pw,
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": str(user.id), "username": user.username})
    return user, token


async def authenticate_user(db: AsyncSession, email_or_username: str, password: str) -> Tuple[User, str]:
    """Authenticates a user via email or username and password, returning user and access token."""
    identifier = email_or_username.strip()
    query = select(User).where(
        or_(
            User.email == identifier.lower(),
            User.username == identifier
        )
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    token = create_access_token({"sub": str(user.id), "username": user.username})
    return user, token
