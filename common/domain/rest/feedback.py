from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel.ext.asyncio.session import AsyncSession

from ...core.db import get_session_dependency
from ...core.rate_limiting import (
    rate_limit_dev_editor_read,
    rate_limit_dev_editor_write,
)
from ...services.feedback import FeedbackService
from ..dtos.feedback import FeedbackReadDTO
from .editor_guard import verify_dev_editor_key

router = APIRouter(
    prefix="/editor",
    dependencies=[Depends(verify_dev_editor_key)],
    tags=["editor"],
)

service = FeedbackService()


@router.get("/feedback", response_model=List[FeedbackReadDTO])
@rate_limit_dev_editor_read()
async def list_feedback(request: Request, session: AsyncSession = Depends(get_session_dependency)):
    return await service.list_feedback(session)


@router.get("/feedback/{feedback_id}", response_model=FeedbackReadDTO)
@rate_limit_dev_editor_read()
async def get_feedback(
    request: Request,
    feedback_id: UUID,
    session: AsyncSession = Depends(get_session_dependency),
):
    dto = await service.get_feedback(session, feedback_id)
    if not dto:
        raise HTTPException(404, "Feedback not found")
    return dto


@router.delete("/feedback/{feedback_id}")
@rate_limit_dev_editor_write()
async def delete_feedback(
    request: Request,
    feedback_id: UUID,
    session: AsyncSession = Depends(get_session_dependency),
):
    await service.delete_feedback(session, feedback_id)
    return {"detail": "Feedback deleted"}
