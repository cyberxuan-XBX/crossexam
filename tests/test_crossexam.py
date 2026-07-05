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
    return (root / "_Msg" / "bus.jsonl").read_text(encoding="utf-8").splitlines()


# ---------------------------------------------------------------- init

def test_init_creates_structure(arena):
    d = arena / "_Msg"
    assert (d / "task.md").is_file()
    assert (d / "PROTOCOL.md").is_file()
    assert (d / "bus.jsonl").is_file()
    assert (d / ".seen").is_dir()
    assert (d / "analysis").is_dir()
    assert "count the sheep" in (d / "task.md").read_text(encoding="utf-8")
    assert cx.read_phase(d) == "blind"


def test_init_idempotent(arena, capsys):
    (arena / "_Msg" / "task.md").write_text("# Task\nstatus: debate\n\ncustom")
    assert cx.main(["init"]) == 0
    assert "custom" in (arena / "_Msg" / "task.md").read_text(encoding="utf-8")  # not clobbered


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


def test_post_as_flag_for_humans(arena, monkeypatch, capsys):
    for var in cx.SEAT_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    assert cx.main(["post", "info", "改用事件級分析", "--as", "wind"]) == 0
    rec = json.loads(bus_lines(arena)[-1])
    assert rec["from"] == "wind"
    assert rec["type"] == "info"


def test_post_and_bus_format(arena, monkeypatch, capsys):
    seat(monkeypatch, "sonnet")
    cx.main(["phase", "debate"])
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
    # a rogue writer bypasses sealing and appends straight to the bus
    cx.append_msg(arena / "_Msg", {"ts": "t", "from": "a", "type": "claim",
                                   "msg": "secret of a"})
    seat(monkeypatch, "b")
    assert cx.main(["read"]) == 0
    out = capsys.readouterr().out
    assert "secret of a" not in out
    assert "withheld" in out


def test_blind_cursor_frozen_then_redelivered(arena, monkeypatch, capsys):
    cx.append_msg(arena / "_Msg", {"ts": "t", "from": "a", "type": "claim",
                                   "msg": "hidden gem"})
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
    cx.main(["phase", "debate"])
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
    assert "posted 1" in out                     # only the info reached the bus
    assert "sealed envelopes: 1" in out          # the claim waits in its envelope


def test_log_blind_filter_and_all_flag(arena, monkeypatch, capsys):
    cx.append_msg(arena / "_Msg", {"ts": "t", "from": "a", "type": "claim",
                                   "msg": "alpha finding"})
    seat(monkeypatch, "b")
    cx.main(["log"])
    assert "alpha finding" not in capsys.readouterr().out
    # --all does NOT lift the blind veil for a seated participant (peek bypass)
    cx.main(["log", "--all"])
    assert "alpha finding" not in capsys.readouterr().out
    # only an unseated moderator sees all
    for var in cx.SEAT_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    cx.main(["log", "--all"])
    assert "alpha finding" in capsys.readouterr().out


def test_hook_silent_without_dir(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert cx.main(["hook"]) == 0
    assert capsys.readouterr().out == ""


def test_hook_reports_unread_and_blind(arena, monkeypatch, capsys):
    cx.append_msg(arena / "_Msg", {"ts": "t", "from": "a", "type": "claim",
                                   "msg": "x"})
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
    seat(monkeypatch, "mod")
    cx.main(["phase", "debate"])
    seat(monkeypatch, "qwen")
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(REPLY))
    assert cx.main(["ingest"]) == 0
    rec = json.loads(bus_lines(arena)[-1])
    assert rec["from"] == "qwen"
    assert rec["via"] == "clipboard"
    assert rec["type"] == "claim"
    assert "long reasoning here" in (arena / "_Msg" / "analysis" / "qwen.md").read_text(encoding="utf-8")


def test_ingest_blind_coerces_and_seals(arena, monkeypatch, capsys):
    seat(monkeypatch, "qwen")
    bad = '{"analysis": "x", "type": "challenge", "msg": "sneaky"}'
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(bad))
    assert cx.main(["ingest"]) == 0
    sealed = (arena / "_Msg" / ".sealed" / "qwen.jsonl").read_text(encoding="utf-8")
    assert json.loads(sealed)["type"] == "claim"     # coerced AND sealed
    assert len(bus_lines(arena)) == 0                # nothing leaked to the bus


