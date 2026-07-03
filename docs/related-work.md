# Related work

Survey date: **2026-07-04**. Stars verified live via GitHub API on that date;
they will drift. PRs correcting or extending this table are welcome — we would
rather be accurate than flattering.

CrossExam's claim: no existing project combines **(a)** live cross-vendor CLI
sessions as peer seats, **(b)** a zero-dependency append-only JSONL bus living
git-diffably in the project root, and **(c)** a mandatory blind-write →
command-verified cross-examination → explicit-disagreement-table protocol.
Below is the evidence for that claim, grouped by what each neighbor actually is.

## Transports (move messages, no verification protocol)

| Project | Stars | Notes |
|---|---|---|
| [fujibee/agmsg](https://github.com/fujibee/agmsg) | 935 | Best-in-class cross-vendor CLI-to-CLI messaging (9+ agent CLIs, bash + SQLite, no daemon). Explicitly leaves protocol semantics to prompts: no phases, no blind stage, no synthesis artifact. SQLite = not git-diffable. |
| [aannoo/hcom](https://github.com/aannoo/hcom) | 365 | Hook-based messaging + transcript observation between CLI agents; bundles a debate script but no blind/phase/synthesis protocol. |
| [avivsinai/agent-message-queue](https://github.com/avivsinai/agent-message-queue) | 65 | Maildir-style file queue for local agents. Transport only. |
| [non4me/cc2cc](https://github.com/non4me/cc2cc) | 11 | JSON-file mailbox between Claude Code sessions. Claude-only, transport only. |
| Claude Code native "agent teams" | — | Emerging file mailbox under `~/.claude/teams/`; Anthropic-only, leader/worker, no verification protocol. Issues [#4993](https://github.com/anthropics/claude-code/issues/4993) / [#24798](https://github.com/anthropics/claude-code/issues/24798) show the demand. |

## API councils (models debate text; reviewers can't run commands)

| Project | Stars | Notes |
|---|---|---|
| [karpathy/llm-council](https://github.com/karpathy/llm-council) | 22,076 | The pattern-maker: N models via OpenRouter → anonymized peer ranking → chairman synthesis. Web app, Q&A only, no code, no execution, explicitly unmaintained. |
| [BeehiveInnovations/pal-mcp-server](https://github.com/BeehiveInnovations/pal-mcp-server) (zen-mcp) | 11,637 | MCP `consensus` tool: multi-vendor opinions with stance steering inside a coding-agent session. Consultants only *read* context the lead passes them — they never execute verification. Lead-mediated, needs API keys. |
| [togethercomputer/MoA](https://github.com/togethercomputer/MoA) | 2,900 | Layered proposer/aggregator ensembles. Text fusion. |
| [massgen/MassGen](https://github.com/massgen/MassGen) | 1,074 | N agents attempt the task, observe each other, vote. Deliberately *not* blind; no command-verified cross-exam. |
| [irthomasthomas/llm-consortium](https://github.com/irthomasthomas/llm-consortium) | 402 | `llm` CLI plugin, arbiter-synthesized consensus loops. |
| [haizelabs/verdict](https://github.com/haizelabs/verdict) | 345 | Declarative judge-ensemble framework. Judging text, not executing. |
| [raiyanyahya/ensemble](https://github.com/raiyanyahya/ensemble) | 9 | Closest protocol cousin: filesystem-mediated PROPOSE→REVIEW→REBUT→VOTE→SYNTHESIZE with anonymized participants. But: drives vendor APIs (needs keys), reviewers cannot execute commands, artifacts live in `~/.ensemble/` not the project root, no disagreement table. |
| Research code: [MIT multiagent debate](https://github.com/composable-models/llm_multiagent_debate) (542), [MAD](https://github.com/Skytliang/Multi-Agents-Debate) (593), [ChatEval](https://github.com/chanchimin/ChatEval) (339), [LLM-Blender](https://github.com/yuchenlin/LLM-Blender) (986) | | The academic lineage (Du et al. ICML 2024; Liang et al.; Chan et al.). All text-vs-text. |

## Process managers & UIs (run many sessions; the sessions never talk)

| Project | Stars | Notes |
|---|---|---|
| [ruvnet/ruflo](https://github.com/ruvnet/ruflo) (claude-flow) | 62,842 | Sprawling agent meta-harness: swarm topologies, consensus voting, 100+ roles. Orchestration-first; no blind cross-examination protocol. |
| [BloopAI/vibe-kanban](https://github.com/BloopAI/vibe-kanban) | 27,253 | Kanban for dispatching agent tasks (sunsetting). |
| [smtg-ai/claude-squad](https://github.com/smtg-ai/claude-squad) | 8,013 | tmux + worktrees TUI for parallel Claude/Codex/Gemini/aider sessions. Composes nicely *with* CrossExam: squad runs the seats, CrossExam makes them talk. |
| [dagger/container-use](https://github.com/dagger/container-use) | 3,901 | Isolated environments for parallel agents. |
| [stravu/crystal](https://github.com/stravu/crystal) | 3,095 | Desktop app for parallel sessions in worktrees. |
| [openclaw/acpx](https://github.com/openclaw/acpx) | 2,930 | Typed agent-drives-agent protocol client (ACP); `compare` runs one prompt on N agents, no cross-exam. |
| [asheshgoplani/agent-deck](https://github.com/asheshgoplani/agent-deck) | 427 | TUI session manager. |

## Orchestrator-graders (one lead shells out to others and grades the answers)

| Project | Stars | Notes |
|---|---|---|
| [alecnielsen/adversarial-review](https://github.com/alecnielsen/adversarial-review) | 18 | Closest workflow cousin: independent review → cross-review → meta-review → synthesis over real code. Two vendors only, orchestrator-driven (not live peer sessions), no bus, no disagreement table, reviewers don't execute commands. |
| [todd866/codex-adversary](https://github.com/todd866/codex-adversary) | 38 | Codex as adversarial reviewer inside Claude Code. Lead/follower. |
| [Bambushu/crucible](https://github.com/Bambushu/crucible) | 47 | DeepSeek+Gemini review panel as a Claude Code skill. |
| [wan-huiyan/agent-review-panel](https://github.com/wan-huiyan/agent-review-panel) | 25 | 4–6 personas debate + judge — same model underneath; docs honestly call it "structured self-critique, not independent verification". |

## Reading the map

Two axes matter: **who verifies** (nobody / the lead model / independent
peers) and **how** (rhetoric / ranking / executed commands). Everything above
sits at "nobody-or-lead" × "rhetoric-or-ranking". CrossExam sits at
"independent peers" × "executed commands" — which is also just... how human
engineering review works when it works.

If we missed a project that genuinely occupies this cell, open an issue; we
will happily cite it.
