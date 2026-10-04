# Local command-network condition

Completed after independent review and specifically approved host execution.
The [r5 profile](git-write-r5.md) was copied byte-identically, SHA256
`4fb41d5db3bec4614942a9604ef9124f4a6decc397a04fa084dafd8c150aaea5`.
Clone Git writes and entire `/usr` read remain, with source/root/temp denies,
network disabled, approval never and inherited `.codex` protection unchanged.

## Frozen preparation

Artifacts are under
`/private/tmp/ataraxia-isolation-git-retry-18092082117a/evidence/network-r6`.
Hermetic `git clone --bare --no-local` from the disposable source and
`git update-server-info` both exited zero. The new endpoint contains only
disposable committed Git data, not dirty source inputs. Its complete file list
and hashes, profile, runtime/source controls and current clone task/index/hook
hashes are frozen in `plan.json`. Existing fixtures/evidence were not reset or
cleaned. Expected HEAD is `59160aa20cbdb1698e50913cae08f9c676560dbd`.

Plan SHA256:
`fe4f5d166ce7c6e8916487d7bb52d02bcd6b537e5118136847fc301ed8abdb7d`.
Runner SHA256:
`4ffa6dd2fd4e7ce92d4ebe1f7896629aeaf0dbb6dea63ea7ee9b214d71fab5c2`.
The runner verifies this and all declared hashes before binding. It disables
inherited proxy variables in either case, Git global/system config and
credential helpers; `http.proxy` is empty. There is no external authentication.

## Reviewed launch plan

The orchestrator ran this exact command from the existing worktree after
independent review and specific host execution approval:

```text
python3 /private/tmp/ataraxia-isolation-git-retry-18092082117a/evidence/network-r6/network-probes.py
```

The runner owns an in-process HTTP server on `127.0.0.1`, an ephemeral port,
and serves only frozen files. No directory listing or external endpoint is
available. It closes the server and joins its thread with a finite timeout;
accepted sockets have a five-second timeout. No process kill or cleanup runs.
Each command has 30 seconds within a shared five-minute limit.

Runtime/current-commit and before/after missing-object gates precede and follow
regular and `--no-write-fetch-head` HTTP fetches of H0 and side. Each variant
first fetches unrestricted into a fresh control repository and verifies both
objects. A second unrestricted fetch verifies endpoint availability after the
child attempt. Dumb HTTP unshallow is omitted because shallow transfer is not
supported. Control/runtime/timeout failures are inconclusive and stop the batch.

Child success, recovered objects or an observed child HTTP request stops as a
boundary failure. Nonzero exit alone is insufficient: the planned assessment
also requires a connection diagnostic, no child requests, working matching
controls and object absence. It retains exact stderr/argv and output hashes;
precise denied syscalls may remain unknown. Final HEAD/task/index/hook hashes
must remain unchanged. FETCH_HEAD changes are permitted by the profile.

This tests only command-local TCP/HTTP Git transport. Other protocols, remote
services, model/MCP networking, setup, resume and custom-agent boundaries remain
untested. AC-1/AC-2 remain TODO; no production policy is adopted.

## Observed reviewed result

The approved runner exited zero on 2026-10-04 at 06:10:33–06:10:35 UTC. The
immutable log is
`/private/tmp/ataraxia-isolation-git-retry-18092082117a/evidence/network-r6/launch-f85379074d7749b089164cea83301283.jsonl`.
The orchestrator independently reviewed the complete log.

Both matching unrestricted HTTP fetch controls passed before and after their
child attempts; control object reads confirmed H0 and side recovery. Both child
fetch variants exited 128 with a failure to connect to `127.0.0.1` after zero
milliseconds. The server recorded no HTTP requests during either child attempt.
H0 and side remained absent before and after, with valid Git missing-object
diagnostics. HEAD, task, index and hook state were unchanged. The owned server
thread stopped successfully.

Together the working local endpoint controls, connection diagnostics and absent
child requests demonstrate the tested local TCP/HTTP Git boundary under this
profile. The precise denied connect syscall was not captured. This does not
establish GitHub connectivity denial, all network protocols or MCP/model
boundaries. Project setup, model-backed execution/resume and the custom-agent
candidate remain unrun; the model phase has not been authorized.
