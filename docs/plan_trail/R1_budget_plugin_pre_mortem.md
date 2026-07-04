# Pre-Mortem Meta-Audit: LiteLLM Budget Plugin

**Date**: 2026-06-04
**Plan**: LiteLLM Spend & Budget — Dashboard Plugin + Read-Only MCP
**Cycles**: Red Team → Peer Review → Blue Team Synthesis

---

## Triage Summary

| # | Finding | Red Team | Peer Review | Verdict |
|---|---------|----------|-------------|---------|
| 1 | Master key in container env | 🔴 Critical | FUD (container already compromised if shell access exists) | ⚠️ See #9 |
| 2 | BUDGET_SCOPE bypass (SQLi/traversal) | 🔴 Critical | FUD (string matching, not SQL; keys are alphanumeric) | ✅ No action |
| 3 | Hermes plugin uses Node.js not FastAPI | 🔴 Critical | FUD (verified: plugins use `plugin_api.py` with FastAPI `APIRouter`) | ✅ No action |
| 4 | Stale spend data (5-min batch delay) | 🟡 Medium | Low (real but trivial at homelab scale, ~$5/mo spend) | ℹ️ Accept |
| 5 | Concurrent budget modifications | 🟡 Medium | FUD (2-user household, edits happen ≤1/month) | ✅ No action |
| 6 | Cross-domain cookie attack | 🟡 Medium | FUD (separate subdomains, nginx isolates, no shared cookies) | ✅ No action |
| 7 | LiteLLM rotates master key every 24h | 🟡 Medium | FUD (static `LITELLM_MASTER_KEY` is never rotated by LiteLLM) | ✅ No action |
| 8 | MCP server crash on boot (LiteLLM not ready) | 🟡 Medium | FUD (MCP tools are lazy-loaded, not boot-time) | ✅ No action |
| 9 | Agent terminal access → `printenv` → master key | 🔴 Critical | **REAL — the only critical finding** | 🛡️ Fix required |

---

## The One Real Finding: Agent Can Read Master Key

### The Problem

The plan puts `LITELLM_MASTER_KEY` in the container environment so the plugin backend can use it. But the Hermes gateway agent also runs in the same container and has terminal/code execution access. The agent could run:

```bash
printenv LITELLM_MASTER_KEY
```

This would give the LLM-driven agent admin access to LiteLLM — it could modify any key's budget, reset spend, or even delete keys.

### Why It Matters

This isn't about external attackers. It's about the agent itself. An LLM with tool access could accidentally or through prompt injection read the master key and take actions outside its intended scope.

### 🛡️ Defense Against Failure: Secret File Mount

**Fix**: Don't put the master key in the container environment at all. Instead:

1. Write the master key to a file: `secrets/litellm_master_key`
2. Mount it into the container at a path only the dashboard process reads
3. The `plugin_api.py` reads from the file, not from `os.environ`
4. The agent process has no reason to read arbitrary files from that path

```yaml
# docker-compose.yml
volumes:
  - ./secrets/litellm_master_key:/run/secrets/litellm_master_key:ro
```

```python
# plugin_api.py
def get_master_key():
    with open("/run/secrets/litellm_master_key") as f:
        return f.read().strip()
```

**Why this is better than env vars:**
- `printenv` won't show it
- `/proc/1/environ` won't contain it
- Docker secrets convention (`/run/secrets/`) is a known pattern
- The agent *could* still `cat /run/secrets/litellm_master_key` if it tried, but it's not in the obvious env var namespace

**Why not full Docker secrets:** Docker secrets require Swarm mode. File mount is the compose-native equivalent.

> [!NOTE]
> **Residual risk**: The agent has file read access and could theoretically find the secret file. True isolation would require separate containers for the dashboard and gateway. This is already the architecture — `hermes-tim` (gateway) and `hermes-tim-dashboard` (dashboard) are separate containers. The master key should go in the **dashboard container only**, not the gateway container.

### 🛡️ Final Defense: Master Key in Dashboard Container Only

The existing architecture already has separate containers:
- `hermes-tim` — gateway (agent with LLM + tools)
- `hermes-tim-dashboard` — web UI (serves the dashboard)

**The plugin backend runs in the dashboard container, not the gateway container.** Therefore:

1. `LITELLM_MASTER_KEY` (or secret file) goes in `hermes-tim-dashboard` only
2. `hermes-tim` (gateway) never sees the master key
3. The MCP server in the gateway uses only `OPENAI_API_KEY` (virtual key)

**This completely eliminates the finding.** The agent cannot access the master key because it's in a different container.

---

## Accepted Risks

### Stale Spend Data (~1-5 min delay)
LiteLLM batches spend log writes. Budget enforcement won't catch overspend within the batch window. At $0.93 total lifetime spend, the maximum overshoot during a batch window is ~$0.01. **Accepted — not worth optimizing.**

---

## Findings Dismissed as FUD (Homelab Context)

- **BUDGET_SCOPE bypass**: Keys are validated as string matches against a fixed list. No SQL, no filesystem paths.
- **Plugin compatibility**: Verified working — existing plugins use identical `plugin_api.py` + `APIRouter` pattern.
- **Concurrent modifications**: 2-user household. Statistical impossibility.
- **Cross-domain cookies**: Nginx serves separate subdomains with separate auth. No cookie sharing.
- **Key rotation**: Static master key, never rotated by LiteLLM.
- **MCP boot order**: Lazy-loaded tools, no boot-time dependency.
