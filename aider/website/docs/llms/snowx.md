---
parent: Connecting to LLMs
nav_order: 850
---

# SnowX

SnowX is a free AI provider that offers various state-of-the-art models without requiring an API key.

## Available Models

SnowX provides access to the following models:

### GPT Models
- `snowx/gpt-4o` - GPT-4o model
- `snowx/gpt-4.1` - GPT-4.1 model 
- `snowx/gpt-4.1-mini` - GPT-4.1 Mini model
- `snowx/gpt-4.1-nano` - GPT-4.1 Nano model
- `snowx/o4-mini` - o4-mini reasoning model (supports `--reasoning-effort`)
- `snowx/o4-mini-high` - o4-mini with high reasoning effort by default

### Claude Models
- `snowx/claude-opus-4` - Claude Opus 4 model
- `snowx/claude-sonnet-4` - Claude Sonnet 4 model
- `snowx/claude-3-7-sonnet` - Claude 3.7 Sonnet model
- `snowx/claude-3-5-sonnet` - Claude 3.5 Sonnet model

### Other Models
- `snowx/grok-3` - Grok-3 model
- `snowx/grok-3-mini` - Grok-3 Mini model
- `snowx/mai-ds-r1` - MAI-DS-R1 reasoning model (uses `<think>` tags)
- `snowx/llama-maverick` - Llama 4 Maverick 17B model
- `snowx/deepseek-r1` - DeepSeek-R1 reasoning model (uses `<think>` tags)
- `snowx/deepseek-v3` - DeepSeek-V3 model

## Usage

Since SnowX doesn't require an API key, you can use any SnowX model directly:

```bash
aider --model snowx/gpt-4o
```

```bash
aider --model snowx/claude-3-5-sonnet
```

```bash
aider --model snowx/deepseek-r1
```

## Reasoning Models

Some SnowX models support reasoning features:

### o4-mini models
The o4-mini models support reasoning effort control:

```bash
# Use o4-mini with default reasoning
aider --model snowx/o4-mini

# Use o4-mini with medium reasoning effort
aider --model snowx/o4-mini --reasoning-effort medium

# Use o4-mini-high (pre-configured with high reasoning effort)
aider --model snowx/o4-mini-high
```

### Models with thinking tags
These models use `<think>` tags for their reasoning process:
- `snowx/mai-ds-r1`
- `snowx/deepseek-r1`

The thinking content is automatically handled and hidden from the main output.

## Features

- **No API key required** - All SnowX models are free to use
- **Streaming support** - Real-time response streaming
- **Vision support** - GPT and Claude models support image inputs
- **Function calling** - All models support function/tool calling
- **Thinking blocks** - Reasoning models automatically handle thinking content

## Limitations

- Rate limits may apply during high usage periods
- Models are provided as-is without guaranteed uptime
- Some models may have different behavior compared to their official counterparts 