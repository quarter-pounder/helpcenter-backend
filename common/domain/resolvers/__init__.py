import strawberry

from .category import CategoryQuery
from .feedback import FeedbackMutation
from .guide import GuideQuery


@strawberry.type
class Query(CategoryQuery, GuideQuery):
    """Root Query composed of all sub-queries."""


@strawberry.type
class Mutation(FeedbackMutation):
    """Root Mutation composed of all sub-mutations."""


__all__ = ["Query", "Mutation"]
