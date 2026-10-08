# Package layout and wheel-link contracts

After records, isolate package/layout/link fixtures and layout/wheel-link cases.
Preserve canonical root/origin/name/version/archive and wheel-target promises,
linked-parent/external/missing-link refusals. No inventory/metadata fixture
migration yet. Follow [parent ownership, sequencing and checks](../README.md).

- **AC-1 DONE** Given literal package/link observations, validators accept the
  supported layout and reject each unsafe observation with exact contextual
  errors and causes.

  Validation: Run marked layout/link cases and remaining validators; review
  independent cases and precise fixture inclusion, registry/Make consumers,
  lint/format, doc/ac and latest CI.
