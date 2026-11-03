# Saved reviewer results

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
