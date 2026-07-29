# INSTRUCTIONS FOR HERMES-AGENT WORKSPACE

This document provides comprehensive instructions and boundaries for AI agents working in the `hermes-agent` repository workspace.

## OVERVIEW

This workspace is focused on configuring and orchestrating instances of the **NousResearch/hermes-agent** framework. `hermes-agent` is an agentic framework designed to power autonomous agents using the Hermes LLM. 

**CRITICAL DISTINCTION:**
- **Hermes** is the LLM (the brain/weights).
- **hermes-agent** is the framework (the body/software running the loop).

## ARCHITECTURE & DEPLOYMENT

The goal of this workspace is to orchestrate two strictly isolated instances of the `hermes-agent` framework:

1. **Tim's Agent**
   - Connects to: `http://litellm-tim:4000/v1` (or `localhost:4001` from host)
   - API Key: `[Stored securely in .tim-agent.env]`
   - Vault Access: `/home/cia-one/dev/hermes-agent/data/tim/obsidian`

2. **Chrisann's Agent**
   - Connects to: `http://litellm-chrisann:4000/v1` (or `localhost:4002` from host)
   - API Key: `[Stored securely in .chrisann-agent.env]`
   - Vault Access: `/home/cia-one/dev/hermes-agent/data/chrisann/obsidian`

**Strict Isolation:** There must be ZERO crossover between these two environments. Tim's agent cannot access Chrisann's proxy or vault, and vice versa.

## RULES OF ENGAGEMENT & AGENT BOUNDARIES

As established in the system rules, any agent operating in this workspace MUST adhere to the following strict boundaries:

1. **No Unauthorized Action:** Do NOT execute terminal commands, modify files, clone repositories, or alter the environment without explicit user authorization.
2. **Phase Adherence:** If proposing a plan, STOP and wait for the user to say "proceed" or "yes" before executing any steps. Do not jump ahead.
3. **No Assumptions:** If you are unsure of the user's intent, the desired configuration, or the architectural direction, ask clarifying questions rather than guessing. 
4. **Architectural Separation:** The agent framework code (`hermes-agent`) must remain separate from the proxy infrastructure (`litellm`). Do not mix their directories or configuration files.

## REPOSITORY STRUCTURE

- `/home/cia-one/dev/hermes-agent/` - The isolated workspace containing the agent framework code cloned from `NousResearch/hermes-agent`.
- Custom configuration files (e.g. `.tim-agent.env`, `.chrisann-agent.env`) should be created here specifically to bridge the framework to the local LiteLLM proxies.

## DEVELOPMENT GUIDELINES

When working on or configuring the `hermes-agent` codebase:
- Check the official `hermes-agent` documentation for correct environment variable schemas (e.g., how to point the `OPENAI_API_BASE` and `OPENAI_API_KEY`).
- Ensure all API endpoints point to the internal LiteLLM proxies rather than external providers like OpenRouter or OpenAI.
- Configure tools properly so that the agents can read their assigned Obsidian vaults without breaching isolation.
- **LiteLLM Proxy Health Probes:** When probing proxy availability, agents MUST query `http://<proxy-host>:4000/health/readiness` (unauthenticated 200 OK readiness probe). Do not probe `/health` without an `Authorization: Bearer <key>` header, as it requires master key auth and returns `401 Unauthorized`.
- Before executing any upstream merges or core framework updates, consult and follow the step-by-step upgrade protocol documented in [UPSTREAM_SYNC.md](file:///home/cia-one/dev/hermes-agent/docs/UPSTREAM_SYNC.md) to preserve the custom multi-tenant configuration layer.

---

## 🔒 SYSTEM-WIDE AGENT POLICY
Before committing any code in this repository, you **MUST** read and adhere to the global directives at:
`/home/cia-one/dev/system-management/DIRECTIVES.md`

