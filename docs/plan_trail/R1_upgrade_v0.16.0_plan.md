# R1: Initial Upgrade Plan (v0.15.2 -> v0.16.0)

This is the draft R1 version of the upgrade plan before Dialectical Plan Hardening.

## Summary of Planned Steps
1. Create Git backup branch.
2. Copy customized files to external backup folder:
   - `docker-compose.yml`
   - `nginx.conf`
   - `.tim-agent.env`, `.chrisann-agent.env`
   - `.htpasswd-tim`, `.htpasswd-chrisann`
   - `cli-config-tim.yaml`, `cli-config-chrisann.yaml`
   - Workspace rules (`AGENTS.md`, etc.)
   - Custom plugins and MCP servers (`plugins/`, `mcp-servers/`)
3. Git fetch and reset `upstream-sync` branch to tag `v2026.6.5`.
4. Restore customized configurations.
5. Re-apply `chromium` dependency package to `Dockerfile`.
6. Run `uv lock` and build containers via `docker compose build --no-cache`.
7. Merge back to `main` and verify container health.
