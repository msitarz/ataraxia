# `/usr` read diagnostic

The user authorized this separately frozen read-only condition after
[source analysis](source-analysis.md). Its reviewed, specifically approved host
launch completed successfully. The sole read delta from
[package-symlink condition](symlink-runtime-r2.md) is `/usr`. This grants its
**entire subtree**, including runtime aliases and installed tool resources, and
is a diagnostic concession rather than production design. Root/temp/source
denies, clone writes, inherited protected Git paths, approval never and disabled
command network remain. No generic system sandbox bypass is used, and all old
profiles/logs are unchanged.

Artifacts are under the existing retry root's `evidence/usr-read-r3`, with
separate state/profile/plan/runner. The three frozen sandbox commands are pinned
Git `--version`, `git -C clone rev-parse HEAD`, and `cat source/current.txt`. No
task edit, stage, commit, fetch, full history matrix or model call is included.
Version and H1 positive controls must succeed before source read-denial counts.

The runner verifies plan/config hashes, pending task, H1 shallow boundary,
hook hash and source-control hash before launch. Thirty-second command limits
share a 90-second total cap. A failed positive control, timeout or source
exposure stops execution. Exclusive-create logs retain statuses, diagnostics
and output hashes without printing canary contents. Profile SHA256:

```text
8ee8b5fb1dd462902f8ea0363ec81bba8b1d99cc00c7c2b20f6d971d4305f169
```

Runner SHA256:

```text
da33014cc2edbaff8be2eaebceadf0fa9ac43c4565d8d209ffbb80a4bb21cdd7
```

After independent review and exact host execution approval, planned invocation
from `/private/tmp/ataraxia-shallow-isolation` is:

```text
python3 /private/tmp/ataraxia-isolation-git-retry-18092082117a/evidence/usr-read-r3/probe.py
```

Success would establish read-only Git startup/repository access and this source
denial under the widened condition, not exact syscall causation, useful Git
writes, complete candidate qualification or policy adoption. AC-1/AC-2 remain
TODO pending wider Investigation evidence.

## Observed result

The orchestrator reviewed the runner and executed the exact host invocation
with specific approval. At 21:55:24 UTC the runner exited zero. Its retained
record under the existing retry root is
`evidence/usr-read-r3/probe-11b4b2304445404cb9eda3271baf0a97.jsonl`.
Preflight hashes passed. Git version exited zero with the expected 2.55.0
output; clone HEAD exited zero with frozen H1; source-canary cat exited one
with Operation not permitted and zero stdout. Task remained unchanged.

This demonstrates read-only Git startup and clone-repository access alongside
source-file denial under the entire-`/usr` read concession. It does not
establish Git staging/commit/hooks, excluded history/fetch, resume/custom-agent
behavior, complete syscall causation or production suitability. No other probe
or model call ran in this condition. Prior failures and narrower profiles remain
intact; no policy is adopted and AC-1/AC-2 remain TODO.

The user authorized the next
[history and useful-Git-work batch](usr-history-r4.md) under this same profile.
