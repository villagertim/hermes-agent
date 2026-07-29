# Post-Update Brief — Hermes Agent Workspace (v0.19.0 Upgrade & OpenRouter MCP Integration)

**Date:** 2026-07-29  
**Workspace:** `/home/cia-one/dev/hermes-agent`  
**Base Version:** Upgraded from `v0.18.0` (`v2026.7.1`) ➔ **`v0.19.0` (`v2026.7.20`)**  
**Remote Target:** `villagertim/main` (`https://github.com/villagertim/hermes-agent.git`)  
**Commit:** `3f31d082b` (`chore(sync): restore custom multi-tenant configuration layer on v2026.7.20`)

---

## Executive Summary

The `hermes-agent` workspace was upgraded to `v0.19.0` (`v2026.7.20`), and registered with `openrouter-mcp-2` (`universal-mcp-for-openrouter`). 

The multi-tenant architecture (Tim and Chrisann instances) remains 100% isolated, with primary LLM inference routed through local LiteLLM proxy gateways (`:4000/v1`) while acquiring advanced MCP capabilities (voting consensus, smart cost routing, multi-manager lockfile auditing, and local secret firewalls).

---

## 🛠️ Major Changes & Enhancements

### 1. OpenRouter MCP Server Integration (`openrouter-mcp-2`)
- **Client Configuration Updates:** Registered `openrouter_tools` in [`cli-config-tim.yaml`](file:///home/cia-one/dev/hermes-agent/cli-config-tim.yaml) and [`cli-config-chrisann.yaml`](file:///home/cia-one/dev/hermes-agent/cli-config-chrisann.yaml) under `mcp_servers:` using `--profile antigravity`.
- **New Capabilities Unlocked for Hermes Agents:**
  - `chat_ensemble`: Multi-model voting consensus & peer review.
  - `chat_routed`: Cost-optimized task delegation to $0.07/1M token models.
  - `dependency_graph`: Sub-millisecond lockfile auditing for npm, Yarn, pnpm, and Cargo.
  - `semantic_code_search`: Vector-based project code symbol search.
  - **Secret Redaction Firewall:** Subprocess secret filtering for Anthropic, GitHub, AWS, and GCP keys.
- **Architectural Hybrid Model:**
  - **Inference Gateway:** LiteLLM proxy (`base_url: http://litellm-tim:4000/v1` and `http://litellm-chrisann:4000/v1`) retained for main agent thinking, database logging, and tier aliases (`cheap`, `complex`, `reasoning`).
  - **Tool Server:** `openrouter_tools` MCP handles specialized agent tool execution.

### 2. Framework Upstream Sync: `v0.18.0` ➔ `v0.19.0` (`v2026.7.20`)
- **Security Hardening (`security/terminal` & `security/vertex`):** Prevents spawned terminal tools and subprocesses from inheriting sensitive environment variables (`GOOGLE_APPLICATION_CREDENTIALS`, `VERTEX_CREDENTIALS_PATH`), preventing key leaks.
- **Local Context Window Enforcement (`fix/agent`):** Enforces live context limits on local vLLM and LiteLLM endpoints to prevent context overflow crashes.
- **TLS / Custom CA Certificate Resolution (`fix/agent`):** Fixes SSL verification errors when connecting to local HTTPS proxies.
- **Reasoning Token Accounting (`fix/usage`):** Captures `reasoning_tokens` from `completion_tokens_details` on `/chat/completions` for accurate spend metrics on models like Gemini 3.1 Flash and Claude 3.7.

---

## 🛡️ Customization Preservation & Upstream Protection

1. **Upstream Sync Playbook Updated ([`docs/UPSTREAM_SYNC.md`](file:///home/cia-one/dev/hermes-agent/docs/UPSTREAM_SYNC.md)):**
   - **Step 2 (Backup Layer):** Expanded `cp --parents` command to include all 44 custom files, scripts (`setup_open_webui.sh`, `vault_backup.sh`), notes, `.agents/AGENTS.md`, and `debriefs/*`.
   - **Step 5b (Local Patches):** Added patch reapplication rules for `mcp-servers/litellm-spend/server.py` (`LITELLM_VIRTUAL_KEY` fallback) and `hermes_cli/model_switch.py` (`key_env` resolution).
   - **Step 5c (MCP Audit):** Added explicit verification for `openrouter_tools` MCP server definitions in client configs.

2. **Persistent Upgrade Log Updated ([`docs/UPGRADE_LOG.md`](file:///home/cia-one/dev/hermes-agent/docs/UPGRADE_LOG.md)):**
   - Recorded full upgrade history, configuration snippets, and safety protocols for `v0.19.0` and `openrouter-mcp-2`.

---

## 🧪 Verification & Repository Status

| Check | Result | Detail |
| :--- | :---: | :--- |
| **Git Pre-Commit Scanner** | ✅ PASSED | Zero raw credentials detected; placeholder tokens sanitized. |
| **Recovery Branch** | ✅ ACTIVE | `backup-stable-2026-07-29` created for 1-command rollback. |
| **External Physical Backup** | ✅ VERIFIED | `/home/cia-one/dev/custom-deployment-backup/` created (44 files, 8 subdirs). |
| **Remote Synchronization** | ✅ PUSHED | `main` pushed to `villagertim/main` (`3f31d082b`). |

---

## 📋 Recommended Next Steps

1. **Restart Agent Services (When Operating):**  
   If container services are running on the deployment host, restart them to apply the new `v0.19.0` code image and updated CLI configs:
   ```bash
   docker compose restart agent-tim agent-chrisann
   ```
2. **Observe Multi-Model Consensus (`chat_ensemble`):**  
   Test running a complex query on Hermes agents to verify tool dispatch to `openrouter_tools`.
