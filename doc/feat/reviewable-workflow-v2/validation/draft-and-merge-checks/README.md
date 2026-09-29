# Draft and merge checks

Run checks affected by the change while preparing a draft PR. Require full CI
on the reviewed head before merge. Report failed, pending, reused, and unrun
evidence accurately. Remove the rule requiring local `make ci` before every
small draft; keep focused Conventional Commit subjects and put routine rationale
in the PR.
