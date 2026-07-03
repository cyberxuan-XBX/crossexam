#!/usr/bin/env python3
"""CrossExam — same question, N AIs, N answers. Let them cross-examine each other.

A zero-dependency, file-based protocol + CLI that lets multiple AI coding
agents (Claude Code, Codex CLI, Gemini CLI, aider, ...) collaborate on the
same project: blind-write independent analyses, cross-examine each other's
claims with real commands, and converge to a synthesis with an explicit
disagreement table.

Everything lives in a `_Msg/` directory in your project root. No server,
no API keys, no vendor lock-in. If your agent can run shell commands, it
can sit at the table.
"""

__version__ = "0.1.0"

import argparse
import datetime
import json
import os
import re
import sys
import time
from pathlib import Path

MSG_DIR = "_Msg"
TYPES = ("claim", "verify", "challenge", "concede", "info")
PHASES = ("blind", "debate", "closed")
SEAT_ENV_VARS = ("CX_SEAT", "MQ_SEAT", "QUAN_SEAT")  # first hit wins

PROTOCOL_TEXT = """\
# CrossExam Protocol v1

This project uses CrossExam (https://github.com/cyberxuan-XBX/crossexam):
multiple AI CLI sessions collaborate through this `_Msg/` directory instead
of a human copy-pasting between windows.

## Structure

    _Msg/
    ├── PROTOCOL.md        this file
    ├── task.md            task description + `status:` phase line (moderator edits)
    ├── bus.jsonl          conclusion bus, append-only JSON lines
    ├── .seen/<seat>       per-seat read cursor (integer = lines already read)
    ├── analysis/<seat>.md long-form analysis, raw data, code
    └── synthesis.md       final synthesis + disagreement table (closed phase)

## Seats

Every session gets a seat name via environment variable:
`CX_SEAT=sonnet claude` / `CX_SEAT=gpt codex` / `CX_SEAT=gemini gemini`.
All messages are signed with the seat name.

## Message types

- claim      my conclusion (one line + key numbers)
- verify     I checked someone's claim with real commands: it holds (attach evidence ref)
- challenge  I checked someone's claim: it does not hold (attach evidence ref)
- concede    my claim lost; I adopt the winner's framework (say which)
- info       status note / moderator note

The bus carries CONCLUSIONS ONLY. Long reasoning, raw data, and code go to
`analysis/<seat>.md`; point at them with `ref`.

## Phases (the `status:` line in task.md; moderator flips it)

1. blind   Write your own analysis to `analysis/<seat>.md`, then post ONE
           `claim` summarizing it. DO NOT read other seats' analyses or
           claims. This prevents anchoring. `cxam read` enforces the filter.
2. debate  Read others' analyses. Pick their CONCRETE, CHECKABLE statements
           and verify them by running real commands — no praising, no
           doubting without evidence. Post `verify`/`challenge` with refs.
           If your claim loses, post `concede` and absorb the winner's frame.
3. closed  A designated seat writes `synthesis.md`: consensus conclusions
           PLUS an explicit disagreement table. Disagreements are signal,
           not noise — they mark exactly where the human must decide.

## Per-turn loop (your CLI's hook or memory file should remind you)

    cxam read            # unread messages (blind-filtered when appropriate)
    ...work...
    cxam post verify "claim X holds, 7/7 rows reproduced" --ref analysis/me.md#x
    # cursor advances automatically on read

## Iron rules

- Append-only. Never rewrite or delete another seat's messages.
- One message = one line of JSON; keep msg <= 200 words.
- Evidence or it didn't happen: verify/challenge must carry a ref.
- The value of the synthesis is the disagreement table, not the consensus.
"""

TASK_TEMPLATE = """\
# Task
status: blind
moderator: human

---

{task}
"""


# ---------------------------------------------------------------- helpers

def now_iso():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def find_msg_dir(start=None):
    """Walk up from start (default cwd) looking for _Msg, like git does."""
    cur = Path(start or os.getcwd()).resolve()
    for p in [cur, *cur.parents]:
        cand = p / MSG_DIR
        if cand.is_dir():
            return cand
    return None


