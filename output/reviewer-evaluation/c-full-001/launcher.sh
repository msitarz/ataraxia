#!/usr/bin/env bash
set -e

WORKTREE=/private/tmp/ataraxia-reviewer-c-full-terminal
BASE=6d06876d1fa74d6db872c79f086fbf70293f93a6
OUTROOT="$HOME/ataraxia-eval-results/c-remaining-c25-001"
PILOT="$HOME/ataraxia-eval-results/c-medium-c3-001"
cd "$WORKTREE"

# The destination is exclusive; preserve the launcher and scope before dispatch.
mkdir -p "$HOME/ataraxia-eval-results"
if ! mkdir "$OUTROOT"; then
  echo "Refusing existing output root: $OUTROOT" >&2
  exit 2
fi
cp "$0" "$OUTROOT/launcher.sh"
cat > "$OUTROOT/pre-execution.txt" <<META
Scope: 2,046 new C calls at concurrency 25; 11 blocks of 186 calls.
Base: $BASE; worktree: $WORKTREE; model: gpt-6-luna.
Each call: min instructions; timeout 300s; cleanup 10s; output cap 1048576 bytes; retry limits 0.
Order: rep1 none,low,high; rep2 low,medium,high,none; rep3 medium,high,none,low.
Rep1 medium is reused from $PILOT (completed pilot; counts as repetition 1).
The schedule has this pilot reuse and ordered execution deviation; it is not a full protocol freeze or budget-compliance claim.
No quota waiting, probes, skips, retries, refills, or automatic reruns.
META
shasum -a 256 "$OUTROOT/launcher.sh" > "$OUTROOT/launcher.sha256"

run_block() {
  rep=$1
  effort=$2
  if [ "$(git rev-parse HEAD)" != "$BASE" ] || [ -n "$(git status --porcelain)" ]; then
    echo "Refusing dispatch: checkout drifted from clean base $BASE" >&2
    return 2
  fi
  if ! codex --version 2>&1 | grep -Fx 'codex-cli 0.166.0' >/dev/null; then
    echo "Refusing dispatch: expected codex-cli 0.166.0" >&2
    return 2
  fi
  block="$OUTROOT/rep${rep}-${effort}"
  if [ -e "$block" ]; then
    echo "Refusing existing block output: $block" >&2
    return 2
  fi
  echo "Dispatching rep${rep}-${effort}: 186 calls at concurrency 25"
  uv run --cache-dir .cache/uv --no-sync python -m script.eval \
    -d doc/feat/reviewer/engineering/evaluation/inputs/c-shared \
    -d doc/feat/reviewer/engineering/evaluation/inputs/c-rules \
    -d doc/feat/reviewer/engineering/evaluation/inputs/c-functions \
    -i doc/feat/reviewer/engineering/evaluation/preparation/min.md \
    -m gpt-6-luna -e "$effort" -c 25 \
    --timeout-seconds 300 --cleanup-timeout-seconds 10 \
    --output-limit-bytes 1048576 --retry-limit 0 --capacity-retry-limit 0 \
    -o "$block" </dev/null
}

while read -r repetition effort; do
  run_block "$repetition" "$effort"
done <<'SCHEDULE'
1 none
1 low
1 high
2 low
2 medium
2 high
2 none
3 medium
3 high
3 none
3 low
SCHEDULE
