# Upgrade Debrief: v0.16.0 → v0.18.0 (v2026.7.1)

**Date of Upgrade:** July 4, 2026  
**Methodology:** Backup-Reset-Restore with Dialectical Red/Blue Teaming  

This document serves as a post-mortem and debrief for the upgrade to Hermes Agent v0.18.0. It documents the exact processes that succeeded, the unexpected hurdles encountered, and the lessons learned to ensure future upgrades of this multi-tenant architecture remain stable.

---

## 1. The Strategy That Worked

Because our `hermes-agent` deployment hosts multiple isolated tenants (Tim and Chrisann) and relies on custom `.gitignore` exclusions and proxy files, a standard `git pull origin main` is too dangerous. We utilized a **Dialectical Planning (Red/Blue Team)** approach to formulate a 13-step plan. 

**The successful upgrade flow:**
1. **Full Backup:** Copied the entire repository to `../custom-deployment-backup/` to protect our un-tracked data and secrets.
2. **Branching & Reset:** Checked out the `upstream-sync` branch and performed a hard reset to the specific tag (`v2026.7.1`).
3. **Selective Restoration:** Restored our custom `nginx.conf`, `.env` files, and `.gitignore` rules from the backup, deliberately skipping core framework files (like the upstream `Dockerfile` and `docker-compose.yml`) so we inherited the new versions.
4. **Patching:** Re-applied our custom `chromium` package dependency to the new Dockerfile.
5. **Clean Rebuild:** Used `docker compose build --no-cache` to ensure no stale layers persisted.

## 2. Unexpected Hurdles & Breaking Changes

### A. Dashboard Security Hardening (Crash Loop)
- **The Issue:** Upstream `v0.18.0` introduced a security hardening measure that completely deprecated the `--insecure` flag for the dashboard. If the dashboard binds to a non-loopback address (`0.0.0.0`)—which is required for our Nginx reverse proxy—it **must** have an authentication provider configured. Because we were relying on Nginx for `auth_basic` and leaving the dashboard "insecure", the dashboard containers entered a silent restart loop and refused to bind.
- **The Fix:** We had to configure the internal dashboard authentication by hashing passwords with the built-in script (`python -c "from plugins.dashboard_auth.basic import hash_password..."`) and explicitly populating the `dashboard.basic_auth` block in both `data/tim/hermes/config.yaml` and `data/chrisann/hermes/config.yaml`.
- **Lesson for next time:** Always check the upstream release notes for security or authentication changes. When exposing internal services to Nginx, ensure the internal service's own security requirements are satisfied.

### B. Base Image Migration
- **The Issue:** The `Dockerfile` base image was updated upstream from Alpine to `debian:13.4` (Trixie). 
- **The Fix:** We had to verify that the `chromium` package (which we manually inject for web-extraction capabilities) was available in the Debian 13.4 repositories. It was, so the injection succeeded.
- **Lesson for next time:** When base images change, any custom `apt-get` or `apk` additions in our Dockerfile patches must be cross-checked against the new OS package manager.

## 3. Best Practices Identified for Future Upgrades

1. **Enforce Volume Permissions:** Always pass `HERMES_UID=$(id -u) HERMES_GID=$(id -g)` during `docker compose up -d`. This ensures that any new files created by the containers (especially the SQLite databases or session files) match the host user's permissions. 
2. **Targeted Verification via CLI:** Instead of relying solely on the web UI to verify if the LLM is connected, use the internal CLI. Executing `docker exec hermes-<tenant> hermes chat --cli -m <model-alias> -q "Hello"` is the most definitive way to test if the LiteLLM proxy and model routing (e.g., `chrisann-cheap`) are correctly enforcing isolation and budgets.
3. **Check SQLite Integrity:** After starting the new containers, running a PRAGMA check on the databases (`python3 -c 'import sqlite3; c = sqlite3.connect("data/tim/hermes/db.sqlite"); print(c.execute("PRAGMA integrity_check;").fetchall())'`) is a fast and reliable way to ensure the schema migrations didn't corrupt the historical data.
4. **Update `.gitignore` Immediately:** Before committing the upgrade to the `upstream-sync` branch, explicitly double-check `.gitignore`. The new upstream version may have removed or altered `.gitignore` rules. We must ensure our tenant directories (`data/tim`, `data/chrisann`) and `.env` files are appended to prevent accidental secret leakage.

---
*End of Debrief*
