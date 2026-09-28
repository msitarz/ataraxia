.DEFAULT_GOAL := help

# Keep prepared environments writable and reusable inside the agent sandbox.
export UV_CACHE_DIR ?= $(CURDIR)/.cache/uv
export PREK_HOME ?= $(CURDIR)/.cache/prek

.PHONY: help
help:
	@echo "Usage:"
	@echo "make setup     - setup for development"
	@echo "make test      - run pytest"
	@echo "make lint      - run ruff check"
	@echo "make format    - run ruff format"
	@echo "make typecheck - run pyrefly check"
	@echo "make arch-check - run architecture checks"
	@echo "make verify    - run all local CI checks offline (setup required)"
	@echo "make ci        - run all CI checks, including audit, examples, and wheel smoke test"

.PHONY: setup
setup: ci-setup
	uv run --no-sync prek install --hook-type pre-commit --hook-type commit-msg
	@echo "✓ Dev environment ready. Run 'make verify' to verify offline."

.PHONY: lint
lint:
	uv run ruff check . --fix

.PHONY: format
format:
	uv run ruff format .

.PHONY: typecheck
typecheck:
	uv run pyrefly check
	uv run pyrefly check --expectations test/typecheck/*.py

.PHONY: arch-check
arch-check:
	uv run tach check
	uv run tach check-external

.PHONY: test
test:
	uv run pytest --cov

.PHONY: ci ci-setup ci-check ci-test ci-examples ci-package ci-audit
.PHONY: verify verify-setup verify-check verify-test verify-examples verify-package
# Every check uses the prepared environment; only setup may install dependencies.
ci ci-check ci-test ci-examples ci-package verify: export UV_NO_SYNC := true
verify: export UV_OFFLINE := true
verify: verify-setup
	$(MAKE) verify-check verify-test verify-examples verify-package

# Run local evidence before the network-dependent audit, even with make -j.
ci: ci-setup
	$(MAKE) verify
	$(MAKE) ci-audit

ci-setup:
	uv sync --locked --group dev
	uv run --no-sync prek prepare-hooks
	uv build --wheel --out-dir .cache/build

verify-setup:
	uv sync --locked --group dev --check --offline

ci-check: ci-setup
	$(MAKE) verify-check
	$(MAKE) ci-audit

ci-audit:
	uv audit --frozen --preview-features audit

verify-check:
	uv run prek run --all-files check-yaml check-merge-conflict detect-private-key
	uv run ruff check .
	uv run ruff format --check .
	$(MAKE) typecheck
	$(MAKE) arch-check

ci-test: ci-setup
	$(MAKE) verify-test

verify-test:
	$(MAKE) test

ci-examples: ci-setup
	$(MAKE) verify-examples

verify-examples:
	uv run pytest example/

ci-package: ci-setup
	$(MAKE) verify-package

verify-package:
	uv run python script/smoke_installed_package.py

.PHONY: clean
clean:
	rm -rf .venv .ruff_cache .pytest_cache .coverage
