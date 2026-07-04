# Synthesis — CrossExam v0.5.0 audit (crossexam.py)

> **Status:** all six cross-verified findings below were fixed in v0.5.1, each
> with a regression test (see [CHANGELOG](../CHANGELOG.md)). Item 7's TOCTOU
> window is closed by the same fix — `post_message` now re-reads the phase
> under `phase_lock`. The text below preserves the audit exactly as it ran
> against v0.5.0.

Panel: sonnet, gpt, qwen. Blind phase: 3 claims sealed, then revealed on
`phase -> debate`. qwen's blind claim ("no bugs, protocol-compliant") was
challenged by both other seats and conceded in full at close
(`analysis/qwen.md`, log #14). No seat currently holds a dissenting position.

## Consensus

All 7 items below were reproduced with a running python3 repro against the
real, unmodified `crossexam.py` (not a mock). Tests were green going in
(gpt: `pytest -q` → 48 passed) — these are gaps the test suite doesn't cover,
not regressions.

1. **`cmd_log --all` bypasses blind secrecy for any seated agent, no race needed.**
   `crossexam.py:708` (`if phase == "blind" and seat and not args.all:`) gates
   only on the `--all` flag itself — no unseated/human/moderator check.
   Originated by gpt (`analysis/gpt.md` Finding 1), independently re-run and
   confirmed by sonnet against the real module (log #6). Deterministic,
   single-threaded.

2. **Direct `blind -> closed` transition reveals sealed claims early.**
   `set_phase()` guards with `if phase != "blind"` (`crossexam.py:1048`), so
   *any* non-blind target — not just `debate` — triggers `merge_sealed()`.
   Contradicts PROTOCOL.md/SECURITY.md's "revealed when debate opens."
   Originated by gpt (Finding 2), confirmed by sonnet against real
   `cx.set_phase` (log #7). Deterministic, single-threaded.

3. **Seat name is unsanitized in filesystem paths → path traversal / arbitrary file write.**
   Affects `_Msg/.sealed/<seat>.jsonl`, `_Msg/.seen/<seat>`, and
   `_Msg/analysis/<seat>.md` (`crossexam.py:344, 371, 378` region; also
   `get_seat()` at 294-299). `CX_SEAT="../../pwned"` writes a `.jsonl` file
   outside `_Msg/` entirely. Discovered **independently by both sonnet (Bug 4)
   and gpt (Finding 3)** via separate repro harnesses, then each re-ran the
   other's repro and got the same result (log #10, sonnet's debate-pass
   corroboration). Not covered by SECURITY.md's "Bus integrity" section, which
   only admits in-bus content forgery, not sandbox escape. Impact is bounded
   to attacker-controlled JSON content and requires the parent dir to already
   exist — arbitrary-file-*creation*, not RCE.

4. **`merge_sealed()` has no lock: unlocked read-then-unlink crashes under concurrent phase-flip calls.**
   `crossexam.py:384-400` globs `.sealed/*.jsonl`, reads, then unlinks per
   file with no lock between the two `set_phase()` calls that could race it.
   Sonnet reproduced against a faithful copy (widened read/unlink window) and
   against the actual unmodified `cx.merge_sealed` (repro3b, monkeypatched
   `Path.unlink` to widen the window, no logic changed) — both crash with
   `FileNotFoundError`. gpt independently re-ran this against the real
   function and got the same crash (log #11). Note: sonnet's bug title
   mentions "can duplicate reveals" as a theoretical second outcome of the
   same lock gap, but only the crash was actually demonstrated in a repro —
   treat the crash as confirmed, the duplicate-reveal variant as unverified.

5. **Stale `.sealed/` envelopes leak across an abandoned/reused `_Msg/` session.**
   Neither `cmd_init()` nor `cxam run`'s "already has traffic" guard
   (`bus_line_count(d) > 0`, `crossexam.py:957-960`) accounts for `.sealed/`.
   An abandoned blind-phase run leaves `bus.jsonl` at 0 lines (looks "fresh")
   while a per-seat sealed file still holds a claim from the old task; a new
   unrelated run reusing the same seat name inherits it and it surfaces as if
   it answered the new question when debate opens. Sonnet's repro (Bug 3),
   independently re-run by gpt against the real code with the same outcome
   (log #12). Deterministic, no concurrency needed.

6. **Blind-claim vs. phase-flip race can strand a claim in `.sealed/` past the debate flip (opposite failure mode of #4).**
   `post_message()` reads phase before appending to the sealed file
   (`crossexam.py:375`); if `set_phase()`'s `merge_sealed()` pass completes
   before that seat's append finishes, the claim is never merged onto the bus
   and never revealed — it sits invisibly in `.sealed/` after debate has
   already opened. Originated by gpt (Finding 4, threaded repro), confirmed
   by sonnet against real `cx.post_message`/`cx.set_phase` (log #8). Sonnet
   notes this is the same root cause (missing lock around `set_phase` +
   `merge_sealed`) producing a third distinct failure shape alongside #4's
   crash and the TOCTOU unsealed-leak below — three outcomes, one missing lock.

7. **Phase-flip TOCTOU lets a blind claim skip sealing entirely and land unsealed on the bus.**
   `post_message()` re-reads `read_phase(d)` independently of the check
   `cmd_post()` already did; if a seat's post lands in the window after
   `set_phase()` rewrites `task.md`'s status but the seat still believes it's
   blind, the claim skips `.sealed/` and goes straight to the bus — defeating
   the anchoring guarantee SECURITY.md calls "mechanically enforced." Sonnet's
   Bug 1, with a deterministic repro forcing the exact interleaving.
   **Caveat: this is the one item without independent second-seat
   re-verification** — gpt's debate-pass explicitly re-ran sonnet's other
   three findings (path traversal, merge_sealed crash, stale-seal leak) but
   its log/analysis contain no re-run of this specific repro. qwen's
   concession was blanket ("adopting their verified issues"), not per-item.
   Still uncontested by any seat, but resting on single-source verification.

**Not bugs (checked, ruled out, uncontested):** `fcntl.flock` in
`append_line` correctly serializes concurrent bus appends (sonnet stress-
tested 8 threads × 50 lines → 400 clean, non-interleaved lines). Blind-phase
cursor freeze/re-delivery logic loses no messages in the single-writer-per-
seat case (sonnet checked, no counter-check from gpt/qwen).

## Disagreements

| Claim | Seats for | Seats against | Evidence status |
|---|---|---|---|
| qwen's original claim: crossexam.py has no correctness bugs, no security issues beyond SECURITY.md, fully protocol-compliant | qwen (blind phase only) | sonnet, gpt | **Resolved, not open** — qwen conceded at close (log #14, `analysis/qwen.md` debate entry), adopting sonnet's and gpt's findings wholesale. No seat currently holds this position. Listed here only because it was the panel's one substantive disagreement before resolution. |
| Bug 2's "can duplicate reveals" sub-claim (vs. confirmed crash) | sonnet (asserted, unconfirmed) | none explicitly, but no seat demonstrated it | **Open evidence gap, not a seat conflict** — no repro output shows a duplicate reveal, only the `FileNotFoundError` crash. Flagged for the human: treat crash as solid, duplicate-reveal as speculative until someone repros it. |
| Bug 1 (TOCTOU unsealed-leak) verification depth | sonnet (authored + repro'd) | none — uncontested | **Single-seat evidence** — unlike items 1–6 above, no second seat independently re-ran this repro against the real module. Recommend one more pass before treating it as equally solid to the cross-verified items. |

Bottom line for the human: 6 of 7 findings have two-seat independent
confirmation against the real, unmodified code; 1 (TOCTOU unsealed-leak) has
one seat's repro only; qwen's dissent was fully retracted, not overruled by
majority vote.
