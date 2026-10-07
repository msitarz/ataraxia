# Correct the synthetic scratch witness

The
[renewed attempt](../matched-measurements.md#corrected-final-renewed-attempt-stopped)
passed repository isolation assertions but failed decoding external `xcrun_db`.
Change only the synthetic scratch filename in the named fixture and regression
to avoid the actual dispatch-cache name. Preserve the repository's legitimate
`tmp/xcrun_db`, similarly named witness data, full file snapshots, refs and
registrations, external home/scratch containment and existing covers provenance.
No filename exclusions, weaker snapshots, Git replacement/pinning or production
changes. Follow strict typing and [testing](../../../../testing.md).

The witness must survive subsequent real Git state inspection with deterministic
expected bytes; the regression must still fail the old inside-repository layout.
Merge before [witness-final Evaluation](../witness-final/README.md). One short
fixture-witness review; no measurement or unrelated cleanup.

- **AC-1 TODO** Given a repository snapshot before real Make writes its
  synthetic process scratch witness, subsequent real Git inspection preserves
  deterministic witness bytes outside the repository and complete repository
  files, refs and registrations; the regression detects the old layout.

  Validation: run marked regression, demonstrate intended old-layout failure and
  restore the fix; run scratch/removal/pruning cases and complete Make suite on
  the affected macOS host, strict typing, lint/format, doc/ac checks and
  latest-head full CI. Review unchanged snapshot strength and provenance.
