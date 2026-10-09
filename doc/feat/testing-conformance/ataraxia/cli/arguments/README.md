# Argument-only CLI units

After reporting, own new `unit/test_cli_arguments.py`, its typed local argv
arrangements and strict include. Exercise actual main parsing using scoped
sys.argv state: missing sink, missing shards directory, unknown option and help.
Valid-looking paths in refusal inputs must not be opened because parsing exits
first. Preserve supported long/short option names; do not invent parser policy.

Assert SystemExit 2 with distinctive option/usage reasons for refusals; help
exits 0 with the promised options in stdout and empty stderr. Inputs/outputs
stay under disposable state; no subprocess or patched backtest_dir. The existing
`test_main_print_error_and_exit` is a backtest outcome, remains untouched here,
and migrates to a real command failure later.

- **AC-1 DONE** Given parser-only arguments, public main reports exact parser
  exits/options before real work starts, with precise tests and restored process
  state rather than an internal backtest double.

  Validation: review boundary/reasons and normal short/long option handling;
  run this module, reporting and the legacy remainder, plus subtree checks.
