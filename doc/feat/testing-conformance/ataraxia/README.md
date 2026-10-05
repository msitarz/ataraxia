# Ataraxia testing boundaries

Replace patched product internals with real execution and strengthen independent
results while preserving trading, graph, resource, and user-visible contracts.

The next planning deliveries define bounded leaves within these groups:

- Values: separate Bar, features, positions, and broker contracts; public
  construction, literal outcomes, warm-up/zero values, price equality and gap
  boundaries, and prevention of same-bar exits.
- Input: provider/source contracts using real temporary CSVs, contextual errors,
  complete Bars, and cleanup on exhaustion, failure, and explicit closure.
- Backtest: named real strategy fixtures, followed by real graph result
  selection and invalid-result rejection; remove redundant mocked coverage only
  afterward.
- CLI: unit argument handling, complete acceptance success artifacts, then
  parametrized failure flows proving exit codes and retained output.
- Compute: separate graph/result and lifecycle/binding reviews, retaining small
  hand-written collaborators, real execution, and precise type-contract cases.

Result selection follows strategy fixtures. Acceptance failures follow the
success flow's explicit process helper. Derive sample trades by hand and review
complete golden artifacts; preserve lower-level malformed-input coverage before
reducing duplicate acceptance cases. Sequence shared test/helper edits.
