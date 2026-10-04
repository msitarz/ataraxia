# Explicit clone Git-write condition

The user authorized this new condition after
[protected Git writes blocked useful work](usr-history-r4.md#observed-outcomes-and-failing-boundary).
It completed after independent review and specific host-launch approval. The
only profile change from working r4 is:

```text
/private/tmp/ataraxia-isolation-git-retry-18092082117a/clone/.git = write
```

There is no additional FETCH_HEAD restriction. This permits clone Git metadata,
including refs/config/hooks, rather than only index writes. Entire `/usr` read,
clone writes, source/root/temp denies, disabled command networking and approval
never remain. Inherited `.codex` protection is unchanged. No bypass flag,
production policy change or model trial is included.

The matching source represents more-specific writes as
[independent writable roots](https://github.com/openai/codex/blob/01fc69f4026735edfdf6789820549727a4867b11/codex-rs/protocol/src/permissions.rs#L1681)
and derives protected metadata names from the
[effective write matcher](https://github.com/openai/codex/blob/01fc69f4026735edfdf6789820549727a4867b11/codex-rs/protocol/src/permissions.rs#L2513).
Seatbelt
[checks this effective access](https://github.com/openai/codex/blob/01fc69f4026735edfdf6789820549727a4867b11/codex-rs/sandboxing/src/seatbelt.rs#L610)
before adding protected names. This supports testing an explicit override;
the approved runtime trial below demonstrated this override for the tested
clone. An unsupported override must be reported, not bypassed or rescued with
another grant.

## Frozen preparation and controls

The same fixture is retained at H1 with the r4 task already `ready`, unchanged
index and absent hook marker. No reset or task overwrite occurred. Separate
state/profile/manifest/runner are under its `evidence/git-write-r5`. Existing
regular fetch/unshallow controls retain r4 provenance. Five new separate Git
controls exited zero: depth-one control clone, matching no-write-fetch-head
H0/side fetch and unshallow, and both recovered-object reads. Logs contain
statuses and output hashes; source/control/resource/fixture hashes are frozen.

The runner repeats version/H1 gates, H0/side absence before/after, all five
source-denial probes, regular and no-write-fetch-head fetch/unshallow variants.
It reads/checks the existing ready task, stages only `task.txt`, and attempts a
vetted-hook commit only after staging succeeds. It records final HEAD/index/
task/hook state plus assigned-only tracked diff/status. Source exposure,
recovered objects, unsupported runtime or timeout stops. Fetch transport versus
Git-write failures remain separately interpreted. No setup/server/resume trial
or model inference is included.

## Approved host launch and observed outcomes

Profile SHA256:

```text
4fb41d5db3bec4614942a9604ef9124f4a6decc397a04fa084dafd8c150aaea5
```

Runner SHA256:

```text
782b9810996ccc2676036e47e87dd50c558cea88ef3a382fd68cc1682546d52c
```

The orchestrator ran this exact command from the existing worktree cwd after
independent review and specific host execution approval:

```text
python3 /private/tmp/ataraxia-isolation-git-retry-18092082117a/evidence/git-write-r5/history-probes.py
```

The runner exited zero at 22:16:57–22:17:01 UTC. Its immutable log is
`/private/tmp/ataraxia-isolation-git-retry-18092082117a/evidence/batch-launch-5a9a2b3e8beb4afea2e6c11de3ba276f.jsonl`.
Thirty-second command limits shared five minutes total; prior evidence remains
unchanged.

Runtime/H1 positive controls passed. H0 and side objects were absent before and
after, with actual Git missing-object diagnostics. All five direct source
probes returned permission-denial diagnostics and empty stdout. All four local
fetch/unshallow variants exited 128 with source-repository/remote-read failures,
without the prior FETCH_HEAD write failure. Matching unrestricted controls
passed. Together these support source-access restriction as the fetch failure
explanation; the precise denied syscall was not captured.

Task read/check, staging and commit passed. The vetted hook ran. Final commit
`59160aa20cbdb1698e50913cae08f9c676560dbd` contains only the assigned `task.txt`
change from pending to ready, independently verified by the orchestrator's
commit stat/patch inspection. The cached diff was empty; final status contained
only untracked fixture-owned `hook-marker` and `source-link`. The final index
SHA256 was `835ae931a5290d3c22dcff5b29d6103c67681f40cdbcbb0f55b7acf54c38a25f`.

This demonstrates the bounded deterministic filesystem/history/useful-work
subset under the explicit clone Git-write and entire `/usr` read conditions.
Networking was configured disabled; no endpoint test ran. Setup, model-backed
execution, resume/correction and the custom-agent boundary remain untested.
AC-1/AC-2 remain TODO pending the wider Investigation and recommendation; no
production policy is adopted.
