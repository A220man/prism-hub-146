import pytest
from httpx import AsyncClient, ASGITransport
from main import app

transport = ASGITransport(app=app)

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "prism-hub"}

@pytest.mark.asyncio
async def test_version_endpoint():
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/version")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "prism-hub"
        assert "version" in data

