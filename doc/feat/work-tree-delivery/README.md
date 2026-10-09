# Deliver the requested Work tree in one final PR

Extend the existing Work-tree ownership foundation with bounded leaf reviews,
tree-wide decision pauses and one final publication for the requested Work.
Keep the definer name/models and role-policy ownership with the pending
[agent responsibilities Work](../agent-responsibilities/README.md).

## Delivery map

- **TODO** [Planning and escalation](planning/README.md): leaf sizing, contract
  iteration, safe whole-tree pauses and the five-level recommendation.
- **TODO** [Sequential delivery](sequential/README.md): one executor/session and
  accumulating isolated branch for a requested parent's direct leaves.
- **TODO** [Recursive integration](integration/README.md): child-parent
  ownership, dependency-ready parallel subtrees, integration cleanup and final
  publication.
- **TODO** [Visually descriptive contracts](visuals/README.md): proportionate
  before/after relationships, interactions and public API descriptions.

```mermaid
sequenceDiagram
    participant M as Maintainer
    participant T as Requested Work owner
    participant A as Child parent A orchestrator
    participant EA as Executor A
    participant B as Child parent B orchestrator
    participant EB as Executor B
    T->>A: Assign ready subtree and base ref
    T->>B: Assign independent ready subtree and base ref
    par Subtree A
        A->>EA: Implement leaf A1
        EA-->>A: Artifact and evidence
        A->>A: Review and verification/cleanup pair
        A->>EA: Implement dependent leaf A2 after local acceptance
        EA-->>A: Artifact and evidence
        A->>A: Review leaf and parent verification/cleanup pairs
    and Subtree B
        B->>EB: Implement sequential leaves with local reviews
        EB-->>B: Artifacts and evidence
        B->>B: Review leaf and parent verification/cleanup pairs
    end
    alt Maintainer decision or new split needed anywhere
        A-->>T: Escalate decision or split
        T->>A: Pause entire requested tree at safe stopping points
        T->>B: Pause entire requested tree at safe stopping points
        T->>M: Preserve artifacts and request concrete decision
        M-->>T: Decide scope; expanded implementation waits for plan merge
    else Subtrees ready for integration
        A-->>T: Retained contract, commits and evidence
        B-->>T: Retained contract, commits and evidence
        T->>T: Review interfaces/integration; record child cleanup/maps
        T->>T: Complete parent verification/cleanup pair
        T->>M: Publish one final PR; require final-head full CI
        M->>M: Own merge decision
    end
```

Merge these concrete contracts before expanded implementation. Adopt the leaves
in order; the maintainer explicitly authorizes batching their reviewed delivery
in one final requested-Work PR. Each complete leaf, including supporting edits,
still targets a five-minute review. Shared owner/map edits are serial.
Do not reopen the delivered tree-orchestration child in workflow-efficiency.
The sequential trial in PR #257 is seed context, not cost or parallel evidence.
No tool, product, model-policy or automatic legacy-tree reorganization scope.

- **AC-1 TODO** Given adopted owner guidance, requested leaves and parent trees
  retain bounded independent reviews, safe decision pauses and verified linear
  delivery history through one final publication with preserved authority and
  proportionate verified visual descriptions of meaningful changes.

  Validation: independently review the four child outcomes and owner routes
  using leaf-only, direct-leaf parent, nested-parent, escalation and CI-specific
  acceptance examples. Final-head full CI remains the maintainer merge gate.
