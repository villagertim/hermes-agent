"""Norman ShadeAuto HUB02 native tool module for Hermes.

Registers three LLM-callable tools for motorized shade control:
- ``norman_get_shades`` -- get status of left, center, and right shades
- ``norman_set_shade`` -- set position of a single shade (left, center, or right)
- ``norman_set_all_shades`` -- set position for all shades sequentially with timing delays

Norman Hub uses BottomRailPosition: 100 = fully open, 0 = fully closed.
Hermes interface presents percent_closed: 0 = fully open, 100 = fully closed.
Conversion: BottomRailPosition = 100 - percent_closed.

Configuration via env:
- ``NORMAN_HUB_HOST`` (required for availability)
- ``NORMAN_HUB_PORT`` (optional, default 10123)
"""

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from tools.registry import registry, tool_error

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration & Hardware Mapping
# ---------------------------------------------------------------------------

_NORMAN_HUB_HOST: str = ""
_NORMAN_HUB_PORT: Optional[int] = None

# Known shade mappings for Norman HUB02
KNOWN_SHADES: Dict[str, int] = {
    "left": 28713,
    "center": 14535,
    "right": 16493,
}

REVERSE_SHADE_MAP: Dict[int, str] = {v: k for k, v in KNOWN_SHADES.items()}

# Lazy registration cache
_cached_thing_name: Optional[str] = None


def _get_config() -> Tuple[str, int]:
    """Return (host, port) from env vars or testing overrides."""
    host = (_NORMAN_HUB_HOST or os.getenv("NORMAN_HUB_HOST", "")).strip()
    port_val = _NORMAN_HUB_PORT
    if port_val is None:
        port_str = os.getenv("NORMAN_HUB_PORT", "10123").strip()
        port_val = int(port_str) if port_str.isdigit() else 10123
    return host, port_val


def reset_registration_cache() -> None:
    """Reset cached registration state (used in testing and reconnects)."""
    global _cached_thing_name
    _cached_thing_name = None


# ---------------------------------------------------------------------------
# Async Helpers
# ---------------------------------------------------------------------------

async def _get_thing_name(
    session: aiohttp.ClientSession,
    base_url: str,
    force_refresh: bool = False
) -> Tuple[str, List[Dict[str, Any]]]:
    """Perform registration with Norman Hub and return (ThingName, Peripherals)."""
    global _cached_thing_name
    if not force_refresh and _cached_thing_name:
        return _cached_thing_name, []

    ts = int(time.time() * 1000)
    reg_url = f"{base_url}/NM/v1/registration"
    timeout = aiohttp.ClientTimeout(total=10)

    async with session.post(reg_url, json={"Timestamp": ts}, timeout=timeout) as resp:
        resp.raise_for_status()
        data = await resp.json()
        if not isinstance(data, dict):
            raise ValueError(f"Invalid registration response from Norman Hub (not a dict): {data!r}")
        thing_name = data.get("ThingName")
        if not thing_name:
            raise ValueError(f"Registration response missing 'ThingName': {data}")

        _cached_thing_name = thing_name
        peripherals = data.get("Peripherals")
        peripherals_list = peripherals if isinstance(peripherals, list) else []
        return thing_name, peripherals_list


# Alias for backward compatibility / tests
_async_register = _get_thing_name


async def _async_get_shades() -> Dict[str, Any]:
    """Fetch status of known Norman shades."""
    host, port = _get_config()
    if not host:
        raise ValueError("NORMAN_HUB_HOST is not configured")

    base_url = f"http://{host}:{port}"

    async with aiohttp.ClientSession() as session:
        thing_name, peripherals = await _get_thing_name(session, base_url, force_refresh=True)

        periph_by_uid: Dict[int, Dict[str, Any]] = {}
        for p in peripherals:
            if isinstance(p, dict):
                uid = p.get("PeripheralUID") or p.get("UID")
                if uid is not None:
                    try:
                        periph_by_uid[int(uid)] = p
                    except (ValueError, TypeError):
                        pass

        shades_out = []
        for name, uid in KNOWN_SHADES.items():
            entry = periph_by_uid.get(uid, {})
            # Norman returns BottomRailPosition (100 = open, 0 = closed)
            norman_pos = entry.get("BottomRailPosition")
            if norman_pos is None:
                norman_pos = entry.get("Position")

            if norman_pos is not None and isinstance(norman_pos, (int, float)):
                norman_pos = int(norman_pos)
                percent_closed = max(0, min(100, 100 - norman_pos))
            else:
                norman_pos = None
                percent_closed = None

            shades_out.append({
                "name": name,
                "uid": uid,
                "norman_position": norman_pos,
                "percent_closed": percent_closed,
            })

        return {
            "count": len(shades_out),
            "thing_name": thing_name,
            "shades": shades_out,
        }


