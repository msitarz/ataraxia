# Selector unit cases

After CLI relocation, clean remaining four selector functions/14 parametrized
cases. Preserve whole accepted selection and all changed/unsupported refusals
with exact errors/causes and complete cache state. Retain single accepted record
read using a scoped signature-compatible filesystem edge only with boundary
justification; restore it after each case. Follow
[parent ownership, sequencing and checks](../README.md).

- **AC-1 DONE** Given accepted, changed or unsupported records, the public
  selector returns only reviewed inputs or precise refusals without cache
  mutation and consumes the accepted record once.

  Validation: Run all marked selector cases; review whole independent oracle and
  read-double boundary/restoration, strict test/fixture includes, Make registry
  checks, lint/format, doc/ac and latest CI.
