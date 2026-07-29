"""Hermes Agent Tool Module for Lanai Shade Controller Service.

Placing this file in Hermes' `tools/` directory registers native LLM tools:
- ``norman_get_shades``: Query status of all lanai shades
- ``norman_set_shade``: Set position (0-100%) for a single shade ('left', 'center', 'right')
- ``norman_set_all_shades``: Set position (0-100%) for all shades simultaneously
- ``norman_set_override_hold``: Dynamically adjust physical remote override hold duration in minutes
- ``norman_set_vacation_mode``: Enable/disable Vacation Mode lock
- ``norman_clear_override``: Clear manual remote control override flag
"""

import json
import os
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def _get_service_config():
    base_url = os.getenv("LANAI_SHADE_SERVICE_URL", "http://localhost:38472").rstrip("/")
    api_key = os.getenv("SHADE_API_KEY", "YOUR_API_KEY_HERE")
    return base_url, api_key

def _make_api_request(endpoint: str, method: str = "GET", payload: Optional[dict] = None) -> Dict[str, Any]:
    base_url, api_key = _get_service_config()
    url = f"{base_url}{endpoint}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    data_bytes = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else str(e)
        return {"error": True, "status_code": e.code, "detail": error_body}
    except Exception as e:
        return {"error": True, "detail": f"Failed to connect to Lanai Shade Service at {url}: {e}"}

def norman_get_shades() -> str:
    """Get current open/close status, positions (0%=Closed, 100%=Open), and remote override flags for all Lanai shades (left, center, right)."""
    res = _make_api_request("/api/shades", method="GET")
    return json.dumps(res, indent=2)

def norman_set_shade(shade: str, position: int) -> str:
    """Set position percentage for a specific Lanai shade.
    
    CRITICAL RULE FOR LLM: Pass the user's requested open percentage DIRECTLY to position.
    DO NOT perform math or subtract from 100!
    - Example: '25% open' -> position = 25
    - Example: '75% open' -> position = 75
    - Example: '0% open' (closed) -> position = 0
    - Example: '100% open' (fully open) -> position = 100
    
    Args:
        shade: Target shade name ('left', 'center', 'right', or 'all').
        position: Target open percentage directly from 0 (Fully Closed) to 100 (Fully Open).
    """
    shade = shade.lower().strip()
    payload = {"position": max(0, min(100, int(position)))}
    res = _make_api_request(f"/api/shades/{shade}/position", method="POST", payload=payload)
    return json.dumps(res, indent=2)

def norman_set_all_shades(position: int) -> str:
    """Set position percentage for ALL Lanai shades simultaneously.
    
    CRITICAL RULE FOR LLM: Pass the user's requested open percentage DIRECTLY to position.
    DO NOT perform math or subtract from 100!
    - Example: '25% open' -> position = 25
    - Example: '75% open' -> position = 75
    - Example: '0% open' (closed) -> position = 0
    - Example: '100% open' (fully open) -> position = 100
    
    Args:
        position: Target open percentage directly from 0 (Fully Closed) to 100 (Fully Open).
    """
    payload = {"position": max(0, min(100, int(position)))}
    res = _make_api_request("/api/shades/all/position", method="POST", payload=payload)
    return json.dumps(res, indent=2)

def norman_set_override_hold(minutes: int) -> str:
    """Dynamically set the hold-off duration in minutes for physical remote control overrides.
    
    Args:
        minutes: Number of minutes to pause background automation after a physical remote is used (resets to 120m default at scheduled boundaries).
    """
    payload = {"minutes": max(1, int(minutes))}
    res = _make_api_request("/api/config/override-duration", method="POST", payload=payload)
    return json.dumps(res, indent=2)

def norman_set_vacation_mode(enabled: bool) -> str:
    """Enable or disable Vacation Mode. When active, all shades are locked at 100% (closed).
    
    Args:
        enabled: True to lock shades in vacation mode, False to return to normal mode.
    """
    payload = {"enabled": bool(enabled)}
    res = _make_api_request("/api/mode/vacation", method="POST", payload=payload)
    return json.dumps(res, indent=2)

