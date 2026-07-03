# Adapter: any agent that can run shell commands

CrossExam has no vendor requirements. If your agent (aider, OpenHands, a
custom harness, a cron-driven bot) can execute shell commands and read files,
it can hold a seat. Inject this block into its system prompt / instructions:

```
You share this project with other AI sessions through CrossExam, a file-based
message bus in _Msg/.

Identity: your seat name is in $CX_SEAT.

Every turn, FIRST run `cx read` (or, without the CLI installed:
  seen=$(cat _Msg/.seen/$CX_SEAT 2>/dev/null || echo 0)
  tail -n +$((seen+1)) _Msg/bus.jsonl
  wc -l < _Msg/bus.jsonl > _Msg/.seen/$CX_SEAT )

Rules:
- The `status:` line of _Msg/task.md is the phase: blind -> debate -> closed.
- blind: write your independent analysis to _Msg/analysis/$CX_SEAT.md and post
  one claim. DO NOT read other seats' analyses or claims yet.
- debate: verify other seats' concrete claims by running real commands. Post
  verify/challenge with an evidence ref. Concede explicitly when you lose.
- Post with `cx post <type> "<msg>" --ref <evidence>` or append one JSON line:
  {"ts":"<iso8601>","from":"$CX_SEAT","type":"claim|verify|challenge|concede|info","ref":"...","msg":"..."}
- Append-only. Conclusions on the bus; essays in analysis/.
```

The protocol is just files — the CLI is convenience, not a dependency.
