# B-only exploratory run: pre-execution record

Recorded before dispatch on 2026-11-04. The maintainer authorized the full B
scenario on a separate branch with the same execution profile and recorded
isolation limitation as the exploratory A run. This scoped authorization
permits B execution despite the protocol's isolation gate. It does not verify
source immutability, withheld-label or prior-answer isolation, effective tools,
or server-side model or effort binding. It does not authorize A, C, neutral,
or probe calls or complete the Evaluation. No prompt tuning or replacements
are authorized.

The assigned base is `8f2fc075b4302feb5bfeeebc0c3f947fc98b597a`.
The public input bytes use two LF separators, with these SHA-256 digests;
paths are relative to this Evaluation directory:

- `inputs/shared/review-instructions-and-schema.txt`:
  `2c464b98b96d562f3dbef2cc5e3d9515ebb0c7b58f9777fa5e1133f11f7c632f`
- `inputs/cases/B/r1.txt`:
  `1af05867b464bce554f56a1abf2d549688ec18377ddd60f5ba434bf6db15b048`
- `inputs/cases/B/r3.txt`:
  `d7d636ae60be01188afe8c477105c2e3069123b0c8ba444524ba3af443380bc5`
- `inputs/cases/B/r4.txt`:
  `4dc696fa4f261d2acefa6307b613292d0ea7adcf3b77107c9a0053f543e32006`
- `inputs/corpus/source.txt`:
  `27a1972f0c79684682a3fb164a4776bd203f00cbf24aed4ced8278ba55fe1f66`
- `preparation/min.md`:
  `e6a735386f908f03c35bbe65be9e786d7c23ab471ce112b6d0b7f6f198be1cdd`

Use system CLI `/usr/local/Caskroom/codex/0.166.0/bin/codex`, version 0.166.0,
`execution-controls-v3`, `gpt-6-luna`, an owned empty external working
directory, requested read-only sandbox, disabled local tools, ignored user
configuration, and approval policy never. Actual effective isolation and
server-side model or effort remain unverified.

Thirty-six fresh sessions run serially. In each effort, run R1, R3, then R4,
with the same whole source corpus. Effort rotation:

| Repetition | Efforts |
| --- | --- |
| 1 | none, low, medium, high |
| 2 | low, medium, high, none |
| 3 | medium, high, none, low |

The Evaluation-owned caller selects one original case path from the frozen B
directory. Run the following once per scheduled slot, substituting `RULE`,
`EFFORT`, and a fresh external `OUTPUT` path. Check the settled evidence before
starting the next slot.

```sh
uv run --cache-dir .cache/uv --no-sync python -m doc.feat.reviewer.engineering.evaluation.preparation.run_b_case RULE -m gpt-6-luna -e EFFORT -c 1 --timeout-seconds 300 --cleanup-timeout-seconds 10 --output-limit-bytes 1048576 --retry-limit 0 --capacity-retry-limit 0 -o OUTPUT
```

For a dry run replace `-o OUTPUT` with `-n`. The full-directory dry run
selected R1, R3, and R4 with approximate context estimates of 9,738, 10,372,
and 10,418 tokens respectively, plus 50 instruction tokens per call. These
`tiktoken` 0.14.0 estimates exclude automatic context and framing.

Each slot has one attempt, 300 seconds execution, 10 seconds cleanup, 1 MiB
combined output, no retries or quota probe. Stop on observed unauthorized tool
activity, access or exposure, drift, cancellation, unsafe cleanup, invalid
accounting, exhausted bounds, or three consecutive infrastructure-failed
planned calls. Record every remaining slot as not started; never refill a
failure. Stage original evidence externally during dispatch and retain the
byte-identical run directories with original path provenance under
`output/reviewer-evaluation/b-full-001` afterward.

Previously observed neutral input counts are candidate estimates of 3,570,
3,568, 3,570, and 3,570 for none, low, medium, and high respectively. They
include the neutral task and have variable-context uncertainty; they are not
reviewed, frozen trial baselines. Report raw usage primarily and subtraction
only as a candidate estimate. Hard token enforcement is unavailable. Reserve
32,000 input and 14,000 output tokens per attempt (1,656,000 total), 11,160
seconds including cleanup, and at least 36 MiB stream capacity plus other
evidence within the shared 40-hour, 1 GiB, and 16,192,000 raw-token envelopes
including A and preparation. Reservations are not hard token limits.
