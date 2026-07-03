# Adapter: Claude Code

Two pieces: a hook (mechanical reminder every turn) and a memory-file snippet
(protocol awareness). The hook is the part that removes the human bus — every
prompt you type, the session first sees its unread count.

## 1. Hook (recommended)

Add to `.claude/settings.json` (project) or `~/.claude/settings.json` (global —
safe: `cx hook` prints nothing in projects without `_Msg/`):

```json
{
  "hooks": {
    "UserPromptSubmit": [
      { "hooks": [ { "type": "command", "command": "cx hook", "timeout": 3 } ] }
    ]
  }
}
```

## 2. CLAUDE.md snippet

```markdown
## CrossExam
This project may contain a `_Msg/` directory: a message bus shared with other
AI CLI sessions working the same task. When the hook reports unread messages:
run `cx read` before working, do the work, then post your conclusion with
`cx post <type> "<one-liner>" --ref analysis/<seat>.md#anchor`.
Obey the phase: during `blind`, never read other seats' analyses or claims.
Verify others' claims by RUNNING COMMANDS, not by rhetoric.
```

## 3. Launch a seat

```bash
CX_SEAT=sonnet claude     # then /model to pin the exact model you want
CX_SEAT=opus   claude
```

Version-pinning across sessions is exactly what CrossExam is for: subagent
APIs usually only expose alias tiers, but an interactive session can pin any
model — Sonnet 4.6 vs Sonnet 5 vs Opus, each holding a seat.
