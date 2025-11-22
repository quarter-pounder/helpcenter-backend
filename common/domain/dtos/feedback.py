from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ...core.validation import CommonValidators


class FeedbackCreateDTO(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Feedback submitter name")
    email: str = Field(..., description="Feedback submitter email")
    message: str = Field(..., min_length=1, max_length=5000, description="Feedback message")
    expect_reply: bool = Field(default=False, description="Whether submitter expects a reply")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        return CommonValidators.validate_non_empty_string(v)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        return CommonValidators.validate_email(v)

    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        return CommonValidators.validate_non_empty_string(v)


class FeedbackReadDTO(BaseModel):
    id: UUID
    name: str
    email: str
    message: str
    expect_reply: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
