# PR review and merge gates

Start each Work branch from current `master` and target its small PR to `master`,
the integration point. Directory ancestry routes context but does not create a
branch dependency. Only an explicit maintainer instruction may base a Work on
another Work and target that Work's branch, for example during a prototype or
rewrite. Identify that exception and its base in the PR.

The PR owns checks, discussion, and rationale; the maintainer reviews its
current revision and performs merges. A larger Work's direction and material
contract changes need explicit approval. Smaller Works within that direction can
proceed to their own review. The parent's Work list on `master` records which
children remain open and which were delivered or abandoned. Consult the PR for
review details when needed; routine status checks do not need a GitHub lookup.
No status field in the child's README or retained Work branch is required.
Delete merged remote and local branches once no dependent stacked PR needs them.
GitHub-approved or manually merged PRs provide durable decisions across
sessions; an available conversation can supply the current session's approval.
