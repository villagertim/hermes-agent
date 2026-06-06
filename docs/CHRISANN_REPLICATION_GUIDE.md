# Chrisann Agent Replication Guide

A step-by-step playbook for replicating every enhancement made to Tim's agent onto Chrisann's. Designed for a future AI agent session.

**Source of truth**: Tim's config at `data/tim/hermes/config.yaml` and `data/tim/hermes/.env`
**Target**: Chrisann's config at `data/chrisann/hermes/config.yaml` and `data/chrisann/hermes/.env`

---

## Pre-flight Checklist

Before starting, verify:
- [ ] Both agents are running: `docker ps | grep hermes`
- [ ] Chrisann's LiteLLM proxy is reachable: `docker exec hermes-chrisann curl -s http://litellm-chrisann:4000/health`
- [ ] Chrisann's Obsidian vault is mounted: `docker exec hermes-chrisann ls /opt/data/obsidian/`

---

## 1. Reasoning Model (ALREADY DONE)

The `reasoning` tier was updated in **all** LiteLLM configs (including `config_chrisann.yaml`) on 2026-06-04:
```yaml
reasoning → openrouter/qwen/qwen3-235b-a22b-thinking-2507
```
**No action needed** — this was applied globally.

---

## 2. SearXNG Web Search (ALREADY DONE)

SearXNG is a shared service. Both agents already have:
- `web.search_backend: "searxng"` in their `config.yaml`
- `SEARXNG_URL=http://searxng:8080` in their `.env`

**No action needed** — verified working for Chrisann on 2026-06-04.

---

## 3. Web Extract — Firecrawl + Tavily API Keys (NEEDS KEYS)

**What Tim has:**
```
# In data/tim/hermes/.env
FIRECRAWL_API_KEY=fc-bf0fa4dfd3fa46c1bf0d72665e89c3bc
TAVILY_API_KEY=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
```

```yaml
# In data/tim/hermes/config.yaml under 'web:'
web:
  search_backend: "searxng"
  extract_backend: "firecrawl"
```

