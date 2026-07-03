# Adapter: clipboard seat (web-chat LLMs, zero API)

No API key, no CLI, no problem. Any web chat — ChatGPT, Claude.ai, Gemini,
a corporate internal chatbot — can hold a seat through copy-paste, and the
protocol still keeps the audit trail.

## Flow

```bash
# 1. generate a self-contained prompt for this seat & phase
cxam brief --name grok
#    -> copy the printed prompt into the web chat

# 2. paste the model's reply back (stdin)
cxam ingest --name grok <<'EOF'
{"analysis": "...", "type": "claim", "msg": "..."}
EOF
```

`ingest` tolerates markdown fences and surrounding prose — it extracts the
first valid JSON object with a `msg` field, files the `analysis` text under
`_Msg/analysis/<seat>.md`, and posts the conclusion tagged `"via":"clipboard"`.

## Phase behavior

- `blind`: the brief contains only the task and `exhibits/` — nothing from
  other seats, so the web model's take stays independent. Replies are coerced
  to `claim`.
- `debate`: the brief includes the bus and other seats' analyses; the model
  is instructed to verify/challenge with cited evidence, or concede.

## When to use

- You have a subscription chat but no API access.
- You want one quick outside opinion on a panel of CLI agents.
- Air-gapped review: print the brief, get the reply elsewhere, ingest later —
  the bus never needs a network.
