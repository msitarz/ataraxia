# Saved reviewer results

This command selects `function-assessments-v2` or historical `findings-v1`
from the exact frozen shared prompt and schema. Unknown formats are invalid.
A version 2 report identifies the format for each call and keeps current
assessments and missing public pairs separate from historical findings. Public
completeness does not establish private-control coverage or semantic accuracy.
A complete response may contain UNKNOWN or NOT_APPLICABLE judgments; completion
is not a quality PASS. The validator derives qualified lexical function names
locally from source ASTs without generating line requirements for model output.
Historical `findings-v1` responses retain their original interpretation.

For example, this excerpt shows one incomplete current-format call:

```json
{
  "version": 2,
  "calls": [{
    "state": "incomplete",
    "response_format": "function-assessments-v2",
    "assessments": [{"rule_id": "R1", "file_id": "example.py", "function_name": "C.f", "judgement": "UNKNOWN"}],
    "missing_pairs": [{"rule_id": "R1", "file_id": "example.py", "function_name": "C.g"}],
    "findings": []
  }]
}
```

Completed calls include their persisted attempt records and validated response.

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
The accepted JSONL shape has one thread start, an optional known disabled Code
Mode host error notice before the turn, one turn start, optional completed
reasoning items with string IDs and text, one completed agent message, and one
successful terminal turn. Only the exact known notice with a nonempty string ID
is accepted; other errors and tool events are rejected. The raw stream retains
the notice.
The reader validates recorded stream references against the frozen output path
and reads retained files beneath the supplied run directory. A relocated archive
can be inspected when its recorded paths and retained artifacts remain
internally consistent; relocation does not authenticate provenance or repair
missing data.
