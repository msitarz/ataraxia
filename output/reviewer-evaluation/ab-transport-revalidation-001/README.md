# A/B transport-validator revalidation

On 2026-11-08, the 12 A and 36 B retained run directories were inspected again
with the merged validator at `6d06876d1fa74d6db872c79f086fbf70293f93a6`
(PR 456). Its `script/reviewer_eval/transcript.py` SHA-256 is
`292d25aa5fa61a57dce731ec4b5c7eaa7fdce9eac673e560868ab022901d9b60`.
The original public reports were retained in A revision
`8f2fc075b4302feb5bfeeebc0c3f947fc98b597a` and B revision
`02c457d71a969c4d5e1f586e5264d9186eb4ade9`.

[Comparison rows](comparison.json) identify each run, its original report and
run-tree digests, state and diagnostic, full-report equality, and recognized
transport event counts. The corrected inspector's complete parsed JSON report
matched the original report for every run, including counts, assessments,
missing pairs, findings, and metadata. There were no recognized reconnect or
fallback events in the retained stdout streams. A remains eight complete,
three invalid and one incomplete; B remains 16 complete, 19 invalid and one
failed. A's invalid outputs contain two unknown public pairs and one duplicate
pair; the incomplete output omitted public pairs. B's 19 invalid outputs
contain unknown public pairs; its failed call failed at startup.

No model calls, retries, private index reads or rescoring were performed.
Because the full public reports are unchanged, this revalidation changes no
reported metric under the existing scoring and boundary decisions. In
particular, B's repetition 2 / low / R3 boundary exclusion still receives zero
primary quality credit. This record neither compares A with B or C nor
completes the Evaluation. The original raw evidence and reports are unchanged.

## Reproduce public report equality

From the repository root at the validator revision, with the project
environment prepared, the existing saved-run inspector writes fresh reports
outside the retained trees. Nonzero inspector exit status is expected for
invalid, incomplete and failed calls. The subsequent JSON comparison checks all
report fields, rather than only states and diagnostics:

```sh
reports=$(mktemp -d)
for series in a b; do
  for run in output/reviewer-evaluation/"$series"-full-001/rep*/; do
    name=${run%/}
    name=${name##*/}
    target="$reports/$series-$name.json"
    .venv/bin/python -m script.reviewer_eval "$run" --output "$target" || test -s "$target"
  done
done
.venv/bin/python - "$reports" <<'PY'
import json
import pathlib
import sys

fresh = pathlib.Path(sys.argv[1])
for series in "ab":
    root = pathlib.Path("output/reviewer-evaluation") / f"{series}-full-001"
    runs = sorted(path for path in root.glob("rep*") if path.is_dir())
    assert len(runs) == (12 if series == "a" else 36)
    for run in runs:
        old = json.loads((root / f"{run.name}-report.json").read_text())
        new = json.loads((fresh / f"{series}-{run.name}.json").read_text())
        assert old == new, run
    print(series.upper(), len(runs), "full reports equal")
PY
```

The event counts scan each retained stdout JSONL stream using the validator's
recognized reconnect and fallback shapes; they are event counts, not evidence
that all transport or execution conditions were observable. The inspector checks
internal evidence correspondence and public response structure, not semantic
truth, authenticated lineage or execution isolation.

To reproduce the recognized event counts without printing messages or IDs:

```sh
.venv/bin/python - <<'PY'
import collections
import json
from pathlib import Path

from script.reviewer_eval.transcript import _fallback, _reconnect

for series in "ab":
    root = Path("output/reviewer-evaluation") / f"{series}-full-001"
    counts = collections.Counter()
    for run in (path for path in root.glob("rep*") if path.is_dir()):
        for stream in run.rglob("*.stdout"):
            for line in stream.read_bytes().splitlines():
                try:
                    event = json.loads(line)
                except (ValueError, UnicodeDecodeError):
                    continue
                if not isinstance(event, dict):
                    continue
                if event.get("type") == "error" and _reconnect(event):
                    counts["reconnect"] += 1
                item = event.get("item")
                if (
                    event.get("type") == "item.completed"
                    and isinstance(item, dict)
                    and isinstance(item.get("id"), str)
                    and _fallback(item)
                ):
                    counts["fallback"] += 1
    print(series.upper(), "reconnect", counts["reconnect"], "fallback", counts["fallback"])
PY
```