def test_seat_calls_endpoint_and_posts(arena, monkeypatch, capsys):
    seen_prompt = {}

    def fake_chat(endpoint, model, key, prompt, timeout=180):
        seen_prompt["p"] = prompt
        return REPLY

    monkeypatch.setattr(cx, "http_chat", fake_chat)
    seat(monkeypatch, "qwen")
    assert cx.main(["seat", "--endpoint", "http://x/v1", "--model", "m"]) == 0
    sealed = (arena / "_Msg" / ".sealed" / "qwen.jsonl").read_text(encoding="utf-8")
    rec = json.loads(sealed)                          # blind claim -> sealed
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
    assert (arena / "_Msg" / "analysis" / "qwen.raw.txt").read_text(encoding="utf-8") == "utter prose, no json"


# ---------------------------------------------------------------- setup / presets

@pytest.fixture()
def cfg_home(tmp_path, monkeypatch):
    cfg = tmp_path / "cfgdir" / "config.json"
    monkeypatch.setenv("CROSSEXAM_CONFIG", str(cfg))
    return cfg


def test_setup_detects_and_writes_config(arena, cfg_home, monkeypatch, capsys):
    monkeypatch.setattr(cx.shutil, "which",
                        lambda c: "/usr/bin/" + c if c == "claude" else None)
    monkeypatch.setattr(cx, "detect_local_models", lambda *a, **k: ["qwen2.5:14b"])
    assert cx.main(["setup"]) == 0
    out = capsys.readouterr().out
    assert "anthropic-trio" in out and "local-trio" in out and "default" in out
    cfg = json.loads(cfg_home.read_text(encoding="utf-8"))
    assert cfg["default_preset"] == "anthropic-trio"
    assert cfg["presets"]["anthropic-trio"]["synthesis"] == "opus"
    assert cfg["presets"]["local-trio"]["apis"][0][2] == "qwen2.5:14b"


def test_setup_nothing_detected(arena, cfg_home, monkeypatch, capsys):
    monkeypatch.setattr(cx.shutil, "which", lambda c: None)
    monkeypatch.setattr(cx, "detect_local_models", lambda *a, **k: [])
    assert cx.main(["setup"]) == 1


def test_run_uses_default_preset_and_positional_task(arena, cfg_home, monkeypatch, capsys):
    cfg_home.parent.mkdir(parents=True, exist_ok=True)
    cfg_home.write_text(json.dumps({
        "default_preset": "anthropic-trio",
        "presets": {"anthropic-trio": {
            "agents": [["haiku", "c1 {prompt}"], ["opus", "c2 {prompt}"]],
            "apis": [], "synthesis": "opus"}}}), encoding="utf-8")
    ran = []

    def fake_runner(seat_name, cmd_template, prompt, timeout, cli="cxam"):
        ran.append((seat_name, cx.read_phase(cx.find_msg_dir())))
        d = cx.find_msg_dir()
        if cx.read_phase(d) == "blind":
            cx.append_msg(d, {"ts": "t", "from": seat_name, "type": "claim", "msg": "x"})
        elif cx.read_phase(d) == "closed":
            (d / "synthesis.md").write_text("## Consensus\n", encoding="utf-8")
        return True

    monkeypatch.setattr(cx, "run_agent_turn", fake_runner)
    assert cx.main(["run", "數羊", "--force"]) == 0
    out = capsys.readouterr().out
    assert "preset: anthropic-trio" in out
    assert "數羊" in (arena / "_Msg" / "task.md").read_text(encoding="utf-8")
    # synthesis went to the preset's designated top-tier seat
    assert ("opus", "closed") in ran


def test_run_explicit_flags_beat_preset(arena, cfg_home, monkeypatch, capsys):
    cfg_home.parent.mkdir(parents=True, exist_ok=True)
    cfg_home.write_text(json.dumps({"default_preset": "x", "presets": {"x": {
        "agents": [["never", "nope {prompt}"]], "apis": []}}}), encoding="utf-8")
    monkeypatch.setattr(cx, "run_agent_turn", fake_agent_runner({}))
    assert cx.main(["run", "--force", "--task", "t",
                    "--agent", "mine=claude -p {prompt}"]) == 0
    froms = {json.loads(l)["from"] for l in bus_lines(arena)}
    assert "mine" in froms and "never" not in froms


