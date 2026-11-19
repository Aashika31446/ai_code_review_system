import os
import uuid
try:
    import aiofiles
    HAS_AIOFILES = True
except ImportError:
    aiofiles = None
    HAS_AIOFILES = False
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.scan import ScanResponse, DashboardStats
from app.schemas.finding import FindingResponse
from app.schemas.ai_review import AIReviewResponse
from app.services.project_service import get_project_by_id
from app.services.scan_service import (
    run_scan,
    get_project_scans,
    get_scan_by_id,
    get_scan_findings,
    get_finding_review,
    get_dashboard_stats
)
from app.utils.security import get_current_user
from app.utils.file_utils import (
    validate_file_extension,
    safe_extract_zip,
    cleanup_directory
)

router = APIRouter()


# -------------------------------------------------------------------------
# Dashboard Stats Endpoint
# -------------------------------------------------------------------------
@router.get("/dashboard/stats", response_model=DashboardStats)
async def dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns aggregated scan metrics and recent reviews for the authenticated user."""
    stats = await get_dashboard_stats(db, current_user.id)
    return stats


# -------------------------------------------------------------------------
# Project Scan Endpoints
# -------------------------------------------------------------------------
@router.post(
    "/projects/{project_id}/scans",
    response_model=ScanResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def create_scan_for_project(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None, description="Single Python (.py) file or ZIP archive (.zip)"),
    files: Optional[List[UploadFile]] = File(None, description="One or more Python (.py) files or ZIP archives (.zip)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Uploads a codebase (single Python file, list of files, or ZIP archive) and schedules an automated code review."""
    # 1. Verify project existence and ownership
    project = await get_project_by_id(db, project_id, current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    # Gather uploaded files from either 'file' or 'files'
    upload_list: List[UploadFile] = []
    if file is not None and file.filename:
        upload_list.append(file)
    if files:
        for f in files:
            if f is not None and f.filename and f not in upload_list:
                upload_list.append(f)

    if not upload_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files uploaded. Only single Python (.py) files or ZIP (.zip) archives are accepted."
        )

    # 2. Validate file extensions
    for upload_item in upload_list:
        filename = upload_item.filename or ""
        if not validate_file_extension(filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format for '{filename}'. Only single Python (.py) files or ZIP (.zip) archives are accepted."
            )

    # 3. Create isolated directory for this upload
    scan_unique_dir = os.path.join(settings.UPLOAD_DIR, str(uuid.uuid4()))
    os.makedirs(scan_unique_dir, exist_ok=True)

    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    try:
        for upload_item in upload_list:
            filename = os.path.basename(upload_item.filename or "uploaded.py")
            temp_file_path = os.path.join(scan_unique_dir, filename)
            total_bytes = 0

            if HAS_AIOFILES and aiofiles is not None:
                async with aiofiles.open(temp_file_path, "wb") as out_file:
                    while chunk := await upload_item.read(1024 * 64):  # 64KB chunks
                        total_bytes += len(chunk)
                        if total_bytes > max_bytes:
                            raise HTTPException(
                                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                                detail=f"File '{filename}' exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB."
                            )
                        await out_file.write(chunk)
            else:
                with open(temp_file_path, "wb") as out_file:
                    while chunk := await upload_item.read(1024 * 64):  # 64KB chunks
                        total_bytes += len(chunk)
                        if total_bytes > max_bytes:
                            raise HTTPException(
                                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                                detail=f"File '{filename}' exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB."
                            )
                        out_file.write(chunk)

            # If ZIP, unpack safely
            if filename.lower().endswith(".zip"):
                try:
                    safe_extract_zip(temp_file_path, scan_unique_dir)
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                except ValueError as ve:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=str(ve)
                    )
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Corrupt or invalid ZIP archive '{filename}': {str(e)}"
                    )
    except HTTPException:
        cleanup_directory(scan_unique_dir)
        raise
    except Exception as e:
        cleanup_directory(scan_unique_dir)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}"
        )

    # 4. Initialize Scan in Database
    from app.models.scan import Scan
    scan = Scan(
        project_id=project.id,
        status="pending"
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    # 5. Dispatch background task
    background_tasks.add_task(run_scan, scan.id, scan_unique_dir)

    return scan


@router.get("/projects/{project_id}/scans", response_model=List[ScanResponse])
async def list_scans(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists all scans initiated under a specific project."""
    project = await get_project_by_id(db, project_id, current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    scans = await get_project_scans(db, project_id)
    return scans


# -------------------------------------------------------------------------
# Scan & Findings Endpoints
# -------------------------------------------------------------------------
@router.get("/scans/{scan_id}", response_model=ScanResponse)
async def get_scan_details(
    scan_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves full details and metrics for a specific scan."""
    scan = await get_scan_by_id(db, scan_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )

    # Check project ownership
    project = await get_project_by_id(db, scan.project_id, current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this scan"
        )

    return scan


@router.get("/scans/{scan_id}/findings", response_model=List[FindingResponse])
async def list_findings(
    scan_id: UUID,
    severity: Optional[str] = Query(
        default=None,
        description="Filter findings by severity (critical, high, medium, low)"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves findings identified by a scan, with optional severity filter."""
    scan = await get_scan_by_id(db, scan_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )

    project = await get_project_by_id(db, scan.project_id, current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this scan"
        )

    findings = await get_scan_findings(db, scan_id, severity)
    return findings


@router.get("/scans/{scan_id}/findings/{finding_id}/review", response_model=AIReviewResponse)
async def get_finding_ai_review(
    scan_id: UUID,
    finding_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves the AI-generated review, impact analysis, and suggested fix for a finding."""
    scan = await get_scan_by_id(db, scan_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )

    project = await get_project_by_id(db, scan.project_id, current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this scan"
        )

    review = await get_finding_review(db, finding_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI review not found for this finding"
        )

    return review
