# Hermes Agent — AgentMail Native Email Integration Guide

This guide documents the architecture, configuration, and verification steps for providing a Hermes Agent instance with a **100% native, supervised email system** using **AgentMail** (`agentmail.to`) over standard IMAP and SMTP protocols.

---

## 1. Architectural Overview

Hermes Agent includes a built-in native **Email Platform Adapter** (`plugins/platforms/email/adapter.py`). Rather than running custom background scripts, WebSocket listeners, or separate cron workers, email integration is handled natively by the Hermes Gateway daemon.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Hermes Agent Gateway                            │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Native Email Platform Adapter                 │  │
│  │                  (plugins/platforms/email/adapter.py)            │  │
│  └───────────────▲──────────────────────────────────┬───────────────┘  │
│                  │ IMAP (993)                       │ SMTP (587)       │
│                  │ Poll interval: 15s               │ Sends replies    │
└──────────────────┼──────────────────────────────────┼──────────────────┘
                   │                                  │
                   ▼                                  ▼
        ┌──────────────────────────────────────────────────┐
        │          AgentMail (imap.agentmail.to)           │
        └──────────────────────────────────────────────────┘
```

### Key Advantages
- **Zero Custom Overhead**: Uses Hermes core codebase, requiring no custom Python wrappers or extra process supervisors.
- **Supervised Lifecycle**: Starts, stops, and recovers automatically alongside the Gateway under `s6-overlay`.
- **Sender Whitelisting**: Restricts message handling to allowed email senders via `EMAIL_ALLOWED_USERS`.
- **Thread Context & Disclosure**: Automatically preserves email conversation threads and appends mandatory AI agent disclosures.

---

## 2. AgentMail Connection Specifications

AgentMail inboxes support standard encrypted IMAP and SMTP connections.

| Setting | Value |
| :--- | :--- |
| **IMAP Host** | `imap.agentmail.to` |
| **IMAP Port** | `993` (SSL/TLS required) |
| **SMTP Host** | `smtp.agentmail.to` |
| **SMTP Port** | `587` (STARTTLS) or `465` (SSL) |
| **Username** | The full AgentMail email address (e.g. `bucky-1840@agentmail.to`) |
| **Password** | The AgentMail API Key (e.g. `am_us_...`) |

---

## 3. Configuration Steps

### A. Environment Configuration (`.env`)

Add the following environment variables to the agent's environment configuration file (e.g. `.tim-agent.env` or `.chrisann-agent.env` and the tenant's `data/<tenant>/hermes/.env`):

```env
# =============================================================================
# NATIVE EMAIL PLATFORM CONFIGURATION (AgentMail IMAP/SMTP)
# =============================================================================
EMAIL_ADDRESS=<agent-inbox-id>@agentmail.to
EMAIL_PASSWORD=<agentmail-api-key>
EMAIL_IMAP_HOST=imap.agentmail.to
EMAIL_IMAP_PORT=993
EMAIL_SMTP_HOST=smtp.agentmail.to
EMAIL_SMTP_PORT=587
EMAIL_ALLOWED_USERS=<human-operator-email>
EMAIL_HOME_ADDRESS=<human-operator-email>
EMAIL_POLL_INTERVAL=15
EMAIL_TRUST_FROM_HEADER=true
```

### Configuration Breakdown

- `EMAIL_ADDRESS`: The full inbox address created in the AgentMail dashboard.
- `EMAIL_PASSWORD`: The AgentMail API key (`am_us_...`).
- `EMAIL_IMAP_HOST` / `EMAIL_SMTP_HOST`: Set to `imap.agentmail.to` and `smtp.agentmail.to`.
- `EMAIL_ALLOWED_USERS`: Comma-separated list of allowed human sender email addresses (e.g. `villagertim@gmail.com`). Messages from unlisted senders are silently ignored for security.
- `EMAIL_POLL_INTERVAL`: Mailbox check frequency in seconds (default: 15).
- `EMAIL_TRUST_FROM_HEADER`: Set to `true` to allow authorization matching against the `From:` header when receiving mail delivered to AgentMail.

---

## 4. Deploying & Restarting the Agent

After updating the environment file, restart the target agent container so Docker populates the new environment variables into the Gateway process:

```bash
# Restart the specific tenant's container
docker compose restart agent-<tenant>
```

---

## 5. Verifying Active Email Connection

Inspect the gateway logs to confirm that the native `EmailAdapter` initialized and connected successfully:

```bash
docker logs hermes-<tenant> --tail 50 | grep -i email
```

**Expected Log Output**:
```text
[Email] Connected as <agent-inbox-id>@agentmail.to
```

---

## 6. Pre-flight Python Connectivity Verification Script

You can verify AgentMail IMAP/SMTP credentials out-of-band before starting the container using this test snippet:

```python
import imaplib, smtplib, ssl

addr = "<agent-inbox-id>@agentmail.to"
pwd = "<agentmail-api-key>"

# 1. Test IMAP
imap = imaplib.IMAP4_SSL("imap.agentmail.to", 993, timeout=10)
imap.login(addr, pwd)
imap.select("INBOX")
status, data = imap.uid("search", None, "ALL")
print(f"✓ IMAP Success! Found {len(data[0].split()) if data and data[0] else 0} messages.")
imap.logout()

# 2. Test SMTP
ctx = ssl.create_default_context()
smtp = smtplib.SMTP("smtp.agentmail.to", 587, timeout=10)
smtp.starttls(context=ctx)
smtp.login(addr, pwd)
print("✓ SMTP Success!")
smtp.quit()
```
