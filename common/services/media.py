import time
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, UploadFile
from google.cloud import storage
from sqlalchemy import select as sa_select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..core.settings import GCS_BUCKET_NAME
from ..domain.dtos.media import MediaCreateDTO, MediaReadDTO
from ..domain.models import Media as MediaModel
from ..repositories.media import MediaRepository


class MediaService:
    def __init__(self, repo: MediaRepository | None = None):
        self.repo = repo or MediaRepository()

        # Configure Google Cloud Storage
        self.gcs_client = None
        if GCS_BUCKET_NAME:
            try:
                # Try to initialize GCS client - will use service account if available
                self.gcs_client = storage.Client()
                self.bucket_name = GCS_BUCKET_NAME
            except Exception as e:
                print(f"Warning: Failed to initialize GCS client: {e}")
                self.gcs_client = None

    async def upload_media(
        self, session: AsyncSession, file: UploadFile, alt: str = None, guide_id: str = None
    ) -> MediaReadDTO:
        """Upload media to Google Cloud Storage and save metadata to database."""
        try:
            # Check if GCS is configured
            if self.gcs_client and self.bucket_name:
                # Upload to Google Cloud Storage
                bucket = self.gcs_client.bucket(self.bucket_name)
                filename = f"helpcenter/{file.filename}_{int(time.time())}"
                blob = bucket.blob(filename)

                # Upload file content
                file.file.seek(0)  # Reset file pointer
                blob.upload_from_file(file.file, content_type=file.content_type)

                # Make blob publicly readable
                blob.make_public()
                url = blob.public_url
            else:
                # Mock URL for testing without GCS
                url = (
                    f"https://via.placeholder.com/300x200/0066CC/FFFFFF"
                    f"?text={file.filename or 'uploaded-image'}"
                )

            # Create media record
            media_dto = MediaCreateDTO(url=url, alt=alt or file.filename)

            media = await self.repo.create_from_dto(session, media_dto)
            await session.commit()
            await session.refresh(media)

            # If guide_id is provided, attach media to guide
            if guide_id:
                await self.attach_to_guide(session, media.id, UUID(guide_id))

            return MediaReadDTO.model_validate(media)

        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to upload media: {str(e)}")

    async def get_media(self, session: AsyncSession, id: UUID) -> Optional[MediaReadDTO]:
        """Get media by ID."""
        return await self.repo.get_read(session, id)

    async def list_media(self, session: AsyncSession) -> List[MediaReadDTO]:
        """List all media."""
        return await self.repo.list_read(session)

    async def delete_media(self, session: AsyncSession, id: UUID) -> None:
        """Delete media from both database and Google Cloud Storage."""
        media = await self.repo.get(session, id)
        if not media:
            raise HTTPException(status_code=404, detail="Media not found")

        try:
            # Delete from Google Cloud Storage if GCS is configured
            if self.gcs_client and self.bucket_name and "storage.googleapis.com" in media.url:
                bucket = self.gcs_client.bucket(self.bucket_name)
                # Extract blob name from URL
                blob_name = media.url.split(f"{self.bucket_name}/")[-1]
                blob = bucket.blob(blob_name)
                blob.delete()

            # Delete from database
            await self.repo.delete(session, id)
            await session.commit()

        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete media: {str(e)}")

    async def attach_to_guide(self, session: AsyncSession, media_id: UUID, guide_id: UUID) -> None:
        """Attach media to a guide."""
        from ..domain.models import GuideMediaLink

        # Check if association already exists
        stmt = sa_select(GuideMediaLink).where(
            GuideMediaLink.media_id == media_id, GuideMediaLink.guide_id == guide_id
        )
        result = await session.execute(stmt)
        if result.scalars().first():
            return  # Already attached

        # Create association
        link = GuideMediaLink(media_id=media_id, guide_id=guide_id)
        session.add(link)
        await session.commit()

    async def detach_from_guide(
        self, session: AsyncSession, media_id: UUID, guide_id: UUID
    ) -> None:
        """Detach media from a guide."""
        from sqlalchemy import delete as sa_delete

        from ..domain.models import GuideMediaLink

        stmt = sa_delete(GuideMediaLink).where(
            GuideMediaLink.media_id == media_id, GuideMediaLink.guide_id == guide_id
        )
        await session.execute(stmt)
        await session.commit()

    async def get_guide_media(self, session: AsyncSession, guide_id: UUID) -> List[MediaReadDTO]:
        """Get all media attached to a specific guide."""
        from sqlalchemy import select as sa_select

        from ..domain.models import GuideMediaLink

        stmt = sa_select(MediaModel).join(GuideMediaLink).where(GuideMediaLink.guide_id == guide_id)
        result = await session.execute(stmt)
        media_list = result.scalars().all()

        return [MediaReadDTO.model_validate(media) for media in media_list]

    async def get_media_guides(self, session: AsyncSession, media_id: UUID) -> List:
        """Get all guides attached to a specific media."""
        from sqlalchemy import select as sa_select

        from ..domain.dtos.guide import GuideReadDTO
        from ..domain.models import GuideMediaLink, UserGuide

        stmt = sa_select(UserGuide).join(GuideMediaLink).where(GuideMediaLink.media_id == media_id)
        result = await session.execute(stmt)
        guides_list = result.scalars().all()

        return [GuideReadDTO.model_validate(guide) for guide in guides_list]
