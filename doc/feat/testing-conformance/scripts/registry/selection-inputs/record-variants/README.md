# Precise record variants

Own only adaptation of external accepted/variant JSON and the existing seven
named record mutations. Preserve reviewed literal fixtures, all untouched
fields and current serialization/digest behavior. Model and validate only data
needed at this arrangement boundary; do not reproduce full production-record
validation. A recursive JSON model, if chosen, must truthfully represent the
supported JSON values and narrow changed fields before use, without broad
casts or implicit Any. No production API, validator or unrelated fixture
redesign. Follow [parent scope and sequencing](../README.md).

- **AC-1 DONE** Given fresh accepted record copies and each of the seven named
  variants, preparation changes only the named record fields, retains all other
  values and source fixture bytes, and preserves the reviewed acceptance digest
  for accepted input and the changed-byte digest for variant input.

  Validation: Run criterion-marked independent complete record/digest and source
  immutability cases, existing selection and Make registry consumers; review
  precise external adaptation and unchanged variant promises. Include changed
  helpers/tests precisely in strict checking; run lint/format, doc/ac and latest
  full CI. Stop and split if complete delivery exceeds five-minute review.
