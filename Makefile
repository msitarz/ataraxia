.DEFAULT_GOAL := help

# Keep prepared environments writable and reusable inside the agent sandbox.
export UV_CACHE_DIR ?= $(CURDIR)/.cache/uv
export PREK_HOME ?= $(CURDIR)/.cache/prek

.PHONY: help
##@ Everyday commands
help: ## display this command index
	@awk 'BEGIN { FS = ":.*##" } \
		/^##@/ { if (section++) printf "\n"; printf "%s\n", substr($$0, 5); next } \
		/^[[:alnum:]_.-]+:.*##/ { printf "  make %-18s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo "Prefer Make targets; direct tool invocation is allowed for targeted tests or diagnostics that existing targets do not expose."

.PHONY: setup
setup: ci-setup ## install development dependencies and hooks
	uv run --no-sync prek install --hook-type pre-commit --hook-type commit-msg
	@echo "✓ Dev environment ready. Run 'make verify' to verify offline."

.PHONY: lint
lint: ## lint and automatically apply fixes
	uv run ruff check . --fix

.PHONY: format
format: ## format project files
	uv run ruff format .

.PHONY: typecheck
typecheck: ## run type checks
	uv run pyrefly check
	uv run pyrefly check --expectations test/typecheck/*.py

.PHONY: arch-check
arch-check: ## check architecture boundaries
	uv run tach check
	uv run tach check-external

.PHONY: test
test: ## run tests with coverage
	uv run pytest --cov

.PHONY: clean
clean: ## remove the virtual environment and test/lint caches
	rm -rf .venv .ruff_cache .pytest_cache .coverage

.PHONY: ci ci-setup ci-check ci-test ci-examples ci-package ci-audit
.PHONY: verify verify-setup verify-check verify-test verify-examples verify-package
# Every check uses the prepared environment; only setup may install dependencies.
ci ci-check ci-test ci-examples ci-package: export UV_NO_SYNC := true
verify verify-setup verify-check verify-test verify-examples verify-package: export UV_OFFLINE := true
verify verify-setup verify-check verify-test verify-examples verify-package: export UV_NO_SYNC := true
##@ Offline verification
verify: verify-setup ## run all local checks offline (prepared environment required)
	$(MAKE) verify-check verify-test verify-examples verify-package

verify-setup: ## check the prepared environment without network access
	uv sync --locked --group dev --check --offline

verify-check: ## run static checks offline
	uv run prek run --all-files check-yaml check-merge-conflict detect-private-key
	uv run ruff check .
	uv run ruff format --check .
	$(MAKE) typecheck
	$(MAKE) arch-check
verify-test: ## run tests offline
	$(MAKE) test

verify-examples: ## run example tests offline
	uv run pytest example/

verify-package: ## build and smoke-test a temporary package install
	uv run python script/smoke_installed_package.py

##@ CI entry points (primarily for automation)
# Run local evidence before the network-dependent audit, even with make -j.
ci: ci-setup ## run CI checks, including the network audit
	$(MAKE) verify
	$(MAKE) ci-audit

ci-setup: ## install CI dependencies and prepare build tooling
	uv sync --locked --group dev
	uv run --no-sync prek prepare-hooks
	uv build --wheel --out-dir .cache/build

ci-check: ci-setup ## run CI checks and the network audit
	$(MAKE) verify-check
	$(MAKE) ci-audit

ci-audit: ## run the network-dependent vulnerability audit
	uv audit --frozen --preview-features audit

ci-test: ci-setup ## run the CI test suite
	$(MAKE) verify-test

ci-examples: ci-setup ## run CI example tests
	$(MAKE) verify-examples

ci-package: ci-setup ## build and smoke-test the installed package
	$(MAKE) verify-package
