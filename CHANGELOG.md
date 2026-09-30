## v0.1.0 (2026-07-28)

### Feat

- **example**: example crossover strategy with tests
- **cli**: include shard and strategy paths in output file
- **cli**: save results as json to file
- **cli**: display_results function
- **broker**: implement Account `__add__` and `__radd__`
- **cli**: init cli.py module
- **backtest**: backtest_dir; backtest_shard; main backtest entry
- **util**: import_file; is_type; is_sink
- **feature**: Simple Moving Average runner and node
- **feature**: sma pure function
- **feature**: RollingWindow computable node
- **feature**: RollingWindowRunner
- **source**: Generic SourceNode computable
- **source**: generic source runner implementation
- **provider**: require Provider protocol to be hashable
- **provider**: make BarProvider hashable
- **provider**: handle basic error cases
- **provider**: initial bar provider from csv file
- **broker**: basic broker implementation (#6)
- **broker**: broker runner implementation
- **broker**: Position set closing_pnl
- **broker**: PositionError; short position tests
- **broker**: position on_bar take_profit case
- **broker**: position on_bar stop loss case
- **bar**: add within method
- **broker**: initial broker implementation
- **compute**: add sink consumer
- **compute**: add Provider protocol
- **bar**: Bar class instantiate from str mapping
- **comput**: introduce Sink and Source protocols
- computation (#2)
- **di**: compute; rename inject_dependencies to compute_step
- **di**: inject_dependencies
- **di**: instantiate_compute_nodes
- **di**: sort_dependency_tree
- **di**: error cases for compute_dependency_tree
- **di**: first compute_dependency_tree
- **features**: rolling bar spec; sma spec
- **features**: RollingWindowSpec
- **features**: rolling window node
- **features**: init features; current bar specification
- **compute**: initial protocols

### Fix

- **cli**: move result check to main instead of display_results
- **feature**: sma works with 0 in values
- **bar**: tick fractional truncation error
- **provider**: remove newline strip code smell
- **broker**: remove leftover debug print
- **provider**: BarProvider same `__exit__` as protocol
- **broker**: update old positions on signal
- **broker**: position on_bar case when bar gapped
- **broker**: do not use Boolean protocol in broker runner check
- README.md typo
- **compute**: allow for None init_params

### Refactor

- **compute**: source node fully delegates to provider
- **cli**: change CLI invocation; add short help to arguments
- **backtest**: module attribute; dict key as return value
- **backtest**: drop BacktestError on invalid shard directory
- **compute**: Provider managed by orchestrator not compute loop
- **bar**: remove magic number; better docs for Bar class
- **broker**: Position on_bar always return status
- **compute**: multi-source single-sink computable DAG design (#5)
- **compute**: remove old compute implementation
- **compute**: rename protocols.py to protocol.py
- **compute**: remove DependencyMapping from `__init__`
- **compute**: new compute function
- **compute**: change kickstart_runners to prime_catalog
- **compute**: kickstart_runners
- **compute**: introduce ataraxia errors
- **compute**: sort_graph
- **compute**: start moving compute to package
- **test**: remove unneeded computable attributes
- **compute**: rename dependency tree to graph
- **compute**: remove computable implementation and attributes
- **compute**: rename protocols
- **di**: compute_dependency_tree
- **di**: compute_dependency_tree

## v0.0.0 (2026-07-07)
