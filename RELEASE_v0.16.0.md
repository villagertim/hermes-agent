# Hermes Agent v0.16.0 (v2026.6.5)

**Release Date:** June 5, 2026
**Since v0.15.2:** 841 commits · 54 merged PRs · major release
**Deployed:** June 6, 2026 (multi-tenant Tim + Chrisann)

> **The Desktop + Model Identity Release.** Headline: a full Electron-based desktop client, complete `key_env` / `discover_models` credential identity overhaul in `model_switch.py` (our local patch is now officially upstreamed), uncapped delegation depth, s6-overlay Docker refresh, and a Starlette CVE patch. For our multi-tenant deployment: the `key_env` local patch is **retired** — zero local core patches remain. Only the `chromium` Dockerfile addition persists as a deployment-layer customisation.

---

## ✨ Highlights (Multi-Tenant Impact)

- **`key_env` patch fully upstreamed** — `hermes_cli/model_switch.py` now natively resolves `key_env` environment variable references in `custom_providers`, with added credential identity grouping, `discover_models` support, and `api_mode` wire protocol separation. Our local patch (maintained since v0.14.0) is **dropped**. ([4b2d00f](https://github.com/NousResearch/hermes-agent/commit/4b2d00f84), [7ae8aac](https://github.com/NousResearch/hermes-agent/commit/7ae8aac3b))

- **CVE-2026-48710 patched** — `starlette>=1.0.1` pinned to fix the BadHost header injection vulnerability. ([#35118](https://github.com/NousResearch/hermes-agent/pull/35118))

- **Playwright headless_shell browser discovery fixed** — Docker containers now correctly discover and use the Playwright-installed headless Chromium shell. ([#35717](https://github.com/NousResearch/hermes-agent/pull/35717))

- **s6-overlay Docker guide refreshed** — Updated documentation for the s6-overlay supervision model. ([42612aa](https://github.com/NousResearch/hermes-agent/commit/42612aa35))

- **Delegation depth uncapped** — `max_spawn_depth` no longer has an artificial ceiling (floor 1, no cap), enabling deeper agent delegation chains. ([#39772](https://github.com/NousResearch/hermes-agent/pull/39772))

- **max_tokens propagation complete** — Full chain from `config.yaml` → `AIAgent` → per-provider `max_output_tokens` now works end-to-end. ([cf78659](https://github.com/NousResearch/hermes-agent/commit/cf786593c), [1c909e7](https://github.com/NousResearch/hermes-agent/commit/1c909e75e), [14275d7](https://github.com/NousResearch/hermes-agent/commit/14275d7ba))

---

## 🖥️ Desktop App (New)

A full Electron-based native desktop client was added in this release cycle. **Not relevant to our Docker deployment**, but notable upstream changes:

- Per-profile remote gateway hosts, drag-sort profiles, concurrent multi-profile gateway sockets
- Session drag-as-links, command palette (Cmd/Ctrl+P), i18n (Chinese/zh-Hans)
- Username/password login for remote gateways
- Per-session profile switching + cross-profile sessions
- "Choose provider later" skip in first-run onboarding

---

## 🔒 Security

- **CVE-2026-48710**: Starlette BadHost header injection — pinned `starlette>=1.0.1` ([#35118](https://github.com/NousResearch/hermes-agent/pull/35118))
- **GHSA-8x6r-g9mw-2r78**: `react-router-dom` bumped to 7.17.0 ([46c16b9](https://github.com/NousResearch/hermes-agent/commit/46c16b928))
- **GHSA-5qr3-c538-wm9j**: Plugin manifest `api` field path-traversal RCE hardened — absolute paths and `..` traversals are now rejected at both discovery and mount time
- File path neutralisation in mutation-verifier footer ([#35684](https://github.com/NousResearch/hermes-agent/pull/35684))
- AWS SDK credentials blocked from subprocess environment ([95b5b72](https://github.com/NousResearch/hermes-agent/commit/95b5b7240))
- Bedrock subprocess strip narrowed to inference bearer token only ([6bebab4](https://github.com/NousResearch/hermes-agent/commit/6bebab476))
- `bws_cache.json` added to file_safety read guard ([4126da6](https://github.com/NousResearch/hermes-agent/commit/4126da65a))
- Dashboard session token stripped from subprocess env ([3278b42](https://github.com/NousResearch/hermes-agent/commit/3278b423d))
- Network egress isolation guide for Docker deployments ([#26385](https://github.com/NousResearch/hermes-agent/pull/26385))

---

## 🐛 Bug Fixes

### Gateway
- New chats honor their profile in global-remote mode ([#39993](https://github.com/NousResearch/hermes-agent/pull/39993))
- Full multi-profile support over one global-remote dashboard ([#39921](https://github.com/NousResearch/hermes-agent/pull/39921))
- Silent file-delivery drops now logged ([#39767](https://github.com/NousResearch/hermes-agent/pull/39767))
- `/voice` explains usage when toggled bare ([#39766](https://github.com/NousResearch/hermes-agent/pull/39766))
- Feishu meeting invitation handling ([f3bbfda](https://github.com/NousResearch/hermes-agent/commit/f3bbfda6d))

### Models
- DeepSeek-v4-flash as Nous silent default (prevents expensive flagship escalation) ([3da44db](https://github.com/NousResearch/hermes-agent/commit/3da44dbda))
- Gemini: default native `maxOutputTokens` + strip OpenAI `extra_body` on Gemini endpoints ([#39730](https://github.com/NousResearch/hermes-agent/pull/39730))
- `qwen/qwen3.7-plus` added to nous + openrouter catalogs ([#39409](https://github.com/NousResearch/hermes-agent/pull/39409))

### CLI
- `/model` autocomplete removed to prevent argument collision ([#39727](https://github.com/NousResearch/hermes-agent/pull/39727))
- Chromium required for local browser readiness in `setup`/`status` surfaces ([3cd1bd9](https://github.com/NousResearch/hermes-agent/commit/3cd1bd971))

### Docker
- Playwright headless_shell browser discovery ([#35717](https://github.com/NousResearch/hermes-agent/pull/35717))

### Dashboard
- Embedded chat always enabled; `--tui` flag removed ([cae6b54](https://github.com/NousResearch/hermes-agent/commit/cae6b5486))
- Generic self-hosted OIDC provider for dashboard auth ([f57ce34](https://github.com/NousResearch/hermes-agent/commit/f57ce341d))
- `rg`/`grep` search error guard made reachable + partial matches preserved ([#39858](https://github.com/NousResearch/hermes-agent/pull/39858))

### Discord
- Voice-channel mixer — ambient idle bed + verbal acks that overlap TTS ([#39659](https://github.com/NousResearch/hermes-agent/pull/39659))

---

## 🛠️ Infrastructure (Dockerfile)

Changes to the upstream Dockerfile since v0.15.2:
- Added `iputils-ping`, `python3-venv`, `libolm-dev` to system deps
- tini backward-compat shim (`ln -sf /init /usr/bin/tini`) for legacy orchestration templates
- `HERMES_TUI_DIR` env var for prebuilt TUI bundle (prevents runtime `npm install` race conditions)
- hindsight memory client (`hindsight-client`) baked into image
- `/opt/hermes/gateway` made runtime-writable for `__pycache__` and gateway state artifacts
- `hermes-exec-shim.sh` privilege-drop shim for `docker exec` safety

---

## 📋 Local Patch Status

| Patch | Status | Notes |
|-------|--------|-------|
| `key_env` in `model_switch.py` | **RETIRED** | Fully upstreamed with enhancements |
| `chromium` in Dockerfile | **ACTIVE** | Required for Playwright MCP headless browser |

---

**Full Changelog**: [v2026.5.29.2...v2026.6.5](https://github.com/NousResearch/hermes-agent/compare/v2026.5.29.2...v2026.6.5)
