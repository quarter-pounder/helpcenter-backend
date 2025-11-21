from uuid import UUID

from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from ..domain.dtos.feedback import FeedbackReadDTO
from ..repositories.feedback import FeedbackRepository


class FeedbackService:
    def __init__(self, repo: FeedbackRepository | None = None):
        self.repo = repo or FeedbackRepository()

    async def get_feedback(self, session: AsyncSession, id: UUID) -> FeedbackReadDTO | None:
        return await self.repo.get_read(session, id)

    async def list_feedback(self, session: AsyncSession) -> list[FeedbackReadDTO]:
        return await self.repo.list_read(session)

    async def delete_feedback(self, session: AsyncSession, id: UUID) -> None:
        obj = await self.repo.get(session, id)
        if not obj:
            raise HTTPException(status_code=404, detail="Feedback not found")
        await self.repo.delete(session, id)
        await session.commit()
