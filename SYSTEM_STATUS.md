# SYSTEM STATUS & ARCHITECTURE REVIEW
**Date**: June 6, 2026
**Project**: Multi-Tenant Hermes Agent Infrastructure

## Executive Summary
The workspace `/home/cia-one/dev/hermes-agent` orchestrates a highly isolated, multi-tenant AI environment for two users: **Tim** and **Chrisann**. The system relies on the `hermes-agent` framework, powered by local LLMs via `LiteLLM`, and features strict data segregation using Docker networks, Nginx reverse proxying, and isolated volume mounts.

All external traffic is routed via a **Cloudflare Zero Trust Tunnel** (`hermes-home-server`) — no port forwarding on the residential router. The hermes-proxy nginx container handles virtual-host routing by `Host:` header.

---

## Domain Routing Map

| Domain | Auth | Target Container | Repo |
| :--- | :--- | :--- | :--- |
| `villagertim.com`, `www.villagertim.com` | None — Public | `villagertim-web:80` | `/home/cia-one/dev/villagertim-website/` |
| `agent.villagertim.com` | Tim | `hermes-tim-dashboard:9119` | this repo |
| `notes.villagertim.com` | Tim | `obsidian-gui-tim:3000` | this repo |
| `briefer.villagertim.com` | Tim | `daily-briefer:8080` | `/home/cia-one/dev/daily-briefer/` |
| `automate.villagertim.com` | Tim | `n8n-tim:5678` | this repo |
| `iqua.villagertim.com` | Tim | `iqua-dashboard:8088` | this repo |
| `agent.villagerchrisann.com` | Chrisann | `hermes-chrisann-dashboard:9119` | this repo |
| `notes.villagerchrisann.com` | Chrisann | `obsidian-gui-chrisann:3000` | this repo |
| `briefer.villagerchrisann.com` | Chrisann | `daily-briefer-chrisann:8081` | `/home/cia-one/dev/daily-briefer/` |
| `automate.villagerchrisann.com` | Chrisann | `n8n-chrisann:5678` | this repo |

---

## Deployed Services & Networking
All private web services are secured behind Nginx reverse proxy using HTTP Basic Authentication (`.htpasswd`). Internal communication happens on the `litellm_default` Docker network.

| Service Description | User | Internal Port | Credentials |
| :--- | :--- | :--- | :--- |
| **Personal Website** | Tim (public) | 80 | None |
| **Hermes Web Dashboard** | Tim | 9119 | `tim` / `tim123` |
| **Hermes Web Dashboard** | Chrisann | 9119 | `chrisann` / `chrisann123` |
| **Obsidian Visual Web GUI** | Tim | 3000 | `tim` / `tim123` |
| **Obsidian Visual Web GUI** | Chrisann | 3000 | `chrisann` / `chrisann123` |
| **n8n Automation Engine** | Tim | 5678 | `tim` / `tim123` |
| **n8n Automation Engine** | Chrisann | 5678 | `chrisann` / `chrisann123` |

*(Note: LiteLLM proxy engines run independently on ports `4001` and `4002` respectively.)*

---

## Recent Accomplishments (June 6, 2026)

1. **Upgraded hermes-agent to v0.16.0** (tag `v2026.6.5`)
   - Backup-reset-restore upgrade from v0.15.2
   - `key_env` patch dropped (fully upstreamed)
   - New desktop app, tini shim, hindsight memory in image

2. **Chrisann Service Provisioning — Full Parity with Tim**
   - **Spotify**: PKCE OAuth completed, 7 tools enabled (playback, search, queue, playlists, albums, library, devices)
   - **FAL.ai**: Image generation key configured (FLUX 2 Klein 9B default)
   - **Firecrawl**: Web search + content extraction key configured
   - **Tavily**: Fallback web search key configured
   - **Config alignment**: web backend, extract routing, compression routing, approvals, ntfy, platform toolsets all matched to Tim's

3. **Both Agents Now Have Identical Capability Sets**:
   - LLM inference via dedicated LiteLLM proxies
   - Web search (SearXNG + Firecrawl + Tavily fallback)
   - Image generation (FAL.ai)
   - Spotify control (7 tools, Premium playback)
   - Obsidian vault access (MCP)
   - Browser automation (Playwright MCP)
   - SQLite memory (MCP)
   - Sequential thinking (MCP)
   - Push notifications (ntfy)
   - Telegram bot integration

---

## Recent Accomplishments (June 2, 2026)

1. **Upgraded hermes-agent to v0.15.2** (tag `v2026.5.29.2`)
   - Backup-reset-restore upgrade from v0.14.0
   - Upstream `model_switch.py` patch dropped (upstreamed in v0.15.1)
   - New s6-overlay process supervision — logs at `/opt/data/logs/gateway.log`

2. **Added MCP Tools** (SQLite, Sequential Thinking, Browser Automation)
   - `sequential-thinking`: `npx -y @modelcontextprotocol/server-sequential-thinking`
   - `sqlite`: `uvx --from mcp-server-sqlite mcp-server-sqlite` (NOT npm — doesn't exist)
   - `puppeteer`: `npx -y @playwright/mcp --headless` (NOT deprecated `server-puppeteer`)
   - Chromium added to Dockerfile for headless browser support

3. **villagertim.com Public Website** — NEW
   - New repo: `/home/cia-one/dev/villagertim-website/`
   - Static HTML/CSS, served by nginx:alpine Docker container (`villagertim-web`)
   - Positioned as: AI tools and guidance for active retirees
   - nginx.conf updated: `server {}` blocks for `villagertim.com` + `www.villagertim.com`
   - Cloudflare Public Hostnames configured — both DNS entries auto-created by tunnel

---

## Recent Accomplishments (May 15, 2026)

1. **Obsidian MCP Integration (`Vasallo94`)**
   - Integrated `Vasallo94/obsidian-mcp-server` for both agents.
   - Enabled Semantic Search (RAG) and vault analysis tools.
   - Enforced strict Read-Only constraints for the Antigravity assistant system.

2. **Access & Security Remediation**
   - Fixed internal gateway blockades (`No user allowlists configured`) by injecting `GATEWAY_ALLOW_ALL_USERS=true`.

3. **Deployment of Human Web GUIs**
   - Deployed `linuxserver/obsidian` containers for both users.
   - Bridges human operators and AI agents in the same live Obsidian vault.

4. **Hermes Core System Update**
   - Merged upstream `NousResearch/hermes-agent` changes into multi-tenant customizations.
   - Full backup at `../hermes-agent-backup-2026-05-15.tar.gz`.

5. **n8n Automation Integration**
   - Isolated n8n engines for Tim and Chrisann — zero crossover, separate databases.

---

## Outstanding Items / Future Roadmap

- **villagerchrisann.com** — Dockerize `VWC_Website` (Next.js in `/home/cia-one/dev/VWC_Website/`); add nginx block + Cloudflare Public Hostnames
- **Chrisann Personality & UX** — Create SOUL.md, custom skin, and BOOT.md startup hook matching Tim's setup
- **n8n Workflow Construction** — Build AI pipelines leveraging local LiteLLM nodes (auto-summarize emails, RAG updates)
- **Discord Integration** — Voice channel support for hands-free agent conversations
- **Home Assistant Integration** — Smart device control (expected ~July 2026)
- **Agent Capability Tuning** — Monitor Semantic Search usage; tune `obsidianrag` prompts as needed
