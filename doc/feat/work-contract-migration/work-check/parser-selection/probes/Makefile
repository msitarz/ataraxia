# SPDX-License-Identifier: Apache-2.0

export UV_CACHE_DIR := /private/tmp/uv-parser-cache

PYTHON ?= /usr/local/opt/python@3.14/bin/python3.14
ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/../../../../../../)
EVIDENCE := $(ROOT)/doc/feat/work-contract-migration/work-check/parser-selection-evidence
PROBE := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/probe.py)
PYROMARK_ENV := /private/tmp/parser-pyromark
MARKDOWN_IT_ENV := /private/tmp/parser-markdownit
CMARKGFM_ENV := /private/tmp/parser-cmarkgfm

.PHONY: setup setup-pyromark setup-markdown-it-py setup-cmarkgfm probe-all \
	probe-pyromark probe-markdown-it-py probe-cmarkgfm

setup: setup-pyromark setup-markdown-it-py setup-cmarkgfm

setup-pyromark:
	uv venv --allow-existing --python "$(PYTHON)" "$(PYROMARK_ENV)"
	uv pip install --python "$(PYROMARK_ENV)/bin/python" "pyromark==0.9.13"

setup-markdown-it-py:
	uv venv --allow-existing --python "$(PYTHON)" "$(MARKDOWN_IT_ENV)"
	uv pip install --python "$(MARKDOWN_IT_ENV)/bin/python" "markdown-it-py==4.2.0"

setup-cmarkgfm:
	uv venv --allow-existing --python "$(PYTHON)" "$(CMARKGFM_ENV)"
	uv pip install --python "$(CMARKGFM_ENV)/bin/python" "cmarkgfm==2025.10.22"

probe-all: probe-pyromark probe-markdown-it-py probe-cmarkgfm

probe-pyromark:
	"$(PYROMARK_ENV)/bin/python" "$(PROBE)" pyromark > "$(EVIDENCE)/pyromark.json"

probe-markdown-it-py:
	"$(MARKDOWN_IT_ENV)/bin/python" "$(PROBE)" markdown-it-py > "$(EVIDENCE)/markdown-it-py.json"

probe-cmarkgfm:
	"$(CMARKGFM_ENV)/bin/python" "$(PROBE)" cmarkgfm > "$(EVIDENCE)/cmarkgfm.json"
