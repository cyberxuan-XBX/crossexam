"""CrossExam test suite. Run: pytest -q"""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import crossexam as cx


@pytest.fixture()
def arena(tmp_path, monkeypatch, capsys):
    """Fresh initialized _Msg in a tmp project dir."""
    monkeypatch.chdir(tmp_path)
    for var in cx.SEAT_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    assert cx.main(["init", "--task", "count the sheep"]) == 0
    capsys.readouterr()
    return tmp_path


def seat(monkeypatch, name):
    monkeypatch.setenv("CX_SEAT", name)


def bus_lines(root):
    return (root / "_Msg" / "bus.jsonl").read_text().splitlines()


# ---------------------------------------------------------------- init

def test_init_creates_structure(arena):
    d = arena / "_Msg"
    assert (d / "task.md").is_file()
    assert (d / "PROTOCOL.md").is_file()
    assert (d / "bus.jsonl").is_file()
    assert (d / ".seen").is_dir()
    assert (d / "analysis").is_dir()
    assert "count the sheep" in (d / "task.md").read_text()
    assert cx.read_phase(d) == "blind"


def test_init_idempotent(arena, capsys):
    (arena / "_Msg" / "task.md").write_text("# Task\nstatus: debate\n\ncustom")
    assert cx.main(["init"]) == 0
    assert "custom" in (arena / "_Msg" / "task.md").read_text()  # not clobbered


def test_find_msg_dir_walks_up(arena, monkeypatch):
    sub = arena / "deep" / "nested"
    sub.mkdir(parents=True)
    monkeypatch.chdir(sub)
    assert cx.find_msg_dir() == arena / "_Msg"


