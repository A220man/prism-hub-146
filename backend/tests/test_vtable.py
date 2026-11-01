import pytest
from httpx import AsyncClient, ASGITransport
from main import app

transport = ASGITransport(app=app)


@pytest.mark.asyncio
async def test_vtable_analyze_endpoint():
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        request_data = {
            "class_name": "BaseClass",
            "vtable_address": "0x401000",
            "entries": [
                {"index": 0, "address": "0x401000"},
                {"index": 1, "address": "0x401050"},
                {"index": 2, "address": "0x4010a0"},
            ]
        }
        response = await client.post("/api/vtable/analyze", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["class_name"] == "BaseClass"
        assert data["vtable_address"] == "0x401000"
        assert len(data["resolved_entries"]) == 3
        # Check first entry resolved
        assert data["resolved_entries"][0]["function_name"] == "BaseClass::virtualFunc1"
        assert data["resolved_entries"][0]["signature"] == "virtualFunc1(int) -> void"
        # Check call sites included
        assert len(data["call_sites"]) > 0


@pytest.mark.asyncio
async def test_vtable_analyze_unknown_function():
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        request_data = {
            "class_name": "UnknownClass",
            "vtable_address": "0x500000",
            "entries": [
                {"index": 0, "address": "0x500000"},
            ]
        }
        response = await client.post("/api/vtable/analyze", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["class_name"] == "UnknownClass"
        # Unknown function gets generic name
        assert data["resolved_entries"][0]["function_name"] == "sub_500000"


@pytest.mark.asyncio
async def test_list_known_functions():
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/vtable/functions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 7
        assert data[0]["address"] == "0x401000"
        assert data[0]["name"] == "BaseClass::virtualFunc1"
