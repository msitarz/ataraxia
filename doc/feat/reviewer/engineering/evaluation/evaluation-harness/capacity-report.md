# Reported model-capacity failures

The [codex-worker issue 48](https://github.com/kaifaty/codex-worker/issues/48),
“Retry a turn once when Codex reports the model is at capacity”, is third-party
reported evidence. Its body was retrieved through the GitHub API by the owning
orchestrator; the underlying CLI captures were not independently verified.
This report is separate from the maintainer-supplied
[quota capture](quota-capture.md).

The reporter described two failures on 19 October 2026, with `turn.failed` or
`error` reporting “Selected model is at capacity. Please try a different model.”
after several minutes of work. The reporter said manual same-thread continuation
succeeded and proposed one retry after 30–60 seconds.

The report motivates considering transient capacity failures, but does not
establish a structured detection interface or that failure occurred before any
semantic result. It does not demonstrate an account-wide or shared five-hour
quota condition. Its same-thread continuation strategy is not the harness
policy:
[AC-7](README.md#ac-7-todo-optional-model-capacity-retries-use-bounded-backoff)
requires eligible fresh independent invocations with bounded backoff and jitter.
No implementation, probe, or model call is established by this report.
