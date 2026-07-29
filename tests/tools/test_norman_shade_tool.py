"""Tests for the Norman ShadeAuto HUB02 native tool module.

Covers availability checks, registration parsing, UID mappings, percent inversion math,
single and all-shade control payloads, boundary conditions, error handling, network timeouts,
non-zero Norman API errors, and sequential execution timing for set_all_shades.
"""

import json
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
import pytest
import aiohttp

from tools.norman_shade_tool import (
    KNOWN_SHADES,
    REVERSE_SHADE_MAP,
    _check_norman_available,
    reset_registration_cache,
    _async_register,
    _get_thing_name,
    _async_get_shades,
    _async_set_shade,
    _async_set_all_shades,
    _handle_get_shades,
    _handle_set_shade,
    _handle_set_all_shades,
    _get_config,
)


@pytest.fixture(autouse=True)
def reset_cache_between_tests():
    """Reset registration cache and config overrides before each test."""
    reset_registration_cache()
    import tools.norman_shade_tool as nst
    nst._NORMAN_HUB_HOST = ""
    nst._NORMAN_HUB_PORT = None


def make_mock_response(status=200, json_data=None):
    """Helper to create a properly configured mock response context manager for aiohttp."""
    mock_resp = MagicMock()
    mock_resp.status = status
    mock_resp.json = AsyncMock(return_value=json_data)
    mock_resp.raise_for_status = MagicMock()

    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_resp)
    cm.__aexit__ = AsyncMock(return_value=None)
    return cm


# ---------------------------------------------------------------------------
# 1. Availability Check Tests
# ---------------------------------------------------------------------------

class TestAvailability:
    def test_unavailable_when_env_not_set(self, monkeypatch):
        monkeypatch.delenv("NORMAN_HUB_HOST", raising=False)
        assert _check_norman_available() is False

    def test_available_when_env_set(self, monkeypatch):
        monkeypatch.setenv("NORMAN_HUB_HOST", "192.168.5.117")
        assert _check_norman_available() is True

    def test_custom_port_config(self, monkeypatch):
        monkeypatch.setenv("NORMAN_HUB_HOST", "192.168.5.117")
        monkeypatch.setenv("NORMAN_HUB_PORT", "10125")
        host, port = _get_config()
        assert host == "192.168.5.117"
        assert port == 10125


# ---------------------------------------------------------------------------
# 2. Known UID Mappings & Inversion Math
# ---------------------------------------------------------------------------

class TestMappingsAndMath:
    def test_known_uids(self):
        assert KNOWN_SHADES["left"] == 28713
        assert KNOWN_SHADES["center"] == 14535
        assert KNOWN_SHADES["right"] == 16493

    def test_reverse_mapping(self):
        assert REVERSE_SHADE_MAP[28713] == "left"
        assert REVERSE_SHADE_MAP[14535] == "center"
        assert REVERSE_SHADE_MAP[16493] == "right"

    @pytest.mark.parametrize("percent_closed, expected_norman_pos", [
        (0, 100),    # 0% closed = 100 Norman (fully open)
        (20, 80),    # 20% closed = 80 Norman
        (50, 50),    # 50% closed = 50 Norman
        (100, 0),    # 100% closed = 0 Norman (fully closed)
    ])
    def test_percent_inversion_calculation(self, percent_closed, expected_norman_pos):
        norman_pos = 100 - percent_closed
        assert norman_pos == expected_norman_pos
        # Vice-versa
        assert 100 - norman_pos == percent_closed


# ---------------------------------------------------------------------------
# 3. Registration Parsing & Caching
# ---------------------------------------------------------------------------