**Steps for Chrisann:**
1. Obtain **separate** Firecrawl and Tavily API keys for Chrisann (strict isolation — do NOT share Tim's keys)
2. Add to `data/chrisann/hermes/.env`:
   ```
   FIRECRAWL_API_KEY=<chrisann's firecrawl key>
   TAVILY_API_KEY=<chrisann's tavily key>
   ```
3. Add to `data/chrisann/hermes/config.yaml`:
   ```yaml
   web:
     search_backend: "searxng"
     extract_backend: "firecrawl"
   ```
4. Restart: `docker restart hermes-chrisann`
5. Verify: `docker exec hermes-chrisann python3 -c "from hermes_cli.config import load_env; load_env(); import os; print('FC:', bool(os.environ.get('FIRECRAWL_API_KEY'))); print('TV:', bool(os.environ.get('TAVILY_API_KEY')))"`

---

## 4. Spotify Integration (DONE — Tim June 4, Chrisann June 6)

**What each tenant needs:**
- Their own Spotify developer app (Spotify requires per-user app registration)
- PKCE OAuth tokens in `auth.json`
- `spotify` in the `toolsets` list in `config.yaml`
- `spotify` in `platform_toolsets` and `known_plugin_toolsets` in `config.yaml`

**Port allocation:**
- Tim: redirect port `43828`
- Chrisann: redirect port `43829`
- Default (upstream): `43827` — do NOT use, conflicts with other services

### Step-by-step procedure (TESTED — this is the exact process that works)

#### A. Create the Spotify Developer App

1. Log into [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) with the tenant's Spotify account
2. **WAIT** — New accounts get "Your account is not ready, please wait a few minutes." The "Web API" checkbox will be greyed out. This resolves in 2-5 minutes. Just refresh the page.
3. Click **Create app** and fill in:

   | Field | Value |
   |-------|-------|
   | App name | `hermes-<tenant>` (e.g. `hermes-chrisann`) |
   | App description | `personal Hermes integration - <tenant>` |
   | Website | leave blank |
   | Redirect URI | `http://127.0.0.1:<port>/spotify/callback` |
   | Which API/SDKs? | check **Web API** (MUST be checked, not greyed out) |

4. Agree to terms → **Save** → click **Settings** → copy the **Client ID**
5. **No client secret needed** — Hermes uses PKCE, which only requires the Client ID

#### B. Add the Client ID to the tenant's `.env`

```bash
# Append to data/<tenant>/hermes/.env
cat >> ./data/<tenant>/hermes/.env << 'EOF'

# Spotify — music curation, playlist management, and playback control
# App registered at developer.spotify.com (PKCE flow, no client secret needed)
# OAuth tokens stored in auth.json after running: hermes auth spotify
HERMES_SPOTIFY_CLIENT_ID=<paste_client_id_here>
HERMES_SPOTIFY_REDIRECT_URI=http://127.0.0.1:<port>/spotify/callback
EOF
```

#### C. Run OAuth from the HOST (NOT from inside the container)

**CRITICAL**: Do NOT run `hermes auth spotify` inside the Docker container. The callback
listener binds to `127.0.0.1:<port>` inside the container's network namespace, which the
browser on the host cannot reach. The container does not expose this port.

**CRITICAL**: Do NOT try to SSH tunnel to the container — the port isn't exposed.

**The working method** is to run hermes auth **on the host machine** with `HERMES_HOME`
pointing to the tenant's data directory. This starts the callback listener on the host's
`127.0.0.1`, which the browser can reach directly:

```bash
cd /home/cia-one/dev/hermes-agent
HERMES_HOME=./data/<tenant>/hermes .venv/bin/hermes auth spotify \
  --client-id <CLIENT_ID> \
  --no-browser
```

The command will:
1. Print an authorization URL
2. Open a local HTTP listener on the redirect port
3. Wait for the browser callback

Copy the authorization URL, open it in a browser, and click **Agree**.
The browser will redirect to `127.0.0.1:<port>/spotify/callback`.
The terminal will print "Spotify authorization received".

**If the browser shows "This site can't be reached"**: The callback listener isn't running
on the host. You probably ran the command inside the container. Kill it and run from the host.

#### D. Verify tokens were saved

```bash
python3 -c "
import json
with open('./data/<tenant>/hermes/auth.json') as f:
    d = json.load(f)
s = d.get('providers',{}).get('spotify',{})
if s.get('access_token'):
    print('✅ Spotify auth SUCCESS')
    print(f'   Scope: {s.get(\"scope\")}')
else:
    print('❌ No Spotify tokens found')
"
```

#### E. Enable the spotify toolset in config.yaml

Add `spotify` to **three** places in `data/<tenant>/hermes/config.yaml`:

```yaml
# 1. Top-level toolsets list
toolsets:
- hermes-cli
- spotify          # ← ADD THIS

# 2. platform_toolsets (under both cli and telegram)
platform_toolsets:
  cli:
  - spotify        # ← ADD THIS (among the other tools)
  telegram:
  - spotify        # ← ADD THIS (among the other tools)

# 3. known_plugin_toolsets
known_plugin_toolsets:
  cli:
  - spotify
  telegram:
  - spotify
```

#### F. Restart the container

```bash
docker restart hermes-<tenant>
```

#### G. Verify end-to-end

```bash
# Check tokens exist
docker exec hermes-<tenant> python3 -c "
import json
with open('/opt/data/auth.json') as f:
    d = json.load(f)
print('spotify' in d.get('providers', {}))
"

# Check toolset is loaded (ask the agent to play something)
```

### Common mistakes (all encountered during Chrisann setup)

| Mistake | What happens | Fix |
|---|---|---|
| Running `hermes` on host without `.venv/bin/` prefix | `Command 'hermes' not found` | Use `.venv/bin/hermes` |
| Running `hermes auth spotify` inside container | Browser callback gets `ERR_CONNECTION_REFUSED` | Run from host with `HERMES_HOME=./data/<tenant>/hermes` |
| SSH tunneling to self | `bind: Address already in use` | Don't tunnel — run on host directly |
| Forgetting `--no-browser` on headless/SSH | Hangs trying to open browser | Add `--no-browser` flag |
| Setting up tokens but not adding `spotify` to `toolsets` in config.yaml | Agent has no Spotify tools | Add to all three places (toolsets, platform_toolsets, known_plugin_toolsets) |
| Using default port 43827 | May conflict with other services | Use 43828 (Tim), 43829 (Chrisann) |

---

## 5. Image Generation — FAL_KEY (NEEDS KEY)

**What Tim has** (once configured):
```
# In .env
FAL_KEY=<tim's fal.ai key>
```
```yaml
# In config.yaml
image_gen:
  model: fal-ai/flux-2/klein/9b
```

**Steps for Chrisann:**
1. Sign up at [fal.ai](https://fal.ai/) (or use same account — FAL keys are not user-specific)
2. Add to `data/chrisann/hermes/.env`:
   ```
   FAL_KEY=<key>
   ```
3. Add to `data/chrisann/hermes/config.yaml`:
   ```yaml
   image_gen:
     model: fal-ai/flux-2/klein/9b
   ```
4. Restart: `docker restart hermes-chrisann`

---

## 6. Auxiliary Model Routing (CONFIG ONLY)

**What Tim has** (once configured):
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

**Steps for Chrisann** — mirror but point to `litellm-chrisann`:
```yaml
auxiliary:
  vision:
    provider: custom:litellm-chrisann
    model: cheap
  web_extract:
    provider: custom:litellm-chrisann
    model: cheap
    timeout: 360
  compression:
    provider: custom:litellm-chrisann
    model: cheap
```

---

## 7. Fallback Provider (NEEDS KEY OR DECISION)

**What Tim has** (once configured):
```yaml
fallback_providers:
  - provider: <chosen_provider>
    model: <chosen_model>
```

**Steps for Chrisann:**
- Use the same fallback provider as Tim (both can share a direct OpenRouter/DeepSeek key since fallback is emergency-only)
- Or get a separate key for strict isolation
- Mirror the exact config from Tim's `config.yaml`

---

## Verification Checklist

After all changes, run these from the host:

```bash
# 1. Gateway health
docker exec hermes-chrisann cat /opt/data/logs/gateway.log | tail -5

# 2. Spotify auth
docker exec hermes-chrisann /opt/hermes/.venv/bin/hermes auth spotify status

# 3. Web search
docker exec hermes-chrisann curl -s "http://searxng:8080/search?q=test&format=json" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('results',[])), 'results')"

# 4. Web extract keys
docker exec hermes-chrisann python3 -c "from hermes_cli.config import load_env; load_env(); import os; print('FC:', bool(os.environ.get('FIRECRAWL_API_KEY'))); print('TV:', bool(os.environ.get('TAVILY_API_KEY')))"

# 5. Image gen key
docker exec hermes-chrisann python3 -c "from hermes_cli.config import load_env; load_env(); import os; print('FAL:', bool(os.environ.get('FAL_KEY')))"
```

---

## Reference: Tim's Complete Enhancement Timeline

| Date | Enhancement | Shared? | Chrisann Status |
|---|---|---|---|
| 2026-06-02 | MCP tools (seq-thinking, sqlite, playwright) | Config per tenant | ✅ Done |
| 2026-06-04 | Reasoning model (qwen3-thinking) | Shared LiteLLM config | ✅ Done |
| 2026-06-04 | SearXNG web search | Shared container | ✅ Done |
| 2026-06-04 | VS Code `useEnvFile` suppression | Host-level setting | ✅ Done |
| 2026-06-04 | Firecrawl + Tavily (web extract) | Per-tenant keys | ✅ Done (June 6) |
| 2026-06-04 | Spotify integration | Per-tenant app + OAuth | ✅ Done (June 6) |
| 2026-06-04 | Image generation (FAL) | Per-tenant or shared key | ✅ Done (June 6) |
| 2026-06-04 | Auxiliary model routing | Config per tenant | ✅ Done (June 6) |
| 2026-06-04 | Fallback provider | — | ⏭ Declined (unnecessary) |
| 2026-06-04 | BOOT.md startup hook | Per-tenant checklist | ❌ Needs checklist |
| 2026-06-04 | Custom skin ("stealth") | Per-tenant skin | ❌ Needs skin |
| 2026-06-04 | SOUL.md personality | Per-tenant personality | ❌ Needs personality |
| 2026-06-04 | Spotify toolset enable | Per-tenant (inside container) | ✅ Done (June 6) |
| 2026-06-04 | Smart approvals | Config per tenant | ✅ Done (June 6) |
| 2026-06-04 | Healthchecks (searxng, ntfy, proxy) | Shared infrastructure | ✅ Done |
| 2026-06-04 | Healthcheck (litellm) | Shared infrastructure | ✅ Done |
| 2026-06-04 | `depends_on` startup ordering | Shared compose | ✅ Done |
| 2026-06-04 | Nginx container name fix | Shared config | ✅ Done |
| 2026-06-04 | LiteLLM Spend Dashboard Plugin | Config per tenant | ✅ Done |
| 2026-06-04 | MCP Spend Monitor Server | Config per tenant | ✅ Done |

---

## 8. BOOT.md Startup Hook (CONFIG + FILES)

**What Tim has:**
- `data/tim/hermes/hooks/boot-md/HOOK.yaml` — fires on `gateway:startup`
- `data/tim/hermes/hooks/boot-md/handler.py` — spawns one-shot agent in background thread, always sends Telegram report
- `data/tim/hermes/BOOT.md` — startup checklist (disk, vault, SearXNG, LiteLLM health)

**Behavior:** On every gateway restart, the agent greets Tim and reports full status — even when all systems are healthy. Uses `curl` with retries (not `hermes` CLI, which isn't reliably in PATH for hook agents). Waits 10 seconds before checking services to avoid false alarms.

**Steps for Chrisann:**
1. Copy the hook structure:
   ```bash
   mkdir -p data/chrisann/hermes/hooks/boot-md
   cp data/tim/hermes/hooks/boot-md/HOOK.yaml data/chrisann/hermes/hooks/boot-md/
   cp data/tim/hermes/hooks/boot-md/handler.py data/chrisann/hermes/hooks/boot-md/
   ```
2. Create `data/chrisann/hermes/BOOT.md` — same template, but change:
   - `http://litellm-tim:4000/health` → `http://litellm-chrisann:4000/health`
   - Greeting should address Chrisann, not Tim
3. Restart: `docker restart hermes-chrisann`

**Gotchas:**
- Handler uses `HERMES_HOME` env var (not `Path.home()`). Works in both containers since both set `HERMES_HOME=/opt/data`.
- Do NOT use `hermes` CLI commands in BOOT.md — use `curl`, `df`, `ls` etc. instead.

---

## 9. Custom Skin (CONFIG + FILE)

**What Tim has:**
- `data/tim/hermes/skins/stealth.yaml` — navy/gold "stealth" theme
- `display.skin: stealth` in `config.yaml`

**Steps for Chrisann:**
1. Create a skin for Chrisann at `data/chrisann/hermes/skins/<name>.yaml` — choose a different theme identity (e.g. warm, floral, or another aesthetic that fits Chrisann)
2. Add to `data/chrisann/hermes/config.yaml`:
   ```yaml
   display:
     skin: <name>
   ```
3. Restart: `docker restart hermes-chrisann`

---

## 10. SOUL.md Personality (FILE ONLY)

**What Tim has:**
- `data/tim/hermes/SOUL.md` — detailed personality spec (direct, technical, dry-witted)

**Steps for Chrisann:**
1. Write `data/chrisann/hermes/SOUL.md` with a personality tailored for Chrisann — ask her what tone/style she prefers
2. No restart needed — SOUL.md is loaded fresh each message

---

## 11. Spotify Toolset Enable (INSIDE CONTAINER)

**What Tim has:**
- Spotify toolset enabled via `hermes tools enable spotify`

**Important:** Adding the Spotify client ID, redirect URI, and OAuth tokens is NOT enough. The toolset itself is disabled by default and must be explicitly enabled inside the running container.

**Steps for Chrisann:**
1. Complete Spotify OAuth first (Section 4 above)
2. Enable the toolset:
   ```bash
   docker exec hermes-chrisann /opt/hermes/.venv/bin/hermes tools enable spotify
   ```
3. Restart: `docker restart hermes-chrisann`
4. Verify: `docker exec hermes-chrisann /opt/hermes/.venv/bin/hermes tools list | grep spotify` — should show `✓ enabled`

---

## 12. Smart Approvals (CONFIG ONLY)

**What Tim has:**
```yaml
approvals:
  mode: smart
```

**Why:** The default `manual` mode prompts the user to approve every flagged command (e.g. `curl http://...` gets flagged for using HTTP). `smart` mode uses an auxiliary LLM to auto-approve safe commands while still catching genuinely destructive operations.

**Steps for Chrisann:**
1. Add to `data/chrisann/hermes/config.yaml`:
   ```yaml
   approvals:
     mode: smart
   ```
2. Restart: `docker restart hermes-chrisann`

---

## 13. Network Hardening (SHARED — NO ACTION NEEDED)

The following changes were made to shared infrastructure. They automatically apply to both Tim and Chrisann's agents — no per-tenant steps required.

**What was done:**
- Added Docker healthchecks to `searxng` (wget), `ntfy` (wget), `hermes-proxy` (curl), and `litellm` (python3 urllib → `/health/readiness`)
- Added `depends_on` with `service_healthy` conditions so agents wait for searxng and ntfy before starting
- Standardized all nginx `proxy_pass` references to use `container_name` instead of compose service names

**What's left (deferred):**
- **Network segmentation** — splitting the flat `litellm_default` network into purpose-specific networks for true isolation. Medium effort.
- **LiteLLM redundancy** — splitting the single LiteLLM container back into per-tenant instances. High effort, +1.5GB RAM.

**Gotchas for future reference:**
- SearXNG and ntfy have no `curl` — use `wget -q --spider` for healthchecks
- LiteLLM has no `curl` or `wget` — use `python3 -c "import urllib.request; ..."`
- LiteLLM `/health` requires API key auth — use `/health/readiness` instead
- LiteLLM needs `start_period: 60s` due to Prisma migration on startup

---

## 14. LiteLLM Spend Dashboard & MCP Spend Monitor (ALREADY DONE)

Both features were deployed and configured for both agents on 2026-06-04.

### 1. Dashboard Plugin (`plugins/litellm-budget`)
- **Config**: Enabled and mounted in `docker-compose.yml` for both dashboard containers.
  - Tim's container is set with `BUDGET_SCOPE=all` to see both budgets.
  - Chrisann's container is set with `BUDGET_SCOPE=self` to see and edit only her own budget.
  - The LiteLLM master key is mounted securely at `/run/secrets/litellm_master_key` only in the dashboard containers.
- **Aesthetic**: Fully integrated tab showing current usage, limit progress bars, reset intervals, and model spend breakdown.

### 2. MCP Spend Monitor (`mcp-servers/litellm-spend`)
- **Config**: The `litellm-spend` MCP server is mounted in the gateway containers and added to `config.yaml` for both Tim and Chrisann.
- **Security**: The server runs under stdio using only the agent's virtual key (`OPENROUTER_API_KEY`) to call LiteLLM `/key/info` — no master key exposure in the gateway containers.
- **Usage**: Agents can query their current spend and budget using `get_spend_summary` and `get_model_spend` tools.
