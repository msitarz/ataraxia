# Supplemental neutral invocation verification

On 2026-11-04 the maintainer authorized one supplemental neutral attempt at
 each of none, low, medium, and high, at concurrency one, with no retries or
quota probes. This is a new four-attempt preparation allocation; it does not
reset the historical none 4/4 or total 4/16 accounting. It does not authorize
corpus trials or a complete input freeze.

The exact instruction bytes are in [min.md](preparation/min.md), SHA-256
`e6a735386f908f03c35bbe65be9e786d7c23ab471ce112b6d0b7f6f198be1cdd`.
The exact neutral prompt bytes are in
[neutral-prompt.txt](preparation/neutral/neutral-prompt.txt), SHA-256
`d85762a537347daee213713bf21413e53fd0d0f5054793a41b0d113087438f7c`.
The prompt reads `Return exactly this single word: READY` followed by LF.

Use the system CLI resolved from PATH to
`/usr/local/Caskroom/codex/0.166.0/bin/codex`, version `codex-cli 0.166.0`,
with the `execution-controls-v3` profile and `gpt-6-luna`. Request the default
owned empty external working directory, read-only sandbox, disabled local tools,
ignored user configuration, approval policy never, and the staged instruction
override. The four separate one-call harness runs allow inspection and a stop
before the next dispatch. Each has a 300-second timeout, 10-second cleanup,
1 MiB combined output cap, zero retries, and no quota probes. Retain every
outcome; do not refill failures. Stop all further dispatch on cleanup
uncertainty, unexpected tool activity or access, drift, cancellation, exposure,
or invalid accounting. Execution evidence is staged outside the checkout to
preserve the harness's clean-checkout requirement and then retained separately.

These requested settings and a successful greeting do not establish effective
model or effort, absolute read isolation, or absence of opaque injected
context. Applicable per-effort baselines include the neutral prompt; their
availability depends on observed usage and matching configuration. The previous
7,983-token observation is not a matched baseline for this run. All Evaluation
acceptance criteria remain TODO.
