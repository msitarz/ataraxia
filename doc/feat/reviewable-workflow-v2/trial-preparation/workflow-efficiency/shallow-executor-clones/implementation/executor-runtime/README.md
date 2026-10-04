# Restrictive executor start and resume

Depend on [clone readiness](../clone-preparation/README.md). Own optional
standalone executor launch/control using the
[tested condition](../../sandbox-isolation/successful-recipe.md#requested-profile-and-effective-runtime-review)
and [actual result](../../sandbox-isolation/standalone-model.md).
Fresh private state/auth stays outside child access; no unrelated sessions,
config, rules, skills or tool catalogs are inherited. Host model-service access
is distinct from denied command network access. No new sandbox is implemented.

Keep this leaf within a five-minute review; split before oversized execution.
Automated tests use criterion markers scoped to this README; manual judgments
remain independent review. All criteria are planned, not observed evidence.

## Acceptance

- **AC-1 TODO** A supported pinned macOS runtime starts with strict effective
  configuration: declared /usr read concession and exact Python reads, one
  assigned clone including explicit .git writes, denied
  source/sibling/history/shared-host-temp/network access, approval never and no
  unauthorized tools. Unsupported runtime/configuration fails closed.

  Validation: Criterion-marked gates test config precedence, tool/schema
  rejection, actual allowed controls and denied file/Git/loopback access with
  matched controls; manual independent review validates effective context,
  declared platform restrictions and privacy-safe evidence.
- **AC-2 TODO** The launcher preserves original host TMPDIR while child TMPDIR
  and TMPPREFIX use clone-local scratch, and start/exact UUID resume preserves
  the same boundary and useful committed work with hooks.

  Validation: Criterion-marked shell/temp and lifecycle tests cover heredocs,
  scratch controls, UUID binding, hook invocation and before/after boundaries.
  Before AC-2 can be DONE, require a bounded actual start and exact UUID resume
  through the newly implemented launcher, after deterministic gates pass.
  Freeze prompts/model/effort and obtain applicable maintainer approval before
  execution: at most one initial and one resume, 15 minutes each/shared 30
  minutes including review. Independently review effective boundaries before
  and after useful work in both turns, actual tools/contexts and hook commits;
  initial checkpoint acceptance precedes resume. Deterministic/mocked tests
  and historical evidence alone do not verify the new launcher integration.
  This is a validation plan, not authorization to run models now.
- **AC-3 TODO** Initial output stops at an independent root review checkpoint
  before resume; unexpected access, genuine runtime errors, timeout or changed
  evidence stops without automatic retry, replacement, login, extra grants or
  rescue.

  Validation: Criterion-marked event/checkpoint tests cover normal
  messages, exact startup warning, real errors, forbidden tools, frozen hashes
  and stale review sentinels; manual review accepts initial output before UUID
  resume and final output before import.
