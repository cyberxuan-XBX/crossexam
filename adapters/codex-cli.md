# Adapter: OpenAI Codex CLI

Codex reads `AGENTS.md` from the project root. Add:

```markdown
## CrossExam
This project contains `_Msg/`: a message bus shared with other AI CLI sessions
(possibly from other vendors) working the same task.

At the START of every turn run:  cxam read
- It prints unread conclusions from other seats and advances your cursor.
- If the phase is `blind`: do not read other seats' analyses or claims; write
  your own analysis to `_Msg/analysis/$CX_SEAT.md`, then `cxam post claim "..."`.
- If the phase is `debate`: pick other seats' concrete, checkable statements
  and verify them by running real commands. Then post:
    cxam post verify    "their claim X holds: <evidence>"    --ref <file#anchor>
    cxam post challenge "their claim Y fails: <evidence>"    --ref <file#anchor>
    cxam post concede   "my claim Z loses to <seat>; adopting their framework"
Full protocol: `_Msg/PROTOCOL.md`.
```

Launch a seat:

```bash
CX_SEAT=gpt codex
```

Headless seat for `cxam run` — two gotchas learned the hard way:

```bash
--agent 'gpt=codex exec --skip-git-repo-check {prompt}'
```

1. `--skip-git-repo-check` is REQUIRED when the arena is not a git repo,
   otherwise codex refuses to start ("Not inside a trusted directory").
2. Codex is thorough but slow: give it a generous `--seat-timeout` (≥900s)
   or keep its share of the task narrow.

No hook mechanism needed — Codex re-reads AGENTS.md each session; the
`cxam read` habit is carried by the instruction above. For extra safety you can
also add the same block to `~/.codex/AGENTS.md` (global).
