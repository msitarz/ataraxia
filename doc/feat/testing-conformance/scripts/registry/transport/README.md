# Make registry transport support

After imports, extract only RegistryCase/RegistryInputs/ProcessResult, argv
observation, copying and run_registry_target with their three registry fixtures.
Keep script ownership and narrow Make reuse. Explicit disposable process
environment, bounded timeout/capture, precise argv/absence/refusal effects; no
generic runner or selection fixture migration. Follow
[parent ownership, sequencing and checks](../README.md).

- **AC-1 TODO** Given isolated literal and missing-input arrangements, real Make
  transports named arguments safely and preserves marker/destination refusal
  effects.

  Validation: Run the three Make registry cases; review annotated owned
  fixtures/helper/recorder and their strict includes, then registry suite,
  lint/format, doc/ac and latest CI.