def test_run_no_seats_no_config_errors(arena, cfg_home, monkeypatch, capsys):
    monkeypatch.setattr(cx.shutil, "which", lambda c: None)
    monkeypatch.setattr(cx, "detect_local_models", lambda *a, **k: [])
    assert cx.main(["run", "--force", "--task", "t"]) == 1
    assert "cxam setup" in capsys.readouterr().err


# ---------------------------------------------------------------- cxam run

def fake_agent_runner(script):
    """Simulate a headless CLI agent: on each turn, act per current phase."""
    def runner(seat_name, cmd_template, prompt, timeout, cli="cxam"):
        d = cx.find_msg_dir()
        phase = cx.read_phase(d)
        if phase == "blind":
            cx.append_msg(d, {"ts": "t", "from": seat_name, "type": "claim",
                              "msg": script.get(seat_name, "claim by " + seat_name)})
        elif phase == "debate":
            cx.append_msg(d, {"ts": "t", "from": seat_name, "type": "verify",
                              "msg": "checked", "ref": "analysis/x.md"})
        else:
            (d / "synthesis.md").write_text(
                "## Consensus\nok\n## Disagreements\nnone", encoding="utf-8")
        return True
    return runner


def test_run_full_lifecycle_with_agents_and_api(arena, monkeypatch, capsys):
    monkeypatch.setattr(cx, "run_agent_turn", fake_agent_runner({}))
    monkeypatch.setattr(cx, "http_chat", lambda *a, **k: REPLY)
    rc = cx.main(["run", "--force", "--task", "count sheep",
                  "--agent", "sonnet=claude -p {prompt}",
                  "--api", "qwen=http://x/v1|m"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "blind round (2 seats)" in out
    assert "== synthesis" in out
    assert "## Consensus" in out
    recs = [json.loads(l) for l in bus_lines(arena)]
    claimants = {r["from"] for r in recs if r["type"] == "claim"}
    assert claimants == {"sonnet", "qwen"}    # both seats claimed in blind
    assert any(r["type"] == "verify" for r in recs)
    assert cx.read_phase(arena / "_Msg") == "closed"


def test_run_refuses_dirty_bus_without_force(arena, monkeypatch, capsys):
    seat(monkeypatch, "a")
    cx.main(["post", "info", "old traffic"])
    capsys.readouterr()
    rc = cx.main(["run", "--agent", "s=claude -p {prompt}"])
    assert rc == 1
    assert "already has traffic" in capsys.readouterr().err


def test_run_requires_seats(arena, cfg_home, monkeypatch, capsys):
    # isolate from the host machine: no CLIs, no local server, no config
    monkeypatch.setattr(cx.shutil, "which", lambda c: None)
    monkeypatch.setattr(cx, "detect_local_models", lambda *a, **k: [])
    assert cx.main(["run", "--force"]) == 1


def test_run_copies_exhibits(arena, monkeypatch, capsys, tmp_path):
    src = tmp_path / "material.txt"
    src.write_text("EVIDENCE")
    monkeypatch.setattr(cx, "run_agent_turn", fake_agent_runner({}))
    assert cx.main(["run", "--force", "--exhibit", str(src),
                    "--agent", "s=claude -p {prompt}"]) == 0
    assert (arena / "_Msg" / "exhibits" / "material.txt").read_text(encoding="utf-8") == "EVIDENCE"


def test_run_warns_on_missing_claim(arena, monkeypatch, capsys):
    def lazy_runner(seat_name, cmd_template, prompt, timeout, cli="cxam"):
        return True  # agent runs but never posts
    monkeypatch.setattr(cx, "run_agent_turn", lazy_runner)
    cx.main(["run", "--force", "--agent", "lazy=claude -p {prompt}"])
    assert "no claim from: lazy" in capsys.readouterr().err


def test_run_agent_turn_appends_prompt_and_env(arena, monkeypatch):
    captured = {}

    def fake_sub(cmd, shell, env, timeout, capture_output, text):
        captured["cmd"] = cmd
        captured["seat"] = env.get("CX_SEAT")

        class R:
            returncode = 0
            stdout = stderr = ""
        return R()

    monkeypatch.setattr(cx.subprocess, "run", fake_sub)
    # force the POSIX path so the assertion is platform-independent
    monkeypatch.setattr(cx.os, "name", "posix")
    assert cx.run_agent_turn("s1", "claude -p {prompt}", "do the thing", 5)
    rendered = " ".join(captured["cmd"]) if isinstance(captured["cmd"], list) else captured["cmd"]
    assert "do the thing" in rendered
    assert "{prompt}" not in rendered
    assert captured["seat"] == "s1"


def test_newlines_in_message_stay_one_bus_line(arena, monkeypatch, capsys):
    seat(monkeypatch, "a")
    before = len(bus_lines(arena))
    assert cx.main(["post", "info", "line one\nline two"]) == 0
    lines = bus_lines(arena)
    assert len(lines) == before + 1
    assert json.loads(lines[-1])["msg"] == "line one\nline two"


# ------------------------------------------- dogfood-found regressions (v0.5.1)

def test_seat_name_path_traversal_rejected(arena, monkeypatch, capsys):
    # finding #3: CX_SEAT="../../pwned" must NOT write outside _Msg/
    seat(monkeypatch, "../../pwned")
    assert cx.main(["post", "claim", "x"]) == 1
    assert "invalid seat name" in capsys.readouterr().err
    assert not (arena.parent.parent / "pwned.jsonl").exists()
    for bad in ["a/b", "..", "a\\b", "", "x" * 65]:
        with pytest.raises(ValueError):
            cx.safe_seat(bad)
    for ok in ["sonnet", "codex-max", "gpt.5", "qwen2.5", "a_b"]:
        assert cx.safe_seat(ok) == ok


def test_traversal_via_as_flag_rejected(arena, capsys):
    assert cx.main(["post", "info", "x", "--as", "../evil"]) == 1
    assert "invalid seat name" in capsys.readouterr().err


def test_traversal_via_agent_spec_rejected(arena, capsys):
    assert cx.main(["run", "--force", "--task", "t",
                    "--agent", "../evil=claude -p {prompt}"]) == 1


def test_log_all_does_not_bypass_blind_for_seated_agent(arena, monkeypatch, capsys):
    # finding #1: a seated agent must not peek via `log --all` during blind
    cx.append_msg(arena / "_Msg", {"ts": "t", "from": "a", "type": "claim",
                                   "msg": "blind secret"})
    seat(monkeypatch, "b")
    cx.main(["log", "--all"])
    out = capsys.readouterr().out
    assert "blind secret" not in out
    # but an unseated moderator still sees everything
    for var in cx.SEAT_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    cx.main(["log", "--all"])
    assert "blind secret" in capsys.readouterr().out


def test_blind_to_closed_does_not_reveal(arena, monkeypatch, capsys):
    # finding #2: jumping straight to closed must NOT dump sealed claims
    seat(monkeypatch, "a")
    cx.main(["post", "claim", "still sealed"])
    capsys.readouterr()
    seat(monkeypatch, "mod")
    cx.main(["phase", "closed"])
    capsys.readouterr()
    assert all("still sealed" not in l for l in bus_lines(arena))
    assert (arena / "_Msg" / ".sealed" / "a.jsonl").is_file()  # stays sealed


def test_run_force_clears_stale_sealed(arena, cfg_home, monkeypatch, capsys):
    # finding #5: a stale envelope must not leak into a new --force run
    sd = arena / "_Msg" / ".sealed"
    sd.mkdir(exist_ok=True)
    cx.append_line(sd / "s0.jsonl",
                   {"ts": "t", "from": "s0", "type": "claim", "msg": "STALE"})
    monkeypatch.setattr(cx, "run_agent_turn", fake_agent_runner({}))
    cx.main(["run", "--force", "--task", "new task", "--agent", "s0=c {prompt}"])
    assert all("STALE" not in l for l in bus_lines(arena))


def test_run_refuses_dirty_sealed_without_force(arena, cfg_home, monkeypatch, capsys):
    sd = arena / "_Msg" / ".sealed"
    sd.mkdir(exist_ok=True)
    cx.append_line(sd / "s0.jsonl",
                   {"ts": "t", "from": "s0", "type": "claim", "msg": "STALE"})
    monkeypatch.setattr(cx.shutil, "which", lambda c: None)
    monkeypatch.setattr(cx, "detect_local_models", lambda *a, **k: [])
    assert cx.main(["run", "--task", "t", "--agent", "s0=c {prompt}"]) == 1
    assert "sealed envelopes" in capsys.readouterr().err


def test_concurrent_seal_and_reveal_no_crash_no_loss(arena, monkeypatch):
    # findings #4 + #6: sealing and revealing must be serialized
    import threading
    d = arena / "_Msg"
    errors = []

    def sealer(i):
        try:
            for j in range(20):
                cx.post_message(d, {"ts": "t{}-{}".format(i, j),
                                    "from": "s{}".format(i), "type": "claim",
                                    "msg": "c{}-{}".format(i, j)})
        except Exception as e:  # noqa
            errors.append(repr(e))

    def revealer():
        try:
            for _ in range(20):
                cx.merge_sealed(d)
        except Exception as e:  # noqa
            errors.append(repr(e))

    threads = [threading.Thread(target=sealer, args=(i,)) for i in range(4)]
    threads += [threading.Thread(target=revealer) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    cx.merge_sealed(d)                      # final drain
    assert errors == []                     # #4: no FileNotFoundError crash
    bus = [json.loads(l)["msg"] for l in bus_lines(arena)]
    # #6: every sealed claim ended up on the bus, none stranded
    assert len(bus) == 4 * 20
    assert not list((d / ".sealed").glob("*.jsonl"))


# ---------------------------------------------------------------- sealed envelopes

def test_sealed_lifecycle(arena, monkeypatch, capsys):
    seat(monkeypatch, "a")
    cx.main(["post", "claim", "sealed secret"])
    out = capsys.readouterr().out
    assert "sealed" in out
    assert len(bus_lines(arena)) == 0                      # bus is clean
    assert (arena / "_Msg" / ".sealed" / "a.jsonl").is_file()
    seat(monkeypatch, "mod")
    cx.main(["phase", "debate"])                           # envelopes open
    capsys.readouterr()
    lines = [json.loads(l) for l in bus_lines(arena)]
    assert lines[0]["msg"] == "sealed secret"              # revealed first
    assert "revealed" in lines[-1]["msg"]                  # phase note says so
    assert not (arena / "_Msg" / ".sealed" / "a.jsonl").exists()


def test_sealed_merge_orders_by_ts(arena, monkeypatch, capsys):
    d = arena / "_Msg"
    (d / ".sealed").mkdir(exist_ok=True)
    cx.append_line(d / ".sealed" / "b.jsonl",
                   {"ts": "2026-01-02", "from": "b", "type": "claim", "msg": "second"})
    cx.append_line(d / ".sealed" / "a.jsonl",
                   {"ts": "2026-01-01", "from": "a", "type": "claim", "msg": "first"})
    cx.set_phase(d, "debate")
    msgs = [json.loads(l)["msg"] for l in bus_lines(arena)]
    assert msgs.index("first") < msgs.index("second")


def test_run_counts_sealed_claims(arena, cfg_home, monkeypatch, capsys):
    def sealing_runner(seat_name, cmd_template, prompt, timeout, cli="cxam"):
        d = cx.find_msg_dir()
        if cx.read_phase(d) == "blind":
            cx.post_message(d, {"ts": "t", "from": seat_name, "type": "claim",
                                "msg": "sealed claim"})
        return True
    monkeypatch.setattr(cx, "run_agent_turn", sealing_runner)
    cx.main(["run", "--force", "--task", "t", "--agent", "s=claude -p {prompt}"])
    err = capsys.readouterr().err
    assert "no claim from" not in err          # sealed claims count as posted


# ---------------------------------------------------------------- windows routing

def test_run_agent_turn_windows_uses_bash(arena, monkeypatch):
    captured = {}

    def fake_sub(runner, shell, env, timeout, capture_output, text):
        captured["runner"] = runner
        captured["shell"] = shell

        class R:
            returncode = 0
            stdout = stderr = ""
        return R()

    monkeypatch.setattr(cx.subprocess, "run", fake_sub)
    monkeypatch.setattr(cx.os, "name", "nt")
    monkeypatch.setattr(cx.shutil, "which", lambda c: r"C:\Git\bash.exe")
    assert cx.run_agent_turn("s", "claude -p {prompt}", "hi", 5)
    assert captured["runner"][0] == r"C:\Git\bash.exe"
    assert captured["runner"][1] == "-lc"
    assert captured["shell"] is False


def test_run_agent_turn_windows_no_bash_fails_clearly(arena, monkeypatch, capsys):
    monkeypatch.setattr(cx.os, "name", "nt")
    monkeypatch.setattr(cx.shutil, "which", lambda c: None)
    assert cx.run_agent_turn("s", "claude -p {prompt}", "hi", 5) is False
    assert "POSIX shell" in capsys.readouterr().err


# ---------------------------------------------------------------- stress

def test_concurrent_appends_do_not_interleave(arena):
    import threading
    d = arena / "_Msg"

    def hammer(n):
        for i in range(50):
            cx.append_msg(d, {"ts": "t", "from": "w{}".format(n),
                              "type": "info", "msg": "m{}-{}".format(n, i)})

    threads = [threading.Thread(target=hammer, args=(n,)) for n in range(8)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    lines = bus_lines(arena)
    assert len(lines) == 400
    for l in lines:
        json.loads(l)                      # every line parses -> no interleaving


def test_ten_seat_panel_stress(arena, cfg_home, monkeypatch, capsys):
    monkeypatch.setattr(cx, "run_agent_turn", fake_agent_runner({}))
    agents = []
    for i in range(10):
        agents += ["--agent", "s{}=cli{} {{prompt}}".format(i, i)]
    assert cx.main(["run", "--force", "--task", "big panel"] + agents) == 0
    recs = [json.loads(l) for l in bus_lines(arena)]
    claimants = {r["from"] for r in recs if r["type"] == "claim"}
    assert claimants == {"s{}".format(i) for i in range(10)}
    cursors = (arena / "_Msg" / ".seen")
    assert (arena / "_Msg" / "synthesis.md").is_file()


# ------------------------------------------------- v0.6.0 regressions

def test_read_phase_fails_closed_without_marker(tmp_path, capsys):
    """No/corrupt task.md phase marker must NOT silently drop blind secrecy
    (defaulting open to 'debate' was the same bug class as the v0.5.1 audit
    findings). Fail closed to 'blind' and say so on stderr, once."""
    d = tmp_path / "_Msg"
    d.mkdir()
    cx._phase_warned = False
    assert cx.read_phase(d) == "blind"
    assert "fail-closed" in capsys.readouterr().err
    (d / "task.md").write_text("status: nonsense\n", encoding="utf-8")
    assert cx.read_phase(d) == "blind"
    assert capsys.readouterr().err == ""  # warned once per process, not spammed
    (d / "task.md").write_text("status: debate\n", encoding="utf-8")
    assert cx.read_phase(d) == "debate"


def test_detect_presets_cross_vendor_default(monkeypatch):
    """With >=2 vendor CLIs installed, setup must offer a cross-vendor panel
    (one mid-tier seat per vendor) and cmd_setup must prefer it as default —
    the flagship demo is cross-vendor disagreement; a same-vendor tier
    ladder shares its vendor's blind spots."""
    monkeypatch.setattr(cx.shutil, "which",
                        lambda c: "/usr/bin/" + c if c in ("claude", "codex") else None)
    monkeypatch.setattr(cx, "detect_local_models", lambda *a, **k: [])
    presets = cx.detect_presets()
    assert "cross-vendor" in presets
    names = [a[0] for a in presets["cross-vendor"]["agents"]]
    assert names == ["sonnet", "codex"]  # mid tier of each detected vendor
    assert presets["cross-vendor"]["synthesis"] == "sonnet"


def test_detect_presets_single_vendor_no_cross(monkeypatch):
    monkeypatch.setattr(cx.shutil, "which",
                        lambda c: "/usr/bin/claude" if c == "claude" else None)
    monkeypatch.setattr(cx, "detect_local_models", lambda *a, **k: [])
    assert "cross-vendor" not in cx.detect_presets()


def test_concede_without_prior_verify_warns(arena, monkeypatch, capsys):
    """T3 review, 2026-07-05: challenge/verify demand --ref but concede
    demanded nothing, and RLHF models yield out of politeness. A concession
    should cost execution: warn when a seat concedes without having posted
    any verify of its own."""
    assert cx.main(["phase", "debate"]) == 0
    capsys.readouterr()
    seat(monkeypatch, "qwen")
    assert cx.main(["post", "concede", "adopting sonnet's frame"]) == 0
    assert "concede without a prior verify" in capsys.readouterr().err
    # after posting a verify, the same seat concedes without the warning
    assert cx.main(["post", "verify", "reproduced sonnet's counter-example",
                    "--ref", "analysis/qwen.md#repro"]) == 0
    capsys.readouterr()
    assert cx.main(["post", "concede", "conceding on executed evidence"]) == 0
    assert "concede without a prior verify" not in capsys.readouterr().err