def get_seat():
    for var in SEAT_ENV_VARS:
        v = os.environ.get(var, "").strip()
        if v:
            return v
    return None


def read_phase(d):
    task = d / "task.md"
    if task.is_file():
        m = re.search(r"^status:\s*(\S+)", task.read_text(encoding="utf-8"), re.M)
        if m and m.group(1) in PHASES:
            return m.group(1)
    return "debate"  # no/invalid phase marker -> least surprising default


def load_msgs(d):
    """Return (messages, bad_line_count). Each message gets ._line (1-based)."""
    bus = d / "bus.jsonl"
    msgs, bad = [], 0
    if not bus.is_file():
        return msgs, bad
    for i, line in enumerate(bus.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            m = json.loads(line)
            m["_line"] = i
            msgs.append(m)
        except (json.JSONDecodeError, TypeError):
            bad += 1
    return msgs, bad


def bus_line_count(d):
    bus = d / "bus.jsonl"
    if not bus.is_file():
        return 0
    return len(bus.read_text(encoding="utf-8").splitlines())


def get_cursor(d, seat):
    f = d / ".seen" / seat
    try:
        return int(re.sub(r"[^0-9]", "", f.read_text()) or 0)
    except (OSError, ValueError):
        return 0


def set_cursor(d, seat, n):
    seen = d / ".seen"
    seen.mkdir(exist_ok=True)
    (seen / seat).write_text(str(n) + "\n", encoding="utf-8")


def append_msg(d, record):
    """Single-line append. On POSIX, one write under 4KB is atomic; we also
    take an advisory lock where available for belt-and-braces."""
    line = json.dumps(record, ensure_ascii=False)  # escapes newlines: 1 msg = 1 line
    with open(d / "bus.jsonl", "a", encoding="utf-8") as f:
        try:
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX)
        except (ImportError, OSError):
            pass  # Windows or exotic FS: fall back to atomic-enough append
        f.write(line + "\n")


def blind_visible(m, seat):
    """During blind phase a seated agent may see: its own messages, and
    info messages (moderator notes)."""
    return m.get("from") == seat or m.get("type") == "info"


def fmt(m):
    ref = " [{}]".format(m["ref"]) if m.get("ref") else ""
    return "#{:<3} {}  {:<10} {:<9}{} {}".format(
        m.get("_line", "?"), m.get("ts", "?")[:19],
        m.get("from", "?"), m.get("type", "?"), ref, m.get("msg", ""))


def die(msg, code=1):
    print("cxam: " + msg, file=sys.stderr)
    return code


def need_dir():
    d = find_msg_dir()
    if d is None:
        print("cxam: no _Msg/ found here or in any parent. Run `cxam init` in the "
              "project root first.", file=sys.stderr)
    return d


# ---------------------------------------------------------------- commands

def cmd_init(args):
    d = Path.cwd() / MSG_DIR
    existed = d.is_dir()
    (d / ".seen").mkdir(parents=True, exist_ok=True)
    (d / "analysis").mkdir(exist_ok=True)
    if not (d / "PROTOCOL.md").is_file():
        (d / "PROTOCOL.md").write_text(PROTOCOL_TEXT, encoding="utf-8")
    if not (d / "task.md").is_file():
        (d / "task.md").write_text(
            TASK_TEMPLATE.format(task=args.task or "(describe the task here)"),
            encoding="utf-8")
    (d / "bus.jsonl").touch()
    print(("updated" if existed else "initialized") + " " + str(d) + "  (phase: "
          + read_phase(d) + ")")
    print("seat a session:  CX_SEAT=<name> <your-ai-cli>")
    return 0