class TestRegistration:
    @pytest.mark.asyncio
    async def test_registration_success(self, monkeypatch):
        monkeypatch.setenv("NORMAN_HUB_HOST", "192.168.5.117")

        mock_cm = make_mock_response(json_data={
            "ThingName": "Hub_12345",
            "Peripherals": [
                {"PeripheralUID": 28713, "BottomRailPosition": 100},
                {"PeripheralUID": 14535, "BottomRailPosition": 50},
                {"PeripheralUID": 16493, "BottomRailPosition": 0},
            ]
        })

        mock_session = MagicMock()
        mock_session.post.return_value = mock_cm

        thing_name, peripherals = await _get_thing_name(mock_session, "http://192.168.5.117:10123", force_refresh=True)
        assert thing_name == "Hub_12345"
        assert len(peripherals) == 3
        assert peripherals[0]["PeripheralUID"] == 28713


# ---------------------------------------------------------------------------
# 4. Get Shades Status
# ---------------------------------------------------------------------------

class TestGetShades:
    @pytest.mark.asyncio
    async def test_async_get_shades(self, monkeypatch):
        monkeypatch.setenv("NORMAN_HUB_HOST", "192.168.5.117")

        mock_cm = make_mock_response(json_data={
            "ThingName": "Hub_9999",
            "Peripherals": [
                {"PeripheralUID": 28713, "BottomRailPosition": 100},  # 0% closed
                {"PeripheralUID": 14535, "BottomRailPosition": 80},   # 20% closed
                {"PeripheralUID": 16493, "BottomRailPosition": 0},    # 100% closed
            ]
        })

        with patch("aiohttp.ClientSession.post", return_value=mock_cm):
            result = await _async_get_shades()

        assert result["count"] == 3
        assert result["thing_name"] == "Hub_9999"
        shades = {s["name"]: s for s in result["shades"]}

        assert shades["left"]["uid"] == 28713
        assert shades["left"]["norman_position"] == 100
        assert shades["left"]["percent_closed"] == 0

        assert shades["center"]["uid"] == 14535
        assert shades["center"]["norman_position"] == 80
        assert shades["center"]["percent_closed"] == 20

        assert shades["right"]["uid"] == 16493
        assert shades["right"]["norman_position"] == 0
        assert shades["right"]["percent_closed"] == 100


# ---------------------------------------------------------------------------
# 5. Set Single Shade Control Payloads & Boundaries
# ---------------------------------------------------------------------------

class TestSetShade:
    @pytest.mark.parametrize("shade_name, uid", [
        ("left", 28713),
        ("center", 14535),
        ("right", 16493),
        ("LEFT", 28713),  # case-insensitive check
    ])
    @pytest.mark.asyncio
    async def test_left_center_right_payloads(self, monkeypatch, shade_name, uid):
        monkeypatch.setenv("NORMAN_HUB_HOST", "192.168.5.117")

        reg_cm = make_mock_response(json_data={"ThingName": "Hub_1001"})
        ctrl_cm = make_mock_response(json_data={"Error": 0})

        with patch("aiohttp.ClientSession.post", side_effect=[reg_cm, ctrl_cm]) as mock_post:
            res = await _async_set_shade(shade_name, 20)

        assert res["success"] is True
        assert res["shade"] == shade_name.lower().strip()
        assert res["uid"] == uid
        assert res["percent_closed"] == 20
        assert res["norman_position"] == 80

        # Verify second call (the control payload)
        ctrl_call_kwargs = mock_post.call_args_list[1].kwargs
        payload = ctrl_call_kwargs["json"]
        assert payload["PeripheralUID"] == uid
        assert payload["BottomRailPosition"] == 80
        assert payload["ThingName"] == "Hub_1001"
        assert "Timestamp" in payload
        assert "TaskID" in payload

    @pytest.mark.parametrize("percent_closed, expected_norman", [(0, 100), (100, 0)])
    @pytest.mark.asyncio
    async def test_boundary_cases_0_and_100(self, monkeypatch, percent_closed, expected_norman):
        monkeypatch.setenv("NORMAN_HUB_HOST", "192.168.5.117")

        reg_cm = make_mock_response(json_data={"ThingName": "Hub_1001"})
        ctrl_cm = make_mock_response(json_data={"Error": 0})

        with patch("aiohttp.ClientSession.post", side_effect=[reg_cm, ctrl_cm]):
            res = await _async_set_shade("center", percent_closed)

        assert res["percent_closed"] == percent_closed
        assert res["norman_position"] == expected_norman


