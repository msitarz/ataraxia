# Vocabulary guidance

Clarify the existing [vocabulary owner](../../../../../README.md#vocabulary)
so authors reuse the established term for the same concept as often as needed,
rather than varying vocabulary merely to avoid repeating a word. The current
owner requires consistent glossary terms and rejects synonyms that suggest an
undefined distinction; it does not explicitly distinguish repeating a term
from duplicating definitions or instructions.

In [PR 117](https://github.com/msitarz/ataraxia/pull/117), acceptance-tracing
prose described the same Git commit as both a commit and a snapshot. The
[bounded correction](https://github.com/msitarz/ataraxia/commit/0ac0655bd9c9e5f6bf64fd40653ee7c75b41497c)
uses commit consistently. Use this as a review example of one concept retaining
one established term, without implying that every use of snapshot is wrong.

Promote the clarification only in `doc/README.md#vocabulary` and review the
bounded example against it. Preserve the existing
[ownership and duplication rules](../../../../../README.md#placement-and-maintenance):
repeating the same term is distinct from repeating a definition or instruction.
This Work does not authorize a repository-wide rename sweep, new glossary
concepts, terminology bans, a mandatory template, or accepted WDR history edits.

Coordinate overlapping edits to `doc/README.md` with
[Guidance editing](../guidance-editing/README.md), which owns the surrounding
review rule. Sequence actual shared-owner conflicts without making this
clarification depend on unrelated Works. The
[parent map](../README.md#works) tracks this outcome.

## Acceptance

- **AC-1 TODO** The vocabulary owner directs authors to reuse the same
  established term for the same concept as often as necessary, without varying
  it solely to avoid repeated words.
  Verification: inspect the updated owner and review the PR 117 commit/snapshot
  example to confirm that repeated commit wording follows the rule.
- **AC-2 TODO** The clarification distinguishes repeated terms from duplicated
  definitions or instructions and preserves documentation ownership rules.
  Verification: review an example that repeats commit for the same Git object
  and an example that repeats its definition, checking that the former retains
  the term and the latter is consolidated or linked to its owner.
- **AC-3 TODO** The owner clarification and bounded example preserve existing
  meanings, links, anchors, and distinct concepts without broad renaming or
  changes to accepted decisions.
  Verification: independently review the complete diff and bounded example,
  walk the vocabulary and placement links, and run the documentation checks.
