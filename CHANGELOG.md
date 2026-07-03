# Changelog

## 0.3.0 — 2026-07-04

The porcelain: one command runs the whole panel.

- `cxam run` — blind → debate → synthesis in a single invocation. Headless
  CLI seats (`--agent 'sonnet=claude -p {prompt}'`, `codex exec`, `gemini -p`)
  actually execute commands in your repo; API seats (`--api name=endpoint|model`)
  are briefed automatically; `--exhibit` copies material in; `--rounds`,
  `--synthesis`, `--force` control the flow.
- Interactive multi-terminal usage reframed as "live mode" (expert path).
- Verified end-to-end with a real panel: headless Claude + self-hosted Ollama
  qwen2.5:14b — Claude byte-diffed the exhibit to verify qwen's table, and the
  synthesis adjudicated a contradiction inside qwen's own blind draft.

## 0.2.0 — 2026-07-04

Universal seats: any LLM can join, not just CLI agents.

- `cxam seat` — one advisory-seat turn against any OpenAI-compatible endpoint
  (OpenAI, Anthropic/Gemini compat, OpenRouter, self-hosted vLLM/Ollama/LM
  Studio). Briefs the model, files its analysis, posts its conclusion.
- `cxam brief` / `cxam ingest` — clipboard seats for web-chat LLMs (zero API).
- `_Msg/exhibits/` — material under review (transcripts, docs, diffs);
  advisory seats are briefed on it automatically. Panel-review mode.
- Seat classes formalized in the protocol: agentic (executes commands) vs
  advisory (citation-based); advisory posts carry `"via":"api"|"clipboard"`.
- Verified end-to-end against a self-hosted Ollama qwen2.5:14b seat.

## 0.1.0 — 2026-07-04

Initial release.

- `cxam init / post / read / status / phase / log / hook / watch`
- Three-phase protocol: blind → debate → closed
- Blind-phase filtering with frozen cursor (withheld messages re-delivered in debate)
- Phase-aware posting rules (no verify/challenge/concede during blind)
- Adapters: Claude Code (hook), Codex CLI (AGENTS.md), Gemini CLI (GEMINI.md), generic
- Zero dependencies, single file, Python ≥ 3.9
- Born from a real divergence: three sessions, same gate-log audit, three different
  vehicle counts — resolved by evidence-based cross-examination.