def cmd_post(args):
    d = need_dir()
    if d is None:
        return 2
    seat = get_seat()
    if not seat:
        return die("no seat. Set CX_SEAT (e.g. `CX_SEAT=sonnet claude`).")
    if args.type not in TYPES:
        return die("type must be one of: " + ", ".join(TYPES))
    phase = read_phase(d)
    if phase == "blind" and args.type in ("verify", "challenge", "concede"):
        return die("phase is 'blind': only claim/info may be posted. "
                   "Write your own analysis first; debate starts when the "
                   "moderator flips the phase.")
    if phase == "closed" and args.type != "info":
        return die("phase is 'closed': bus accepts info only. "
                   "Synthesis lives in _Msg/synthesis.md.")
    if len(args.message) > 1200:
        return die("message too long ({} chars). The bus carries conclusions; "
                   "put the essay in _Msg/analysis/{}.md and point at it with "
                   "--ref.".format(len(args.message), seat))
    rec = {"ts": now_iso(), "from": seat, "type": args.type, "msg": args.message}
    if args.ref:
        rec["ref"] = args.ref
    if (args.type in ("verify", "challenge")) and not args.ref:
        print("cxam: warning: {} without --ref. Evidence or it didn't happen."
              .format(args.type), file=sys.stderr)
    append_msg(d, rec)
    print("posted #{} as {} ({})".format(bus_line_count(d), seat, args.type))
    return 0


def cmd_read(args):
    d = need_dir()
    if d is None:
        return 2
    seat = get_seat()
    msgs, bad = load_msgs(d)
    phase = read_phase(d)
    if seat:
        cursor = get_cursor(d, seat)
        unread = [m for m in msgs if m["_line"] > cursor]
    else:
        cursor, unread = 0, msgs  # unseated caller = human/moderator: full view
    shown = unread
    withheld = 0
    if phase == "blind" and seat:
        shown = [m for m in unread if blind_visible(m, seat)]
        withheld = len(unread) - len(shown)
    if not shown and not withheld:
        print("(no unread messages; phase: {})".format(phase))
        return 0
    for m in shown:
        print(fmt(m))
    if withheld:
        print("({} message(s) withheld until debate phase — blind means blind)"
              .format(withheld))
    if bad:
        print("({} malformed line(s) skipped)".format(bad), file=sys.stderr)
    if seat and not args.peek:
        if phase == "blind" and withheld:
            # freeze cursor so withheld messages are re-delivered in debate
            print("(cursor frozen during blind phase)")
        else:
            set_cursor(d, seat, msgs[-1]["_line"] if msgs else 0)
    return 0


def cmd_status(args):
    d = need_dir()
    if d is None:
        return 2
    seat = get_seat()
    msgs, _ = load_msgs(d)
    phase = read_phase(d)
    per = {}
    for m in msgs:
        per.setdefault(m.get("from", "?"), []).append(m.get("type"))
    print("phase: {}   messages: {}   dir: {}".format(phase, len(msgs), d))
    for s in sorted(per):
        counts = {t: per[s].count(t) for t in TYPES if t in per[s]}
        cur = get_cursor(d, s)
        me = "  <- you" if s == seat else ""
        print("  {:<12} posted {:<3} read {:<3} {}{}".format(
            s, len(per[s]), cur, counts, me))
    if seat:
        cursor = get_cursor(d, seat)
        unread = sum(1 for m in msgs if m["_line"] > cursor)
        print("your seat: {}   unread: {}".format(seat, unread))
    else:
        print("no seat set (moderator view). Set CX_SEAT to take a seat.")
    return 0


def cmd_phase(args):
    d = need_dir()
    if d is None:
        return 2
    task = d / "task.md"
    if not args.phase:
        print(read_phase(d))
        return 0
    if args.phase not in PHASES:
        return die("phase must be one of: " + ", ".join(PHASES))
    text = task.read_text(encoding="utf-8") if task.is_file() else TASK_TEMPLATE.format(task="")
    new, n = re.subn(r"^status:\s*\S+", "status: " + args.phase, text, count=1, flags=re.M)
    if n == 0:
        new = "status: " + args.phase + "\n" + text
    task.write_text(new, encoding="utf-8")
    append_msg(d, {"ts": now_iso(), "from": get_seat() or "moderator",
                   "type": "info", "msg": "phase -> " + args.phase})
    print("phase: " + args.phase)
    return 0


