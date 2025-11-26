from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlmodel.ext.asyncio.session import AsyncSession

from ...core.db import get_session_dependency
from ...core.rate_limiting import (
    rate_limit_dev_editor_read,
    rate_limit_dev_editor_upload,
    rate_limit_dev_editor_write,
)
from ...core.validation import validate_file_upload
from ...services.media import MediaService
from ..dtos.media import MediaReadDTO
from .editor_guard import verify_dev_editor_key

router = APIRouter(
    prefix="/editor",
    dependencies=[Depends(verify_dev_editor_key)],
    tags=["editor"],
)

service = MediaService()


@router.post("/guides/{guide_id}/media/upload", response_model=MediaReadDTO)
@rate_limit_dev_editor_upload()
async def upload_media(
    request: Request,
    guide_id: UUID,
    file: UploadFile = File(...),
    alt: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_session_dependency),
):
    """Upload media file for a guide."""
    # Validate file upload
    file_content = await file.read()
    file_size = len(file_content)

    # Reset file pointer for service
    await file.seek(0)

    # Validate file using comprehensive validation
    validate_file_upload(
        filename=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        max_size=10 * 1024 * 1024,  # 10MB
    )

    return await service.upload_media(session, file, alt, str(guide_id))


# Guide-Media Endpoints
@router.get("/guides/{guide_id}/media", response_model=List[MediaReadDTO])
@rate_limit_dev_editor_read()
async def get_guide_media(
    request: Request, guide_id: UUID, session: AsyncSession = Depends(get_session_dependency)
):
    """Get all media attached to a guide."""
    return await service.get_guide_media(session, guide_id)


@router.delete("/guides/{guide_id}/media/{media_id}")
@rate_limit_dev_editor_write()
async def delete_guide_media(
    request: Request,
    guide_id: UUID,
    media_id: UUID,
    session: AsyncSession = Depends(get_session_dependency),
):
    """Delete media from a guide and database."""
    await service.detach_from_guide(session, media_id, guide_id)
    await service.delete_media(session, media_id)
    return {"message": "Media deleted successfully"}
