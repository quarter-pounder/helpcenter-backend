"""
Help Center Editor API - Cloud Run
A dedicated service for editor operations (REST API)
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from common.core.logger import setup_logging
from common.core.middleware import RequestLoggingMiddleware
from common.core.rate_limiting import setup_rate_limiting
from common.core.security import (
    SecurityHeadersMiddleware,
    StrictOriginValidationMiddleware,
)
from common.core.settings import ALLOWED_ORIGINS, ENVIRONMENT, LOG_LEVEL
from common.domain.rest import (
    categories_router,
    feedback_router,
    guides_router,
    media_router,
)

setup_logging(LOG_LEVEL)

app = FastAPI(
    title="Help Center Editor API",
    description="Editor API for help center content management",
    version="1.0.0",
)
# Security: Strict origin validation (must be before CORS)
app.add_middleware(StrictOriginValidationMiddleware, allowed_origins=ALLOWED_ORIGINS)

# Security: Security headers
app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

setup_rate_limiting(app)
app.include_router(categories_router)
app.include_router(guides_router)
app.include_router(media_router)
app.include_router(feedback_router)


@app.get("/health")
async def health_check(request: Request):
    return {
        "status": "healthy",
        "service": "editor_api",
        "environment": ENVIRONMENT,
        "version": "1.0.0",
    }


@app.get("/")
async def root():
    return {
        "service": "HelpCenter Editor API",
        "version": "1.0.0",
        "description": "Editor API for help center content management",
        "documentation": "/docs",
        "health": "/health",
    }
