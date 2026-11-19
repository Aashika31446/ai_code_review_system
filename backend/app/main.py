import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import create_tables
from app.api.auth import router as auth_router
from app.api.projects import router as projects_router
from app.api.scans import router as scans_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("code_review_backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown procedures."""
    logger.info("Initializing AI-Assisted Code Review System backend...")

    # Ensure uploads directory is ready
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"Upload directory configured: {os.path.abspath(settings.UPLOAD_DIR)}")

    # Initialize database tables
    try:
        await create_tables()
        logger.info("Database connection verified and tables initialized.")
    except Exception as e:
        logger.warning(
            f"Database auto-creation encountered an issue: {e}. "
            "Please ensure database service is active and DATABASE_URL is properly configured."
        )

    yield

    logger.info("AI-Assisted Code Review System backend shutting down.")


# Create FastAPI application
app = FastAPI(
    title="AI-Assisted Code Review System API",
    description="Automated code analyzer and AI-assisted code review engine backend.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware for cross-origin frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers with /api prefix
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(auth_router, prefix="/api", tags=["Authentication"], include_in_schema=False)
app.include_router(projects_router, prefix="/api/projects", tags=["Projects"])
app.include_router(scans_router, prefix="/api", tags=["Scans & Reviews"])


# Health Check Endpoints
@app.get("/health", tags=["Health"], status_code=status.HTTP_200_OK)
@app.get("/api/health", tags=["Health"], status_code=status.HTTP_200_OK, include_in_schema=False)
async def health_check():
    """Health check endpoint indicating service availability."""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "AI Code Review Backend",
            "version": "1.0.0",
            "ai_provider": settings.AI_PROVIDER
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
