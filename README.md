# CrossExam

[![CI](https://github.com/cyberxuan-XBX/crossexam/actions/workflows/ci.yml/badge.svg)](https://github.com/cyberxuan-XBX/crossexam/actions)
[![PyPI](https://img.shields.io/pypi/v/crossexam)](https://pypi.org/project/crossexam/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://pypi.org/project/crossexam/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Same question. Three AIs. Three different answers. Which one do you trust?**

CrossExam is a file-based protocol + tiny CLI that lets multiple AI coding
agents — **Claude Code, Codex CLI, Gemini CLI, aider, anything that can run a
shell command** — work the same problem and **cross-examine each other's
conclusions with real commands** instead of leaving you to copy-paste between
terminal windows.

No server. No API keys. No framework. One directory of plain files you can
`git diff`.

```
 Terminal 1              Terminal 2              Terminal 3
 CX_SEAT=sonnet claude   CX_SEAT=gpt codex       CX_SEAT=gemini gemini
      │                        │                        │
      └────────┬───────────────┴────────────┬───────────┘
               ▼                            ▼
        _Msg/bus.jsonl  ◄── append-only conclusion bus
        _Msg/analysis/  ◄── long-form evidence per seat
        _Msg/task.md    ◄── phase: blind → debate → closed
```

## Why

Run the same analysis in three AI CLI sessions and you will get three
different answers — different models diverge, and even the *same* model
diverges across runs. The research world knows this (it's why
self-consistency, multi-agent debate, and LLM juries exist), but CLI users
are left playing human message bus: copy from one window, paste into another,
ask "is he right?".

CrossExam turns that manual ritual into a protocol. It was born from a real
incident: three sessions audited the same vehicle-gate access log and reported
**56, 61, and 63** vehicles on site. Copy-pasting their claims at each other
produced something remarkable — one session *reproduced* another's
ghost-exit finding with its own queries, conceded its own number was a
dashboard aggregation artifact, and the third surfaced 11 rows both had
missed. The final answer was better than any single seat's. This tool is that
workflow, mechanized.

## Install

```bash
pip install crossexam
# or: no install at all — copy crossexam.py anywhere and alias cxam='python3 crossexam.py'
```

## Quickstart

```bash
cd your-project
cxam init --task "Audit auth.py for the token expiry bug"

# open one terminal per model — pin whatever exact versions you like
CX_SEAT=sonnet claude
CX_SEAT=gpt    codex
CX_SEAT=gemini gemini
```

Wire each CLI with its adapter (one hook or one memory-file snippet — see
[adapters/](adapters/)), then just tell each session "go". Every turn, each
seat reads its unread messages, works, and posts conclusions back:

```bash
cxam read                                                    # what did the others find?
cxam post claim "63 on site; 7 ghost exits" --ref analysis/gpt.md#ghosts
cxam post verify "sonnet's pairing check reproduces, 7/7"    --ref analysis/gpt.md#recheck
cxam post concede "my count was an aggregate artifact; adopting gpt's frame"
```

You stop being the message bus. Your only job: say "continue" in whichever
window you like, flip the phase when claims are in, and read the final
disagreement table.

Want to see the whole lifecycle without any AI attached? Run the 5-second
simulation:

```bash
bash examples/simulated-debate.sh
```

## The protocol

Three phases, enforced by the CLI, flipped by you (`cxam phase debate`):

| Phase | What happens | What's enforced |
|---|---|---|
| **blind** | Each seat writes an independent analysis and posts one `claim` | `cxam read` withholds other seats' messages (anti-anchoring); `verify`/`challenge`/`concede` are rejected |
| **debate** | Seats read each other, pick *concrete, checkable* statements, and verify them **by running commands** | `verify`/`challenge` without an evidence `--ref` get warned; losers post explicit `concede` |
| **closed** | A designated seat writes `synthesis.md`: consensus + **disagreement table** | Bus accepts `info` only |

Five message types: `claim` / `verify` / `challenge` / `concede` / `info`.
One JSON line each. Conclusions on the bus, essays in `analysis/`.

Where the seats agree after cross-examination, confidence is earned. Where
they still disagree, the table shows you **exactly where your judgment is
needed**. Divergence is signal, not noise.

## Design principles

- **Files, not frameworks.** The bus is a JSONL file in your repo. Auditable,
  greppable, git-diffable, survives crashes, works over SSH/NFS/Syncthing.
- **The CLI is convenience, not a dependency.** Any agent that can `tail` and
  `echo >>` can participate ([adapters/generic.md](adapters/generic.md)).
- **Cross-vendor by construction.** Sessions are peers; nobody is the
  orchestrator's subagent. Pin Sonnet 4.6 against Sonnet 5 against GPT — 
  interactive sessions can pin exact model versions that subagent APIs don't
  expose.
- **Full-context peers, not stateless workers.** Each seat is a real session
  with its own memory files, tools, and permissions — not a fresh-context
  subagent that lost the plot.
- **Adversarial by default.** "No praising, no doubting without evidence" is
  the protocol's core norm. Claims survive by being reproduced, not by
  sounding confident.

## What CrossExam is not

- Not a process manager — it doesn't spawn or babysit your CLIs
  (tmux/claude-squad-style tools do that; they compose fine with this).
- Not an API orchestrator — nothing here calls a model API. Councils that
  query N APIs in parallel answer one prompt; CrossExam coordinates *agentic
  sessions* that investigate with tools over hours.
- Not a hard security boundary — the blind phase is enforced by the sanctioned
  interface (`cxam read`) and adapter instructions, but a misbehaving agent
  could still `cat` the bus. It's a discipline, mechanically assisted.

## FAQ

**Do the sessions talk in real time?**
CLI agents are turn-based; messages are picked up at each turn boundary. In
practice you type "continue" in a window and that seat catches up. Hook-based
adapters (Claude Code) surface the unread count automatically on every prompt.

**Why not just use subagents?**
Subagents are one brain fanning out — same vendor, usually no memory, no
version pinning, and the orchestrator grades its own homework. CrossExam seats
are independent full sessions from *different* vendors, cross-grading each
other.

**Does this work with two seats? Five?**
Any number. Two seats gives you a reviewer; three-plus gives you a jury and
majority signals.

**Windows?**
Yes — pure-stdlib Python; the file locking degrades gracefully.

## Related work

We surveyed 40+ neighbors on 2026-07-04 — full table with verified stars in
[docs/related-work.md](docs/related-work.md). The landscape in one paragraph:

- **Transports** ([agmsg](https://github.com/fujibee/agmsg),
  [hcom](https://github.com/aannoo/hcom)) move messages between CLI agents but
  ship no verification protocol — no phases, no blind stage, no synthesis.
- **API councils** ([llm-council](https://github.com/karpathy/llm-council),
  [PAL/zen-mcp](https://github.com/BeehiveInnovations/pal-mcp-server),
  [MoA](https://github.com/togethercomputer/MoA),
  [ensemble](https://github.com/raiyanyahya/ensemble)) make models debate each
  other's *text* — reviewers never run a command against your repo, so
  cross-examination stays rhetorical.
- **Process managers** ([claude-squad](https://github.com/smtg-ai/claude-squad),
  [Crystal](https://github.com/stravu/crystal)) run many sessions side by
  side; the sessions never talk. (They compose nicely with CrossExam.)
- **Orchestrator-graders**
  ([adversarial-review](https://github.com/alecnielsen/adversarial-review),
  [codex-adversary](https://github.com/todd866/codex-adversary)) have one lead
  model shell out to others and grade the answers — the examiner grades its
  own homework.

As far as we could verify, the intersection CrossExam occupies — **live
cross-vendor CLI sessions as peer seats × command-verified cross-examination ×
a git-diffable bus in your project root** — is empty. If we missed someone,
open an issue; we'll cite them.

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

MIT © 2026 XBX (Taiyang Software)
