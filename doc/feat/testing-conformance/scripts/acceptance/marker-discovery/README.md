# Acceptance static marker discovery

Extract only four AST cases from legacy `test_acceptance_coverage.py`: ignore
fenced/other-Work markers, count decorated static candidates, reject unknown
criteria and selected dynamic IDs. Preserve marker identity/errors; discovery
executes no tests. Replace substantial generated Python with named typed
fixtures copied unchanged under `tmp_path`; reuse the report leaf's marker
fixture only if ownership fits. Strictly include only this cleaned subset and
owned fixtures/helpers, not remaining legacy cases. Reuse checker setup; no
framework. Run Make declaration tests after shared changes.

- **AC-1 DONE** Given static test-source arrangements, discovery counts only
  supported decorated candidates for the selected Work and rejects malformed,
  unknown, or dynamic selected marker declarations precisely.

  Validation: review fixture sources and count/error oracles; run marked cases,
  affected Make tests, strict typing, lint/format and doc/ac checks.
