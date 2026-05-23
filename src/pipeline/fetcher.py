import logging
from typing import Any, cast

import httpx

from src.config import settings

log = logging.getLogger(__name__)

TIMEOUT_S = 30.0
MAX_RETRIES = 3


class SpaceXClient:
    """HTTP client for the SpaceX REST API v4."""

    def __init__(self, base_url: str = settings.spacex_api_base_url) -> None:
        self.base_url = base_url

    async def _get(self, path: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    response = await client.get(f"{self.base_url}{path}")
                    response.raise_for_status()
                    return cast(list[dict[str, Any]], response.json())
                except httpx.HTTPStatusError as exc:
                    log.warning("HTTP %s on %s (attempt %d/%d)", exc.response.status_code, path, attempt, MAX_RETRIES)
                    if attempt == MAX_RETRIES:
                        raise
                except httpx.RequestError as exc:
                    log.warning("Request error on %s (attempt %d/%d): %s", path, attempt, MAX_RETRIES, exc)
                    if attempt == MAX_RETRIES:
                        raise
        return []

    async def fetch_all_launches(self) -> list[dict[str, Any]]:
        log.info("Fetching launches from SpaceX API")
        return await self._get("/launches")

    async def fetch_all_launchpads(self) -> list[dict[str, Any]]:
        log.info("Fetching launchpads from SpaceX API")
        return await self._get("/launchpads")

    async def fetch_all_cores(self) -> list[dict[str, Any]]:
        log.info("Fetching cores from SpaceX API")
        return await self._get("/cores")
