from typing import List, Optional
from uuid import UUID

from sqlalchemy import select as sa_select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..domain.dtos.feedback import FeedbackCreateDTO, FeedbackReadDTO
from ..domain.models import Feedback as FeedbackModel
from .base import BaseRepository


class FeedbackRepository(BaseRepository[FeedbackModel]):
    def __init__(self):
        super().__init__(FeedbackModel)

    async def create_from_dto(self, session: AsyncSession, dto: FeedbackCreateDTO) -> FeedbackModel:
        """Stage a new Feedback from DTO. Caller must commit/refresh."""
        obj = FeedbackModel(**dto.model_dump())
        session.add(obj)
        return obj

    async def get_read(self, session: AsyncSession, id: UUID) -> Optional[FeedbackReadDTO]:
        stmt = sa_select(FeedbackModel).where(FeedbackModel.id == id)
        result = await session.execute(stmt)
        feedback = result.scalars().first()

        if not feedback:
            return None

        return FeedbackReadDTO.model_validate(feedback)

    async def list_read(self, session: AsyncSession) -> List[FeedbackReadDTO]:
        stmt = sa_select(FeedbackModel).order_by(FeedbackModel.created_at.desc())
        result = await session.execute(stmt)
        feedbacks = result.scalars().all()

        return [FeedbackReadDTO.model_validate(feedback) for feedback in feedbacks]
