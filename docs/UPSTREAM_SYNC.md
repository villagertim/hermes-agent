# Upstream Synchronization Playbook

This document details the repeatable workflow for pulling upstream updates from the official `NousResearch/hermes-agent` repository while preserving the custom, isolated multi-tenant deployment layer for Tim and Chrisann.

---

## 🏗️ Architecture & Concerns

To prevent merge conflicts and preserve configurations, this repository separates concerns into two distinct layers:

1.  **Upstream Core**: The framework logic (Python modules in `agent/`, `tools/`, core CLI commands, dependencies).
2.  **Deployment & Orchestration Layer**: The custom multi-tenant configuration (Nginx configs, basic-auth settings, `.env` API keys, custom `.yaml` client configurations, and localized orchestration scripts).

---

## ⏱️ Step-by-Step Sync Protocol

Follow these exact steps when pulling upstream updates:

### Step 1: Create a Recovery Backup Branch
Before making any changes, create a git recovery branch to ensure you can revert immediately if needed:
```bash
git branch backup-stable-<date>
```

### Step 2: Extract the Customization Layer
Create an external temporary backup folder outside the repository and physically copy the configuration layer files:
```bash
# Create external backup folder
mkdir -p ../custom-deployment-backup/

# Copy all customized and untracked config files
cp --parents docker-compose.yml nginx.conf .tim-agent.env .chrisann-agent.env .htpasswd-tim .htpasswd-chrisann cli-config-tim.yaml cli-config-chrisann.yaml mcp_wrapper.sh AGENTS.md AGENT_GUIDE.md AGENT_RULES.md MCP_ACCESS_RULES.md SYSTEM_STATUS.md continuation_vasallo94.md continuation.md vasallo94_integration_plan.md obsidian_mcp_evaluation.md docs/local_model_log.md ../custom-deployment-backup/
```

### Step 3: Checkout a Fresh Upstream Sync Branch
Fetch the latest remote updates and check out a clean tracking branch from the upstream repository main branch:
```bash
git fetch origin
git checkout -B upstream-sync origin/main
```

### Step 4: Reapply the Customization Layer
Restore our customized files from the external backup directly into the clean upstream-sync working directory:
```bash
cp -r ../custom-deployment-backup/* ./
cp -r ../custom-deployment-backup/.* ./ 2>/dev/null || true
```

### Step 5: Perform Configuration Reconciliation
Compare the newly fetched upstream `.env.example` and standard configurations to check if new variables or dependencies were introduced:
```bash
# Look for newly added configuration keys in upstream template
git diff backup-stable-<date>..upstream-sync .env.example
```
*Action*: If any new variables are found, append them as comments or default definitions in both `.tim-agent.env` and `.chrisann-agent.env`.

### Step 5b: Reapply Local Core Framework Patches
Check the latest entries in [UPGRADE_LOG.md](file:///home/cia-one/dev/hermes-agent/docs/UPGRADE_LOG.md) to see if there are any active local core patches that have not yet been upstreamed.
For example:
- **Custom Provider key_env Resolution**: Verify that `hermes_cli/model_switch.py` correctly resolves `key_env` to environment variables in Section 4 of `list_authenticated_providers()`. If not, reapply the patch:
  ```python
            api_key = (entry.get("api_key") or "").strip()
            if not api_key:
                key_env = str(entry.get("key_env", "") or "").strip()
                api_key = os.environ.get(key_env, "").strip() if key_env else ""
  ```

### Step 6: Build & Verify Services
Trigger the verification protocol:
1.  **Lock dependencies**: Run `uv lock --check` (or `uv lock` if dependencies need updating) to ensure Python package locking is fully compatible.
2.  **Rebuild Container Images**: Stop running services and trigger a no-cache container build:
    ```bash
    docker compose down
    docker compose build --no-cache
    docker compose up -d
    ```
3.  **Perform Diagnostics**: Verify Nginx reverse proxy routing and execute a local-model diagnostic request.

### Step 7: Fast-Forward Main Branch
Once the containerized services are verified to be fully functional, safe, and isolated, promote this merge back to the `main` branch:
```bash
git checkout main
git merge upstream-sync
```
