# LLM Provider Configuration Guide

Nyayrithm supports multiple LLM providers and lets you assign a different provider (and model) to each agent role. This document covers every supported provider, their free tiers, configuration, and recommended model assignments.

---

## How provider selection works

Provider routing happens at two levels:

**1. Global default** — set once in `.env`:
```env
LLM_DEFAULT_PROVIDER=gemini
```

**2. Per-role defaults** — edit `backend/app/llm/registry.py`:
```python
ROLE_PROVIDER_MAP = {
    "judge":          ("anthropic", "claude-opus-4-5"),
    "prosecutor":     ("openai",    "gpt-4o"),
    "witness":        ("gemini",    "gemini-2.0-flash"),
    ...
}
```

**3. Per-agent override** — when creating a simulation, set `llm_provider` and `llm_model` on any `AgentDefinition`. This takes precedence over both of the above.

---

## Gemini — Google AI (free tier available)

### Free tier
Google AI Studio provides a free tier with no credit card required:

| Model | Free RPM | Free TPD | Context window |
|-------|---------|---------|----------------|
| Gemini 2.0 Flash | 15 | 1,500,000 | 1M tokens |
| Gemini 1.5 Flash | 15 | 1,000,000 | 1M tokens |
| Gemini 1.5 Flash-8B | 15 | 4,000,000 | 1M tokens |
| Gemini 1.5 Pro | 2 | 50,000 | 2M tokens |
| Gemini 2.0 Flash-Lite | 30 | 1,500,000 | 1M tokens |

For most simulations (< 20 turns), **Gemini 2.0 Flash** on the free tier is sufficient.

### Setup
```env
LLM_DEFAULT_PROVIDER=gemini
GEMINI_API_KEY=AIza...          # from https://aistudio.google.com/app/apikey
```

### Recommended role assignments (free tier)
```python
ROLE_PROVIDER_MAP = {
    "judge":          ("gemini", "gemini-2.0-flash"),      # best free reasoning
    "prosecutor":     ("gemini", "gemini-2.0-flash"),
    "defense":        ("gemini", "gemini-2.0-flash"),
    "plaintiff":      ("gemini", "gemini-1.5-flash-8b"),   # lightest / most quota
    "accused":        ("gemini", "gemini-1.5-flash-8b"),
    "witness":        ("gemini", "gemini-1.5-flash-8b"),
    "investigator":   ("gemini", "gemini-2.0-flash"),
    "expert_witness": ("gemini", "gemini-2.0-flash"),
    "custom":         ("gemini", "gemini-1.5-flash-8b"),
}
```

### Notes
- Gemini 1.5 Pro has a 2 RPM free limit — avoid assigning it to high-turn roles
- Free tier responses may be slower during peak hours
- For production, upgrade to the paid tier (priced per million tokens, competitive with GPT-4o-mini)

---

## OpenAI

### Pricing (no free tier)
| Model | Input $/1M | Output $/1M | Best for |
|-------|-----------|------------|---------|
| `gpt-4o` | $2.50 | $10.00 | Complex reasoning roles |
| `gpt-4o-mini` | $0.15 | $0.60 | Simple roles, high volume |
| `o1` | $15.00 | $60.00 | Judge (strongest reasoning) |
| `o1-mini` | $3.00 | $12.00 | Judge (cheaper reasoning) |
| `gpt-3.5-turbo` | $0.50 | $1.50 | Background/utility |

### Setup
```env
LLM_DEFAULT_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

### Recommended role assignments
```python
ROLE_PROVIDER_MAP = {
    "judge":          ("openai", "gpt-4o"),          # or o1-mini for deeper reasoning
    "prosecutor":     ("openai", "gpt-4o"),
    "defense":        ("openai", "gpt-4o"),
    "plaintiff":      ("openai", "gpt-4o-mini"),
    "accused":        ("openai", "gpt-4o-mini"),
    "witness":        ("openai", "gpt-4o-mini"),
    "investigator":   ("openai", "gpt-4o"),
    "expert_witness": ("openai", "gpt-4o"),
    "custom":         ("openai", "gpt-4o-mini"),
}
```

---

## Anthropic (Claude)

### Pricing (no free tier)
| Model | Input $/1M | Output $/1M | Best for |
|-------|-----------|------------|---------|
| `claude-opus-4-5` | $15.00 | $75.00 | Judge, complex legal reasoning |
| `claude-sonnet-4-6` | $3.00 | $15.00 | Prosecutor, Defense, Expert |
| `claude-haiku-4-5-20251001` | $0.25 | $1.25 | Witnesses, simple roles |

### Setup
```env
LLM_DEFAULT_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

### Recommended role assignments
```python
ROLE_PROVIDER_MAP = {
    "judge":          ("anthropic", "claude-opus-4-5"),
    "prosecutor":     ("anthropic", "claude-sonnet-4-6"),
    "defense":        ("anthropic", "claude-sonnet-4-6"),
    "plaintiff":      ("anthropic", "claude-haiku-4-5-20251001"),
    "accused":        ("anthropic", "claude-haiku-4-5-20251001"),
    "witness":        ("anthropic", "claude-haiku-4-5-20251001"),
    "investigator":   ("anthropic", "claude-sonnet-4-6"),
    "expert_witness": ("anthropic", "claude-sonnet-4-6"),
    "custom":         ("anthropic", "claude-haiku-4-5-20251001"),
}
```

