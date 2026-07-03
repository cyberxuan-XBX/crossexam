# Adapter: API seat (any OpenAI-compatible endpoint)

`cxam seat` lets any model behind an OpenAI-compatible `/chat/completions`
endpoint hold a seat — no CLI agent required. One invocation = one full turn:
build a brief (task + exhibits +, in debate, others' analyses) → call the
model → file its long-form analysis under `analysis/<seat>.md` → post its
one-line conclusion to the bus with `"via":"api"`.

```bash
cxam seat --name <seat> --endpoint <base-url> --model <model> [--api-key KEY]
# or via env: CX_SEAT / CX_ENDPOINT / CX_MODEL / CX_API_KEY
```

## Known-good endpoints

| Provider | `--endpoint` | Notes |
|---|---|---|
| OpenAI | `https://api.openai.com/v1` | `--api-key` required |
| Anthropic (compat) | `https://api.anthropic.com/v1` | OpenAI-compatibility layer; use your Anthropic key |
| Google Gemini (compat) | `https://generativelanguage.googleapis.com/v1beta/openai` | Gemini's OpenAI-compatible endpoint |
| OpenRouter | `https://openrouter.ai/api/v1` | one key, hundreds of models |
| **Ollama (self-hosted)** | `http://localhost:11434/v1` | no key; any pulled model |
| **vLLM (self-hosted)** | `http://localhost:8000/v1` | your own weights / fine-tunes |
| **LM Studio (self-hosted)** | `http://localhost:1234/v1` | desktop local models |

Self-hosted rows are the point: **your own-brand model reviews alongside the
big vendors, on equal footing, and the audit trail shows exactly what each
one claimed.**

## Pumping turns

An API seat has no event loop — the moderator (you, or a cron job, or one of
the agentic seats) runs it once per round:

```bash
cxam seat --name qwen ... ; cxam seat --name mistral ...   # blind round
cxam phase debate
cxam seat --name qwen ... ; cxam seat --name mistral ...   # debate round
```

## Limits (also stated in the protocol)

- Advisory: cannot execute commands; verification is citation-based against
  `exhibits/` and quoted analyses. Posts are tagged `"via":"api"`.
- Context is capped (exhibits ~12k chars/file, analyses ~8k each). Bigger
  material: split exhibits or summarize first.
- The model must return one JSON object; weak models that can't are saved to
  `analysis/<seat>.raw.txt` for manual `cxam ingest`.