# ---------------------------------------------------------------------------
# 6. Error & Validation Handling
# ---------------------------------------------------------------------------

class TestValidationAndErrors:
    @pytest.mark.asyncio
    async def test_invalid_shade_name(self, monkeypatch):
        monkeypatch.setenv("NORMAN_HUB_HOST", "192.168.5.117")
        with pytest.raises(ValueError, match="Invalid shade 'top'"):
            await _async_set_shade("top", 50)

    @pytest.mark.parametrize("invalid_percent", [-1, 101, 150, "fifty"])
    @pytest.mark.asyncio
    async def test_invalid_percentage(self, monkeypatch, invalid_percent):
        monkeypatch.setenv("NORMAN_HUB_HOST", "192.168.5.117")
        with pytest.raises(ValueError):
            await _async_set_shade("left", invalid_percent)

    @pytest.mark.asyncio
    async def test_norman_nonzero_error(self, monkeypatch):
        monkeypatch.setenv("NORMAN_HUB_HOST", "192.168.5.117")

        reg_cm = make_mock_response(json_data={"ThingName": "Hub_1001"})
        ctrl_fail_cm = make_mock_response(json_data={"Error": 102, "Message": "Session invalid"})

        with patch("aiohttp.ClientSession.post", side_effect=[reg_cm, ctrl_fail_cm, reg_cm, ctrl_fail_cm]):
            with pytest.raises(ValueError, match="error code 102"):
                await _async_set_shade("left", 50)

    @pytest.mark.asyncio
    async def test_network_timeout(self, monkeypatch):
        monkeypatch.setenv("NORMAN_HUB_HOST", "192.168.5.117")
        with patch("aiohttp.ClientSession.post", side_effect=asyncio.TimeoutError("Connection timed out")):
            with pytest.raises(asyncio.TimeoutError):
                await _async_set_shade("left", 50)

    def test_sync_handler_tool_error_formatting(self, monkeypatch):
        monkeypatch.setenv("NORMAN_HUB_HOST", "192.168.5.117")

        # Invalid shade via handler
        res = _handle_set_shade({"shade": "invalid_shade", "percent_closed": 50})
        assert "tool_error" in res or "Invalid shade" in res

        # Missing parameter
        res_missing = _handle_set_shade({"shade": "left"})
        assert "Missing required parameter" in res_missing


# ---------------------------------------------------------------------------
# 7. Set All Shades Sequential Execution
# ---------------------------------------------------------------------------

class TestSetAllShades:
    @pytest.mark.asyncio
    async def test_three_sequential_commands_with_delay(self, monkeypatch):
        monkeypatch.setenv("NORMAN_HUB_HOST", "192.168.5.117")

        reg_cm = make_mock_response(json_data={"ThingName": "Hub_1001"})
        ctrl_cm = make_mock_response(json_data={"Error": 0})

        sleep_times = []

        async def mock_sleep(seconds):
            sleep_times.append(seconds)

        with patch("aiohttp.ClientSession.post", side_effect=[reg_cm, ctrl_cm, ctrl_cm, ctrl_cm]), patch("asyncio.sleep", side_effect=mock_sleep):
            res = await _async_set_all_shades(30)

        assert res["success"] is True
        assert len(res["shades"]) == 3
        names_called = [s["shade"] for s in res["shades"]]
        assert names_called == ["left", "center", "right"]

        # Verify at least two 0.75s sleeps between 3 sequential calls
        assert len(sleep_times) == 2
        assert all(t >= 0.75 for t in sleep_times)
