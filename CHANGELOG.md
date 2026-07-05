# Changelog

## 0.6.1 — 2026-07-05

Second blind-review round (including one prompted to review at staff-engineer
depth). Same contract as 0.6.0: fix what survives verification.

- **Concede now has a cost.** `challenge`/`verify` always demanded `--ref`;
  `concede` demanded nothing — and RLHF models yield out of politeness. A
  seat that concedes without having posted any `verify` of its own now gets
  a protocol warning: reproduce the winning counter-example first. Soft
  enforcement, same as the evidence-ref rule (60 tests).
- **Correlated injection is now the top-billed risk** (SECURITY.md): one
  poisoned exhibit hits every seat at once — correlated errors are exactly
  what cross-examination assumes away. Audits of adversary-controllable
  input are explicitly unsupported until exhibit sanitization lands.
- **Own-medicine wording fixes** in the AI-reviewer section: "voting rights"
  is labeled a norm (not yet a mechanism — synthesis doesn't weight evidence
  class); "cannot fool a differently-contaminated weight set" downgraded to
  honest odds (frontier corpora overlap; agentic-seat assumption stated);
  synthesis named as our own examiner-grades-own-exam residue.
- Roadmap: benchmark vs. self-consistency k=3 (the null hypothesis to
  kill), exhibit sanitization, seat reliability profiles, non-verifiable
  task labeling.
- **Clarified as breaking in 0.6.0** (below): `read_phase` fail-closed
  changes behavior for hand-rolled `_Msg/` dirs without a `task.md` phase
  marker — 0.5.x treated them as open (`debate`), 0.6.x treats them as
  sealed (`blind`) and warns.

## 0.6.0 — 2026-07-05

Blind-review release. We handed the repo to four fresh AI reviewers
(no shared context) and fixed what they found:

- **Cross-vendor panel is now the default** when `cxam setup` detects two or
  more vendor CLIs: one mid-tier seat per vendor, plus your first local
  model if a server is running. A reviewer caught the contradiction: the
  flagship demo is cross-vendor disagreement, but the old default was a
  same-vendor tier ladder — which shares its vendor's blind spots. Tier
  ladders remain as fallbacks and via `--vendor`.
- **Breaking — `read_phase` now fails closed.** A missing/corrupt `status:`
  marker in `task.md` used to default open to `debate`, silently dropping
  blind-phase secrecy — the same bug class as the v0.5.1 audit findings. It
  now treats the arena as `blind` and warns on stderr. Hand-rolled `_Msg/`
  dirs without a phase marker change behavior: add `status: debate` to your
  `task.md` to keep the old semantics.
- **No more silent degradations**: lock-file creation failure and Windows
  lock-wait timeout now warn on stderr instead of quietly proceeding
  unlocked. Documented in SECURITY.md ("Known degradations").
- README: the human-messenger framing up top; default-panel description
  updated; three regression tests (59 total).

## 0.5.2 — 2026-07-04
- docs: README 內部連結改絕對 GitHub URL — 相對連結在 PyPI 專案頁 404（PyPI 不 host repo 其他檔案）

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
