# Sandbox isolation Investigation

Can a Codex executor read and commit within a shallow local clone while being
unable to read the source repository or obtain excluded history, including after
a correction resumes the same session?

Follow the [parent's execution gate](../README.md#execution-gate-and-limits).
Compare custom-agent configuration with separately launched `codex exec`
sessions using filesystem permission profiles. Verify installed-client behavior:
parent runtime overrides and legacy sandbox settings may defeat profile
defaults. Use current
[subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)
and [permission documentation](https://learn.chatgpt.com/docs/permissions) as
candidate guidance, not proof of enforcement.

## Trials and decision basis

Use the [bounded feasibility protocol](protocol.md) before executing trials.
Preparation does not complete the acceptance criteria below.

Use a disposable source with a non-secret canary only in an earlier commit,
multiple branches and tags, and a tracked current-tree canary. Prepare depth-one
local clones, verify the expected base, refs, shallow boundary, and absent
object alternates, and remove the source remote. Uncommitted source edits are
not inputs; existing destinations and unexpected bases must fail without
overwriting data. An unrestricted control proves the canaries are readable
before testing denial.

Run deterministic probes through the actual Codex sandbox and a bounded real
executor task with the same configuration. A prompt restriction or mocked access
check is insufficient. Record platform, client version, effective configuration,
commands, statuses, and non-secret outputs. Exercise:

- Allowed clone reads, edits, locked offline setup, project checks, staging,
  and commits, including installed hooks and protected Git paths. Preserve fresh
  environments, cache reuse, readiness checks, and setup-failure recovery.
- Denied source reads through ordinary files, `.git`, `git -C`, explicit old
  object requests, and clone symlinks; direct local fetch and unshallow attempts
  must not recover excluded objects.
- History exposure through caches, session storage, additional workspace roots,
  tools, MCP servers, and connectors; disable bypasses or bound the claim.
- Denied unauthorized remote history fetches and publication; distinguish model
  service connectivity from network available to executor-generated commands.
- The same probes after resume and with conflicting legacy or live parent
  settings; unsupported enforcement must fail closed rather than run
  unrestricted.

Check current-tree answer files and inherited prompt context separately: denied
reads cannot undo information already supplied. Recommend a candidate only if
actual source reads and fetches fail while useful clone work succeeds, and the
boundary survives resume without escalation. Report unavailable measurements and
untested platforms as unknown. If neither candidate works, recommend further
feasibility Work or a separate environment; building a new sandbox is out of
scope.

## Current bounded evidence

The
[standalone B executor and same-UUID resume](standalone-model.md#completed-standalone-b-actual-executor-and-resume)
passed on the declared macOS tiny fixture, including actual denial probes,
task-only commits and vetted hook execution. Earlier failures and condition
corrections remain retained. This uses entire `/usr` read and explicit assigned
clone `.git` writes; it is evidence for the tested condition, not an adopted
production boundary. Custom-agent A, full project setup in a model session,
conflicting overrides, additional sandbox transport variants and broader
network/MCP coverage remain unrun. The separate
[orchestrator-owned commit import](../artifact-delivery/delivery-protocol.md#completed-reviewed-importrebase-and-local-delivery)
passed; that host-side delivery test is distinct from sandbox transport probes.
Acceptance and final recommendation remain incomplete.

## Preservation and reproduction

The maintainer requested one preservation commit and PR with all findings,
failed attempts, evidence and the
[fresh-path successful recipe](successful-recipe.md), with no cleanup commit
yet. This explicit request authorizes the larger preservation review surface; it
is no completion/adoption claim. The [in-repository audit](audit/README.md)
retains inspectable logs, configurations, archived runner text and filtered
actual session/tool/context evidence with source/retained hashes. No
credentials, cache payloads or unrelated session content are included. All
contracts and incomplete criteria remain.

## Acceptance

- **AC-1 TODO** Actual probes and a bounded executor task attempt record whether
  clone work, source denial, and resumed-session enforcement succeed or fail,
  with a control and inspectable settings and outputs. Unsupported execution
  records the failing boundary rather than requiring a successful candidate.
  Validation: rerun the declared fixture probes and inspect canary exposure,
  preparation failure cases, commit output, and resumed-session evidence.
- **AC-2 TODO** A comparison recommends a supported boundary or reports
  infeasibility, accounting for inheritance, legacy settings, hooks, caches,
  alternate tools, network, and evaluation contamination.
  Validation: review candidate pros and cons against observations and confirm
  that every untested boundary is disclosed.

Return the tested configuration and evidence for
[Executor communication](../executor-communication/README.md) and
[Artifact delivery](../artifact-delivery/README.md). Preserve reports and
promote lasting findings under the normal Investigation lifecycle.
