# Pre-Mortem & Meta-Audit: hermes-agent v0.16.0 Upgrade

This document tracks the adversarial stress-testing (Red-Teaming) and Principal Architect Peer Reviews conducted for the `v0.16.0` framework upgrade, along with the structural defensive designs implemented to prevent production failures.

---

## 🎭 Adversarial Vulnerability Log & Blue Team Shielding

### 1. Browser Sandbox & Playwright in Docker
*   **Adversarial Threat**: headful/headless browser automation via `@playwright/mcp` (named `puppeteer` in `config.yaml`) will fail on startup inside Docker. Chromium sandboxing requires specific flags (`--no-sandbox`, `--disable-setuid-sandbox`) or it will crash on launch, breaking web extraction capabilities.
*   **Architectural Defense**:
    *   The container executes services under a dedicated non-root user (`hermes`, UID 10000), which mitigates general root sandboxing constraints.
    *   To guarantee stability across hosts with varying kernel namespaces, we configure the Playwright MCP arguments in `data/tim/hermes/config.yaml` and `data/chrisann/hermes/config.yaml` to run headlessly using the host-installed Chromium binary:
        ```yaml
        puppeteer:
          command: npx
          args:
          - -y
          - '@playwright/mcp'
          - --headless
          - --executable-path
          - /usr/bin/chromium
          - --browser
          - chromium
          env:
            PLAYWRIGHT_BROWSERS_PATH: '0'
        ```

### 2. WebSocket Origin Validation & CORS
*   **Adversarial Threat**: Upstream upgrades to newer WebSocket libraries (e.g., `ws@8.18.0`) enforce strict origin checks. Our Nginx reverse proxy routes external domains (`agent.villagertim.com`) to internal ports, which can trigger origin mismatches and cause the dashboard UI to hang on "Connecting...".
*   **Architectural Defense**:
    *   The dashboard containers are started with the `--insecure` flag in `docker-compose.yml`:
        ```yaml
        command: [ "dashboard", "--host", "0.0.0.0", "--port", "9119", "--insecure", "--no-open" ]
        ```
        The `--insecure` flag disables strict WebSocket origin validation at the FastAPI/Uvicorn server level, allowing proxied WebSocket traffic from virtual host domains to establish connections successfully.

### 3. Localhost Port Binding and LAN Wi-Fi Access
*   **Adversarial Threat**: The new framework could default server bindings to `127.0.0.1` inside the container, blocking Nginx reverse proxy connections routing from the Docker bridge network.
*   **Architectural Defense**:
    *   Our container orchestration explicitly specifies binding coordinates. The dashboard service utilizes `--host 0.0.0.0 --port 9119` in `docker-compose.yml`, forcing Uvicorn to bind to all interfaces inside the container. Nginx proxying is thus preserved without breaking network boundaries.

### 4. Transitive Dependency Locking & Security Audit
*   **Adversarial Threat**: Upstream dependency updates or package lock changes can introduce transient library conflicts or security vulnerabilities.
*   **Architectural Defense**:
    *   A clean dependency lock check is performed using `uv lock --check` before deployment.
    *   Docker image rebuilds enforce `--no-cache` to rebuild s6-overlay process supervision steps and ensure dependencies are actualized securely.

### 5. Multi-Tenant Routing & Data Isolation
*   **Adversarial Threat**: A security regression in virtual host mapping or workspace mounting could cause Tenant A's agent configuration/vault to leak to Tenant B.
*   **Architectural Defense**:
    *   Routing is strictly isolated at the Nginx reverse-proxy level based on the distinct hostnames:
        *   `agent.villagertim.com` proxies exclusively to `hermes-tim-dashboard:9119` (Tim's container).
        *   `agent.villagerchrisann.com` proxies exclusively to `hermes-chrisann-dashboard:9119` (Chrisann's container).
    *   No shared file systems are bind-mounted between the two containers (each tenant mounts their own `/opt/data` directory from host: `./data/tim/hermes` and `./data/chrisann/hermes` respectively).
    *   Verification step: We perform active multi-tenant validation queries post-deployment to ensure that cross-tenant access returns HTTP `403 Forbidden` / `401 Unauthorized`.
