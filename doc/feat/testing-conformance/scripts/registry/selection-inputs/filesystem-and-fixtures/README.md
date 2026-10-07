# Filesystem and owned fixtures

After record variants, extract PreparedSelection, literal filesystem setup,
changed-input/collision helpers and their selection-input fixtures using the
precise prerequisite. Keep script ownership and fresh tmp_path arrangements;
annotate/include only extracted helpers, fixtures and changed consumers. Keep
manifest/process observation, single-read doubles and validator fixtures in
place. Follow [parent scope and sequencing](../README.md).

- **AC-1 DONE** Given fresh accepted or damaged named arrangements, selection
  consumers receive precise paths/data, independent accepted digest provenance
  and complete literal file bytes/link targets; changing one arrangement does
  not affect another or shared source fixtures.

  Validation: Run criterion-marked fresh-copy/digest/filesystem isolation cases,
  all existing selection consumers and Make registry cases; independently review
  complete bytes/link targets and fixture ownership, precise strict includes,
  lint/format, doc/ac and latest full CI. Preserve case counts and covers; stop
  and split if complete delivery exceeds five-minute review.