def test_no_dir_errors(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CX_SEAT", "a")
    assert cx.main(["post", "info", "hello"]) == 2


# ---------------------------------------------------------------- post

def test_post_requires_seat(arena, capsys):
    assert cx.main(["post", "claim", "x"]) == 1
    assert "no seat" in capsys.readouterr().err


def test_post_and_bus_format(arena, monkeypatch, capsys):
    seat(monkeypatch, "sonnet")
    assert cx.main(["post", "claim", "63 sheep, not 56", "--ref",
                    "analysis/sonnet.md#count"]) == 0
    rec = json.loads(bus_lines(arena)[-1])
    assert rec["from"] == "sonnet"
    assert rec["type"] == "claim"
    assert rec["ref"] == "analysis/sonnet.md#count"
    assert "ts" in rec


def test_blind_blocks_verify(arena, monkeypatch, capsys):
    seat(monkeypatch, "sonnet")
    assert cx.main(["post", "verify", "checked"]) == 1
    assert "blind" in capsys.readouterr().err


def test_closed_blocks_claims(arena, monkeypatch, capsys):
    seat(monkeypatch, "mod")
    assert cx.main(["phase", "closed"]) == 0
    assert cx.main(["post", "claim", "late claim"]) == 1


def test_overlong_message_rejected(arena, monkeypatch, capsys):
    seat(monkeypatch, "sonnet")
    assert cx.main(["post", "claim", "x" * 1300]) == 1
    assert "too long" in capsys.readouterr().err


# ---------------------------------------------------------------- read / cursor

def test_read_cursor_advances(arena, monkeypatch, capsys):
    seat(monkeypatch, "a")
    cx.main(["post", "claim", "one"])
    capsys.readouterr()
    seat(monkeypatch, "b")
    cx.main(["phase", "debate"])  # unlock full read
    capsys.readouterr()
    assert cx.main(["read"]) == 0
    out = capsys.readouterr().out
    assert "one" in out
    assert cx.main(["read"]) == 0
    assert "no unread" in capsys.readouterr().out


def test_peek_does_not_advance(arena, monkeypatch, capsys):
    seat(monkeypatch, "a")
    cx.main(["phase", "debate"])
    cx.main(["post", "claim", "one"])
    capsys.readouterr()
    seat(monkeypatch, "b")
    cx.main(["read", "--peek"])
    capsys.readouterr()
    cx.main(["read"])
    assert "one" in capsys.readouterr().out


def test_blind_read_withholds_others(arena, monkeypatch, capsys):
    seat(monkeypatch, "a")
    cx.main(["post", "claim", "secret of a"])
    capsys.readouterr()
    seat(monkeypatch, "b")
    assert cx.main(["read"]) == 0
    out = capsys.readouterr().out
    assert "secret of a" not in out
    assert "withheld" in out


def test_blind_cursor_frozen_then_redelivered(arena, monkeypatch, capsys):
    seat(monkeypatch, "a")
    cx.main(["post", "claim", "hidden gem"])
    capsys.readouterr()
    seat(monkeypatch, "b")
    cx.main(["read"])  # withheld, cursor frozen
    capsys.readouterr()
    seat(monkeypatch, "mod")
    cx.main(["phase", "debate"])
    capsys.readouterr()
    seat(monkeypatch, "b")
    cx.main(["read"])
    assert "hidden gem" in capsys.readouterr().out


def test_unseated_read_is_moderator_view(arena, monkeypatch, capsys):
    seat(monkeypatch, "a")
    cx.main(["post", "claim", "visible to humans"])
    capsys.readouterr()
    for var in cx.SEAT_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    cx.main(["read"])
    assert "visible to humans" in capsys.readouterr().out


# ---------------------------------------------------------------- phase / status / log / hook

def test_phase_show_and_set(arena, monkeypatch, capsys):
    assert cx.main(["phase"]) == 0
    assert capsys.readouterr().out.strip() == "blind"
    seat(monkeypatch, "mod")
    assert cx.main(["phase", "debate"]) == 0
    capsys.readouterr()
    assert cx.read_phase(arena / "_Msg") == "debate"
    # phase change is announced on the bus
    assert any(json.loads(l)["msg"] == "phase -> debate" for l in bus_lines(arena))


def test_status_counts(arena, monkeypatch, capsys):
    seat(monkeypatch, "a")
    cx.main(["post", "claim", "one"])
    cx.main(["post", "info", "two"])
    capsys.readouterr()
    assert cx.main(["status"]) == 0
    out = capsys.readouterr().out
    assert "phase: blind" in out
    assert "a" in out and "posted 2" in out


def test_log_blind_filter_and_all_flag(arena, monkeypatch, capsys):
    seat(monkeypatch, "a")
    cx.main(["post", "claim", "alpha finding"])
    capsys.readouterr()
    seat(monkeypatch, "b")
    cx.main(["log"])
    assert "alpha finding" not in capsys.readouterr().out
    cx.main(["log", "--all"])
    assert "alpha finding" in capsys.readouterr().out


def test_hook_silent_without_dir(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert cx.main(["hook"]) == 0
    assert capsys.readouterr().out == ""


def test_hook_reports_unread_and_blind(arena, monkeypatch, capsys):
    seat(monkeypatch, "a")
    cx.main(["post", "claim", "x"])
    capsys.readouterr()
    seat(monkeypatch, "b")
    assert cx.main(["hook"]) == 0
    out = capsys.readouterr().out
    assert "unread=1" in out
    assert "BLIND" in out


# ---------------------------------------------------------------- robustness

def test_malformed_bus_lines_skipped(arena, monkeypatch, capsys):
    with open(arena / "_Msg" / "bus.jsonl", "a") as f:
        f.write("this is not json\n")
    seat(monkeypatch, "a")
    cx.main(["post", "info", "after garbage"])
    capsys.readouterr()
    assert cx.main(["log"]) == 0
    out = capsys.readouterr()
    assert "after garbage" in out.out
    assert "malformed" in out.err


# ---------------------------------------------------------------- advisory seats

REPLY = '{"analysis": "long reasoning here", "type": "claim", "msg": "42 sheep"}'


def test_brief_blind_excludes_others_includes_exhibits(arena, monkeypatch, capsys):
    (arena / "_Msg" / "exhibits" / "log.txt").write_text("EXHIBIT-CONTENT")
    (arena / "_Msg" / "analysis" / "rival.md").write_text("RIVAL-SECRET")
    seat(monkeypatch, "qwen")
    assert cx.main(["brief"]) == 0
    out = capsys.readouterr().out
    assert "count the sheep" in out
    assert "EXHIBIT-CONTENT" in out
    assert "RIVAL-SECRET" not in out
    assert "BLIND PHASE" in out


def test_brief_debate_includes_others(arena, monkeypatch, capsys):
    (arena / "_Msg" / "analysis" / "rival.md").write_text("RIVAL-ARGUMENT")
    seat(monkeypatch, "mod")
    cx.main(["phase", "debate"])
    capsys.readouterr()
    seat(monkeypatch, "qwen")
    cx.main(["brief"])
    out = capsys.readouterr().out
    assert "RIVAL-ARGUMENT" in out
    assert "DEBATE PHASE" in out


def test_parse_reply_variants():
    assert cx.parse_reply(REPLY)["msg"] == "42 sheep"
    assert cx.parse_reply("```json\n" + REPLY + "\n```")["msg"] == "42 sheep"
    assert cx.parse_reply("Sure! Here you go:\n" + REPLY + "\nHope that helps.")["msg"] == "42 sheep"
    assert cx.parse_reply("no json at all") is None


def test_ingest_posts_and_writes_analysis(arena, monkeypatch, capsys):
    seat(monkeypatch, "qwen")
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(REPLY))
    assert cx.main(["ingest"]) == 0
    rec = json.loads(bus_lines(arena)[-1])
    assert rec["from"] == "qwen"
    assert rec["via"] == "clipboard"
    assert rec["type"] == "claim"
    assert "long reasoning here" in (arena / "_Msg" / "analysis" / "qwen.md").read_text()


def test_ingest_blind_coerces_type_to_claim(arena, monkeypatch, capsys):
    seat(monkeypatch, "qwen")
    bad = '{"analysis": "x", "type": "challenge", "msg": "sneaky"}'
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(bad))
    assert cx.main(["ingest"]) == 0
    assert json.loads(bus_lines(arena)[-1])["type"] == "claim"


