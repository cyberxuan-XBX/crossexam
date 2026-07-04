# Changelog

## 0.5.1 — 2026-07-04

Dogfood release. We ran CrossExam on its own source (Claude + Codex + a local
Ollama model). The panel reproduced **6 real bugs the 48-test suite missed** —
two vendors independently confirming each with running repros, the local
model's "looks fine" claim challenged and conceded. All six are fixed here,
each with a regression test:

1. **Seat-name path traversal** (security): `CX_SEAT="../../pwned"` wrote a
   file outside `_Msg/`. Seat names are now validated everywhere they become a
   path.
2. **`log --all` blind bypass** (security): a seated agent could reveal sealed
   blind claims with `--all`; `--all` now only helps an unseated moderator.
3. **Direct `blind → closed` early-revealed** sealed claims; reveal now
   happens only when debate opens.
4. **`merge_sealed()` crash** under concurrent phase flips (unlocked
   read-then-unlink) — now serialized.
5. **Stale `.sealed/` leak** across an abandoned/reused `_Msg/` — the "fresh"
   check now counts sealed envelopes, and `--force` clears them.
6. **Seal-vs-reveal race** could strand a claim in `.sealed/` past debate —
   sealing and revealing now share a lock (`phase_lock`).

The irony is the point: a tool for catching one model's blind spots caught its
own author's, in a release literally named "hardening."

## 0.5.0 — 2026-07-04

Hardening release — closing the gaps from our own audit.

- **Sealed envelopes**: blind-phase claims now go to `_Msg/.sealed/<seat>.jsonl`
  instead of the bus — there is mechanically nothing to peek at until the
  moderator opens debate (claims are then revealed in timestamp order).
  The read/log blind filter remains as a second layer for direct writers.
- **Windows agent seats**: `cxam run --agent` now routes through Git Bash /
  WSL bash automatically on Windows, with a clear error when absent.
- **Prompt-injection hardening**: every debate prompt and the protocol's iron
  rules now state that other seats' text is evidence to check, never
  instructions to follow. New SECURITY.md documents the full threat model
  (injection surface, bus integrity, data egress, sandboxing).
- `--max-chars` on `cxam seat` / `cxam brief` for larger exhibits.
- Stress tests: 8-thread concurrent append integrity, 10-seat panel. The
  concurrency test caught a **real Windows data-loss bug** on CI (bare
  `O_APPEND` isn't atomic there, dropping ~5/400 lines under contention);
  fixed with a portable mkdir-based lock around every bus/envelope write.
- Roadmap section (distributed seats, confidence-weighted synthesis, MCP).

## 0.4.0 — 2026-07-04

One sentence is the whole interface.

- `cxam setup` — one-time detection of installed AI CLIs (claude / codex /
  gemini) and local OpenAI-compatible servers (ollama, vLLM, LM Studio);
  writes editable tier-panel presets to `~/.config/crossexam/config.json`.
- Default panel = one vendor's three model tiers cross-examining each other
  (haiku/sonnet/opus, codex-mini/codex/codex-max, flash-lite/flash/pro, or
  your local models) with the top tier as synthesizer. Cross-vendor panels
  remain one `--preset`/`--agent` away.
- `cxam run "your question"` — positional task, no flags needed after setup.
- `/crossexam` slash-command adapter for Claude Code (one sentence in-session).

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
