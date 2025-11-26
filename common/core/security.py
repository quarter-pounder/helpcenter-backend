"""
Security middleware and utilities for API protection.
"""

import secrets
from typing import Callable, List, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.logger import get_logger
from ..core.settings import ENVIRONMENT

logger = get_logger("security")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HSTS (only in production with HTTPS)
        if ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'"
        )
        response.headers["Content-Security-Policy"] = csp

        return response


class StrictOriginValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to strictly validate that requests come only from allowed origins.

    This enforces that only the frontend can directly contact the backend APIs.
    Blocks requests without Origin/Referer headers (except for health checks).
    """

    def __init__(self, app, allowed_origins: List[str], exempt_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.allowed_origins = [origin.strip() for origin in allowed_origins]
        self.exempt_paths = exempt_paths or ["/health", "/docs", "/openapi.json", "/redoc"]

    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from origin validation."""
        return any(path.startswith(exempt) for exempt in self.exempt_paths)

    def _normalize_origin(self, origin: str) -> str:
        """Normalize origin by removing trailing slashes."""
        return origin.rstrip("/")

    def _is_allowed_origin(self, origin: Optional[str], referer: Optional[str]) -> bool:
        """Check if origin or referer is in allowed list."""
        if origin:
            normalized_origin = self._normalize_origin(origin)
            if normalized_origin in self.allowed_origins:
                return True

        if referer:
            try:
                from urllib.parse import urlparse

                parsed = urlparse(referer)
                referer_origin = f"{parsed.scheme}://{parsed.netloc}"
                normalized_referer = self._normalize_origin(referer_origin)
                if normalized_referer in self.allowed_origins:
                    return True
            except Exception:
                pass

        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Allow exempt paths (health checks, docs, etc.)
        if self._is_exempt_path(path):
            return await call_next(request)

        # Get origin and referer headers
        origin = request.headers.get("origin")
        referer = request.headers.get("referer") or request.headers.get("referrer")

        # In production, require Origin or Referer header
        if ENVIRONMENT == "production":
            if not origin and not referer:
                logger.warning(
                    "Request blocked: Missing Origin and Referer headers",
                    extra={
                        "path": path,
                        "method": request.method,
                        "client_ip": request.client.host if request.client else None,
                        "user_agent": request.headers.get("user-agent"),
                    },
                )
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "Forbidden",
                        "message": "Requests must include Origin or Referer header",
                    },
                )

        # Validate origin/referer
        if not self._is_allowed_origin(origin, referer):
            logger.warning(
                "Request blocked: Origin not allowed",
                extra={
                    "origin": origin,
                    "referer": referer,
                    "path": path,
                    "method": request.method,
                    "client_ip": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                    "allowed_origins": self.allowed_origins,
                },
            )
            return JSONResponse(
                status_code=403,
                content={"error": "Forbidden", "message": "Origin not allowed"},
            )

        return await call_next(request)


def constant_time_compare(a: str, b: str) -> bool:
    """
    Constant-time string comparison to prevent timing attacks.

    Use this instead of == for comparing secrets, API keys, etc.
    """
    return secrets.compare_digest(a, b)
