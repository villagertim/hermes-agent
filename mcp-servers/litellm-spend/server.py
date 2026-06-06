import os
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("litellm-spend")

LITELLM_PROXY_URL = os.environ.get("LITELLM_PROXY_URL", "http://litellm:4000")

def get_api_key() -> str:
    return os.environ.get("OPENROUTER_API_KEY", "")

@mcp.tool()
async def get_spend_summary() -> str:
    """Retrieve the current agent's spend summary and budget limits from LiteLLM."""
    api_key = get_api_key()
    if not api_key:
        return "Error: Agent API key (OPENROUTER_API_KEY) is not set in environment."
        
    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"{LITELLM_PROXY_URL}/key/info", headers=headers)
            if resp.status_code != 200:
                return f"Error: Failed to query LiteLLM spend. Status: {resp.status_code}, Detail: {resp.text}"
            data = resp.json()
            info = data.get("info", {})
            
            spend = info.get("spend", 0.0)
            max_budget = info.get("max_budget")
            budget_duration = info.get("budget_duration")
            blocked = info.get("blocked", False)
            
            duration_str = f" per {budget_duration}" if budget_duration else " lifetime"
            budget_str = f"${max_budget:.2f}{duration_str}" if max_budget is not None else "Unlimited"
            
            summary = (
                f"=== Spend & Budget Summary ===\n"
                f"Agent Key Alias: {info.get('key_alias', 'unnamed')}\n"
                f"Current Spend: ${spend:.4f}\n"
                f"Budget Limit: {budget_str}\n"
                f"Status: {'BLOCKED (Limit Exceeded)' if blocked else 'Active'}\n"
            )
            return summary
        except Exception as e:
            return f"Error connecting to LiteLLM: {str(e)}"

@mcp.tool()
async def get_model_spend() -> str:
    """Retrieve the breakdown of spend by model for the current agent."""
    api_key = get_api_key()
    if not api_key:
        return "Error: Agent API key (OPENROUTER_API_KEY) is not set in environment."
        
    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"{LITELLM_PROXY_URL}/key/info", headers=headers)
            if resp.status_code != 200:
                return f"Error: Failed to query LiteLLM spend. Status: {resp.status_code}, Detail: {resp.text}"
            data = resp.json()
            info = data.get("info", {})
            model_spend = info.get("model_spend", {})
            
            if not model_spend:
                return "No spend recorded on any model yet."
                
            breakdown = "=== Model Spend Breakdown ===\n"
            for model, spend in sorted(model_spend.items(), key=lambda x: x[1], reverse=True):
                breakdown += f"- {model}: ${spend:.4f}\n"
            return breakdown
        except Exception as e:
            return f"Error connecting to LiteLLM: {str(e)}"

if __name__ == "__main__":
    mcp.run()
