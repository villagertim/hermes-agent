# STRICT AGENT BOUNDARIES AND RULES OF ENGAGEMENT

**CRITICAL MANDATE: Read this document before taking ANY action in this workspace.**

The user has explicitly stated that AI agents must not jump ahead, make assumptions, or act outside of strict boundaries. Failure to follow these rules will result in a loss of confidence.

## 1. No Unauthorized Action
*   **DO NOT** execute terminal commands (e.g., `git clone`, `docker build`, `npm install`) unless the user has explicitly authorized you to do so.
*   **DO NOT** create, delete, or modify files based on assumptions of what the user "probably wants."
*   If you propose a plan, **STOP** and wait for the user to say "yes" or "proceed" before executing step 1.

## 2. No Assumptions
*   If a user asks a high-level architectural or conceptual question, answer the question directly. Do not assume the question is a prompt to start building.
*   Do not conflate technologies. For example, if the user asks about an *Agent Framework* (like Hermes Agent or OpenClaw), do not assume they are asking about the *LLM Weights* (like the Hermes model) simply because they share a name or context.
*   If the user's intent is ambiguous, **ASK FOR CLARIFICATION**. "Are you referring to X or Y?" is always better than guessing and building the wrong thing.

## 3. Maintain Focus
*   The user's goal is the primary directive. If the user is focused on *local agentic frameworks*, do not push or suggest *cloud-based alternatives* unless explicitly asked for comparisons.
*   If the user tells you "Stop" or "You are off track," immediately halt your current train of thought, apologize briefly without making excuses, and ask them to explicitly restate their exact focus.

## 4. Provide Options, Not Decisions
*   When multiple paths exist (e.g., deploying via Docker vs. bare metal, or choosing between two frameworks), outline the paths clearly and **wait for the user to decide**. 
*   Do not make the decision for them and start building.

## 5. Mandatory Reads
*   All agents operating in this workspace must read `MCP_ACCESS_RULES.md` before accessing or interacting with any vaults.
*   All agents MUST read `docs/UPSTREAM_SYNC.md` before attempting to pull upstream updates or sync with external branches.

**ENFORCEMENT**: These boundaries supersede all other standard operating procedures. When in doubt, do nothing and ask the user.

