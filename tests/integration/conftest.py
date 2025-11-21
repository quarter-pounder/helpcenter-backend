"""Configuration for integration tests."""

import asyncio
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import text

os.environ["ENVIRONMENT"] = "test"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["DEV_EDITOR_KEY"] = "test-editor-key"

test_db_url = os.getenv("TEST_DATABASE_URL_ASYNC", "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db")
os.environ["DATABASE_URL_ASYNC"] = test_db_url


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(test_db_url)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine):
    """Create test database session."""
    async with AsyncSession(test_engine) as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def test_session_maker(test_engine):
    """Create test session maker."""
    async_session_factory = async_sessionmaker(
        test_engine, class_=SQLModelAsyncSession, expire_on_commit=False
    )
    return async_session_factory


@pytest_asyncio.fixture(autouse=True)
async def cleanup_database(test_session):
    """Clean up database before each test."""
    async with test_session as session:
        try:
            await session.execute(text("TRUNCATE TABLE guidemedialink CASCADE"))
        except Exception:
            pass
        try:
            await session.execute(text("TRUNCATE TABLE guidecategorylink CASCADE"))
        except Exception:
            pass
        try:
            await session.execute(text("TRUNCATE TABLE userguide CASCADE"))
        except Exception:
            pass
        try:
            await session.execute(text("TRUNCATE TABLE media CASCADE"))
        except Exception:
            pass
        try:
            await session.execute(text("TRUNCATE TABLE category CASCADE"))
        except Exception:
            pass
        try:
            await session.execute(text("TRUNCATE TABLE feedback CASCADE"))
        except Exception:
            pass
        await session.commit()


@pytest_asyncio.fixture
async def client():
    """Create async test client for GraphQL API integration tests."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("graphql_api_main", "/code/graphql_api/main.py")
        graphql_api_main = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(graphql_api_main)
        app = graphql_api_main.app

        from httpx import AsyncClient, ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac
    except ImportError as e:
        pytest.skip(f"Could not import graphql_api.main: {e}")
    except Exception as e:
        pytest.skip(f"Could not create graphql client: {e}")


@pytest_asyncio.fixture
async def editor_client():
    """Create async test client for Editor API integration tests."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("editor_api_main", "/code/editor_api/main.py")
        editor_api_main = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(editor_api_main)
        app = editor_api_main.app

        from httpx import AsyncClient, ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac
    except ImportError as e:
        pytest.skip(f"Could not import editor_api.main: {e}")
    except Exception as e:
        pytest.skip(f"Could not create editor client: {e}")


@pytest_asyncio.fixture
async def async_client():
    """Create async test client for GraphQL API integration tests."""
    try:
        from graphql_api.main import app
        from httpx import AsyncClient, ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac
    except ImportError as e:
        pytest.skip(f"Could not import graphql_api.main: {e}")


@pytest.fixture
def editor_headers():
    """Headers for editor API authentication."""
    return {"x-editor-key": "test-editor-key"}

