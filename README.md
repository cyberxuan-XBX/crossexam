English | [繁體中文](https://github.com/cyberxuan-XBX/crossexam/blob/main/README.zh-TW.md)

# CrossExam

[![CI](https://github.com/cyberxuan-XBX/crossexam/actions/workflows/ci.yml/badge.svg)](https://github.com/cyberxuan-XBX/crossexam/actions)
[![PyPI](https://img.shields.io/pypi/v/crossexam)](https://pypi.org/project/crossexam/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://pypi.org/project/crossexam/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/cyberxuan-XBX/crossexam/blob/main/LICENSE)

**Three AIs audited the same access log. They reported 56, 61, and 63 vehicles
on site. The truth only came out when they cross-examined each other.**

Put your AI agents under oath. CrossExam is a multi-agent debate protocol +
zero-dependency CLI that makes **Claude Code, Codex CLI, Gemini CLI, aider,
and any LLM** (API or web chat) answer the same question blind, then
**cross-examine each other with real commands** — for code review, log
audits, document review, anything where one model's confident answer isn't
good enough. No server, no framework, no required API keys: one directory of
plain files you can `git diff`.

This is what a panel looks like on the wire (real output of
`bash examples/simulated-debate.sh` — no AI attached, protocol only, ~5s):

```console
=== 2. blind phase: three seats post independent claims
sealed as sonnet (claim) — envelopes open when the moderator flips to debate
sealed as gpt (claim) — envelopes open when the moderator flips to debate
sealed as gemini (claim) — envelopes open when the moderator flips to debate

=== 3. blind means blind: sonnet tries to read — nothing is even on the bus
(no unread messages; phase: blind)

=== 4. moderator flips to debate: envelopes open
phase -> debate (3 sealed claim(s) revealed)     (…output trimmed…)

=== 8. full transcript (moderator view, timestamps trimmed for width)
#1   sonnet     claim     [analysis/sonnet.md] 56 on site; trusted the dashboard aggregate
#2   gpt        claim     [analysis/gpt.md#ghosts] 63 on site; found 7 ghost exits (entry then fake exit within 5-9s)
#3   gemini     claim     [analysis/gemini.md] 61 on site; excluded 49 unreadable plates from both directions
#4   moderator  info      phase -> debate
#5   sonnet     verify    [analysis/sonnet.md#recheck] gpt's 7 ghost exits reproduce: 7 entry->exit pairs under 10s, physically impossible
#6   gemini     challenge [analysis/gemini.md#unauth] gpt missed 11 rows: 5 drivers with accounts but no plate authorization, always Pass=False
#7   sonnet     concede   my 56 was a dashboard aggregate artifact; adopting gpt's event-level frame
#8   moderator  info      phase -> closed
```

Line #7 is the whole product: a model **conceding on evidence**, not
politeness.

```
 Terminal 1              Terminal 2              Terminal 3
 CX_SEAT=sonnet claude   CX_SEAT=gpt codex       CX_SEAT=gemini gemini
      │                        │                        │
      └────────┬───────────────┴────────────┬───────────┘
               ▼                            ▼
        _Msg/bus.jsonl   ◄── append-only conclusion bus
        _Msg/analysis/   ◄── long-form evidence per seat
        _Msg/exhibits/   ◄── material under review (logs, diffs, docs)
        _Msg/task.md     ◄── phase: blind → debate → closed
```

## Why

The transcript above replays a real incident. Three AI sessions audited the
same vehicle-gate access log and reported **56, 61, and 63** vehicles on
site. If you had opened only one window — and most people open only one
window — you would have shipped whichever number you happened to get, never
knowing the other two existed.

Copy-pasting their claims at each other — and demanding verification by real
queries, not rhetoric — produced something better than any of them: one
session *reproduced* another's ghost-exit finding with its own commands,
conceded that its 56 was a dashboard aggregation artifact, and the third
surfaced 11 rows both had missed. The merged answer was better than any
single model's. Not averaged — **examined into shape**: every surviving
number had been reproduced by a different model running its own commands.

It kept happening once the workflow was mechanized. In a later real panel run
of this tool, the Anthropic seat **mathematically disproved its own earlier
claim** under cross-examination pressure, and the OpenAI seat independently
reproduced the exact same four numbers. Models diverge — different vendors
diverge, and the *same* model diverges across runs (that's why
self-consistency, multi-agent debate, and LLM juries exist; see
[References](#references)). CrossExam turns the human-message-bus ritual into
a protocol.

## Install

```bash
pip install crossexam
# or zero-dep fallback: copy crossexam.py anywhere, alias cxam='python3 crossexam.py'
```

Single file, pure stdlib, Python ≥ 3.9.

## Quickstart — one sentence

```bash
cxam setup                      # once: detects your AI CLIs + local models
cxam run "Audit auth.py for the token expiry bug"
```

`setup` finds what you already have (claude / codex / gemini CLIs, or a local
Ollama/vLLM/LM Studio server) and writes editable presets. The default panel
is your vendor's **own tier ladder cross-examining itself** — every major
vendor ships at least three model tiers (haiku/sonnet/opus,
codex-mini/codex/codex-max, flash-lite/flash/pro), and disagreement between
tiers is exactly where the cheap model is wrong or the flagship is
overthinking. The top tier writes the synthesis.

`run` then drives the full lifecycle: every seat investigates blind (CLI
agents actually run commands in your repo; API seats are briefed on
`_Msg/exhibits/`), the phase flips to debate, seats cross-examine each
other's claims, and you get `synthesis.md` — consensus plus an explicit
disagreement table, printed at the end.

Reviewing a log, document, or conversation instead of code? Add
`--exhibit file.log` (repeatable). Inside Claude Code, there's a
[`/crossexam` slash command](https://github.com/cyberxuan-XBX/crossexam/blob/main/adapters/claude-code-skill.md).

### Cross-vendor and custom panels

Mix any seats explicitly — flags always beat presets:

```bash
cxam run "same question" \
  --agent 'sonnet=claude -p {prompt}' \
  --agent 'gpt=codex exec --skip-git-repo-check {prompt}' \
  --api   'qwen=http://localhost:11434/v1|qwen2.5:14b'
```

Or save your own lineup in `~/.config/crossexam/config.json` and pick it with
`--preset name`.

### Live mode (expert)

Prefer real interactive sessions — your memory files, your pinned model
versions, you steering each seat?

```bash
cxam init --task "..."
# one terminal per seat:
CX_SEAT=sonnet claude      # /model pins any exact version
CX_SEAT=gpt    codex
```

Wire each CLI with its adapter ([adapters/](https://github.com/cyberxuan-XBX/crossexam/tree/main/adapters)); each turn a seat
runs `cxam read`, works, posts back:

```bash
cxam post claim   "63 on site; 7 ghost exits" --ref analysis/gpt.md#ghosts
cxam post verify  "sonnet's pairing check reproduces, 7/7" --ref analysis/gpt.md#recheck
cxam post concede "my count was an aggregate artifact; adopting gpt's frame"
```

Your job shrinks to typing "continue" in whichever window you like and
flipping `cxam phase debate` when the claims are in. You can interject any
time — `cxam post info "check the exit sensor first" --as human` broadcasts
to every seat.

## Any LLM can take a seat

Three seat classes, mix freely on one panel:

| Class | Who | Verification | How |
|---|---|---|---|
| **Agentic** | Claude Code, Codex CLI, Gemini CLI, aider… | **executes commands** | hook / memory-file adapter, or headless via `cxam run` |
| **API** | any OpenAI-compatible endpoint: OpenAI, Anthropic & Gemini compat endpoints, OpenRouter, **self-hosted vLLM / Ollama / LM Studio / your own fine-tune** | citation-based | `cxam seat` runs one full turn: brief → model → analysis filed → conclusion posted |
| **Clipboard** | web-chat users: ChatGPT, Claude.ai, any chat UI, zero API access | citation-based | `cxam brief` prints a self-contained prompt; paste the reply into `cxam ingest` |

```bash
# your own local model takes a seat (e.g. Ollama)
cxam seat --name qwen --endpoint http://localhost:11434/v1 --model qwen2.5:14b

# a web-chat model takes a seat
cxam brief --name grok | <copy to the web chat>
<paste its reply> | cxam ingest --name grok
```

**Honesty note:** API and clipboard seats can't execute commands, so their
verification is citation-based rather than execution-based. Their posts carry
a `via` field (`api` / `clipboard`) so the synthesis can weigh evidence
accordingly.

## The protocol

Three phases, enforced by the CLI:

| Phase | What happens | What's enforced |
|---|---|---|
| **blind** | Each seat writes an independent analysis and posts one `claim` | Claims go into **sealed envelopes** (`.sealed/`, not the bus) and are revealed only when debate opens; `cxam read` additionally filters stray messages; `verify`/`challenge`/`concede` are rejected |
| **debate** | Seats read each other, pick *concrete, checkable* statements, and verify them **by running commands** | `verify`/`challenge` without an evidence `--ref` get warned; losers post explicit `concede` |
| **closed** | A designated seat writes `synthesis.md`: consensus + **disagreement table** | Bus accepts `info` only |

Five message types: `claim` / `verify` / `challenge` / `concede` / `info`.
One JSON line each. Conclusions on the bus, essays in `analysis/`.

Where seats agree after cross-examination, confidence is earned. Where they
still disagree, the table shows you **exactly where your judgment is
needed**. Divergence is signal, not noise.

## FAQ

**Do the sessions talk in real time?**
CLI agents are turn-based; messages are picked up at each turn boundary. In
practice you type "continue" in a window and that seat catches up. Hook-based
adapters (Claude Code) surface the unread count automatically on every
prompt. `cxam run` needs no pumping at all.

**Why not just use subagents?**
Subagents are one brain fanning out — same vendor, usually no memory, no
version pinning, and the orchestrator grades its own homework. CrossExam
seats are independent full sessions, cross-grading each other.

**How many seats?**
Any number. Two gives you a reviewer; three-plus gives you a jury and
majority signals.

**Windows?**
The protocol, tests, and all core commands (init/post/read/status/phase/log/
hook/seat/brief/ingest) are pure-stdlib and run natively — file locking
degrades gracefully. One caveat: `cxam run --agent` spawns seats through a
POSIX shell, so on Windows drive agent seats from WSL or Git Bash (API and
clipboard seats have no such requirement).

**Can a misbehaving agent peek during blind?**
Not at the bus: blind-phase claims live in sealed envelopes and simply aren't
there until debate opens. `analysis/*.md` files remain plain files though —
adapters instruct against reading them early, but that part is discipline,
not a boundary. Full threat model in [SECURITY.md](https://github.com/cyberxuan-XBX/crossexam/blob/main/SECURITY.md).

**Does it spawn/manage my CLIs?**
`cxam run` spawns headless turns; beyond that it's not a process manager —
tmux / claude-squad-style tools do that and compose fine with this. The
protocol itself never requires an API key; `cxam seat` is an optional bridge
for models without a CLI.

## Related work

We surveyed 40+ neighbors on 2026-07-04 — full table with verified stars in
[docs/related-work.md](https://github.com/cyberxuan-XBX/crossexam/blob/main/docs/related-work.md). Two axes matter: **who
verifies** (nobody / the lead model / independent peers) and **how**
(rhetoric & ranking / executed commands):

| | rhetoric & ranking | executed commands |
|---|---|---|
| **nobody / transport only** | [agmsg](https://github.com/fujibee/agmsg), [hcom](https://github.com/aannoo/hcom), [claude-squad](https://github.com/smtg-ai/claude-squad)¹ | — |
| **lead model grades** | [llm-council](https://github.com/karpathy/llm-council) (22k★), [PAL/zen-mcp](https://github.com/BeehiveInnovations/pal-mcp-server) (11.6k★), [ensemble](https://github.com/raiyanyahya/ensemble), [adversarial-review](https://github.com/alecnielsen/adversarial-review) | — |
| **independent peers** | [MassGen](https://github.com/massgen/MassGen), research debate repos | **CrossExam** |

¹ process managers run many sessions side by side that never talk; they
compose nicely with CrossExam.

As far as we could verify, the executed-commands × independent-peers cell was
empty: councils debate *text* (reviewers never run a command against your
repo), transports ship no verification protocol, and orchestrator-graders
have the examiner grading its own homework. If we missed you, open an issue;
we'll cite you.

## References

The protocol stands on prior art:

- Du, Li, Torralba, Tenenbaum & Mordatch (2023). *Improving Factuality and
  Reasoning in Language Models through Multiagent Debate.*
  [arXiv:2305.14325](https://arxiv.org/abs/2305.14325) — debate between model
  instances improves factuality; CrossExam adds command-level verification.
- Wang et al. (2022). *Self-Consistency Improves Chain of Thought Reasoning
  in Language Models.* [arXiv:2203.11171](https://arxiv.org/abs/2203.11171)
  — why even one model deserves multiple independent runs.
- Erman, Hayes-Roth, Lesser & Reddy (1980). *The Hearsay-II
  Speech-Understanding System.* ACM Computing Surveys 12(2) — the original
  blackboard architecture. `_Msg/` is a blackboard, 46 years on.
- Verga et al. (2024). *Replacing Judges with Juries: Evaluating LLM
  Generations with a Panel of LLM Evaluators.*
  [arXiv:2404.18796](https://arxiv.org/abs/2404.18796) — a jury of diverse
  judges beats a single large judge; CrossExam's jurors can subpoena the
  evidence.
- [karpathy/llm-council](https://github.com/karpathy/llm-council) — the
  pattern-maker for API-side model councils. CrossExam moves the council out
  of a web app, into your repo, and hands it a shell.

## Roadmap

- **Distributed seats** — one panel, seats on different machines (the bus is
  already just files; a sync story is the missing piece).
- **Confidence-weighted synthesis** — weigh verify/challenge by evidence
  class (`executed` > `cited`), informed by published LLM-as-judge bias
  research.
- **MCP server mode** — one line to give any MCP-capable host a
  `crossexam` tool.
- Demo recording (asciinema) for the README.

## Disclaimer

CrossExam is an independent open-source project. It is not affiliated with,
endorsed by, or connected to Anthropic, OpenAI, Google, or any of their
products. Product names are used solely to describe interoperability.

## Citation

```bibtex
@software{crossexam2026,
  author = {XBX},
  title  = {CrossExam: file-based cross-examination for multi-LLM CLI collaboration},
  year   = {2026},
  url    = {https://github.com/cyberxuan-XBX/crossexam}
}
```

---

MIT © 2026 XBX — Built in Taiwan 🇹🇼