async def _async_set_shade(shade_name: str, percent_closed: int) -> Dict[str, Any]:
    """Set position for a single Norman shade."""
    if not isinstance(shade_name, str):
        raise ValueError(f"shade must be a string (got {type(shade_name).__name__})")

    clean_shade = shade_name.lower().strip()
    if clean_shade not in KNOWN_SHADES:
        valid_shades = ", ".join(sorted(KNOWN_SHADES.keys()))
        raise ValueError(f"Invalid shade '{shade_name}'. Allowed shades are: {valid_shades}")

    if not isinstance(percent_closed, int) or isinstance(percent_closed, bool) or percent_closed < 0 or percent_closed > 100:
        raise ValueError(f"percent_closed must be an integer between 0 and 100 (got {percent_closed!r})")

    uid = KNOWN_SHADES[clean_shade]
    norman_pos = 100 - percent_closed

    host, port = _get_config()
    if not host:
        raise ValueError("NORMAN_HUB_HOST is not configured")

    base_url = f"http://{host}:{port}"
    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession() as session:
        for attempt in range(2):
            force_reg = (attempt > 0)
            thing_name, _ = await _get_thing_name(session, base_url, force_refresh=force_reg)

            ts = int(time.time() * 1000)
            control_url = f"{base_url}/NM/v1/control"
            payload = {
                "PeripheralUID": uid,
                "BottomRailPosition": norman_pos,
                "TaskID": ts,
                "ThingName": thing_name,
                "Timestamp": ts,
            }

            async with session.post(control_url, json=payload, timeout=timeout) as resp:
                resp.raise_for_status()
                data = await resp.json()
                if not isinstance(data, dict):
                    raise ValueError(f"Invalid control response from Norman Hub (not a dict): {data!r}")

                err_code = data.get("Error")
                if err_code == 0:
                    return {
                        "success": True,
                        "shade": clean_shade,
                        "uid": uid,
                        "percent_closed": percent_closed,
                        "norman_position": norman_pos,
                    }

                # If non-zero error on first attempt, force re-registration once
                if attempt == 0:
                    logger.warning(
                        "Norman Hub control returned error %s on attempt 1. Re-registering and retrying...",
                        err_code
                    )
                    reset_registration_cache()
                    continue

                raise ValueError(f"Norman Hub returned error code {err_code} for shade '{clean_shade}': {data}")

    raise ValueError(f"Failed to control shade '{clean_shade}' after retries")


async def _async_set_all_shades(percent_closed: int) -> Dict[str, Any]:
    """Set position for all Norman shades sequentially with a 750ms delay."""
    if not isinstance(percent_closed, int) or isinstance(percent_closed, bool) or percent_closed < 0 or percent_closed > 100:
        raise ValueError(f"percent_closed must be an integer between 0 and 100 (got {percent_closed!r})")

    results = []
    shades_sequence = ["left", "center", "right"]

    for idx, shade in enumerate(shades_sequence):
        if idx > 0:
            await asyncio.sleep(0.75)
        res = await _async_set_shade(shade, percent_closed)
        results.append(res)

    return {
        "success": True,
        "percent_closed": percent_closed,
        "shades": results,
    }


# ---------------------------------------------------------------------------
# Sync Wrappers for Tool Registry
# ---------------------------------------------------------------------------

