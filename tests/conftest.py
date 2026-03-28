"""Shared pytest fixtures and configuration for all tests.

Provides an async test client, in-memory database session, and
common test data factories used across all test modules.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from api.db.models import Base
from api.db.session import get_db
from api.main import app

TEST_DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create an in-memory SQLite engine for each test function.

    Yields:
        AsyncEngine configured with the test database.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    """Provide a clean async database session for each test.

    Args:
        db_engine: Test database engine fixture.

    Yields:
        AsyncSession bound to the test database.
    """
    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    """Provide an async HTTP test client with the test DB injected.

    Overrides the get_db dependency so all requests use the test database.

    Args:
        db_session: Test database session fixture.

    Yields:
        AsyncClient for making requests against the test app.
    """
    async def override_get_db():
        """Dependency override returning the test session."""
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
