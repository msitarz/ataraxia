# PR review and merge gates

Start each unit branch from current `master` and target its small PR to `master`,
the integration point. Directory ancestry routes context but does not create a
branch dependency. Only an explicit maintainer instruction may base a unit on
another unit and target that unit's branch, for example during a prototype or
rewrite. Identify that exception and its base in the PR.

The PR owns checks, discussion, and rationale; the maintainer reviews its
current revision and performs merges. A larger unit's direction and material
contract changes need explicit approval. Small units within that direction can
proceed to their own review. Use local `master` history to find merged work
without status fields in READMEs or repeated GitHub lookups. GitHub-approved or
manually merged PRs provide durable decisions across sessions; an available
conversation can supply the current session's approval.
