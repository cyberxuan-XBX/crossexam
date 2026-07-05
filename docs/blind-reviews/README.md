# Blind reviews of this repository

Eight commissioned AI reviews of CrossExam, run in two rounds on 2026-07-05
(round 1 against v0.5.2's README era, round 2 against v0.6.0, including one
review prompted to staff-engineer depth). Reviewers shared no context with
each other. Transcripts are verbatim except for marked redactions of
passages tying a review to the author's personal environment — every
technical claim, criticism, and mistake is preserved as written. Most are in
Traditional Chinese; each file carries an English provenance header.

Why publish these: the fix history replays this tool's own thesis. **What
got fixed correlates with evidence class, not eloquence.**

| Review | Evidence class | Distinct contribution | Outcome |
|---|---|---|---|
| [claude-fable5-r1](claude-fable5-r1.md) | **executed** — cloned, ran tests + simulation | two silent degradations, Windows friction | fixed same-day in v0.6.0, regression-tested |
| [claude-opus-r1](claude-opus-r1.md) | read (~1,000 lines, no execution) | the default panel contradicted the flagship demo | v0.6.0's headline change (cross-vendor default) |
| [gpt-r1](gpt-r1.md) | citation (web fetch) | fullest productization roadmap | adopted as roadmap items, none implemented yet |
| [gemini-r1](gemini-r1.md) | summary (restated README) | none | none |
| [claude-fable5-r2](claude-fable5-r2.md) | **executed** — diffed 0.6.0, re-ran tests; declares its conflict of interest up front | caught the README overclaiming by this repo's own standard | wording fixes + Breaking marker in v0.6.1; proposed publishing this directory |
| [claude-opus-r2](claude-opus-r2.md) | read + web search | evidence asymmetry; the AI-reviewer section "walks the line between context and framing" | standing warning |
| [gpt-r2](gpt-r2.md) | citation (web fetch) | seat reliability profiles, non-verifiable task labeling | v0.6.1 roadmap |
| [claude-fable5-staff-depth](claude-fable5-staff-depth.md) | **executed** — line-checked every claim; deliberately did not read the other reviews | correlated exhibit injection, concede's reverse failure mode, the missing self-consistency control | v0.6.1's substance |

Executed findings with line numbers were fixed within hours. Citation-level
strategy went to the roadmap. The summary produced nothing. That gradient —
`executed > cited > prose` — is the protocol, observed in the wild on its
own reviewers.

One honest caveat, from the round-2 reviews themselves: commissioned reviews
of a repo whose README includes a section addressed to AI reviewers are not
a neutral instrument. Read them the way this protocol reads everything:
claims to verify, not conclusions to adopt.
