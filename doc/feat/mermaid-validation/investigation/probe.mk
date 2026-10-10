# Disposable setup reproduction; does not modify project dependencies.
PROBE_ENV ?= /private/tmp/ataraxia-mermaid-probe-reproduction
PROBE_CACHE ?= /private/tmp/ataraxia-mermaid-probe-cache
PYTHON ?= /usr/local/bin/python3.14
.PHONY: setup install info
setup:
	uv venv --python $(PYTHON) $(PROBE_ENV)
install:
	uv pip install --python $(PROBE_ENV)/bin/python --cache-dir $(PROBE_CACHE) mermaidx==0.9.5 quickjs-ng==0.17.0.1 resvg-py==0.5.0 termaid==0.9.0
info:
	$(PROBE_ENV)/bin/mermaidx --info
