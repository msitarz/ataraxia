# First preparation attempt

On 2026-10-03, preparation created the disposable root
`/private/tmp/ataraxia-isolation-20261003`, saved a profile and planned
commands, initialized `source`, committed H0 (`9ae44f7`), and created `side`.
The command `git -C /private/tmp/ataraxia-isolation-20261003/source tag H0`
unexpectedly opened an editor instead of completing noninteractively. The
attempted editor cancellation was interrupted. Clone creation and controls did
not start.

No sandbox probe or model session ran. The saved profile is proposed
configuration, not observed effective enforcement. This attempt establishes a
fixture-construction failure only; all access-denial, useful-work, network,
setup, conflict and resume checks remain unrun.

Read-only process inspection later identified the owned tag process (53933) and
its editor (53962). `kill -TERM 53962 53933` failed with operation not
permitted. An escalation request for that command was interrupted/denied;
termination was not confirmed. No retry or alternative cleanup is part of this
protocol. Retain the interrupted fixture and use a fresh path for any authorized
restart, following the
[protocol's preparation gate](protocol.md#conditions-and-preparation).