def norman_clear_override(shade: str = "all") -> str:
    """Manually clear active physical remote control override hold on shades.
    
    Args:
        shade: Target shade ('left', 'center', 'right', or 'all').
    """
    res = _make_api_request(f"/api/shades/{shade}/override/clear", method="POST")
    return json.dumps(res, indent=2)

def norman_enable_sun_tracker() -> str:
    """Enable automatic sun tracking for lanai shades."""
    res = _make_api_request("/api/v1/sun-tracker/enable", method="POST")
    return json.dumps(res, indent=2)

def norman_disable_sun_tracker() -> str:
    """Disable automatic sun tracking for lanai shades."""
    res = _make_api_request("/api/v1/sun-tracker/disable", method="POST")
    return json.dumps(res, indent=2)

def norman_get_sun_tracker_status() -> str:
    """Get live solar position, glare status, and Sun Tracker operational state."""
    res = _make_api_request("/api/v1/sun-tracker/status", method="GET")
    return json.dumps(res, indent=2)

# ---------------------------------------------------------------------------
# LLM Tool Registration
# ---------------------------------------------------------------------------

from tools.registry import registry

def _check_shade_available() -> bool:
    base_url, api_key = _get_service_config()
    return bool(base_url) and bool(api_key) and api_key != "YOUR_API_KEY_HERE"

def _handle_get_shades(args: dict, **_kw: Any) -> str:
    return norman_get_shades()

def _handle_set_shade(args: dict, **_kw: Any) -> str:
    return norman_set_shade(shade=args.get("shade", "all"), position=args.get("position", 0))

def _handle_set_all_shades(args: dict, **_kw: Any) -> str:
    return norman_set_all_shades(position=args.get("position", 0))

def _handle_set_override_hold(args: dict, **_kw: Any) -> str:
    return norman_set_override_hold(minutes=args.get("minutes", 120))

def _handle_set_vacation_mode(args: dict, **_kw: Any) -> str:
    return norman_set_vacation_mode(enabled=args.get("enabled", False))

def _handle_clear_override(args: dict, **_kw: Any) -> str:
    return norman_clear_override(shade=args.get("shade", "all"))


_GET_SHADES_SCHEMA = {
    "name": "norman_get_shades",
    "description": "Get current open/close status, positions (0%=Closed, 100%=Open), and remote override flags for all Lanai shades (left, center, right).",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}

_SET_SHADE_SCHEMA = {
    "name": "norman_set_shade",
    "description": "Set position percentage (0 = fully closed, 100 = fully open) for a specific Lanai shade ('left', 'center', 'right', or 'all').",
    "parameters": {
        "type": "object",
        "properties": {
            "shade": {
                "type": "string",
                "description": "Target shade name ('left', 'center', 'right', or 'all').",
            },
            "position": {
                "type": "integer",
                "description": "Target percentage OPEN (0 = Fully Closed, 100 = Fully Open). Pass requested open percentage DIRECTLY without subtracting from 100 (e.g. '25% open' -> position=25).",
            },
        },
        "required": ["shade", "position"],
    },
}

_SET_ALL_SHADES_SCHEMA = {
    "name": "norman_set_all_shades",
    "description": "Set position percentage for ALL Lanai shades. Pass requested open percentage DIRECTLY without math (e.g. '25% open' -> position=25).",
    "parameters": {
        "type": "object",
        "properties": {
            "position": {
                "type": "integer",
                "description": "Target percentage OPEN (0 = Fully Closed, 100 = Fully Open). Pass requested open percentage DIRECTLY without subtracting from 100 (e.g. '25% open' -> position=25).",
            },
        },
        "required": ["position"],
    },
}

_SET_OVERRIDE_HOLD_SCHEMA = {
    "name": "norman_set_override_hold",
    "description": "Dynamically set the hold-off duration in minutes for physical remote control overrides.",
    "parameters": {
        "type": "object",
        "properties": {
            "minutes": {
                "type": "integer",
                "description": "Number of minutes to pause background automation after a physical remote is used.",
            },
        },
        "required": ["minutes"],
    },
}

