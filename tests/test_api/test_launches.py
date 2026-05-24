import pytest
from sqlalchemy.dialects.postgresql import insert

from src.models.db import Launch, Launchpad
import datetime


@pytest.fixture(autouse=True)
async def seed_launches(db_session):
    """Insert a minimal launchpad + launch for route testing."""
    await db_session.execute(
        insert(Launchpad).values(
            id="pad-test",
            name="Test Pad",
            full_name="Test Launchpad",
            locality="Cape Canaveral",
            region="Florida",
            latitude=28.561,
            longitude=-80.577,
            launch_attempts=1,
            launch_successes=1,
        ).on_conflict_do_nothing()
    )
    await db_session.execute(
        insert(Launch).values(
            id="launch-test-1",
            flight_number=99,
            name="Test Mission",
            date_utc=datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc),
            success=True,
            details="Test details",
            rocket_id="5e9d0d95eda69973a809d1ec",
            launchpad_id="pad-test",
        ).on_conflict_do_nothing()
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_list_launches_returns_list(api_client):
    response = await api_client.get("/launches/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_launches_filter_by_success(api_client):
    response = await api_client.get("/launches/?success=true")
    assert response.status_code == 200
    data = response.json()
    assert all(item["success"] is True for item in data)


@pytest.mark.asyncio
async def test_get_launch_by_id(api_client):
    response = await api_client.get("/launches/launch-test-1")
    assert response.status_code == 200
    assert response.json()["flight_number"] == 99


@pytest.mark.asyncio
async def test_get_launch_not_found(api_client):
    response = await api_client.get("/launches/does-not-exist")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_landing_stats_returns_valid_shape(api_client):
    response = await api_client.get("/launches/stats/landing")
    assert response.status_code == 200
    data = response.json()
    assert "total_attempts" in data
    assert "success_rate_pct" in data
    assert 0.0 <= data["success_rate_pct"] <= 100.0
