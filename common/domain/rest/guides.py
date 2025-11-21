from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel.ext.asyncio.session import AsyncSession

from ...core.db import get_session_dependency
from ...core.rate_limiting import (
    rate_limit_dev_editor_read,
    rate_limit_dev_editor_write,
)
from ...services.guide import GuideService
from ..dtos.guide import (
    GuideCreateDTO,
    GuideReadDTO,
    GuideUpdateDTO,
)
from .editor_guard import verify_dev_editor_key

router = APIRouter(
    prefix="/editor",
    dependencies=[Depends(verify_dev_editor_key)],
    tags=["editor"],
)

service = GuideService()


@router.post("/guides", response_model=GuideReadDTO)
@rate_limit_dev_editor_write()
async def create_guide(
    request: Request,
    payload: GuideCreateDTO,
    session: AsyncSession = Depends(get_session_dependency),
):
    return await service.create_guide(session, payload)


@router.get("/guides", response_model=List[GuideReadDTO])
@rate_limit_dev_editor_read()
async def list_guides(
    request: Request,
    category_slug: str | None = Query(None, description="Filter by category slug"),
    session: AsyncSession = Depends(get_session_dependency),
):
    return await service.list_guides(session, category_slug)


@router.get("/guides/{guide_id}", response_model=GuideReadDTO)
@rate_limit_dev_editor_read()
async def get_guide(
    request: Request,
    guide_id: UUID,
    session: AsyncSession = Depends(get_session_dependency),
):
    dto = await service.get_guide(session, guide_id)
    if not dto:
        raise HTTPException(404, "Guide not found")
    return dto


@router.get("/guides/slug/{slug}", response_model=GuideReadDTO)
@rate_limit_dev_editor_read()
async def get_guide_by_slug(
    request: Request, slug: str, session: AsyncSession = Depends(get_session_dependency)
):
    dto = await service.get_guide_by_slug(session, slug)
    if not dto:
        raise HTTPException(404, "Guide not found")
    return dto


@router.put("/guides/{guide_id}", response_model=GuideReadDTO)
@rate_limit_dev_editor_write()
async def update_guide(
    request: Request,
    guide_id: UUID,
    payload: GuideUpdateDTO,
    session: AsyncSession = Depends(get_session_dependency),
):
    return await service.update_guide(session, guide_id, payload)


@router.delete("/guides/{guide_id}")
@rate_limit_dev_editor_write()
async def delete_guide(
    request: Request, guide_id: UUID, session: AsyncSession = Depends(get_session_dependency)
):
    await service.delete_guide(session, guide_id)
    return {"detail": "Guide deleted"}