### Notes
- Claude models are especially strong at nuanced instruction-following — good for role-constrained agents
- `claude-opus-4-5` is the most expensive option but produces the most legally coherent Judge turns

---

## Ollama — fully local, offline, free

Run any open-weight model on your own hardware. No API key, no network calls, full data privacy. Ideal for sensitive legal matters or air-gapped deployments.

### Setup
```bash
# Install from https://ollama.com/download
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Pull models
ollama pull llama3.1:8b        # good all-rounder
ollama pull llama3.1:70b       # best quality (needs ~40 GB VRAM)
ollama pull mistral-nemo       # strong, lighter than llama3.1:8b
ollama pull gemma2:9b          # Google's open model, strong reasoning
ollama pull phi3:medium        # Microsoft, good for constrained roles
ollama pull qwen2.5:7b         # Alibaba, good multilingual support

ollama serve                   # starts API at http://localhost:11434
```

```env
LLM_DEFAULT_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
```

### Recommended models by hardware

| VRAM / RAM | Recommended models | Quality tier |
|-----------|-------------------|--------------|
| 8 GB | `mistral-nemo`, `gemma2:9b`, `phi3:medium` | Good |
| 16 GB | `llama3.1:8b`, `qwen2.5:14b` | Very good |
| 32 GB | `llama3.1:8b` (fast), `llama3.3:70b-q4` | Excellent |
| 64 GB+ | `llama3.1:70b` | Best open-source |

### Role assignments for a 16 GB machine
```python
ROLE_PROVIDER_MAP = {
    "judge":          ("ollama", "llama3.1:8b"),
    "prosecutor":     ("ollama", "llama3.1:8b"),
    "defense":        ("ollama", "llama3.1:8b"),
    "plaintiff":      ("ollama", "mistral-nemo"),
    "accused":        ("ollama", "mistral-nemo"),
    "witness":        ("ollama", "mistral-nemo"),
    "investigator":   ("ollama", "llama3.1:8b"),
    "expert_witness": ("ollama", "llama3.1:8b"),
    "custom":         ("ollama", "mistral-nemo"),
}
```

### Notes
- Ollama streaming works the same as cloud providers — tokens are emitted incrementally
- Response latency is hardware-dependent; 8B models typically run at 30–60 tokens/sec on a modern GPU
- CPU-only inference is possible but slow (5–15 tokens/sec for 8B models)

---

## Cohere

Cohere offers a **free trial** with generous limits and is especially strong for multilingual legal cases.

### Setup
```env
LLM_DEFAULT_PROVIDER=cohere        # requires implementing CohereLLMProvider
COHERE_API_KEY=...                  # from https://dashboard.cohere.com
```

> Cohere LLM provider is not bundled by default. Implement `app/llm/cohere.py` following the `LLMProvider` protocol — see [`architecture.md`](architecture.md#add-a-new-llm-provider).

---

## Mixing providers across roles

You can combine multiple providers in a single simulation. Each agent uses its own provider independently.

### Example: premium judge + free witnesses
```python
ROLE_PROVIDER_MAP = {
    "judge":          ("anthropic", "claude-opus-4-5"),   # highest quality for rulings
    "prosecutor":     ("openai",    "gpt-4o"),            # strong argument construction
    "defense":        ("openai",    "gpt-4o"),
    "plaintiff":      ("gemini",    "gemini-2.0-flash"),  # free tier
    "accused":        ("gemini",    "gemini-2.0-flash"),  # free tier
    "witness":        ("ollama",    "llama3.1:8b"),        # fully local
    "investigator":   ("openai",    "gpt-4o-mini"),       # cheaper
    "expert_witness": ("anthropic", "claude-sonnet-4-6"),
    "custom":         ("gemini",    "gemini-1.5-flash-8b"),
}
```

### Cost estimate for this mixed setup (20-turn simulation)
| Role | Turns | Provider | Est. cost |
|------|-------|---------|----------|
| Judge | 4 | Claude Opus | ~$0.08 |
| Prosecutor | 4 | GPT-4o | ~$0.02 |
| Defense | 4 | GPT-4o | ~$0.02 |
| Plaintiff | 2 | Gemini Flash | $0.00 |
| Accused | 2 | Gemini Flash | $0.00 |
| Witnesses | 4 | Ollama local | $0.00 |
| **Total** | 20 | | **~$0.12** |

---

## Provider implementation reference

All providers implement `LLMProvider` from `app/llm/base.py`:

```python
class LLMProvider(Protocol):
    provider_name: str
    model_name: str

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> LLMResponse: ...

    async def stream(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]: ...
```

The `stream()` method must yield raw token strings one at a time. The orchestrator passes these to `stream_callback` which broadcasts `turn.token` WebSocket events.

To add a new provider, see [`architecture.md` → Extending the platform](architecture.md).