_SET_VACATION_MODE_SCHEMA = {
    "name": "norman_set_vacation_mode",
    "description": "Enable or disable Vacation Mode. When active, all shades are locked at 100% (closed).",
    "parameters": {
        "type": "object",
        "properties": {
            "enabled": {
                "type": "boolean",
                "description": "True to lock shades in vacation mode, False to return to normal mode.",
            },
        },
        "required": ["enabled"],
    },
}

_CLEAR_OVERRIDE_SCHEMA = {
    "name": "norman_clear_override",
    "description": "Manually clear active physical remote control override hold on shades.",
    "parameters": {
        "type": "object",
        "properties": {
            "shade": {
                "type": "string",
                "description": "Target shade ('left', 'center', 'right', or 'all'). Default is 'all'.",
            },
        },
        "required": [],
    },
}

registry.register(
    name="norman_get_shades",
    toolset="shade_control",
    schema=_GET_SHADES_SCHEMA,
    handler=_handle_get_shades,
    check_fn=_check_shade_available,
    emoji="🪟",
)

registry.register(
    name="norman_set_shade",
    toolset="shade_control",
    schema=_SET_SHADE_SCHEMA,
    handler=_handle_set_shade,
    check_fn=_check_shade_available,
    emoji="🪟",
)

registry.register(
    name="norman_set_all_shades",
    toolset="shade_control",
    schema=_SET_ALL_SHADES_SCHEMA,
    handler=_handle_set_all_shades,
    check_fn=_check_shade_available,
    emoji="🪟",
)

registry.register(
    name="norman_set_override_hold",
    toolset="shade_control",
    schema=_SET_OVERRIDE_HOLD_SCHEMA,
    handler=_handle_set_override_hold,
    check_fn=_check_shade_available,
    emoji="🪟",
)

registry.register(
    name="norman_set_vacation_mode",
    toolset="shade_control",
    schema=_SET_VACATION_MODE_SCHEMA,
    handler=_handle_set_vacation_mode,
    check_fn=_check_shade_available,
    emoji="🪟",
)

registry.register(
    name="norman_clear_override",
    toolset="shade_control",
    schema=_CLEAR_OVERRIDE_SCHEMA,
    handler=_handle_clear_override,
    check_fn=_check_shade_available,
    emoji="🪟",
)

def _handle_enable_sun_tracker(args: dict, **_kw: Any) -> str:
    return norman_enable_sun_tracker()

def _handle_disable_sun_tracker(args: dict, **_kw: Any) -> str:
    return norman_disable_sun_tracker()

def _handle_get_sun_tracker_status(args: dict, **_kw: Any) -> str:
    return norman_get_sun_tracker_status()

_ENABLE_SUN_TRACKER_SCHEMA = {
    "name": "norman_enable_sun_tracker",
    "description": "Enable automatic sun position tracking to adjust lanai shades against direct glare.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}

_DISABLE_SUN_TRACKER_SCHEMA = {
    "name": "norman_disable_sun_tracker",
    "description": "Disable automatic sun position tracking for lanai shades.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}

_GET_SUN_TRACKER_STATUS_SCHEMA = {
    "name": "norman_get_sun_tracker_status",
    "description": "Get current solar position, glare status, and Sun Tracker operational state.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}

registry.register(
    name="norman_enable_sun_tracker",
    toolset="shade_control",
    schema=_ENABLE_SUN_TRACKER_SCHEMA,
    handler=_handle_enable_sun_tracker,
    check_fn=_check_shade_available,
    emoji="☀️",
)

registry.register(
    name="norman_disable_sun_tracker",
    toolset="shade_control",
    schema=_DISABLE_SUN_TRACKER_SCHEMA,
    handler=_handle_disable_sun_tracker,
    check_fn=_check_shade_available,
    emoji="☀️",
)

registry.register(
    name="norman_get_sun_tracker_status",
    toolset="shade_control",
    schema=_GET_SUN_TRACKER_STATUS_SCHEMA,
    handler=_handle_get_sun_tracker_status,
    check_fn=_check_shade_available,
    emoji="☀️",
)

