from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy import select as sa_select
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession

from ..domain.dtos.guide import GuideCreateDTO, GuideReadDTO, GuideUpdateDTO
from ..domain.models import Category as CategoryModel
from ..domain.models import UserGuide as GuideModel
from ..domain.models.category import GuideCategoryLink
from ..repositories.base import BaseRepository


class GuideRepository(BaseRepository[GuideModel]):
    def __init__(self):
        super().__init__(GuideModel)

    async def create_from_dto(self, session: AsyncSession, dto: GuideCreateDTO) -> GuideModel:
        """Create a guide from DTO with category and media associations."""
        guide = GuideModel(
            title=dto.title,
            slug=dto.slug,
            body=dto.body,
            estimated_read_time=dto.estimated_read_time,
        )

        # Associate with categories if provided
        if dto.category_ids:
            categories = await self._get_categories_by_ids(session, dto.category_ids)
            guide.categories = categories

        # Associate with media if provided
        if dto.media_ids:
            media_items = await self._get_media_by_ids(session, dto.media_ids)
            guide.media = media_items

        session.add(guide)
        return guide

    async def update_from_dto(
        self, session: AsyncSession, id: UUID, dto: GuideUpdateDTO
    ) -> Optional[GuideModel]:
        """Update a guide from DTO with category and media associations."""
        guide = await session.get(GuideModel, id)
        if not guide:
            return None

        # Update basic fields
        if dto.title is not None:
            guide.title = dto.title
        if dto.slug is not None:
            guide.slug = dto.slug
        if dto.body is not None:
            guide.body = dto.body
        if dto.estimated_read_time is not None:
            guide.estimated_read_time = dto.estimated_read_time

        # Update category associations if provided
        if dto.category_ids is not None:
            categories = await self._get_categories_by_ids(session, dto.category_ids)
            guide.categories = categories

        # Update media associations if provided
        if dto.media_ids is not None:
            media_items = await self._get_media_by_ids(session, dto.media_ids)
            guide.media = media_items

        return guide

    async def get_read(self, session: AsyncSession, id: UUID) -> Optional[GuideReadDTO]:
        """Get a guide as DTO with category and media IDs."""
        stmt = (
            sa_select(GuideModel)
            .options(selectinload(GuideModel.categories), selectinload(GuideModel.media))
            .where(GuideModel.id == id)
        )
        result = await session.execute(stmt)
        guide = result.scalars().first()

        if not guide:
            return None

        return GuideReadDTO(
            id=guide.id,
            title=guide.title,
            slug=guide.slug,
            body=guide.body,
            estimated_read_time=guide.estimated_read_time,
            created_at=guide.created_at,
            updated_at=guide.updated_at,
            category_ids=[cat.id for cat in guide.categories],
            media_ids=[media.id for media in guide.media],
        )

    async def get_read_by_slug(self, session: AsyncSession, slug: str) -> Optional[GuideReadDTO]:
        """Get a guide by slug as DTO with category and media IDs."""
        stmt = (
            sa_select(GuideModel)
            .options(selectinload(GuideModel.categories), selectinload(GuideModel.media))
            .where(GuideModel.slug == slug)
        )
        result = await session.execute(stmt)
        guide = result.scalars().first()

        if not guide:
            return None

        return GuideReadDTO(
            id=guide.id,
            title=guide.title,
            slug=guide.slug,
            body=guide.body,
            estimated_read_time=guide.estimated_read_time,
            created_at=guide.created_at,
            updated_at=guide.updated_at,
            category_ids=[cat.id for cat in guide.categories],
            media_ids=[media.id for media in guide.media],
        )

    async def list_read(
        self, session: AsyncSession, category_slug: Optional[str] = None
    ) -> List[GuideReadDTO]:
        """List guides as DTOs, optionally filtered by category slug."""
        stmt = sa_select(GuideModel).options(
            selectinload(GuideModel.categories), selectinload(GuideModel.media)
        )

        if category_slug:
            stmt = stmt.where(GuideModel.categories.any(CategoryModel.slug == category_slug))

        result = await session.execute(stmt)
        guides = result.scalars().all()

        return [
            GuideReadDTO(
                id=guide.id,
                title=guide.title,
                slug=guide.slug,
                body=guide.body,
                estimated_read_time=guide.estimated_read_time,
                created_at=guide.created_at,
                updated_at=guide.updated_at,
                category_ids=[cat.id for cat in guide.categories],
                media_ids=[media.id for media in guide.media],
            )
            for guide in guides
        ]

    async def list_read_by_category(
        self, session: AsyncSession, category_id: str
    ) -> List[GuideReadDTO]:
        """List guides for a specific category."""
        stmt = (
            sa_select(GuideModel)
            .options(selectinload(GuideModel.categories), selectinload(GuideModel.media))
            .where(GuideModel.categories.any(CategoryModel.id == category_id))
        )
        result = await session.execute(stmt)
        guides = result.scalars().all()

        return [
            GuideReadDTO(
                id=guide.id,
                title=guide.title,
                slug=guide.slug,
                body=guide.body,
                estimated_read_time=guide.estimated_read_time,
                created_at=guide.created_at,
                updated_at=guide.updated_at,
                category_ids=[cat.id for cat in guide.categories],
                media_ids=[media.id for media in guide.media],
            )
            for guide in guides
        ]

    async def get_categories(self, session: AsyncSession, guide_id: UUID) -> List[CategoryModel]:
        """Get categories for a specific guide."""
        stmt = (
            sa_select(CategoryModel)
            .join(GuideCategoryLink)
            .where(GuideCategoryLink.guide_id == str(guide_id))
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def _get_categories_by_ids(
        self, session: AsyncSession, category_ids: List[UUID]
    ) -> List[CategoryModel]:
        """Helper to fetch categories by IDs."""
        if not category_ids:
            return []

        stmt = sa_select(CategoryModel).where(CategoryModel.id.in_(category_ids))
        result = await session.execute(stmt)
        return result.scalars().all()

    async def _get_media_by_ids(self, session: AsyncSession, media_ids: List[UUID]) -> List:
        """Helper to fetch media by IDs."""
        if not media_ids:
            return []

        from ..domain.models import Media

        stmt = sa_select(Media).where(Media.id.in_(media_ids))
        result = await session.execute(stmt)
        return result.scalars().all()

    async def delete(self, session: AsyncSession, id: UUID) -> bool:
        """Delete a guide by ID and its relationships."""
        # Check if guide exists
        obj = await session.get(GuideModel, id)
        if not obj:
            return False

        # Delete guide-category relationships
        from ..domain.models import GuideCategoryLink

        stmt = sa_delete(GuideCategoryLink).where(GuideCategoryLink.guide_id == id)
        await session.execute(stmt)

        # Delete guide-media relationships
        from ..domain.models import GuideMediaLink

        stmt = sa_delete(GuideMediaLink).where(GuideMediaLink.guide_id == id)
        await session.execute(stmt)

        # Delete the guide directly with SQL
        stmt = sa_delete(GuideModel).where(GuideModel.id == id)
        result = await session.execute(stmt)

        # Commit all deletions
        await session.commit()
        return result.rowcount > 0
