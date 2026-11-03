# Saved reviewer results

A report gives each planned call one outcome and disjoint counts, for example:

```json
{
  "version": 1,
  "evidence_state": "complete",
  "diagnostic": null,
  "run_id": "example-run",
  "head_commit": "example-commit",
  "planned_count": 1,
  "counts": {"complete": 0, "incomplete": 0, "invalid": 0, "failed": 0, "not_started": 1},
  "calls": [{"position": 0, "model": "example", "effort": "low", "call_id": "opaque", "state": "not_started", "diagnostic": null, "attempts": [], "selected_attempt": null, "findings": [], "thread_id": null}],
  "scope": "Internal artifact consistency and correspondence to frozen source bytes only; not authenticated lineage, safe-read verification, semantic truth, or quality readiness."
}
```

Completed calls include their persisted attempt records and validated findings.

- `complete` means a successful terminal attempt produced a valid complete
  response.
- `incomplete` means evidence or the review response is incomplete.
- `invalid` means consumed evidence, relationships, or the response are invalid.
- `failed` means the terminal call or process did not complete successfully.
- `not_started` means a consistent run summary explicitly records no dispatch.

Inspect the original directory of a saved initial A/B harness run:

```sh
uv run --no-sync python -m script.reviewer_eval /path/to/original-run \
  --output /path/to/new-report.json
```

The output must be a new file outside the evidence directory. Exit status 0
means all planned calls have complete validated responses and the run summary
is complete; 1 means incomplete, invalid, failed, or a write/read failure;
argument errors return 2. A missing or invalid plan has unknown inventory.
A missing run summary leaves every known planned call incomplete.

The adapter checks the retained records and frozen prepared A/B inputs for
internal consistency and correspondence to original source bytes. It does not
establish authenticated lineage, approved input authenticity, runtime binding,
safe reads, or semantic truth. Findings remain unadjudicated and undeduplicated.
The accepted JSONL shape has one thread start, one turn start, optional
completed reasoning items with string IDs and text, one completed agent message,
and one successful terminal turn. Other events, including tools, are rejected.
Absolute stream references require inspection in the original run directory;
relocated runs are not supported.
