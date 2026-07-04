# LiteLLM Proxy — Agent Guide

This document describes the multi-tenant LiteLLM proxy environment running on this machine.
Read this before making any API calls or modifying configurations.

---

## Overview

A containerized [LiteLLM](https://docs.litellm.ai/) proxy is running that routes all AI model
requests through [OpenRouter](https://openrouter.ai/). Each user has their own isolated proxy
instance with their own API key. Models are organised into **tiers** by capability.

```
Host Machine
├── litellm-tim       → port 4001  (Tim's proxy)
├── litellm-chrisann  → port 4002  (Chrisann's proxy)
└── postgres (db)     → internal only
```

---

## Proxy Instances

| User     | Base URL                    | Master Key                |
|----------|-----------------------------|---------------------------|
| Tim      | `http://localhost:4001/v1`  | `[See .tim.env]`          |
| Chrisann | `http://localhost:4002/v1`  | `[See .chrisann.env]`     |

All requests must include the header:
```
Authorization: Bearer <USER_MASTER_KEY>
```

---

## Available Models

Both proxy instances expose the same model tier names. Requests are automatically routed
to the correct underlying model on OpenRouter.

### Text / Chat

| Tier name   | Underlying model                    | Use case                              |
|-------------|-------------------------------------|---------------------------------------|
| `cheap`     | `deepseek/deepseek-v4-flash`        | Fast, low-cost tasks. Simple Q&A, summarisation, classification. |
| `complex`   | `deepseek/deepseek-v4-pro`          | Multi-step reasoning, code generation, longer context. |
| `reasoning` | `deepseek/deepseek-v4-pro`          | Same as complex — use this alias when the task requires explicit chain-of-thought. |

### Audio

| Tier name | Underlying model                    | Use case                              |
|-----------|-------------------------------------|---------------------------------------|
| `tts`     | `openai/gpt-4o-mini-tts-2025-12-15` | Text-to-speech. Returns raw MP3 audio bytes. |
| `whisper` | `openai/whisper-1`                  | Speech-to-text transcription. ⚠️ See note below. |

> **⚠️ Whisper note**: OpenRouter's `/audio/transcriptions` endpoint is currently returning
> a server-side JSON parse error (400) for all transcription models. This has been confirmed
> as an OpenRouter platform bug (reproduced with raw `curl`, bypassing LiteLLM entirely).
> The proxy configuration is correct and will work automatically once OpenRouter resolves the issue.

---

## API Usage Examples

### Chat Completion

```bash
curl -X POST http://localhost:4001/v1/chat/completions \
  -H "Authorization: Bearer <USER_MASTER_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "cheap",
    "messages": [{"role": "user", "content": "Summarise this in one sentence: ..."}]
  }'
```

Use `"model": "complex"` or `"model": "reasoning"` for harder tasks.

### Text-to-Speech (TTS)

```bash
curl -X POST http://localhost:4001/v1/audio/speech \
  -H "Authorization: Bearer <USER_MASTER_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts",
    "input": "Hello, this is a test.",
    "voice": "alloy"
  }' \
  --output output.mp3
```

**Supported voices** (OpenAI standard): `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`

### Speech-to-Text (Whisper)

```bash
curl -X POST http://localhost:4001/v1/audio/transcriptions \
  -H "Authorization: Bearer <USER_MASTER_KEY>" \
  -F "file=@audio.mp3" \
  -F "model=whisper"
```

> ⚠️ Currently failing at OpenRouter's servers — see Whisper note above.

### Using the OpenAI Python SDK

The proxy is 100% OpenAI-compatible. Point the `base_url` at the proxy and use the master key:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:4001/v1",
    api_key="<USER_MASTER_KEY>",
)

# Chat
response = client.chat.completions.create(
    model="cheap",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)

# TTS
audio = client.audio.speech.create(
    model="tts",
    input="Hello from LiteLLM.",
    voice="alloy",
)
audio.stream_to_file("output.mp3")
```

---

## Infrastructure

### Starting / Stopping

```bash
cd /home/cia-one/dev/litellm

# Start all containers
docker compose up -d

# Stop all containers
docker compose down

# View logs for Tim's proxy
docker logs litellm-litellm-tim-1 -f

# View logs for Chrisann's proxy
docker logs litellm-litellm-chrisann-1 -f
```

> The proxy takes ~20–30 seconds after `docker compose up -d` to finish database migrations
> and begin accepting requests.

### File Layout

```
/home/cia-one/dev/litellm/
├── docker-compose.yaml       # Container definitions
├── .tim.env                  # Tim's API keys (do NOT commit)
├── .chrisann.env             # Chrisann's API keys (do NOT commit)
├── config_tim.yaml           # Tim's model routing config
├── config_chrisann.yaml      # Chrisann's model routing config
└── AGENT_GUIDE.md            # This file
```

### Environment Variables (`.tim.env` & `.chrisann.env`)

| Variable               | Purpose                                      |
|------------------------|----------------------------------------------|
| `TIM_OPENROUTER_KEY`   | Tim's OpenRouter API key (in .tim.env)       |
| `CHRISANN_OPENROUTER_KEY` | Chrisann's API key (in .chrisann.env)     |
| `DATABASE_URL`         | PostgreSQL connection string (internal)      |
| `LITELLM_MASTER_KEY`   | Proxy authentication key                     |

---

## Modifying Configurations

### Changing a model

Edit the relevant `config_*.yaml` file, then restart that user's container:

```bash
# Example: after editing config_tim.yaml
docker compose restart litellm-tim
```

### Adding a new model tier

Add an entry to `model_list` in the config YAML:

```yaml
- model_name: my-new-tier
  litellm_params:
    model: openrouter/some-provider/some-model
    api_key: "os.environ/TIM_OPENROUTER_KEY"
```

Then restart the container.

### Audio models (TTS/Whisper)

Audio models **must** include `api_base` and `custom_llm_provider: "openai"` to ensure
LiteLLM uses the OpenAI SDK client, which sends the correct binary/multipart format:

```yaml
- model_name: tts
  litellm_params:
    model: openai/gpt-4o-mini-tts-2025-12-15
    api_key: "os.environ/TIM_OPENROUTER_KEY"
    api_base: "https://openrouter.ai/api/v1"
    custom_llm_provider: "openai"
```

---

## Model Selection Guide for Agents

Use this decision tree when choosing a tier:

```
Is the task a single simple question or classification?
  └─ YES → use "cheap"
  └─ NO  → Does it require multi-step logic, code, or long context?
              └─ YES → use "complex"
              └─ Need explicit reasoning trace? → use "reasoning"

Need to generate spoken audio from text?
  └─ use "tts"

Need to transcribe audio to text?
  └─ use "whisper" (currently awaiting OpenRouter platform fix)
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `401 Authentication Error` (to proxy) | Wrong master key | Use correct `<USER_MASTER_KEY>` |
| `401 User not found` (from OpenRouter) | Invalid/expired OpenRouter API key | Regenerate key at openrouter.ai/settings/keys and update environment files |
| `500 Internal Server Error` on TTS | Audio streaming issue | Check `docker logs litellm-litellm-tim-1` |
| Whisper `400 JSON parse error` | OpenRouter platform bug | Known issue, not a config problem |
| Container not responding | Proxy still starting | Wait 30s after `docker compose up -d` |
