"""LiteLLM Budget dashboard plugin backend.

Mounted at /api/plugins/litellm-budget/ by the dashboard plugin system.
"""

import os
import hashlib
import logging
from typing import Any, List, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import httpx

log = logging.getLogger(__name__)

router = APIRouter()

# Config
LITELLM_PROXY_URL = os.environ.get("LITELLM_PROXY_URL", "http://litellm:4000")
BUDGET_SCOPE = os.environ.get("BUDGET_SCOPE", "all").lower()

def get_master_key() -> str:
    """Read LiteLLM master key from docker secrets or environment."""
    secret_path = "/run/secrets/litellm_master_key"
    if os.path.exists(secret_path):
        try:
            with open(secret_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            log.warning("Failed to read master key from secret file: %s", e)
    return os.environ.get("LITELLM_MASTER_KEY", "")

def get_self_hash() -> str:
    """Get the SHA-256 hash of the local agent's virtual key."""
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        return ""
    return hashlib.sha256(key.strip().encode("utf-8")).hexdigest()

class UpdateBudgetRequest(BaseModel):
    token: str
    max_budget: Optional[float] = None
    budget_duration: Optional[str] = None

@router.get("/keys")
async def get_keys():
    master_key = get_master_key()
    if not master_key:
        raise HTTPException(
            status_code=500,
            detail="LiteLLM Master Key not configured on the dashboard host"
        )
    
    self_hash = get_self_hash()
    
    headers = {"Authorization": f"Bearer {master_key}"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"{LITELLM_PROXY_URL}/spend/keys", headers=headers)
            if resp.status_code != 200:
                log.error("LiteLLM /spend/keys failed with %d: %s", resp.status_code, resp.text)
                raise HTTPException(
                    status_code=502,
                    detail=f"LiteLLM proxy returned error: {resp.text}"
                )
            keys = resp.json()
        except httpx.RequestError as exc:
            log.error("Request to LiteLLM /spend/keys failed: %s", exc)
            raise HTTPException(
                status_code=502,
                detail="Could not reach LiteLLM proxy"
            )

    # Filter keys based on scope
    filtered_keys = []
    for k in keys:
        token = k.get("token")
        
        # Determine if this key matches "self"
        is_self = (self_hash and token == self_hash)
        
        if BUDGET_SCOPE == "self":
            if is_self:
                filtered_keys.append(k)
        else:
            # BUDGET_SCOPE is "all", return everything
            filtered_keys.append(k)
            
    return {
        "keys": filtered_keys,
        "scope": BUDGET_SCOPE,
        "self_hash": self_hash
    }

@router.post("/update-budget")
async def update_budget(req: UpdateBudgetRequest):
    master_key = get_master_key()
    if not master_key:
        raise HTTPException(
            status_code=500,
            detail="LiteLLM Master Key not configured on the dashboard host"
        )
        
    self_hash = get_self_hash()
    
    # Enforce scope check
    if BUDGET_SCOPE == "self":
        if not self_hash or req.token != self_hash:
            raise HTTPException(
                status_code=403,
                detail="Permission denied: Cannot modify other user's budget"
            )
            
    # Send update to LiteLLM
    headers = {
        "Authorization": f"Bearer {master_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "key": req.token,
        "max_budget": req.max_budget,
        "budget_duration": req.budget_duration or None
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(
                f"{LITELLM_PROXY_URL}/key/update",
                headers=headers,
                json=payload
            )
            if resp.status_code != 200:
                log.error("LiteLLM /key/update failed with %d: %s", resp.status_code, resp.text)
                raise HTTPException(
                    status_code=502,
                    detail=f"LiteLLM proxy returned error: {resp.text}"
                )
            return resp.json()
        except httpx.RequestError as exc:
            log.error("Request to LiteLLM /key/update failed: %s", exc)
            raise HTTPException(
                status_code=502,
                detail="Could not reach LiteLLM proxy"
            )
