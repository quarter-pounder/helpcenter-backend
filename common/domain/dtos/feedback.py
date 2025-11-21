from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FeedbackReadDTO(BaseModel):
    id: UUID
    name: str
    email: str
    message: str
    expect_reply: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
