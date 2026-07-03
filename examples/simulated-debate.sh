#!/usr/bin/env bash
# Simulated three-seat debate — no AI, no API keys. Shows the full protocol
# lifecycle in ~5 seconds so you can see what your agents will be doing.
# Run from anywhere:  bash examples/simulated-debate.sh
set -e
CX="${CX:-cx}"
command -v "$CX" >/dev/null || CX="python3 $(cd "$(dirname "$0")/.." && pwd)/crossexam.py"

ARENA=$(mktemp -d)
cd "$ARENA"
echo "=== arena: $ARENA"

echo; echo "=== 1. moderator initializes the task"
$CX init --task "Gate log audit: how many vehicles are actually on site?"

echo; echo "=== 2. blind phase: three seats post independent claims"
CX_SEAT=sonnet $CX post claim "56 on site; trusted the dashboard aggregate" --ref analysis/sonnet.md
CX_SEAT=gpt    $CX post claim "63 on site; found 7 ghost exits (entry then fake exit within 5-9s)" --ref analysis/gpt.md#ghosts
CX_SEAT=gemini $CX post claim "61 on site; excluded 49 unreadable plates from both directions" --ref analysis/gemini.md

echo; echo "=== 3. blind means blind: sonnet tries to read, others' claims are withheld"
CX_SEAT=sonnet $CX read

echo; echo "=== 4. moderator flips to debate"
$CX phase debate

echo; echo "=== 5. now sonnet sees everything"
CX_SEAT=sonnet $CX read

echo; echo "=== 6. cross-examination: verify with evidence, concede when beaten"
CX_SEAT=sonnet $CX post verify    "gpt's 7 ghost exits reproduce: 7 entry->exit pairs under 10s, physically impossible" --ref analysis/sonnet.md#recheck
CX_SEAT=gemini $CX post challenge "gpt missed 11 rows: 5 drivers with accounts but no plate authorization, always Pass=False" --ref analysis/gemini.md#unauth
CX_SEAT=sonnet $CX post concede   "my 56 was a dashboard aggregate artifact; adopting gpt's event-level frame"

echo; echo "=== 7. moderator closes; the human reads the disagreement table"
$CX phase closed
$CX status

echo; echo "=== 8. full transcript (moderator view)"
$CX log --all

echo; echo "=== done. arena kept at $ARENA (rm -rf it when done)"
