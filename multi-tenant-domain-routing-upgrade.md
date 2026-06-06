# Walkthrough - Multi-tenant Stack Infrastructure Upgrade

We have successfully upgraded the infrastructure of the local multi-tenant Hermes stack. This allows routing incoming traffic for custom domains (`villagertim.com` and `villagerchrisann.com`) to the internal multi-tenant service containers with proper WebSockets and basic authentication support.

Additionally, we connected `daily-briefer`, `daily-briefer-chrisann`, and `iQUA` to the shared `litellm_default` network and configured their corresponding subdomains through the same proxy and tunnel.

---

## Changes Made

### 1. Daily Briefer & iQUA Docker Compose Configurations
We updated each respective repository's `docker-compose.yml` to attach the services to the shared `litellm_default` external network.

- **[daily-briefer docker-compose.yml](file:///home/cia-one/dev/daily-briefer/docker-compose.yml)**:
  ```yaml
      networks:
        - litellm_default
  networks:
    litellm_default:
      external: true
  ```
- **[daily-briefer-chrisann docker-compose.yml](file:///home/cia-one/dev/daily-briefer-chrisann/docker-compose.yml)**:
  ```yaml
      networks:
        - litellm_default
  networks:
    litellm_default:
      external: true
  ```
- **[iQUA docker-compose.yml](file:///home/cia-one/dev/iQUA/docker-compose.yml)**:
  ```yaml
      container_name: iqua-dashboard
      networks:
        - litellm_default
  networks:
    litellm_default:
      external: true
  ```

### 2. Hermes Agent [docker-compose.yml](file:///home/cia-one/dev/hermes-agent/docker-compose.yml)

We modified the `proxy` service to drop individual port mappings and exposed standard ports `80` and `443` for global HTTP/HTTPS ingress. We also appended the new `cloudflare-tunnel` outbound service.

```yaml
  proxy:
    image: nginx:alpine
    container_name: hermes-proxy
    restart: unless-stopped
    networks:
      - litellm_default
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./.htpasswd-tim:/etc/nginx/.htpasswd-tim:ro
      - ./.htpasswd-chrisann:/etc/nginx/.htpasswd-chrisann:ro

  cloudflare-tunnel:
    image: cloudflare/cloudflared:latest
    container_name: cloudflare-tunnel
    restart: unless-stopped
    networks:
      - litellm_default
    command: tunnel --no-autoupdate run --token ${CLOUDFLARE_TUNNEL_TOKEN}
```

### 3. Hermes Agent [nginx.conf](file:///home/cia-one/dev/hermes-agent/nginx.conf)

We rewrote Nginx configurations to listen on port `80` and handle virtual host routing via Host headers, preserving basic authentication credentials and adding WebSocket upgrade headers.

```nginx
events {}

http {
    # ─────────────────────────────────────────────────────────────────────────────
    # TIM'S DOMAINS
    # ─────────────────────────────────────────────────────────────────────────────

    # Tim's Hermes Agent Dashboard
    server {
        listen 80;
        server_name agent.villagertim.com;
        auth_basic "Tim's Hermes Agent";
        auth_basic_user_file /etc/nginx/.htpasswd-tim;

        location / {
            proxy_pass http://hermes-tim-dashboard:9119;
            proxy_set_header Host $host;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }

    # Tim's Obsidian Vault (Web GUI)
    server {
        listen 80;
        server_name notes.villagertim.com;
        auth_basic "Tim's Obsidian Vault";
        auth_basic_user_file /etc/nginx/.htpasswd-tim;

        location / {
            proxy_pass http://obsidian-gui-tim:3000;
            proxy_set_header Host $host;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }

    # Tim's n8n Automation
    server {
        listen 80;
        server_name automate.villagertim.com;
        auth_basic "Tim's n8n Automation";
        auth_basic_user_file /etc/nginx/.htpasswd-tim;

        location / {
            proxy_pass http://n8n-tim:5678;
            proxy_set_header Host $host;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }

    # Tim's Daily Briefer
    server {
        listen 80;
        server_name briefer.villagertim.com;
        auth_basic "Tim's Daily Briefer";
        auth_basic_user_file /etc/nginx/.htpasswd-tim;

        location / {
            proxy_pass http://daily-briefer:8080;
            proxy_set_header Host $host;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }

    # Tim's iQUA Dashboard
    server {
        listen 80;
        server_name iqua.villagertim.com;
        auth_basic "Tim's iQUA";
        auth_basic_user_file /etc/nginx/.htpasswd-tim;

        location / {
            proxy_pass http://iqua-dashboard:8088;
            proxy_set_header Host $host;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }

    # ─────────────────────────────────────────────────────────────────────────────
    # CHRISANN'S DOMAINS
    # ─────────────────────────────────────────────────────────────────────────────

    # Chrisann's Hermes Agent Dashboard
    server {
        listen 80;
        server_name agent.villagerchrisann.com;
        auth_basic "Chrisann's Hermes Agent";
        auth_basic_user_file /etc/nginx/.htpasswd-chrisann;

        location / {
            proxy_pass http://hermes-chrisann-dashboard:9119;
            proxy_set_header Host $host;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }

    # Chrisann's Obsidian Vault (Web GUI)
    server {
        listen 80;
        server_name notes.villagerchrisann.com;
        auth_basic "Chrisann's Obsidian Vault";
        auth_basic_user_file /etc/nginx/.htpasswd-chrisann;

        location / {
            proxy_pass http://obsidian-gui-chrisann:3000;
            proxy_set_header Host $host;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }

    # Chrisann's n8n Automation
    server {
        listen 80;
        server_name automate.villagerchrisann.com;
        auth_basic "Chrisann's n8n Automation";
        auth_basic_user_file /etc/nginx/.htpasswd-chrisann;

        location / {
            proxy_pass http://n8n-chrisann:5678;
            proxy_set_header Host $host;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }

    # Chrisann's Daily Briefer
    server {
        listen 80;
        server_name briefer.villagerchrisann.com;
        auth_basic "Chrisann's Daily Briefer";
        auth_basic_user_file /etc/nginx/.htpasswd-chrisann;

        location / {
            proxy_pass http://daily-briefer-chrisann:8081;
            proxy_set_header Host $host;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

---

## Validation & Verification Results

### 1. Network Attachment & Container Startups
We launched/recreated the stacks so they successfully registered on the shared network:
- `daily-briefer` -> **Started and Connected**
- `daily-briefer-chrisann` -> **Started and Connected**
- `iqua-dashboard` -> **Started and Connected**

### 2. Nginx Configuration Reload
We successfully reloaded the active reverse proxy configurations to register all routing definitions:
- Command: `docker compose exec -T proxy nginx -s reload`
- Result: **Success** (no syntax or upstream resolution errors).
