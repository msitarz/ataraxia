# Package-symlink runtime condition

This separately authorized resource condition follows the
[path-specific diagnostic](runtime-diagnosis.md#actual-diagnostic-outcomes).
The approved host launch repeated the runtime blocker; this condition is closed.
Prior configurations/logs are unchanged.
No model inference or policy adoption is included.

Only three read grants are added: `/usr/local/opt/pcre2`,
`/usr/local/opt/gettext` and `/usr/local/opt/git`. Read-only inspection confirms
these package symlinks target `../Cellar/pcre2/10.48`, `../Cellar/gettext/1.0`
and `../Cellar/git/2.55.0`. These are **package-content read grants**, not
metadata-only permissions. There is no grant to all of `/usr/local/opt` or
`/usr/local/Cellar`. Source/history denial and Git write protection remain.

## Complete requested filesystem rules

The profile retains `extends = ":workspace"`, approval never and command
network disabled. Under the existing retry root, the clone is writable and the
source denied; these are the exact path rules:

```text
:root = deny
:minimal = read
:tmpdir = deny
:slash_tmp = deny
/private/tmp/ataraxia-isolation-git-retry-18092082117a/clone = write
/private/tmp/ataraxia-isolation-git-retry-18092082117a/source = deny
/usr/local/opt/pcre2/lib/libpcre2-8.0.dylib = read
/usr/local/Cellar/pcre2/10.48/lib/libpcre2-8.0.dylib = read
/usr/local/opt/gettext/lib/libintl.8.dylib = read
/usr/local/Cellar/gettext/1.0/lib/libintl.8.dylib = read
/usr/local/opt/git/libexec/git-core/git-upload-pack = read
/usr/local/Cellar/git/2.55.0/libexec/git-core/git-upload-pack = read
/usr/local/Cellar/git/2.55.0/bin/git = read
/usr/local/opt/pcre2 = read
/usr/local/opt/gettext = read
/usr/local/opt/git = read
```

Git protected-path behavior is expected from inheritance, not yet observed.
Effective symlink handling remains an empirical question for this condition.

## Frozen executed launch

The same unchanged H1 fixture is reused: pending task, shallow boundary and
hook match. Current-source and source-HEAD controls are hashed without printing
contents. Source object controls reuse the documented frozen revision evidence.
New artifacts are under `evidence/symlink-runtime-r2` in the retry root, with
separate state/config/manifest/runner. The manifest freezes prior provenance,
package symlink targets, resource hashes, and source-control hashes; the runner
checks them before executing. Requested profile SHA256:

```text
7fb3b23a5d802b8f5fc65d2f130ba241bd7c5a189a13287c87e5909c6e98764a
```

Runner SHA256:

```text
10efb9bb348cf3a18d7ec0264bbc748f07856ce6dd4a229c86c4338b409fb763
```

After independent review and explicit host approval, planned invocation from
the existing worktree cwd is:

```text
python3 /private/tmp/ataraxia-isolation-git-retry-18092082117a/evidence/symlink-runtime-r2/history-probes.py
```

Version and readable-H1 gates run first, then the existing bounded source,
history/fetch and staging/commit probes. Runtime startup success tests whether
this resource condition resolves the blocker; success would not establish the
complete original cause. Each command has a 30-second cap within five minutes
total. Actual missing-object diagnostics require successful H1 control. Source
read, fetch and protected Git-write failures remain separately interpreted;
staging failure skips commit without changing restrictions. Any unsupported
runtime, timeout or exposure stops. No further runtime/resource correction is
implicit in this plan. AC-1/AC-2 remain TODO pending wider Investigation
evidence.

## Actual result and stop

The orchestrator specifically approved and host-executed this runner. Its
retained log under the existing retry root is
`evidence/batch-launch-0deed16ff6134592b7de8a0a226e2745.jsonl`. Preflight passed
and runtime-version again exited 134 with the opt pcre2 library blocked by
sandbox. The runner exited one; every remaining phase was unrun. No further
probe or profile revision followed.

Resolved-file read succeeds while alias read/metadata fails in the prior
diagnostic. Adding named package-directory reads did not resolve Git startup.
This does not establish the complete cause or prove the profile was ignored.
Previous clone edits and direct source-read denial remain valid limited
observations; no full candidate is qualified and protected Git-write behavior
remains unobserved. All prior profiles/manifests/logs are preserved.

The same runtime finding remains after the diagnosis’s one correction; stop
under the
[orchestrator correction rule](../../../../../../orchestrator.md#review-and-return).
This authorized batch has ended. AC-1/AC-2 remain TODO; there is no policy,
performance or model-inference conclusion.

A next separately reviewed candidate could pin resolved Git helper and runtime
library search paths, or use a vetted relocatable runtime in a permitted area.
Changing search paths is a new declared execution/resource condition, not a
continuation implicitly authorized here. A different supported environment is
the other candidate. Neither is implemented. Do not rescue this condition with
a broad `/usr/local/opt` grant; obtain reviewed steering before further work.

The user authorized subsequent matching-version
[source inspection](source-analysis.md); it adds explanation, not another trial
or runtime permission condition.
