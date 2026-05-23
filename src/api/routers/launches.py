from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.dependencies import get_db
from src.models.db import Launch, LaunchCore
from src.models.schemas import LandingStats, LaunchListItem, LaunchSchema

router = APIRouter()


@router.get("/", response_model=list[LaunchListItem])
async def list_launches(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    success: bool | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[Launch]:
    stmt = select(Launch).order_by(Launch.date_utc.desc()).limit(limit).offset(offset)
    if success is not None:
        stmt = stmt.where(Launch.success == success)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/stats/landing", response_model=LandingStats)
async def landing_stats(db: AsyncSession = Depends(get_db)) -> LandingStats:
    result = await db.execute(
        select(LaunchCore).where(LaunchCore.landing_attempt == True)  # noqa: E712
    )
    cores = list(result.scalars().all())

    rtls = [c for c in cores if c.landing_type == "RTLS"]
    asds = [c for c in cores if c.landing_type == "ASDS"]

    return LandingStats(
        total_attempts=len(cores),
        total_successes=sum(1 for c in cores if c.landing_success),
        rtls_attempts=len(rtls),
        rtls_successes=sum(1 for c in rtls if c.landing_success),
        asds_attempts=len(asds),
        asds_successes=sum(1 for c in asds if c.landing_success),
    )


@router.get("/{launch_id}", response_model=LaunchSchema)
async def get_launch(launch_id: str, db: AsyncSession = Depends(get_db)) -> Launch:
    stmt = (
        select(Launch)
        .where(Launch.id == launch_id)
        .options(selectinload(Launch.launch_cores))
    )
    result = await db.execute(stmt)
    launch = result.scalar_one_or_none()
    if launch is None:
        raise HTTPException(status_code=404, detail=f"Launch '{launch_id}' not found")
    return launch
