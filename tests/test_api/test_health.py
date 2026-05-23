import pytest


@pytest.mark.asyncio
async def test_health_returns_ok(api_client):
    response = await api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
