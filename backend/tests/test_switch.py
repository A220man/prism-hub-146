"""Smoke test for switch statement recognition / jump table analysis."""
import sys
sys.path.insert(0, '..')

import pytest

from httpx import AsyncClient, ASGITransport
from main import app

transport = ASGITransport(app=app)


@pytest.mark.asyncio
async def test_switch_analyze_endpoint():
    """Test that the switch analyze endpoint recognizes jump table patterns."""
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Use 0x402000 which has exactly 3 cases in SWITCH_DB
        request_data = {
            "function_address": "0x402000",
            "jump_table_address": "0x404000",
            "switch_variable": "ecx",
            "cases": [
                {"case_value": 10, "target_address": "0x402100", "target_function": "case_ten_handler"},
                {"case_value": 20, "target_address": "0x402150", "target_function": "case_twenty_handler"},
                {"case_value": 30, "target_address": "0x4021a0", "target_function": "case_thirty_handler"},
            ],
            "default_case": "default_handler",
        }
        response = await client.post("/api/switch/analyze", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["function_address"] == "0x402000"
        assert data["jump_table_address"] == "0x404000"
        assert data["switch_variable"] == "ecx"
        assert len(data["recognized_cases"]) == 3
        # Check first case
        assert data["recognized_cases"][0]["case_value"] == 10
        assert data["recognized_cases"][0]["target_function"] == "case_ten_handler"
        # Check decompiled output contains switch/case
        assert "switch (ecx) {" in data["decompiled_output"]
        assert "case 10:" in data["decompiled_output"]
        assert "case 20:" in data["decompiled_output"]
        assert "case 30:" in data["decompiled_output"]
        assert "default:" in data["decompiled_output"]
        assert "break;" in data["decompiled_output"]


@pytest.mark.asyncio
async def test_switch_analyze_no_database():
    """Test switch analysis when no database entry exists."""
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        request_data = {
            "function_address": "0x500000",
            "jump_table_address": "0x600000",
            "switch_variable": "index",
            "cases": [
                {"case_value": 10, "target_address": "0x700000"},
            ],
        }
        response = await client.post("/api/switch/analyze", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["function_address"] == "0x500000"
        assert len(data["recognized_cases"]) == 1
        assert data["recognized_cases"][0]["case_value"] == 10
        # Without target_function, should generate sub_ address
        assert "sub_700000" in data["decompiled_output"] or "default" in data["decompiled_output"]
