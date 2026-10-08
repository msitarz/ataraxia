# Mechanical PR publisher

Define a reusable `publisher` subagent, using Luna at medium effort, for
mechanical PR push/create/update after the orchestrator has reviewed the exact
artifact and description. The orchestrator retains independent artifact and
description review, acceptance assessment, final-CI assessment, and maintainer
handoff. Publisher execution does not review or merge.

The minimal handoff names the authoritative guidance, worktree, exact reviewed
commit, title, approved description file, and existing PR when updating. The
publisher resolves repository and base from metadata unless the handoff
explicitly overrides them; checks that the local reviewed head and intended
description still match; and stops on remote divergence, refusal, or
uncertainty. A rewrite requires an explicit expected-remote lease. The role
does not commit, edit code or content, merge, comment, or bypass a permission
or review gate. It returns the PR URL, published SHA, CI status, and blockers
concisely. Preserve the full-CI gate.

Update `doc/pull-requests.md` as the publication owner and add a short route in
`doc/orchestrator.md`; keep detailed procedure in the owner. Inspect WDR 17
before changing its publication responsibility. If the durable policy changes
that decision, reserve WDR 19 (after cleanup's reserved WDR 18) and add the
reciprocal amendment metadata only when warranted. Do not change global leaf
executor policy or claim cost savings. The explicitly authorized publisher
pilot for this planning PR is separate from durable-guidance acceptance.

- **AC-1 TODO** Given an approved reviewed head and description, guidance
  bounds publication to mechanical actions, verifies exact inputs, stops on
  divergence or uncertainty, and returns inspectable publication state without
  weakening review or CI authority.

  Validation: manually inspect the handoff and refusal boundaries against the
  current PR owner, orchestrator responsibilities, WDR 17, and maintainer gates.
