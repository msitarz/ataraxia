# Initial static corpus draft

This is an authored draft for independent engineering-owner review. It is not
frozen and does not authorize model trials. The three Python files are source
material stored as data, not runnable project modules. The names below select
24 assessments without specifying their expected judgments. A later preparation
step must select and verify C packets, construct and freeze prompts and call
lists, and establish the protocol's invocation and isolation guarantees.

The source files are newly authored freight-dispatch examples. They are not
extracted from historical incidents and do not establish incident diversity.
The rule files copy the indicated passages from `doc/engineering.md` at base
revision `30155f93e89e47cf0ffb580677277e0ae786eabf`: R1 lines 144–180,
R3 lines 264–290, and R4 lines 102–112, 170–180, and 292–316. The copies retain
exceptions and operation-specific error guidance; no deterministic-tool
exclusions have been applied. These copies do not replace the guidance owner.

Counts use Python `splitlines()` and count lines for which `line.strip()` is
nonempty, including comments, docstrings, imports, and code. Owner review must
check realism, applicability, context sufficiency, and reference rationales
before any freeze. These authored examples do not complete any Evaluation
acceptance criterion or support a production granularity decision.

| Rule | Source | Selected qualified function names |
| --- | --- | --- |
| R1 | `r1/dispatch.py.txt` | `booking_record`, `claim_record`, `consignment_record`, `delivery_record`, `invoice_record`, `quote_record`, `route_record`, `vehicle_record` |
| R3 | `r3/planning.py.txt` | `allocate`, `assignment`, `load_sequence`, `next_stops`, `reschedule`, `route_estimate`, `select_offer`, `urgency` |
| R4 | `r4/ledger.py.txt` | `Ledger.add_booking`, `Ledger.add_payment`, `Ledger.allocate`, `Ledger.allocation`, `Ledger.booking`, `Ledger.events`, `Ledger.payment`, `Ledger.set_state` |
