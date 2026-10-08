# Real export and strategy-error failures

After invalid arrangements, own new `integration/test_backtest_exports.py` and
its strict include. Move only `test_backtest_shard_requires_sink_export`, the
four `requires_sink_class` variants and both `preserves_strategy_errors` cases
from integration's legacy module. Copy merged named fixtures; no source editing,
internal doubles or new unchecked helper ownership.

Preserve absent-export ModuleError with exact strategy path and AttributeError
cause; invalid exports require the contextual Sink-class reason and their actual
cause state. Module execution and sink construction preserve AttributeError's
`strategy bug` reason rather than converting it into a missing-export error. Use
exact error types, contractual contextual formatting and independent literals.
Leave result/empty-shard/ordering cases with their owners.

- **AC-1 TODO** Given all seven retained export/error arrangements, real loading
  and construction preserve contextual rejection and underlying strategy errors
  through the actual backtest boundary with precise test/fixture typing.

  Validation: review every old/new variant, reason/path/cause oracle; run this
  module, legacy remainders and the subtree's required checks.
