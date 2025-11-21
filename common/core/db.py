"""
Database configuration and session management.

Handles async SQLAlchemy engine creation with appropriate connection pooling
for different environments (test, development, production).
"""

import ssl
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Optional

from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession as SQLAlchemyAsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy.pool.impl import AsyncAdaptedQueuePool
from sqlmodel.ext.asyncio.session import AsyncSession

from . import settings

_engine: Optional[AsyncEngine] = None
_async_session_factory: Optional[async_sessionmaker[SQLAlchemyAsyncSession]] = None


def _new_engine() -> AsyncEngine:
    """Create a new async engine with environment-appropriate pooling."""
    kwargs = {
        "echo": settings.DEBUG,
        "future": True,
    }

    if settings.ENVIRONMENT == "test":
        kwargs["poolclass"] = NullPool
    else:
        kwargs.update(
            {
                "poolclass": AsyncAdaptedQueuePool,
                "pool_size": settings.DB_POOL_SIZE,
                "max_overflow": settings.DB_MAX_OVERFLOW,
                "pool_pre_ping": True,
                "pool_recycle": settings.DB_POOL_RECYCLE,
            }
        )

    # Log the connection URL (masked for security)
    db_url = settings.DATABASE_URL
    if db_url:
        # Mask credentials but show host and database
        if "@" in db_url:
            parts = db_url.split("@")
            masked_url = f"***@{parts[-1]}" if len(parts) > 1 else "***"
        else:
            masked_url = "***"
        print(f"[db] Creating engine with connection string: {masked_url}")
        print(f"[db] Driver: {make_url(db_url).drivername}")
        print(f"[db] Host: {make_url(db_url).host}")
        print(f"[db] Database: {make_url(db_url).database}")

    url = make_url(settings.DATABASE_URL)
    connect_args = {}

    # Handle asyncpg + Neon DB SSL parameters
    if url.drivername.startswith("postgresql+asyncpg"):
        url_str = str(url)
        # Handle Neon DB SSL requirements for asyncpg
        if "sslmode=require" in url_str or "channel_binding=require" in url_str:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connect_args["ssl"] = ssl_context
            # Remove SSL parameters from URL to avoid conflicts
            url_str = url_str.replace("?sslmode=require", "").replace("&sslmode=require", "")
            url_str = url_str.replace("?channel_binding=require", "").replace(
                "&channel_binding=require", ""
            )
            url_str = url_str.replace("?&", "?").replace("&&", "&")
            if url_str.endswith("?") or url_str.endswith("&"):
                url_str = url_str[:-1]
            url = make_url(url_str)

    return create_async_engine(url, connect_args=connect_args, **kwargs)


def get_engine() -> AsyncEngine:
    """Get or create the global engine."""
    global _engine
    if _engine is None:
        _engine = _new_engine()
    return _engine


def get_async_session_factory() -> async_sessionmaker[SQLAlchemyAsyncSession]:
    """Get or create the global session factory."""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _async_session_factory


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session."""
    async_session_factory = get_async_session_factory()
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_session_dependency() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides a database session."""
    async_session_factory = get_async_session_factory()
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


def close_engine():
    """Close the global engine."""
    global _engine, _async_session_factory
    if _engine is not None:
        _engine.sync_engine.dispose()
        _engine = None
        _async_session_factory = None
