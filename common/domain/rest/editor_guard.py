from fastapi import Header, HTTPException, status

from ...core import settings


async def verify_dev_editor_key(x_editor_key: str = Header(...)) -> None:
    if x_editor_key != settings.EDITOR_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: invalid editor key",
        )
