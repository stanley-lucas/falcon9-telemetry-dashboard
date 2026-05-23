import pandas as pd
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db import Core, Launch, LaunchCore, Launchpad


async def upsert_launchpads(session: AsyncSession, df: pd.DataFrame) -> None:
    for _, row in df.iterrows():
        data = row.to_dict()
        stmt = insert(Launchpad).values(data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={col: stmt.excluded[col] for col in data if col != "id"},
        )
        await session.execute(stmt)


async def upsert_cores(session: AsyncSession, df: pd.DataFrame) -> None:
    for _, row in df.iterrows():
        data = row.to_dict()
        stmt = insert(Core).values(data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["serial"],
            set_={col: stmt.excluded[col] for col in data if col != "serial"},
        )
        await session.execute(stmt)


async def upsert_launches(session: AsyncSession, df: pd.DataFrame) -> None:
    for _, row in df.iterrows():
        cores_data: list[dict] = row.get("cores", []) or []
        launch_data = row.drop("cores").to_dict()

        stmt = insert(Launch).values(launch_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={col: stmt.excluded[col] for col in launch_data if col != "id"},
        )
        await session.execute(stmt)

        # Delete-and-reinsert for idempotency — see ARCHITECTURE.md §6
        await session.execute(delete(LaunchCore).where(LaunchCore.launch_id == launch_data["id"]))

        for core in cores_data:
            if not core.get("core"):
                continue
            await session.execute(
                insert(LaunchCore).values(
                    launch_id=launch_data["id"],
                    core_serial=core.get("core"),
                    flight=core.get("flight"),
                    gridfins=core.get("gridfins"),
                    legs=core.get("legs"),
                    reused=core.get("reused"),
                    landing_attempt=core.get("landing_attempt"),
                    landing_success=core.get("landing_success"),
                    landing_type=core.get("landing_type"),
                )
            )
