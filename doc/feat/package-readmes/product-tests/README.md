# Product test package documentation

Plan ordered bounded leaves: overview; unit; unit/compute; integration;
acceptance; typecheck. Cover `test/ataraxia` and these namespaces, preserving
existing test-type/command guidance. Inventory reusable fixtures/helpers/types
where present; summarize case modules instead of listing individual tests.
Explain intentional-negative expectations and their separate checking route;
link source and testing owners without claiming all legacy tests are strict.

Follow [parent scope, convention and delivery validation](../README.md).

- **AC-1 TODO** Product test readers can navigate each namespace/direct case
  module and understand reusable arrangements, behavior coverage and separate
  runtime/type expectations routes without duplicated testing policy.

  Validation: Merge bounded contracts first; compare filesystem contents and
  owned fixtures/types, review case/source links and preserved
  commands/typecheck limits under parent delivery checks.
