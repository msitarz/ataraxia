# Initial static corpus draft

This authored draft awaits independent engineering-owner review. It is not
frozen and does not authorize model trials. The three Python files are source
material stored as data, not runnable project modules. The names below select
24 assessments without specifying their expected judgments.

The source files are newly authored freight-dispatch examples. They are not
extracted from historical incidents and do not establish incident diversity.
The rule files copy the indicated passages from `doc/engineering.md` at base
revision `30155f93e89e47cf0ffb580677277e0ae786eabf`:

- [R1 guidance](r1/rule.txt): lines 144–180.
- [R3 guidance](r3/rule.txt): lines 264–290, with separately delimited context
  from lines 144–180 and the illustration at lines 182–235.
- [R4 guidance](r4/rule.txt): lines 102–112, 170–180, and 292–316, with
  separately delimited context from lines 19, 102–112, and 144–180.

The copies retain exceptions and operation-specific error guidance; no
objective deterministic-tool exclusions have been applied. These copies do not
replace the guidance owner. Counts use Python `splitlines()` and count lines for
which `line.strip()` is nonempty, including comments, docstrings, imports, and
code.

| Rule | Source | Nonblank lines | Selected qualified function names |
| --- | --- | ---: | --- |
| R1 | [Dispatch](r1/dispatch.py.txt) | 364 | `booking_record`, `claim_record`, `consignment_record`, `delivery_record`, `invoice_record`, `quote_record`, `route_record`, `vehicle_record` |
| R3 | [Planning](r3/planning.py.txt) | 301 | `allocate`, `assignment`, `load_sequence`, `next_stops`, `reschedule`, `route_estimate`, `select_offer`, `urgency` |
| R4 | [Ledger](r4/ledger.py.txt) | 381 | `Ledger.add_booking`, `Ledger.add_payment`, `Ledger.allocate`, `Ledger.allocation`, `Ledger.booking`, `Ledger.events`, `Ledger.payment`, `Ledger.set_state` |

Owner review must check realism, applicability, context sufficiency, and the
separately held reference rationales before any freeze.
[Draft packets and prompts](../inputs/preparation.md) are prepared separately.
Call lists, runtime binding, invocation protections, and model trials remain
outside this draft. These authored examples do not complete any Evaluation
acceptance criterion or support a production granularity decision.
