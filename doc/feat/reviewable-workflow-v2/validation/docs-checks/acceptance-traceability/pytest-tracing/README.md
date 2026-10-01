# Pytest tracing

Register and document pytest markers that let contributors find tests from
file-scoped acceptance criteria.

## Acceptance

- Register a strict `covers` marker. Each marker uses keyword arguments with a
  repository-relative `work` path to the owning README or spec and an `ac` ID.
  AC IDs are stable and unique within that file.
- Repeat the decorator for each AC a test covers. Include the covered AC text
  in the test docstring.
- Put `TODO` or `DONE` beside each AC, using the same labels as Work maps.
  `TODO` means required test coverage or a stated non-test method is missing.
  `DONE` means tests are implemented and linked, or the method is stated; it
  does not mean tests passed, review approved, or merge is authorized.
- Show how to find matching tests without running them, and how to run them by
  removing `--collect-only`:

  ```sh
  uv run pytest --collect-only -q \
    -m "covers(work='doc/feat/example/README.md', ac='AC-8')"
  ```

- Use pytest and existing targeted-test tooling; do not add Gherkin, another
  runner, or a custom selection plugin.
