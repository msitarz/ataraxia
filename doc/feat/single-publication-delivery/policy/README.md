# Adopt local acceptance and final-head publication

Own the sequence in `doc/acceptance-tracing.md`, publication in
`doc/pull-requests.md`, their concise `doc/orchestrator.md` routes, and the
acceptance-versus-CI evidence distinction in `doc/validation.md`. Avoid
duplicate procedures. Before publishing, perform affected focused validation and
independent artifact/evidence review; mark only actually verified acceptance
DONE in the retained verification commit, then make the separate contract/map
cleanup commit. Independently review both commits and the final description,
publish once, and require full CI on that exact final reviewed head before
maintainer merge consideration. Preserve both commits without squash.

DONE denotes verified acceptance using inspectable available evidence, not
maintainer approval, merge or passed CI. Actual selected local execution can
support behavior acceptance; it cannot claim authoritative passing CI checks
or replace the full mechanical merge gate. Agent summaries alone prove neither.
No unrun method or pending CI becomes evidence. If acceptance explicitly needs
full CI, it remains TODO until actual CI passes; do not remove that contract or
silently waive the method to force the ordinary sequence. Report the conflict
for maintainer steering rather than routinely publishing twice.

Narrowly reconcile the TODO Validation clauses in the active Ataraxia parent,
Compute parent and Compute binding Work: move generic latest-head full-CI
requirements out of behavior-acceptance methods to their existing merge-gate
prose/validation-owner link, preserving all actual behavior/type review methods.
Do this prospectively while criteria remain TODO, then execute their revised
methods. Never rewrite DONE history or weaken a criterion whose actual outcome
is CI-specific. Serialize these shared edits with #254; do not modify its
branch, PR or cleanup state. If additional active conflicts appear, return their
exact scope before expanding this adoption.

Failures or later material corrections still require consolidated same-session
correction, affected criteria back to TODO, refreshed evidence and independent
review. Restore a removed contract when required; publication of a corrected
head requires fresh full CI. One planned publication is not a ban on necessary
corrections or an automatic second CI/publication phase. Keep maintainer
control, role/model boundaries and existing scope/recovery/correction-count
rules.

Add/index WDR 21, coordinated after reserved 18 cleaner, 19 publisher and 20
role routing. It records this consequential sequence and evidence choice;
inspect WDRs 7/9/15/17, amend 15 for local behavior-acceptance evidence and 17
for publication sequencing with reciprocal metadata in the same adoption PR.
Preserve 7's final-head CI gate and 9's observed acceptance/separate cleanup,
accepted history and independent review. Recheck numbering before delivery.
No CI automation, tool/test changes or unrelated workflow implementation.

- **AC-1 TODO** Given revised owners/contracts and WDR metadata, ordinary
  acceptance reaches verified separate commits before one publication, while
  CI-dependent acceptance stays unsupported until observed and all delivery
  paths retain independent review and final-head CI/maintainer merge gates.

  Validation: manually trace ordinary behavior acceptance, an explicit CI
  criterion and a post-cleanup correction through owners and active TODO plans;
  inspect WDR amendments/index, serial scope and preserved authority. Run
  doc-format, doc-check and ac-check.
