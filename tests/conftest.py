import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.config import settings
from src.models.db import Base
from src.api.main import app

# Separate test database — never touches the development DB
_BASE_URL = settings.database_url.rsplit("/", 1)[0]
TEST_DATABASE_URL = _BASE_URL + "/falcon9_test"


@pytest_asyncio.fixture
async def engine():
    # CREATE DATABASE cannot run inside a transaction; connect to the
    # maintenance DB with autocommit and create falcon9_test if absent.
    admin_engine = create_async_engine(_BASE_URL + "/postgres", isolation_level="AUTOCOMMIT")
    async with admin_engine.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = 'falcon9_test'")
        )
        if not exists:
            await conn.execute(text("CREATE DATABASE falcon9_test"))
    await admin_engine.dispose()

    eng = create_async_engine(TEST_DATABASE_URL)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def api_client(engine):
    Session = async_sessionmaker(engine, expire_on_commit=False)
    app.state.engine = engine
    app.state.session_factory = Session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
