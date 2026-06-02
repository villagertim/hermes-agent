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
