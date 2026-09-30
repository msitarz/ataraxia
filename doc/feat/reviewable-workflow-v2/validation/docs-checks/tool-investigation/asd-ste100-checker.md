# ASD-STE100 checker

## Pros

- Python CLI with structured diagnostics and prose rules for vocabulary,
  sentence length, passive voice, and other STE guidance.
- Upstream declares Python `>=3.11`, a `ste100` entry point, and Markdown
  support.

## Cons

- Advertised PyPI package was absent during the probe. This is a distribution
  problem, not proof of incompatibility with uv.
- spaCy and its downloaded language model add provisioning overhead. Python
  3.14 operation, Markdown exclusions, and a source install remain untested.
- Upstream flags redistribution concerns about its derived ASD dictionary and
  rule data. Its checks are unofficial, not proof of STE compliance.

## Probe and decision

On 2026-09-30, uv 0.12.19 on macOS ran this isolated install probe:

```sh
UV_CACHE_DIR=/tmp/ataraxia-ste-uv-cache UV_TOOL_DIR=/tmp/ataraxia-ste-uv-tools \
  uvx --python 3.14 --from asd-ste100-checker ste100 --help
```

It failed with package-not-found resolution. No checker version ran. Defer;
before adoption, test a pinned source revision, model provisioning, and
diagnostics on representative Markdown. It does not replace Markdown formatting
or link validation.

Sources:
[README](https://github.com/sourdough-bread/asd-ste100-checker/blob/main/README.md),
[packaging metadata](https://github.com/sourdough-bread/asd-ste100-checker/blob/main/pyproject.toml).
