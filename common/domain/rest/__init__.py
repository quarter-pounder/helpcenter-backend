"""
REST API routers for the help center application.

This module contains all REST API endpoints organized by domain:
- categories: Category management
- guides: Guide management
- media: Media management
- feedback: Feedback management
- editor_guard: Authentication/authorization for editor endpoints
"""

from .categories import router as categories_router
from .editor_guard import verify_dev_editor_key
from .feedback import router as feedback_router
from .guides import router as guides_router
from .media import router as media_router

__all__ = [
    "categories_router",
    "guides_router",
    "media_router",
    "feedback_router",
    "verify_dev_editor_key",
]
