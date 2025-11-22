import strawberry

from ...services.feedback import FeedbackService
from ..dtos.feedback import FeedbackCreateDTO
from ..schema import Feedback as FeedbackType


@strawberry.type
class FeedbackMutation:
    @strawberry.mutation
    async def submitFeedback(
        self, info, name: str, email: str, message: str, expectReply: bool
    ) -> FeedbackType:
        """Submit feedback and save to database."""
        get_session_func = info.context["get_session"]
        async with get_session_func() as session:
            feedback_service = FeedbackService()
            dto = FeedbackCreateDTO(
                name=name, email=email, message=message, expect_reply=expectReply
            )
            feedback_dto = await feedback_service.create_feedback(session, dto)
            return FeedbackType(
                id=str(feedback_dto.id),
                name=feedback_dto.name,
                email=feedback_dto.email,
                message=feedback_dto.message,
                expectReply=feedback_dto.expect_reply,
                createdAt=feedback_dto.created_at,
            )