def _run_async(coro):
    """Run an async coroutine from a sync handler."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result(timeout=35)
    else:
        return asyncio.run(coro)


def _handle_get_shades(args: dict, **kw) -> str:
    """Handler for norman_get_shades tool."""
    try:
        result = _run_async(_async_get_shades())
        return json.dumps({"result": result})
    except Exception as e:
        logger.error("norman_get_shades error: %s", e)
        return tool_error(f"Failed to get Norman shades status: {e}")


def _handle_set_shade(args: dict, **kw) -> str:
    """Handler for norman_set_shade tool."""
    shade = args.get("shade")
    if not shade:
        return tool_error("Missing required parameter: 'shade'")

    percent_closed = args.get("percent_closed")
    if percent_closed is None:
        return tool_error("Missing required parameter: 'percent_closed'")

    try:
        percent_int = int(percent_closed)
    except (ValueError, TypeError):
        return tool_error(f"Invalid 'percent_closed' parameter (must be an integer 0..100): {percent_closed!r}")

    try:
        result = _run_async(_async_set_shade(shade, percent_int))
        return json.dumps({"result": result})
    except Exception as e:
        logger.error("norman_set_shade error for '%s': %s", shade, e)
        return tool_error(f"Failed to set Norman shade '{shade}': {e}")


def _handle_set_all_shades(args: dict, **kw) -> str:
    """Handler for norman_set_all_shades tool."""
    percent_closed = args.get("percent_closed")
    if percent_closed is None:
        return tool_error("Missing required parameter: 'percent_closed'")

    try:
        percent_int = int(percent_closed)
    except (ValueError, TypeError):
        return tool_error(f"Invalid 'percent_closed' parameter (must be an integer 0..100): {percent_closed!r}")

    try:
        result = _run_async(_async_set_all_shades(percent_int))
        return json.dumps({"result": result})
    except Exception as e:
        logger.error("norman_set_all_shades error: %s", e)
        return tool_error(f"Failed to set all Norman shades: {e}")


# ---------------------------------------------------------------------------
# Availability Check
# ---------------------------------------------------------------------------

def _check_norman_available() -> bool:
    """Tool is available only when NORMAN_HUB_HOST is set."""
    host, _ = _get_config()
    return bool(host)


# ---------------------------------------------------------------------------
# Tool Schemas & Registration
# ---------------------------------------------------------------------------

NORMAN_GET_SHADES_SCHEMA = {
    "name": "norman_get_shades",
    "description": (
        "Get status of Norman motorized shades (left, center, right), returning "
        "UID, reported Norman position, and percent closed (0% = fully open, 100% = fully closed)."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

NORMAN_SET_SHADE_SCHEMA = {
    "name": "norman_set_shade",
    "description": (
        "Set position of a specific Norman motorized shade (left, center, or right). "
        "percent_closed: 0 = fully open, 100 = fully closed."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "shade": {
                "type": "string",
                "enum": ["left", "center", "right"],
                "description": "Target shade name: 'left', 'center', or 'right'.",
            },
            "percent_closed": {
                "type": "integer",
                "description": "Desired closed percentage: 0 = fully open, 100 = fully closed.",
            },
        },
        "required": ["shade", "percent_closed"],
    },
}

NORMAN_SET_ALL_SHADES_SCHEMA = {
    "name": "norman_set_all_shades",
    "description": (
        "Set position for all Norman motorized shades (left, center, and right) "
        "sequentially with timing delays. percent_closed: 0 = fully open, 100 = fully closed."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "percent_closed": {
                "type": "integer",
                "description": "Desired closed percentage for all shades: 0 = fully open, 100 = fully closed.",
            },
        },
        "required": ["percent_closed"],
    },
}

registry.register(
    name="norman_get_shades",
    toolset="norman_shade",
    schema=NORMAN_GET_SHADES_SCHEMA,
    handler=_handle_get_shades,
    check_fn=_check_norman_available,
    emoji="🪟",
)

registry.register(
    name="norman_set_shade",
    toolset="norman_shade",
    schema=NORMAN_SET_SHADE_SCHEMA,
    handler=_handle_set_shade,
    check_fn=_check_norman_available,
    emoji="🪟",
)

registry.register(
    name="norman_set_all_shades",
    toolset="norman_shade",
    schema=NORMAN_SET_ALL_SHADES_SCHEMA,
    handler=_handle_set_all_shades,
    check_fn=_check_norman_available,
    emoji="🪟",
)
