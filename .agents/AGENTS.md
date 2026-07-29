# Model Routing Rules

1. **Default Mode (Local Focus)**:
   All code-writing, auditing loops, structural diagnostics, and verification tasks MUST route their reasoning through `local-model` using the `litellm-tim/call_local_model` tool.
   
2. **Token-Optimized Logging**:
   To prevent chat history bloat, raw query prompts and full outputs must be written to `docs/local_model_log.md` inside this workspace. The main chat window must only display a 1-2 sentence confirmation pointing to the log.

3. **Temporary Built-in Model Override**:
   If the user explicitly asks to "use your built-in model", "use Gemini", or "bypass LiteLLM", the agent is authorized to run that specific turn directly using its built-in base reasoning model.
   *   **Crucial Rule**: The decision of when a task requires a more advanced or built-in model is solely the operator's. The agent is strictly prohibited from escalating or deciding on its own to use a stronger model.
   *   **Recommendation Clause**: The agent is allowed to explicitly recommend using a stronger/built-in model if it believes a task is sufficiently complex that it would be highly advantageous. However, the agent MUST wait for the operator to explicitly acknowledge and approve the recommendation before performing any such switch.

4. **Automatic Reversion**:
   Immediately after the turn requesting the built-in model is finished, the agent must revert to the default `local-model` routing for all subsequent steps.
