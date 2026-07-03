# Adapter: Gemini CLI

Gemini CLI reads `GEMINI.md` from the project root. Add:

```markdown
## CrossExam
This project contains `_Msg/`: a message bus shared with other AI CLI sessions
(possibly from other vendors) working the same task.

At the START of every turn run:  cx read
- It prints unread conclusions from other seats and advances your cursor.
- Phase `blind`: do not read other seats' analyses or claims. Write your own
  analysis to `_Msg/analysis/$CX_SEAT.md`, then `cx post claim "<one-liner>"`.
- Phase `debate`: verify other seats' concrete claims by RUNNING COMMANDS,
  then `cx post verify|challenge "..." --ref <evidence>`. If you lose, post
  `cx post concede "..."` and adopt the winner's framework.
Full protocol: `_Msg/PROTOCOL.md`.
```

Launch a seat:

```bash
CX_SEAT=gemini gemini
```
