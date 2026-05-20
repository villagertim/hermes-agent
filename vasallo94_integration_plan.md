# Implementation Plan: Vasallo94/obsidian-mcp-server Integration

This plan is split into two phases as requested, focusing on security first and then integration.

## Plan A: Setup & Security Scan (In the New Workspace)
*Goal: Clone, audit, and verify the MCP server before exposing any data to it.*

1. **Clone Repository**: Clone `https://github.com/Vasallo94/obsidian-mcp-server` into the new workspace.
2. **Security Scan (Code)**: 
    * Scan the Python code for unsafe file operations or directory traversal risks (since it handles vault files).
    * Check for hardcoded secrets or unsafe network calls.
    * *Suggestion*: Use a tool like `bandit` for static security analysis of the Python code.
3. **Security Scan (Dependencies)**:
    * Analyze the `requirements.txt` or lock files for known vulnerabilities.
    * *Suggestion*: Use `safety` or `pip-audit` to check dependencies against vulnerability databases.
4. **Build & Verify**:
    * Install dependencies in a clean virtual environment.
    * Verify the server starts and responds to basic MCP initialization requests without errors.

## Plan B: Integration & Orchestration (Back in the Hermes-Agent Workspace)
*Goal: Connect the agents and Antigravity to the verified server while maintaining strict isolation.*

1. **Decide Execution Mode**: 
    * Choose between running via `stdio` inside the containers (Option A) or as separate Docker services (Option B).
2. **Configure Tim & Chrisann**:
    * Update `cli-config-tim.yaml` and `cli-config-chrisann.yaml` with the paths or endpoints.
    * Ensure each agent can only access its own specific vault.
3. **Configure Antigravity (Me)**:
    * Update `mcp_config.json` to use the new server.
    * Enforce **Read-Only** access to both vaults to prevent accidental modifications.

## Recommendations & Suggestions
* **Security Scanners**: I recommend running automated scans in Plan A, Step 2 and 3. I can execute these if the tools are available or can be installed in the new workspace.
* **Building**: For a Python project, "building" usually means resolving dependencies and verifying the entry point works. If the repo includes a Dockerfile, it could also mean building the Docker image. We will assess this once we see the repo structure.
* **Isolation Check**: In Plan B, we must double-check that the server instance for Tim cannot be forced to read Chrisann's path, even if requested by the agent.
