from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.routers import health, launches
from src.models.db import Base
from src.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Django analogy: AppConfig.ready() — runs once at startup
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.state.engine = engine
    app.state.session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    yield
    await engine.dispose()


app = FastAPI(
    title="Falcon 9 Telemetry API",
    description="Historical launch data from SpaceX Falcon 9 missions",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(launches.router, prefix="/launches", tags=["launches"])
