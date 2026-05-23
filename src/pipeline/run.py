import asyncio
import logging

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.config import settings
from src.models.db import Base
from src.pipeline.fetcher import SpaceXClient
from src.pipeline.loader import upsert_cores, upsert_launchpads, upsert_launches
from src.pipeline.transformer import normalize_cores, normalize_launchpads, normalize_launches

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


async def run_pipeline() -> None:
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False)
    client = SpaceXClient()

    log.info("Fetching data from SpaceX API (3 endpoints in parallel)...")
    raw_launches, raw_launchpads, raw_cores = await asyncio.gather(
        client.fetch_all_launches(),
        client.fetch_all_launchpads(),
        client.fetch_all_cores(),
    )
    log.info("Fetched %d launches, %d launchpads, %d cores", len(raw_launches), len(raw_launchpads), len(raw_cores))

    log.info("Transforming...")
    launches_df = normalize_launches(raw_launches)
    launchpads_df = normalize_launchpads(raw_launchpads)
    cores_df = normalize_cores(raw_cores)
    log.info("Filtered to %d Falcon 9 launches", len(launches_df))

    log.info("Loading into PostgreSQL (upsert)...")
    async with Session() as session:
        async with session.begin():
            await upsert_launchpads(session, launchpads_df)
            await upsert_cores(session, cores_df)
            await upsert_launches(session, launches_df)

    log.info("Pipeline complete. %d launches in database.", len(launches_df))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_pipeline())
