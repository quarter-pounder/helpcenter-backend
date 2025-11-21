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

    # Log connection details (without password)
    port = url.port or 5432
    print(f"[db] Connecting as user: {url.username}")
    print(f"[db] Host: {url.host}, Port: {port}, Database: {url.database}")

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
            print("[db] SSL context configured for Neon/secure connection")

        original_username = url.username
        original_password = url.password
        print(f"[db] Original username: {original_username}")
        print(f"[db] Original password present: {bool(original_password)}")
        if original_password and original_password != original_password.strip():
            print("[db] WARNING: Password has leading/trailing whitespace!")

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
                print("[db] ERROR: Password changed during query cleaning!")
                print("[db] Restoring original URL to preserve password")
                url = make_url(settings.DATABASE_URL)
                if "?" in settings.DATABASE_URL:
                    base_url = settings.DATABASE_URL.split("?")[0]
                    url = make_url(base_url)
            elif url.password:
                print("[db] Password preserved after query cleaning")

        port_str = url.port or 5432
        print(
            f"[db] Cleaned URL (removed sslmode/channel_binding): "
            f"{url.drivername}://{url.username}:***@{url.host}:{port_str}/{url.database}"
        )
        print(f"[db] Password still present after cleaning: {bool(url.password)}")

    try:
        engine = create_async_engine(url, connect_args=connect_args, **kwargs)
        print("[db] Engine created successfully")
        return engine
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"[db] ERROR creating engine: {error_type}: {error_msg}")

        port = url.port or 5432
        print(
            f"[db] Connection URL (masked): "
            f"{url.drivername}://{url.username}:***@{url.host}:{port}/{url.database}"
        )

        if (
            "password authentication failed" in error_msg.lower()
            or "authentication failed" in error_msg.lower()
        ):
            print(
                "[db] AUTHENTICATION ERROR: Check that: "
                "1) Password matches the user password in Neon, "
                "2) Password is URL-encoded if it contains special characters, "
                "3) User has correct permissions in Neon"
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