def test_seat_calls_endpoint_and_posts(arena, monkeypatch, capsys):
    seen_prompt = {}

    def fake_chat(endpoint, model, key, prompt, timeout=180):
        seen_prompt["p"] = prompt
        return REPLY

    monkeypatch.setattr(cx, "http_chat", fake_chat)
    seat(monkeypatch, "qwen")
    assert cx.main(["seat", "--endpoint", "http://x/v1", "--model", "m"]) == 0
    rec = json.loads(bus_lines(arena)[-1])
    assert rec["via"] == "api"
    assert rec["msg"] == "42 sheep"
    assert "count the sheep" in seen_prompt["p"]


def test_seat_requires_endpoint(arena, monkeypatch, capsys):
    seat(monkeypatch, "qwen")
    monkeypatch.delenv("CX_ENDPOINT", raising=False)
    monkeypatch.delenv("CX_MODEL", raising=False)
    assert cx.main(["seat"]) == 1


def test_seat_unparseable_reply_saves_raw(arena, monkeypatch, capsys):
    monkeypatch.setattr(cx, "http_chat", lambda *a, **k: "utter prose, no json")
    seat(monkeypatch, "qwen")
    assert cx.main(["seat", "--endpoint", "http://x/v1", "--model", "m"]) == 1
    assert (arena / "_Msg" / "analysis" / "qwen.raw.txt").read_text() == "utter prose, no json"


def test_newlines_in_message_stay_one_bus_line(arena, monkeypatch, capsys):
    seat(monkeypatch, "a")
    before = len(bus_lines(arena))
    assert cx.main(["post", "info", "line one\nline two"]) == 0
    lines = bus_lines(arena)
    assert len(lines) == before + 1
    assert json.loads(lines[-1])["msg"] == "line one\nline two"
