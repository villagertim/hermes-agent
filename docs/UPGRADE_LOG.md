# hermes-agent Multi-Tenant Upgrade Log

This file is untracked by Git to ensure that it survives future repository resets and serves as a persistent record of the platform's upgrade history.

---

## Service Provisioning: Chrisann — Full Parity with Tim

**Date**: 2026-06-06
**Base version**: `v0.16.0` (tag `v2026.6.5`)
**Conversation**: `d6e1ab72-b8a8-4c64-9091-b4beff00312e`

### What Was Done

Provisioned all external service integrations for Chrisann's agent to match Tim's setup. Previously, Chrisann only had LiteLLM proxy access and basic SearXNG search. Now she has full feature parity.

### API Keys Added (`data/chrisann/hermes/.env`)

| Service | Env Var | Purpose |
|---|---|---|
| FAL.ai | `FAL_KEY` | Image generation (FLUX 2 Klein 9B default) |
| Firecrawl | `FIRECRAWL_API_KEY` | Web search + content extraction |
| Tavily | `TAVILY_API_KEY` | Fallback web search (1,000 free/mo) |

### Spotify OAuth (`data/chrisann/hermes/auth.json`)

- Registered new Spotify developer app for Chrisann at `developer.spotify.com/dashboard`
- PKCE OAuth completed — tokens stored under `providers.spotify` in `auth.json`
- Redirect URI: `http://127.0.0.1:43829/spotify/callback` (port 43829 to avoid collision with Tim's 43828)
- Full scope: playback control, library, playlists, search, recently played
- `HERMES_SPOTIFY_CLIENT_ID` and `HERMES_SPOTIFY_REDIRECT_URI` added to `data/chrisann/hermes/.env`

### Config Alignment (`data/chrisann/hermes/config.yaml`)

Changes made to match Tim's config structure:

| Setting | Before | After |
|---|---|---|
| `toolsets` | `[hermes-cli]` | `[hermes-cli, spotify]` |
| `web.backend` | `''` (empty) | `firecrawl` |
| `web.extract_backend` | `''` (empty) | `firecrawl` |
| `auxiliary.web_extract.provider` | `auto` | `custom:litellm-chrisann` |
| `auxiliary.web_extract.model` | `''` | `chrisann-cheap` |
| `auxiliary.compression.provider` | `auto` | `custom:litellm-chrisann` |
| `auxiliary.compression.model` | `''` | `chrisann-cheap` |
| `approvals.mode` | `manual` | `smart` |
| `approvals.destructive_slash_confirm` | `true` | `false` |
| `image_gen.model` | (missing) | `fal-ai/flux-2/klein/9b` |
| `custom_providers` | (missing) | `litellm-chrisann` registered |
| `ntfy.home_channel` | (missing) | `hermes-chrisann` |
| `platform_toolsets` | (missing) | Full cli + telegram toolset lists |
| `known_plugin_toolsets` | (missing) | `spotify` for cli + telegram |

### Remaining Intentional Differences (Personal Preference)

| Setting | Tim | Chrisann | Reason |
|---|---|---|---|
| `display.personality` | `kawaii` | `''` | Personal style |
| `display.skin` | `stealth` | `default` | Personal style |
| `stt.openai.model` | `whisper` | `chrisann-whisper` | Tenant-specific model name |

### Verification

- [x] Spotify tokens confirmed in `auth.json` (access + refresh token present)
- [x] FAL_KEY uncommented and set in `.env`
- [x] FIRECRAWL_API_KEY set in `.env`
- [x] TAVILY_API_KEY added to `.env`
- [x] Config aligned with Tim's for all functional settings
- [x] Container restarted and running (`hermes-chrisann` up)

### Lessons

- Spotify developer dashboard has a provisioning delay for new accounts — "Your account is not ready" error resolves in 2-5 minutes.
- The "Web API" checkbox is greyed out during this delay. Just wait and refresh.
- PKCE flow does not need a client secret — only the Client ID.
- For containerized OAuth: run `hermes auth spotify` from the host with `HERMES_HOME=./data/<tenant>/hermes` to avoid port-exposure issues with Docker.
- Use unique redirect ports per tenant: Tim=43828, Chrisann=43829.

---

## Upgrade: v0.15.2 → v0.16.0

**Date**: 2026-06-06
**Target**: tag `v2026.6.5` @ commit `3c231eb39`
**Method**: backup-reset-restore (Upstream Synchronization Playbook)
**Conversation**: `b4d73ce7-d2e8-4660-8e62-a4c31cecefcd`

### Pre-Upgrade State
- Running version: `v0.15.2` (tag `v2026.5.29.2`)
- Local patches: `key_env` patch in `hermes_cli/model_switch.py` — now upstreamed in v0.16.0, dropped
- Custom files: ~60 files (docker-compose, nginx, .env files, budget plugin, MCP servers, etc.)
- Docker image: `hermes-agent:latest` tagged for backup reference

### Plan
Perform safe upgrade by backing up all customized files to `../custom-deployment-backup/`, creating git branch `backup-stable-2026-06-06`, checking out tag `v2026.6.5`, restoring the customization layer, re-applying `chromium` to the Dockerfile `apt-get install` line, and rebuilding images with `--no-cache`.

### What Changed Upstream (v0.15.2 → v0.16.0)
- **Dockerfile**: Added `iputils-ping`, `python3-venv`, `libolm-dev`; tini backward-compat shim (`ln -sf /init /usr/bin/tini`); `HERMES_TUI_DIR` env var for prebuilt TUI bundle; hindsight memory client baked into image; gateway dir made runtime-writable
- **model_switch.py**: Our `key_env` patch fully upstreamed with additional improvements (credential identity grouping, `discover_models` support, `api_mode` wire protocol separation)
- **pyproject.toml**: New extras (`computer-use`, `mistral`, `youtube`, `google`); `starlette==1.0.1` pinned for CVE-2026-48710; hindsight extra added to `[all]`
- **Desktop app**: New Electron-based native desktop client (not relevant to our Docker deployment)
- **.env.example**: New STT providers (ElevenLabs, Mistral, xAI) and override variables

### Result
- [x] Git reset clean to `v2026.6.5`
- [x] Customization layer restored
- [x] Chromium re-applied to Dockerfile
- [x] Docker build succeeded (`--no-cache`, 277s)
- [x] All containers started
- [x] Tim gateway healthy (v0.16.0 confirmed)
- [x] Chrisann gateway healthy (v0.16.0 confirmed)
- [x] Tim dashboard accessible (HTTP 200)
- [x] Chrisann dashboard accessible (HTTP 200)
- [x] SearXNG reachable from both agents
- [x] LiteLLM-Tim reachable and healthy
- [x] Chromium installed (`148.0.7778.215`)
- [x] Main branch merged

### Post-Upgrade Adjustments
- `key_env` patch in `hermes_cli/model_switch.py` **dropped** — fully upstreamed in v0.16.0 with enhanced credential identity grouping
- Chrisann's Telegram polling showed transient conflict on restart (self-healed within 20s)

### Lessons for Next Upgrade
- Upstream now ships with `libolm-dev` for Matrix encryption support — no longer needs separate installation
- `HERMES_TUI_DIR` env var is critical for Docker deployments — prevents runtime `npm install` race conditions across concurrent embedded-chat connections
- The tini backward-compat shim (`/usr/bin/tini → /init`) means legacy orchestration templates still work
- Always use tag pinning (e.g. `v2026.6.5`) rather than branch-head `origin/main`

---

## Upgrade: v0.14.0 → v0.15.2

**Date**: 2026-06-02
**Target**: tag `v2026.5.29.2` @ commit `77a1650c7`
**Method**: backup-reset-restore
**Conversation**: `1c103f38-5674-41e5-9354-59b67d894707`

### Pre-Upgrade State
- Tracked files modified:
  - `docker-compose.yml` (our custom multi-tenant configuration)
  - `AGENTS.md` (workspace rules)
  - `hermes_cli/model_switch.py` (a `key_env` patch that has been upstreamed in v0.15.1)
- Untracked custom files: ~25 files (all custom environment files `.tim-agent.env`, `.chrisann-agent.env`, nginx configs, and user data vaults)
- Docker image: `hermes-agent:latest` → tagged as `hermes-agent:v0.14.0-backup`

### Plan
Perform safe upgrade by backing up `docker-compose.yml` and `AGENTS.md` locally, doing a hard reset to the immutable stable tag `v2026.5.29.2` (to drop the local `model_switch.py` patch that was already upstreamed), restoring the custom files, rebuilding the images with `--no-cache` to accommodate s6-overlay and Node.js 22 LTS, and restarting all services.

### Result
- [x] Git reset clean
- [x] Docker build succeeded
- [x] Containers started
- [x] Tim gateway healthy
- [x] Chrisann gateway healthy
- [x] Tim dashboard accessible
- [x] Chrisann dashboard accessible
- [x] MCP (Obsidian) servers initialized

### Post-Upgrade Adjustments
None. The gateway ran out of the box with the new wrapper script routing args cleanly, and the custom compose commands worked without changes.

### Lessons for Next Upgrade
- Check if any local workarounds/patches (like our `key_env` fix) have been upstreamed in the new release so they can be safely dropped during git reset.
- Upstream changed process supervision in the Docker container from `tini` to `s6-overlay`. This makes `docker logs` quiet after boot because supervised processes have stdout routed to `/opt/data/logs/` instead. Use `docker exec <container> tail -f /opt/data/logs/gateway.log` for troubleshooting.
- Always use tag pinning (e.g. `v2026.5.29.2`) rather than branch-head `origin/main` to guarantee stable release behaviors.

---

## Addition: MCP Tools — Sequential Thinking, SQLite, Browser Automation

**Date**: 2026-06-02
**Base version**: `v0.15.2` (tag `v2026.5.29.2`)
**Conversation**: `1c103f38-5674-41e5-9354-59b67d894707`

### What Was Added

Three MCP server capabilities added to both `data/tim/hermes/config.yaml` and `data/chrisann/hermes/config.yaml`:

| Tool | Final Config | Notes |
|---|---|---|
| `sequential-thinking` | `npx -y @modelcontextprotocol/server-sequential-thinking` | Works as-is. No issues. |
| `sqlite` | `uvx --from mcp-server-sqlite mcp-server-sqlite --db-path /opt/data/memory.db` | See failures below. |
| `puppeteer` (browser) | `npx -y @playwright/mcp --headless --executable-path /usr/bin/chromium --browser chromium` | See failures below. |

**Dockerfile change**: Added `chromium` to the `apt-get install` layer for headless browser support. Rebuilt with `--no-cache`.

**Storage**: SQLite DB lives at `/opt/data/memory.db` inside the container, which is bind-mounted to the host at `data/<tenant>/` — so the DB is host-resident and does not consume Docker overlay storage.

### Package Failures Discovered During Verification

#### 1. `@modelcontextprotocol/server-sqlite` — Does Not Exist on npm

The initial plan used `@modelcontextprotocol/server-sqlite` (commonly referenced in MCP documentation). This package **does not exist** in the npm registry (returns 404). Do not use it.

Intermediate attempt: `mcp-server-sqlite-npx` — exists on npm but requires native compilation (`sqlite3` via `node-gyp`), which fails in the container because build tools (`python3-dev`, `make`, `g++`) are not present in the runtime image.

**Resolution**: Use the official Python implementation via `uvx`:
```yaml
sqlite:
  command: "uvx"
  args: ["--from", "mcp-server-sqlite", "mcp-server-sqlite", "--db-path", "/opt/data/memory.db"]
```
`uv`/`uvx` is already present in the image (used by the hermes-agent Python env). `mcp-server-sqlite` is the canonical PyPI package from the MCP project. It caches on first use; subsequent starts are fast. No build tools needed.

#### 2. `@modelcontextprotocol/server-puppeteer` — Deprecated

This package exists on npm but is **explicitly deprecated** as of 2025. Its bundled `puppeteer@23` is also too old (minimum is `>=24.15.0`). Do not use it.

**Resolution**: Use `@playwright/mcp` (Microsoft's actively maintained replacement):
```yaml
puppeteer:
  command: "npx"
  args: ["-y", "@playwright/mcp", "--headless", "--executable-path", "/usr/bin/chromium", "--browser", "chromium"]
  env:
    PLAYWRIGHT_BROWSERS_PATH: "0"
```
`PLAYWRIGHT_BROWSERS_PATH=0` prevents Playwright from trying to download its own browser bundle. `--executable-path /usr/bin/chromium` points it at the system Chromium installed in the Dockerfile. MCP stdio servers start silently (no stdout on launch) — this is correct behavior, not a failure.

### Verification Method

MCP stdio servers do not produce output on startup; they wait for JSON-RPC input. A clean exit (code 0) with no stdout from a `timeout 5 npx ...` invocation is the correct positive signal. The DB file existence and writability at `/opt/data/memory.db` confirms the SQLite path is correct.

### Config Is Bind-Mounted

`config.yaml` is bind-mounted from the host (`data/<tenant>/hermes/config.yaml`) into the container at `/opt/data/config.yaml`. This means config changes take effect after a `docker restart hermes-<tenant>` — **no image rebuild required**.

### Lessons for Next Agent

- Do not trust MCP documentation that references `@modelcontextprotocol/server-sqlite` — it does not exist on npm. Use `uvx --from mcp-server-sqlite`.
- Do not use `@modelcontextprotocol/server-puppeteer` — it is deprecated. Use `@playwright/mcp`.
- All JS MCP servers that rely on native SQLite bindings (`better-sqlite3`, `sqlite3`) will fail in this container without a build stage. Prefer `uvx`-based Python alternatives.
- When in doubt about whether an MCP server started correctly: silence is success for stdio transports. Only an error exit code or a printed error message indicates failure.
- `PLAYWRIGHT_BROWSERS_PATH=0` is required to prevent `@playwright/mcp` from downloading a redundant browser bundle when using a system-installed Chromium.

---

## Patch: Custom Provider key_env Resolution in model_switch.py

**Date**: 2026-06-04
**Base version**: `v0.15.2` (tag `v2026.5.29.2`)
**Conversation**: `83a33105-6449-4f98-83c2-cc7774eab754`

### What Was Patched

We patched `hermes_cli/model_switch.py` to fix a bug in Section 4 of `list_authenticated_providers()`.

**The Bug**: Section 4 (grouping custom providers) resolved `api_key` only from `entry.get("api_key")`. If the user used `key_env` to load the API key from environment variables (e.g. `key_env: OPENROUTER_API_KEY`), the key remained empty `""`. This caused unauthenticated queries to the custom provider's `/models` endpoint (such as `http://litellm-tim:4000/v1/models`), resulting in `401 Unauthorized` and listing `0` models.

**The Fix**: Checked for `key_env` and resolved the API key from `os.environ` when `api_key` is not defined inline:
```python
            api_key = (entry.get("api_key") or "").strip()
            if not api_key:
                key_env = str(entry.get("key_env", "") or "").strip()
                api_key = os.environ.get(key_env, "").strip() if key_env else ""
```

### Lessons for Next Agent / Future Upgrades

- This is a local patch to a core framework file (`hermes_cli/model_switch.py`). 
- When performing future upstream merges or upgrades (using the [Upstream Synchronization Playbook](file:///home/cia-one/dev/hermes-agent/docs/UPSTREAM_SYNC.md)), check if this fix has been officially upstreamed. If not, **you must re-apply this patch** after resetting/merging, otherwise local multi-tenant custom providers configured via `key_env` (such as `litellm-tim` and `litellm-chrisann`) will show `0` models.

---

## Configuration: Reasoning Model Differentiation

**Date**: 2026-06-04

### What Changed

The `reasoning` tier in all LiteLLM proxy configs was pointing to the same model as `complex` (`deepseek/deepseek-v4-pro`). Changed `reasoning` to use a dedicated thinking model.

**Files Updated**:
- `config_all.yaml` (active merged config)
- `config_tim.yaml`
- `config_chrisann.yaml`
- `config_shared.yaml`

**Before**:
```yaml
reasoning → openrouter/deepseek/deepseek-v4-pro  # same as complex
```

**After**:
```yaml
reasoning → openrouter/qwen/qwen3-235b-a22b-thinking-2507  # dedicated thinking model
```

**Rationale**: `qwen3-235b-a22b-thinking-2507` is a 235B-param MoE model with explicit chain-of-thought reasoning at $0.15/$1.50 per 1M tokens — purpose-built for reasoning tasks, unlike the general-purpose `deepseek-v4-pro`.

---

## Infrastructure: SearXNG Web Search Deployment

**Date**: 2026-06-04

### Problem

Both agents (Tim and Chrisann) had **no web search backend configured**. When asked for current data (weather, market prices, news), the models fabricated answers from stale training data.

### Solution

Deployed a self-hosted SearXNG instance as a shared Docker service:

1. **SearXNG container** added to `docker-compose.yml` — shared by both agents on `litellm_default` network
2. **Pre-configured settings** at `data/searxng/settings.yml`:
   - JSON format enabled (required by hermes-agent's `web_search` tool)
   - Rate limiting disabled (private instance)
   - Engines: Google, Bing, DuckDuckGo, Brave, Mojeek, Google News, Bing News, arXiv, Wikipedia, Yahoo Finance, wttr.in
3. **Agent configs** updated (`data/tim/hermes/config.yaml` and `data/chrisann/hermes/config.yaml`):
   ```yaml
   web:
     search_backend: "searxng"
   ```
4. **Environment variables** added to both `.env` files:
   ```
   SEARXNG_URL=http://searxng:8080
   ```

### Verification

- SearXNG returns 30+ results for weather queries from Tim's container
- SearXNG returns 36 results for market queries from Chrisann's container
- Both agents can reach `http://searxng:8080` on the Docker network

### Notes for Future Upgrades

- SearXNG settings live at `data/searxng/settings.yml` (bind-mounted into container)
- The `web.search_backend: "searxng"` config in each agent's `config.yaml` must be preserved during upstream syncs
- `SEARXNG_URL=http://searxng:8080` in each agent's `.env` must be preserved
- `web_extract` is currently not configured — agents use Playwright MCP (`puppeteer` in config) for page content extraction. To add dedicated extract, set `web.extract_backend: "firecrawl"` and add `FIRECRAWL_API_KEY` to `.env`.

---

## Integration: Spotify (Tim — June 4 / Chrisann — June 6)

**Date**: 2026-06-04 (Tim), 2026-06-06 (Chrisann)

### What Was Added

Full Spotify integration for both agents via PKCE OAuth. Adds 7 tools: `spotify_playback`, `spotify_devices`, `spotify_queue`, `spotify_search`, `spotify_playlists`, `spotify_albums`, `spotify_library`.

**Tim** — Completed June 4:
- `data/tim/hermes/.env` — `HERMES_SPOTIFY_CLIENT_ID`, redirect port `43828`
- `data/tim/hermes/auth.json` — OAuth tokens under `providers.spotify`

**Chrisann** — Completed June 6 (see "Service Provisioning: Chrisann" entry above):
- `data/chrisann/hermes/.env` — `HERMES_SPOTIFY_CLIENT_ID`, redirect port `43829`
- `data/chrisann/hermes/auth.json` — OAuth tokens under `providers.spotify`

**OAuth Note**: Standard containerized `hermes auth spotify` cannot receive browser callbacks because the callback server listens on `127.0.0.1` inside the container. Workaround: use the manual PKCE script at `scratch/spotify_auth.py` which generates its own verifier, prints the auth URL, and accepts the pasted callback URL from the browser.

**Port**: Tim uses redirect port `43828` (not the default `43827`, which had a bind conflict). Chrisann should use `43829` to avoid collision.

### Lessons for Chrisann Setup
- Each user needs their own Spotify developer app (Spotify requires per-user app registration)
- Use the manual PKCE script, not `hermes auth spotify`, for containerized deployments
- See `docs/CHRISANN_REPLICATION_GUIDE.md` for full walkthrough

---

## Configuration: Auxiliary Model Routing (Tim Only)

**Date**: 2026-06-04

### What Changed

Explicitly routed all auxiliary LLM tasks through Tim's LiteLLM proxy:

```yaml
auxiliary:
  vision:
    provider: custom:litellm-tim
    model: cheap
  web_extract:
    provider: custom:litellm-tim
    model: cheap
    timeout: 360
  compression:
    provider: custom:litellm-tim
    model: cheap
```

**Previously**: Only `vision` was explicitly routed. `web_extract` and `compression` used auto-detect, which cascades through OpenRouter → Nous → etc. with unpredictable results.

**Rationale**: Since Tim's agent doesn't have a real OpenRouter API key (it's the LiteLLM proxy key), auto-detect could route through unintended providers or fail silently. Explicit routing ensures all auxiliary calls go through the managed LiteLLM proxy.

---

## Planned Future Enhancements

**Date Added**: 2026-06-04

### Discord Integration
- **Priority**: Medium
- **Purpose**: Voice channel support — the only platform that enables live back-and-forth voice conversations with the agent (hands-free while cooking, driving, etc.)
- **Requirements**: Discord bot token, server setup
- **Docs**: `website/docs/user-guide/messaging/discord.md`

### Home Assistant Integration
- **Priority**: Medium (user expects HA back online ~July 2026)
- **Purpose**: Smart device control via natural language. Adds 4 tools: `ha_list_entities`, `ha_get_state`, `ha_call_service`, `ha_list_services`
- **Requirements**: HA instance with long-lived access token, network reachability from agent containers
- **Docs**: `website/docs/user-guide/messaging/homeassistant.md`

### X (Twitter) Search
- **Priority**: Low
- **Purpose**: Search X posts/threads in real time via xAI's Grok
- **Requirements**: `XAI_API_KEY` (paid) or SuperGrok OAuth subscription
- **Docs**: `website/docs/user-guide/features/x-search.md`

---

## Enhancement: Personality & UX Layer (Tim)

**Date**: 2026-06-04
**Conversation**: `83a33105-6449-4f98-83c2-cc7774eab754`

### BOOT.md Startup Hook
- **Files created**:
  - `data/tim/hermes/hooks/boot-md/HOOK.yaml` — subscribes to `gateway:startup`
  - `data/tim/hermes/hooks/boot-md/handler.py` — spawns one-shot agent in background thread
  - `data/tim/hermes/BOOT.md` — startup checklist (cron health, disk, vault, SearXNG)
- **Behavior**: On gateway restart, runs the checklist autonomously. Messages Tim on Telegram only if issues are found. Silent when healthy.
- **Note**: Handler uses `HERMES_HOME` env var, not `Path.home()`, to resolve the BOOT.md path inside Docker containers.

### Custom Skin ("stealth")
- **File**: `data/tim/hermes/skins/stealth.yaml`
- **Config**: `display.skin: stealth` added to `config.yaml`
- **Theme**: Deep navy/slate with subtle gold accents. Professional, sharp aesthetic.
- **Branding**: Agent name "Tim's Agent", prompt `▸`, response label `◆ Tim`, spinner verbs ("assessing", "running recon", "analyzing signals")

### SOUL.md Overhaul
- **File**: `data/tim/hermes/SOUL.md` — rewritten from 12-line skeleton to comprehensive personality spec
- **Sections**: Identity, Style, Principles, Avoid, About Tim
- **Key directives**: Correctness over speed, autonomy with guardrails, tool-first, no sycophancy, match Tim's technical level

### Spotify Toolset Enablement
- **Issue**: Spotify tools were disabled by default despite OAuth tokens being configured
- **Fix**: `hermes tools enable spotify` inside the container
- **Lesson**: New toolsets must be explicitly enabled via `hermes tools enable <name>` — adding config/keys is not enough

### Smart Approvals
- **Config**: `approvals.mode: smart` (was `manual`)
- **Reason**: The BOOT.md hook's `curl http://searxng:8080/healthz` command triggered the security scanner for using `http://`. Smart mode auto-approves safe commands using an auxiliary LLM while still catching genuinely destructive operations.

### BOOT.md Always-Report
- **Change**: Removed `[SILENT]` suppression from handler + BOOT.md checklist
- **Behavior**: Agent now always sends a Telegram message on startup — greets Tim and reports full status even when all systems are healthy
- **Timing fix**: Added 10-second delay + `curl --retry 2 --retry-delay 5` to avoid false alarms on services still initializing after restart
- **CLI fix**: Removed `hermes cron list` command (not in PATH for hook agents). Replaced with `curl` checks against LiteLLM and SearXNG.

---

## Network Hardening (Priorities 1-3)

**Date**: 2026-06-04
**Conversation**: `83a33105-6449-4f98-83c2-cc7774eab754`
**Audit**: Full peer review of Docker network topology identified 6 issues. Priorities 1-3 implemented; 4-5 deferred.

### Priority 1: Healthchecks on All Critical Services
- **Files modified**:
  - `docker-compose.yml` — added healthchecks for `searxng`, `ntfy`, `hermes-proxy`
  - `/home/cia-one/dev/litellm/docker-compose.yml` — added healthcheck for `litellm`
- **Gotchas discovered**:
  - SearXNG and ntfy containers have no `curl` — use `wget -q --spider` instead
  - LiteLLM container has no `curl` or `wget` — use `python3 urllib` instead
  - LiteLLM `/health` endpoint requires API key auth — use `/health/readiness` (unauthenticated)
  - LiteLLM needs `start_period: 60s` (not 15s) due to Prisma migration on startup (~6s)
- **Result**: All 5 services now report `healthy` via `docker inspect`

### Priority 2: Startup Dependencies (`depends_on`)
- **File**: `docker-compose.yml`
- **Changes**:
  - `agent-tim` depends on `searxng` + `ntfy` (`condition: service_healthy`)
  - `agent-chrisann` depends on `searxng` + `ntfy` (`condition: service_healthy`)
  - `agent-tim-dashboard` depends on `agent-tim` (`condition: service_started`)
  - `agent-chrisann-dashboard` depends on `agent-chrisann` (`condition: service_started`)
- **Note**: Cross-project dependency on LiteLLM cannot use `depends_on` — handled by BOOT.md retry logic
- **Result**: Agents no longer start before their dependencies are ready

### Priority 3: Nginx Container Name Standardization
- **File**: `nginx.conf`
- **Changes**: All 4 `proxy_pass` references changed from compose service names to container names:
  - `agent-tim-dashboard` → `hermes-tim-dashboard`
  - `agent-chrisann-dashboard` → `hermes-chrisann-dashboard`
- **Reason**: Container names are more portable across compose projects; service names only resolve within the same project

### Deferred (Not Implemented)
- **Priority 4: Network Segmentation** — Split flat `litellm_default` into purpose-specific networks. Medium effort, deferred until needed.
- **Priority 5: LiteLLM Redundancy** — Split single LiteLLM back to per-tenant containers. High effort / +1.5GB RAM, deferred.

### Antigravity IDE Cache Cleanup
- **Script**: `scripts/cleanup-antigravity-cache.sh` — prunes old conversations, brain dirs, and browser recordings
- **Cron**: Weekly Sunday 3 AM, keeps 15 days: `0 3 * * 0 .../cleanup-antigravity-cache.sh 15`
- **First run**: Reduced cache from 575 MB → 399 MB (30 conversations, 55 brain dirs, 1 recording dir deleted)

---

## Addition: LiteLLM Spend & Budget Dashboard + MCP Spend Monitor

**Date**: 2026-06-04
**Base version**: `v0.15.2` (tag `v2026.5.29.2`)
**Conversation**: `83a33105-6449-4f98-83c2-cc7774eab754`

### What Was Added

1. **Dashboard Plugin (`plugins/litellm-budget`)**:
   - **Backend (`plugin_api.py`)**: FastAPI router mounted dynamically at `/api/plugins/litellm-budget`. Connects to LiteLLM admin endpoints using the master key. Uses `BUDGET_SCOPE` environment variable and `OPENROUTER_API_KEY` (virtual key) to enforce strict tenant isolation.
   - **Frontend (`dist/index.js` + `dist/style.css`)**: Vanilla JS React component using the window-exposed Hermes Plugin SDK. Features real-time spend display, progress bars, limit adjustment inputs, monthly/weekly/daily/lifetime reset intervals, and a model spend breakdown list.
   - **Aesthetics**: Sleek dark mode card matching the dashboard's design token system, hover transitions, and custom scrollbars.

2. **MCP Spend Server (`mcp-servers/litellm-spend`)**:
   - **Server (`server.py`)**: Light Python MCP server using `mcp` SDK and `FastMCP`. Exposes two tools: `get_spend_summary` and `get_model_spend`.
   - **Security**: Runs completely read-only. Uses only the agent's own virtual API key (`OPENROUTER_API_KEY`) to call LiteLLM `/key/info` — **does not** require or have access to the LiteLLM master key.

3. **Multi-Tenant Routing & Isolation**:
   - **Tim's Dashboard**: Runs with `BUDGET_SCOPE=all`. Queries and updates budgets for BOTH keys (`tim-agent` and `chrisann-agent`).
   - **Chrisann's Dashboard**: Runs with `BUDGET_SCOPE=self`. Can only see and adjust her own key budget (`chrisann-agent`). Attempting to read or update Tim's key is blocked at the backend with a `403 Forbidden` error.
   - **Secrets Management**: LiteLLM Master Key is kept strictly out of the gateway container. It is mounted inside the dashboard containers only via Docker Secrets (`/run/secrets/litellm_master_key`).

### Verification & Test Results
- **Dashboard API**: Verified using `FastAPI` `TestClient` inside both dashboard containers.
  - Tim's container returned both keys and successfully updated budget.
  - Chrisann's container returned only hers, successfully updated it, and returned `403 Forbidden` when attempting to edit Tim's budget.
- **MCP Server**: Verified using python stdio test scripts inside both gateway containers.
  - Tim's gateway queried `get_spend_summary` successfully returning `$10.00 monthly` limit.
  - Chrisann's gateway queried `get_spend_summary` successfully returning `$6.00 monthly` limit.

---

## Infrastructure: System Backup Hardening & OneDrive Upload

**Date**: 2026-06-04
**Conversation**: `83a33105-6449-4f98-83c2-cc7774eab754`

### What Was Hardened

1. **ntfy Authentication integration in backup.sh**:
   - The backup script was previously posting notifications anonymously to `http://localhost:80/hermes-tim`, resulting in a silent `403 Forbidden` due to ACL policies on the local ntfy container.
   - Updated [backup.sh](file:///home/cia-one/dev/homelab-docs/scripts/backup.sh) to read the credentials file `.tim-agent.env` dynamically, retrieve `NTFY_USER` and `NTFY_PASS`, base64 encode them on the host, and pass them as a custom Basic Auth header (`Authorization: Basic ...`) via `docker exec ntfy wget`. This guarantees delivery of notifications to your local ntfy channel.
2. **rclone lsf Resilience**:
   - Because the new OneDrive remote (`onedrive-crypt:`) did not initially contain `/weekly` and `/monthly` folders, `rclone lsf` calls returned exit code 3, crashing the script mid-execution due to `set -euo pipefail`.
   - Hardened the daily, weekly, and monthly pruning lists with `|| true` guards and explicit line-count parsing (using `grep -c '^'`) to prevent failures when listing empty or missing directories.
3. **Typo Correction**:
   - Corrected the success notification destination string from `Google Drive` to `OneDrive` to match the target storage service.

### Execution Verification
- Ran the hardened backup script in dry-run and full mode.
- Created and successfully uploaded `homelab-backup-2026-06-04_112650.tar.gz` (~841 MB) to `onedrive-crypt:daily/`.
- Verified that the `ntfy` container successfully authorized the publish request (`200 OK` from basic auth) and logged the local publication.

