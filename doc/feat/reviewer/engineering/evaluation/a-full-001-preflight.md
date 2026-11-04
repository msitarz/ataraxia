# A-only exploratory run: pre-execution record

Recorded before dispatch on 2026-11-04. The maintainer explicitly directed the
full A scenario and overrode the protocol decision blocking execution on
unverified isolation: “don't care about that protocol block, just run the A
scenario evaluation and i override that protocol decision explicitly”. This
is an exploratory deviation, not verification of source immutability, withheld
label or prior-answer isolation, effective tools, or server-side model binding.
It does not complete the Evaluation or authorize B or C.

The input revision is `15d44afad6f917cbc632a06688784a579e451535`. The
model-visible bytes are fixed, composed in the listed order with two LF
separators. SHA-256:

- `inputs/shared/review-instructions-and-schema.txt`:
  `2c464b98b96d562f3dbef2cc5e3d9515ebb0c7b58f9777fa5e1133f11f7c632f`
- `inputs/cases/A/a.txt`:
  `496f29907509b97a20e67f502ceb6828933cbf63670d5648cf544cc3b1314342`
- `inputs/corpus/source.txt`:
  `27a1972f0c79684682a3fb164a4776bd203f00cbf24aed4ced8278ba55fe1f66`
- `preparation/min.md`:
  `e6a735386f908f03c35bbe65be9e786d7c23ab471ce112b6d0b7f6f198be1cdd`

Paths above are relative to this Evaluation directory. Use the system CLI
`/usr/local/Caskroom/codex/0.166.0/bin/codex`, version 0.166.0,
`execution-controls-v3`, model `gpt-6-luna`, owned empty external working
directory, requested read-only sandbox, disabled local tools, ignored user
configuration, and approval policy never. Actual effective isolation and
server-side model or effort are unverified.

Twelve fresh sessions run serially in this order:

| Repetition | Efforts |
| --- | --- |
| 1 | none, low, medium, high |
| 2 | low, medium, high, none |
| 3 | medium, high, none, low |

Each call has one attempt, 300 seconds execution, 10 seconds cleanup, 1 MiB
combined output, no retry or quota probe. Stop for observed unauthorized tool
activity, access or exposure, drift, cancellation, unsafe cleanup, invalid
accounting, exhausted bounds, or three consecutive infrastructure failures.
Retain every planned slot and never refill a failed result. Stage evidence
outside the checkout until dispatch ends; retain originals and path provenance
under `output/reviewer-evaluation/a-full-001` afterward.

The dry run estimates 11,838 context tokens and 50 instruction tokens per
call using approximate `tiktoken` 0.14.0 `o200k_base`; automatic context and
framing are excluded. Previously observed neutral input counts are candidate
estimates of 3,570, 3,568, 3,570, and 3,570 for none, low, medium, and high,
respectively. They include the neutral task and have variable-context
uncertainty; they are not reviewed, frozen trial baselines. Report raw usage
primarily and any subtraction as a candidate estimate, not guaranteed overhead
or cost. Hard token enforcement is unavailable. Reserve 32,000 input and
14,000 output tokens per attempt (552,000 total), 3,720 seconds including
cleanup, and at least 12 MiB stream capacity plus other evidence within the
protocol's 40-hour, 1 GiB and 16,192,000-token aggregate envelopes. Those
planning reservations are not hard token consumption limits.
