# Typed reporting arrangements

Own `cli_result_inputs.py` and `fixtures/cli/reporting_expected.json`, including
precise strict inclusion of the helper. Define the retained broker_returns
arrangement with explicit typed Account/Position/Bar values; preserve all entry
and closing fields, realized 30/50 and unrealized -40/0. Arrange closing state
from independent literals rather than deriving expected values through on_bar.
The fixture is input to display/save, not evidence of broker calculation.

Move the existing complete JSON literal into the named expected data artifact.
Its independent account/position fields and null closing state must remain
complete; do not generate it through save_results/asdict or observed output.
Validate loaded JSON at its external boundary without losing fields or exposing
unchecked broad helper types. Leave legacy consumers unchanged until adoption.

- **AC-1 TODO** Given the retained reporting input, precisely typed arrangements
  and independently reviewed complete JSON expectations are available before
  display/serialization consumers, without forward or unchecked dependencies.

  Validation: inspect every retained input/expected field and annotations; run
  strict typing, lint/format, doc/ac checks and legacy compatibility cases.
  Following consumer execution verifies actual reporting, not declarations
  alone.
