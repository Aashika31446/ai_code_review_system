from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os
from typing import Literal


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env file."""

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:password@localhost:5432/code_review_db",
        description="SQLAlchemy Database URL"
    )

    # JWT Security
    SECRET_KEY: str = Field(
        default="change-me-in-production",
        description="Secret key for signing JWT tokens"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT encoding algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Expiration time for access tokens in minutes"
    )

    # File uploads
    UPLOAD_DIR: str = Field(
        default="./uploads",
        description="Directory to store uploaded code files"
    )
    MAX_FILE_SIZE_MB: int = Field(
        default=50,
        description="Maximum upload size in megabytes"
    )

    # AI Configuration
    AI_PROVIDER: str = Field(
        default="gemini",
        description="AI provider to use ('gemini' or 'openai')"
    )
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @property
    def async_database_url(self) -> str:
        """Returns the async-compatible database connection string."""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("sqlite://") and not url.startswith("sqlite+aiosqlite://"):
            return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return url

    @property
    def sync_database_url(self) -> str:
        """Returns the synchronous database connection string for Alembic or sync drivers."""
        url = self.DATABASE_URL
        if url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql+asyncpg://", "postgresql://", 1)
        if url.startswith("sqlite+aiosqlite://"):
            return url.replace("sqlite+aiosqlite://", "sqlite://", 1)
        return url


settings = Settings()
