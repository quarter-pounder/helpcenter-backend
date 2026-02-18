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
from .logger import get_logger

logger = get_logger("db")

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
        logger.debug(
            "Creating engine",
            extra={
                "connection_masked": masked_url,
                "driver": make_url(db_url).drivername,
                "host": make_url(db_url).host,
                "database": make_url(db_url).database,
            },
        )

    url = make_url(settings.DATABASE_URL)
    connect_args = {}

    # Log connection details (without password)
    port = url.port or 5432
    logger.debug(
        "Connecting",
        extra={"user": url.username, "host": url.host, "port": port, "database": url.database},
    )

    # Handle asyncpg + Neon DB SSL parameters
    if url.drivername.startswith("postgresql+asyncpg"):
        url_str = str(url)

        is_neon = url.host and (
            "neon.tech" in url.host
            or ".aws.neon.tech" in url.host
            or "ep-" in url.host  # Neon endpoint pattern
        )

        if is_neon or "sslmode=require" in url_str or "channel_binding=require" in url_str:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connect_args["ssl"] = ssl_context
            logger.debug("SSL context configured for Neon/secure connection")

        original_username = url.username
        original_password = url.password
        logger.debug(
            "URL credentials",
            extra={"username": original_username, "password_set": bool(original_password)},
        )
        if original_password and original_password != original_password.strip():
            logger.warning("Password has leading/trailing whitespace")

        if url.query and ("sslmode=require" in url.query or "channel_binding=require" in url.query):
            from urllib.parse import parse_qs, urlencode

            query_params = parse_qs(url.query)
            query_params.pop("sslmode", None)
            query_params.pop("channel_binding", None)

            if query_params:
                new_query = urlencode(query_params, doseq=True)
                url = url.set(query=new_query)
            else:
                url = url.set(query=None)

            if url.password != original_password:
                logger.error("Password changed during query cleaning; restoring original URL")
                url = make_url(settings.DATABASE_URL)
                if "?" in settings.DATABASE_URL:
                    base_url = settings.DATABASE_URL.split("?")[0]
                    url = make_url(base_url)
            elif url.password:
                logger.debug("Password preserved after query cleaning")

        port_str = url.port or 5432
        logger.debug(
            "Cleaned URL (removed sslmode/channel_binding)",
            extra={
                "url_masked": f"{url.drivername}://{url.username}:***@{url.host}:{port_str}/{url.database}",
                "password_present": bool(url.password),
            },
        )

    try:
        engine = create_async_engine(url, connect_args=connect_args, **kwargs)
        logger.info("Engine created successfully")
        return engine
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        port = url.port or 5432
        logger.error(
            "Failed to create engine",
            extra={
                "error_type": error_type,
                "error_message": error_msg,
                "url_masked": f"{url.drivername}://{url.username}:***@{url.host}:{port}/{url.database}",
            },
        )
        if (
            "password authentication failed" in error_msg.lower()
            or "authentication failed" in error_msg.lower()
        ):
            logger.warning(
                "Authentication error: check Neon password, URL-encoding of special chars, and user permissions"
            )

        raise


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
