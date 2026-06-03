# hermes-agent Multi-Tenant Upgrade Log

This file is untracked by Git to ensure that it survives future repository resets and serves as a persistent record of the platform's upgrade history.

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