def cmd_log(args):
    d = need_dir()
    if d is None:
        return 2
    seat = get_seat()
    msgs, bad = load_msgs(d)
    phase = read_phase(d)
    withheld = 0
    if phase == "blind" and seat and not args.all:
        visible = [m for m in msgs if blind_visible(m, seat)]
        withheld = len(msgs) - len(visible)
        msgs = visible
    for m in msgs:
        print(fmt(m))
    if withheld:
        print("({} message(s) withheld — blind phase; humans can pass --all)"
              .format(withheld))
    if bad:
        print("({} malformed line(s) skipped)".format(bad), file=sys.stderr)
    return 0


def cmd_hook(args):
    """One or two lines for prompt-injection hooks (silent when no _Msg)."""
    d = find_msg_dir()
    if d is None:
        return 0
    seat = get_seat() or "unseated"
    msgs, _ = load_msgs(d)
    phase = read_phase(d)
    cursor = get_cursor(d, seat)
    unread = sum(1 for m in msgs if m["_line"] > cursor)
    print("[CrossExam] seat={} phase={} unread={} (of {}). Run `cxam read` before "
          "working, post conclusions with `cxam post`. Protocol: {}/PROTOCOL.md"
          .format(seat, phase, unread, len(msgs), d))
    if phase == "blind":
        print("[CrossExam] BLIND PHASE: do not read other seats' analyses or "
              "claims. Write analysis/{}.md, post one claim.".format(seat))
    return 0


def cmd_watch(args):
    d = need_dir()
    if d is None:
        return 2
    print("watching {} (Ctrl-C to stop)".format(d / "bus.jsonl"))
    last = 0
    try:
        while True:
            msgs, _ = load_msgs(d)
            for m in msgs:
                if m["_line"] > last:
                    print(fmt(m))
                    last = m["_line"]
            time.sleep(args.interval)
    except KeyboardInterrupt:
        return 0


# ---------------------------------------------------------------- main

def main(argv=None):
    p = argparse.ArgumentParser(
        prog="cxam",
        description="CrossExam: let your AI CLIs cross-examine each other.")
    p.add_argument("--version", action="version", version="crossexam " + __version__)
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("init", help="create _Msg/ in the current directory")
    sp.add_argument("--task", help="task description for task.md")
    sp.set_defaults(fn=cmd_init)

    sp = sub.add_parser("post", help="append a message to the bus")
    sp.add_argument("type", choices=TYPES)
    sp.add_argument("message")
    sp.add_argument("--ref", help="evidence pointer, e.g. analysis/sonnet.md#ghosts")
    sp.set_defaults(fn=cmd_post)

    sp = sub.add_parser("read", help="print unread messages, advance cursor")
    sp.add_argument("--peek", action="store_true", help="do not advance cursor")
    sp.set_defaults(fn=cmd_read)

    sp = sub.add_parser("status", help="phase, seats, unread counts")
    sp.set_defaults(fn=cmd_status)

    sp = sub.add_parser("phase", help="show or set phase (blind|debate|closed)")
    sp.add_argument("phase", nargs="?", choices=PHASES)
    sp.set_defaults(fn=cmd_phase)

    sp = sub.add_parser("log", help="print the whole bus")
    sp.add_argument("--all", action="store_true", help="ignore blind filter (humans)")
    sp.set_defaults(fn=cmd_log)

    sp = sub.add_parser("hook", help="one-line status for prompt-injection hooks")
    sp.set_defaults(fn=cmd_hook)

    sp = sub.add_parser("watch", help="live tail of the bus (for humans)")
    sp.add_argument("--interval", type=float, default=2.0)
    sp.set_defaults(fn=cmd_watch)

    args = p.parse_args(argv)
    if not getattr(args, "fn", None):
        p.print_help()
        return 0
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
