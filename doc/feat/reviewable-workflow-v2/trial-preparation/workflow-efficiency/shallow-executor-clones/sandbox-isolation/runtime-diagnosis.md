# Bounded runtime diagnosis

The user authorized inspection after the
[repeated runtime blocker](history-batch.md#runtime-read-revision-and-batch-closeout).
The current runtime-read-r1 profile and untouched fixture remain unchanged.
The approved diagnostic completed; no model inference ran.

## Read-only findings

Installed `codex sandbox --help` supports explicit named profile selection,
managed-config inclusion and `--log-denials`, which captures macOS sandbox
denials through `log stream`. `doctor --help` offers a redacted JSON health
report but includes auth/runtime checks; it was not executed. Inspected CLI help
exposes no non-model effective-rule dump. No interactive session/app-server ran.

Permission-only parsing found the dedicated config's exact read grants,
`default_permissions = "isolation"`, approval never, and no legacy sandbox keys.
The state directory contains only its config TOML; the clone has no project
config. `/etc/codex/managed_config.toml` and `/etc/codex/requirements.toml` were
absent. Other managed sources were not enumerated; effective precedence remains
unverified. User/auth configuration contents were not printed.

Current parent environment metadata includes
`CODEX_PERMISSION_PROFILE=:workspace`, `CODEX_SANDBOX=seatbelt` and network
disabled. The host runner will record its own corresponding metadata while
explicitly selecting the unchanged dedicated CODEX_HOME. These values do not
establish which profile rules became effective.

Read-only path inspection found `/usr/local/opt/pcre2` is a directory symlink
to `../Cellar/pcre2/10.48`. Its opt and resolved library file paths identify a
regular read-only file of 602344 bytes. The gettext file resolves to its already
declared Cellar target. Dependencies were inspected in the preceding batch;
no new resource grant is proposed. Fixture task is still pending and H1/hook
hashes match. Metadata/symlink traversal or configuration precedence are
hypotheses, not diagnosed causes. Exact requested grants are known; their
effective presence in the sandbox remains unknown.

## Frozen executed diagnostic

Artifacts are under the existing retry root's `evidence/runtime-diagnosis-r1`.
The frozen plan pins prior profile hashes and contains six sandbox commands:
read one library byte through opt and resolved paths; stat the opt directory;
read its symlink target; stat the resolved file; run pinned Git version with
`--log-denials`. The added flag is diagnostic logging, not a permission change.
Host execution approval must cover this supported logger as well as commands.

Runner SHA256:

```text
35c776bd3d33840120cf2ae2d43845988f3611f89e950c165986d376c2d0fef6
```

After independent review and exact host approval, planned invocation from the
existing worktree cwd is:

```text
python3 /private/tmp/ataraxia-isolation-git-retry-18092082117a/evidence/runtime-diagnosis-r1/diagnose.py
```

The runner verifies frozen plan/config and unchanged fixture before launch.
Each command has a 30-second maximum within a shared three-minute cap. Distinct
exclusive-create records retain statuses, metadata, output hashes and denials;
library bytes are not printed. Read denials are retained as diagnostic outcomes,
not source-isolation claims. Actual sandbox-launch failure or timeout stops.
All prior files/logs are preserved. No profile edits, broader grants, network,
source-canary reads, process cleanup, installs or production changes occur.

Interpret byte reads, metadata and loader diagnostics separately. A library
read success cannot establish dynamic-loader access; metadata denial cannot
prove it caused startup failure. Missing effective-state visibility remains a
limit. Further correction needs the completed evidence and reviewed steering.

## Actual diagnostic outcomes

The orchestrator’s approved host launch exited one at 21:27:10–11 UTC. Its
immutable log is
`evidence/runtime-diagnosis-r1/diagnostic-80f89c6517e9447a91efc4051e15a8ae.jsonl`
under the existing retry root. Profile/fixture preflight passed. Opt-path byte
read was denied with Operation not permitted; the resolved-path byte read
succeeded with one byte. Opt-directory stat was denied; readlink exited one with
empty output. Resolved-file stat succeeded. Git startup still exited 134 with
its opt-library lookup denied; `--log-denials` reported None found. The fixture
was unchanged. These are command outcomes, not a complete effective sandbox-rule
dump; absent logger events do not negate observed denials.

This establishes a path-specific difference. Symlink traversal is a plausible
explanation supported by the differing reads, but complete causation remains
unproven. Honoring the resolved-file read makes wholesale config ignorance
less likely; profile precedence is still not directly inspected.

The user authorized the separately declared
[package-symlink runtime condition](symlink-runtime-r2.md). Its approved host
launch repeated the startup blocker. The authorized diagnosis/correction batch
is closed; prior diagnosis profile and evidence are unchanged.
