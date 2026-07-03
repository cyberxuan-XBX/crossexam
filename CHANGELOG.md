# Changelog

## 0.1.0 — 2026-07-04

Initial release.

- `cx init / post / read / status / phase / log / hook / watch`
- Three-phase protocol: blind → debate → closed
- Blind-phase filtering with frozen cursor (withheld messages re-delivered in debate)
- Phase-aware posting rules (no verify/challenge/concede during blind)
- Adapters: Claude Code (hook), Codex CLI (AGENTS.md), Gemini CLI (GEMINI.md), generic
- Zero dependencies, single file, Python ≥ 3.9
- Born from a real divergence: three sessions, same gate-log audit, three different
  vehicle counts — resolved by evidence-based cross-examination.
