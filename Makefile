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
	@echo "Run project tools through Make targets; use ARGS=repo/path for focused checks."

singlequote := '
# Quote caller selectors as literal, whitespace-separated shell words.
_SHELL_WORDS = $(foreach arg,$(1),'$(subst $(singlequote),'"'"',$(arg))')
_ARGS = $(call _SHELL_WORDS,$(ARGS))
_CLI_ARGS = $(call _SHELL_WORDS,$(CLI_ARGS))
_TARGET_PATHS = $(if $(strip $(ARGS)),$(_ARGS),.)
ifneq ($(filter -%,$(ARGS)),)
$(error ARGS accepts paths, not options)
endif

.PHONY: setup
setup: ci-setup ## install development dependencies and hooks
	uv run --no-sync prek install --hook-type pre-commit --hook-type commit-msg
	@echo "✓ Dev environment ready. Run 'make verify' to verify offline."

.PHONY: lint lint-check
# --exit-zero is limited to this advisory-only rule; the normal lint command
# retains its failure behavior and the blocking threshold is 50.
_SIZE_ADVISORY = uv run ruff check --select too-many-statements \
	--config 'lint.pylint.max-statements=25' --exit-zero $(_TARGET_PATHS)
lint: ## lint and apply fixes; reports function-size advice; ARGS=paths narrows the files
	uv run ruff check $(_TARGET_PATHS) --fix
	@echo "Advisory: review functions with more than 25 statements"
	$(_SIZE_ADVISORY)

lint-check: ## check lint without fixes; reports function-size advice; ARGS=paths narrows the files
	uv run ruff check $(_TARGET_PATHS)
	@echo "Advisory: review functions with more than 25 statements"
	$(_SIZE_ADVISORY)

.PHONY: format format-check
format: ## format project files; ARGS=paths narrows the files
	uv run ruff format $(_TARGET_PATHS)

format-check: ## check formatting; ARGS=paths narrows the files
	uv run ruff format --check $(_TARGET_PATHS)

.PHONY: typecheck typecheck-expectations
typecheck: ## type-check source; default also checks all expectations
ifneq ($(strip $(ARGS)),)
	uv run pyrefly check $(_ARGS)
else
	uv run pyrefly check
	$(MAKE) typecheck-expectations ARGS=
endif

typecheck-expectations: ## type-check assertion cases; ARGS=paths narrows the files
	uv run pyrefly check --expectations $(if $(strip $(ARGS)),$(_ARGS),test/typecheck/*.py)

.PHONY: arch-check
arch-check: ## check architecture boundaries
	uv run tach check
	uv run tach check-external

.PHONY: doc-check doc-format
doc-check doc-format: export UV_OFFLINE := true
doc-check doc-format: export UV_NO_SYNC := true

_DOC_PATHS = $(_TARGET_PATHS)
_DOC_GRAPH_PATHS = $(if $(strip $(ARGS)),$(_ARGS) . ,.)

doc-check: ## check Markdown formatting and local links (read only)
	uv run rumdl check $(_DOC_GRAPH_PATHS)
	uv run rumdl fmt --check $(_DOC_PATHS)

doc-format: ## format Markdown; ARGS selects files or directories
	uv run rumdl fmt $(_DOC_PATHS)

.PHONY: test
test: ## run full tests with coverage; ARGS=paths runs a focused selection
ifeq ($(strip $(ARGS)),)
	uv run pytest --cov
else
	uv run pytest $(_ARGS)
endif

.PHONY: run deps-lock
run: ## run the project CLI; CLI_ARGS='options and values'
ifeq ($(strip $(CLI_ARGS)),)
	@echo "Set CLI_ARGS to the CLI options to run." >&2
	@exit 2
else
	uv run ataraxia $(_CLI_ARGS)
endif

deps-lock: ## update uv.lock after dependency changes
	uv lock

.PHONY: ac-collect ac-test
ac-collect: ## collect tests for WORK=path/to/README.md [AC=AC-8]
	uv run python script/acceptance_tests.py collect

ac-test: ## run tests for WORK=path/to/README.md [AC=AC-8]
	uv run python script/acceptance_tests.py test

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
	$(MAKE) lint-check ARGS=
	$(MAKE) format-check ARGS=
	$(MAKE) doc-check ARGS=
	$(MAKE) typecheck ARGS=
	$(MAKE) arch-check
verify-test: ## run tests offline
	$(MAKE) test ARGS=

verify-examples: ## run example tests offline
	$(MAKE) test ARGS=example/

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
