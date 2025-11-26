from fastapi import Header, HTTPException, status

from ...core import settings
from ...core.security import constant_time_compare


async def verify_dev_editor_key(x_editor_key: str = Header(...)) -> None:
    """Verify editor API key using constant-time comparison to prevent timing attacks."""
    if not constant_time_compare(x_editor_key, settings.EDITOR_KEY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: invalid editor key",
        )
