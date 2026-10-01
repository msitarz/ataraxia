# CI scheduling

Return main test evidence even when static checks or the vulnerability audit
fail, while keeping all existing checks necessary before merge.

The [CI test job](../../../../../.github/workflows/ci.yml) depends on the check
job, which includes the network audit. A check or audit failure skips the main
tests although they could supply useful independent evidence.

Remove that unnecessary scheduling dependency. Preserve local verification
before audit in the Make CI entry points and keep the installed-package and
example checks. Update affected descriptions in
[validation policy](../../../../validation.md) if needed.

## Acceptance

- **AC-1 DONE** Main tests, example tests, and installed-package checks can run
  when the static-check job or its network audit fails.
  Verification: inspect the workflow dependency graph and commands; confirm
  independent job scheduling and that a check-job failure cannot skip them.
- **AC-2 DONE** Audit or static-check failure still prevents satisfying the full
  CI merge gate; all previous verification responsibilities remain covered.
  Verification: compare the workflow and Make commands before and after the
  change, review validation policy, and report a full CI run on the PR head.

Keep this change focused on scheduling. Setup recipe changes belong to
[CI preparation](../ci-preparation/README.md).
