# Disposable reproduction only; project dependencies/CI remain unchanged.
BASE := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PROBE_ENV ?= /private/tmp/ataraxia-mermaid-reproduce-env
PROBE_CACHE ?= /private/tmp/ataraxia-mermaid-probe-cache
SOURCE ?= /private/tmp/ataraxia-mermaid-reproduce-source
OUT ?= /private/tmp/ataraxia-mermaid-reproduce-output
PYTHON ?= /usr/local/bin/python3.14
.PHONY: source setup build install info run
source:
	git clone https://github.com/genotrance/quickjs-ng.git $(SOURCE)
	git -C $(SOURCE) checkout --detach f2ac026f5105b492b15b331bf1b71bd7a4e9cfb2
	git -C $(SOURCE) submodule update --init --recursive
	git -C $(SOURCE)/upstream-quickjs checkout --detach 6d46d07d04041b40f4f49eaa7fdebe44c314c699
	sed -i.bak 's/^version = "0.12.1.1"/version = "0.17.0.1"/' $(SOURCE)/pyproject.toml
setup:
	uv venv --python $(PYTHON) $(PROBE_ENV)
build:
	uv build --wheel --python $(PYTHON) --cache-dir $(PROBE_CACHE) --build-constraint $(BASE)build-constraints.txt --out-dir $(OUT)/wheels $(SOURCE)
install:
	uv pip install --python $(PROBE_ENV)/bin/python --cache-dir $(PROBE_CACHE) mermaidx==0.9.5 resvg-py==0.5.0 termaid==0.9.0 $(OUT)/wheels/quickjs_ng-0.17.0.1-cp310-abi3-macosx_10_15_universal2.whl
info:
	$(PROBE_ENV)/bin/mermaidx --info
run:
	$(PROBE_ENV)/bin/python $(BASE)probe.py $(OUT)
