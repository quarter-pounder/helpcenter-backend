from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ...core.validation import CommonValidators


class GuideCreateDTO(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Guide title")
    slug: str = Field(..., min_length=1, max_length=100, description="URL-friendly slug")
    body: Dict[str, Any] = Field(..., description="Rich text content with blocks structure")
    estimated_read_time: int = Field(
        ..., ge=1, le=300, description="Estimated read time in minutes"
    )
    category_ids: Optional[List[UUID]] = Field(
        default=[], description="Category IDs to associate with this guide"
    )
    media_ids: Optional[List[UUID]] = Field(
        default=[], description="Media IDs to associate with this guide"
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        return CommonValidators.validate_non_empty_string(v)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v):
        return CommonValidators.validate_slug(v)

    @field_validator("body")
    @classmethod
    def validate_body(cls, v):
        return CommonValidators.validate_rich_text_body(v)

    @field_validator("estimated_read_time")
    @classmethod
    def validate_read_time(cls, v):
        return CommonValidators.validate_positive_int(v)

    @field_validator("category_ids")
    @classmethod
    def validate_category_ids(cls, v):
        if v is None:
            return []
        if len(v) > 10:  # Reasonable limit
            raise ValueError("Cannot associate more than 10 categories with a guide")
        return v

    @field_validator("media_ids")
    @classmethod
    def validate_media_ids(cls, v):
        if v is None:
            return []
        if len(v) > 20:  # Reasonable limit
            raise ValueError("Cannot associate more than 20 media items with a guide")
        return v


class GuideUpdateDTO(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Guide title")
    slug: Optional[str] = Field(None, min_length=1, max_length=100, description="URL-friendly slug")
    body: Optional[Dict[str, Any]] = Field(
        None, description="Rich text content with blocks structure"
    )
    estimated_read_time: Optional[int] = Field(
        None, ge=1, le=300, description="Estimated read time in minutes"
    )
    category_ids: Optional[List[UUID]] = Field(
        None, description="Category IDs to associate with this guide"
    )
    media_ids: Optional[List[UUID]] = Field(
        None, description="Media IDs to associate with this guide"
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if v is not None:
            return CommonValidators.validate_non_empty_string(v)
        return v

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v):
        if v is not None:
            return CommonValidators.validate_slug(v)
        return v

    @field_validator("body")
    @classmethod
    def validate_body(cls, v):
        if v is not None:
            return CommonValidators.validate_rich_text_body(v)
        return v

    @field_validator("estimated_read_time")
    @classmethod
    def validate_read_time(cls, v):
        if v is not None:
            return CommonValidators.validate_positive_int(v)
        return v

    @field_validator("category_ids")
    @classmethod
    def validate_category_ids(cls, v):
        if v is not None and len(v) > 10:
            raise ValueError("Cannot associate more than 10 categories with a guide")
        return v

    @field_validator("media_ids")
    @classmethod
    def validate_media_ids(cls, v):
        if v is not None and len(v) > 20:
            raise ValueError("Cannot associate more than 20 media items with a guide")
        return v


class GuideReadDTO(BaseModel):
    id: UUID
    title: str
    slug: str
    body: Dict[str, Any]
    estimated_read_time: int
    created_at: datetime
    updated_at: Optional[datetime]
    category_ids: List[UUID] = Field(default=[], description="Associated category IDs")
    media_ids: List[UUID] = Field(default=[], description="Associated media IDs")

    model_config = ConfigDict(from_attributes=True)
