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

singlequote := $(shell echo "'")
# Quote caller selectors as literal, whitespace-separated shell words.
_SHELL_WORDS = $(foreach arg,$(1),'$(subst $(singlequote),'"'"',$(arg))')
# Quote one shell value while preserving embedded spaces and apostrophes.
_SHELL_VALUE = '$(subst $(singlequote),'"'"',$(1))'
_ARGS = $(call _SHELL_WORDS,$(ARGS))
_CLI_ARGS = $(call _SHELL_WORDS,$(CLI_ARGS))
_TARGET_PATHS = $(if $(strip $(ARGS)),$(_ARGS),.)
ifneq ($(filter -%,$(ARGS)),)
$(error ARGS accepts paths, not options)
endif

.PHONY: setup
setup: ci-setup ## prepare development dependencies, hooks, and build tooling
	uv run --no-sync prek prepare-hooks
	uv run --no-sync prek install --hook-type pre-commit --hook-type commit-msg
	uv build --wheel --out-dir .cache/build
	@echo "✓ Dev environment ready. Run 'make verify' to verify offline."

.PHONY: registry-select
unexport CACHE RECORD PREPARATION_SHA256 DESTINATION
registry-select: export UV_OFFLINE := true
registry-select: export UV_NO_SYNC := true
registry-select: ## validate a reviewed registry cache selection into a new destination

	uv run python script/registry_selection.py \
		--cache $(call _SHELL_VALUE,$(value CACHE)) --record $(call _SHELL_VALUE,$(value RECORD)) \
		--expected $(call _SHELL_VALUE,$(value PREPARATION_SHA256)) \
		--destination $(call _SHELL_VALUE,$(value DESTINATION))

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
	uv run pyrefly check --expectations $(if $(strip $(ARGS)),$(_ARGS),test/ataraxia/typecheck/*.py)

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
	uv run rumdl fmt --config pyproject.toml $(_DOC_PATHS)

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

.PHONY: ac-collect ac-test ac-check
ac-collect: ## collect tests for WORK=path/to/README.md [AC=AC-8]
	uv run python script/acceptance_tests.py collect

ac-test: ## run tests for WORK=path/to/README.md [AC=AC-8]
	uv run python script/acceptance_tests.py test

ac-check: ## validate AC declarations/references (WORK=path/to/README.md)
	uv run python script/acceptance_coverage.py check

.PHONY: clean
clean: ## remove the virtual environment and test/lint caches
	rm -rf .venv .ruff_cache .pytest_cache .coverage

.PHONY: ci ci-setup ci-check-setup ci-check ci-test ci-examples ci-package
.PHONY: ci-package-setup ci-audit
.PHONY: verify verify-setup verify-check verify-test verify-examples verify-package
# Every check uses the prepared environment; only setup may install dependencies.
ci ci-check ci-test ci-examples ci-package: export UV_NO_SYNC := true
verify verify-setup verify-check verify-test verify-examples verify-package: export UV_OFFLINE := true
verify verify-setup verify-check verify-test verify-examples verify-package: export UV_NO_SYNC := true
##@ Offline checks
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
ci: ci-check-setup ## run CI checks, including the network audit
	$(MAKE) verify
	$(MAKE) ci-audit

ci-setup: ## install locked CI dependencies
	uv sync --locked --group dev

ci-check-setup: ci-setup
	uv run --no-sync prek prepare-hooks

ci-check: ci-check-setup ## run CI checks and the network audit
	$(MAKE) verify-check
	$(MAKE) ci-audit

ci-audit: ## run the network-dependent vulnerability audit
	uv audit --frozen --preview-features audit

ci-test: ci-setup ## run the CI test suite
	$(MAKE) verify-test

ci-examples: ci-setup ## run CI example tests
	$(MAKE) verify-examples

ci-package: ci-package-setup ## build and smoke-test the installed package
	$(MAKE) verify-package

ci-package-setup:
	uv python install
	uv build --wheel --out-dir .cache/build

##@ Worktrees
# Cleanup selectors are literal values, not recursively expanded Make expressions.
unexport WORKTREE EXPIRE
.PHONY: worktree-list worktree-remove worktree-prune-preview worktree-prune
worktree-list: ## list linked worktrees, branches, locks, and stale registrations
	git worktree list --porcelain

worktree-remove: ## remove one clean linked worktree; requires WORKTREE=/path (keeps branch)
	@destination=$(call _SHELL_VALUE,$(value WORKTREE)); \
	if [ -z "$$destination" ]; then \
		echo "Usage: make worktree-remove WORKTREE=/path" >&2; exit 2; \
	fi; \
	git worktree remove -- "$$destination"

worktree-prune-preview: ## preview repository-wide stale registration pruning; requires EXPIRE=date
worktree-prune: ## apply repository-wide stale registration pruning; requires EXPIRE=date
worktree-prune-preview worktree-prune:
	@expiry=$(call _SHELL_VALUE,$(value EXPIRE)); \
	if [ -z "$$expiry" ]; then \
		echo "Usage: make $@ EXPIRE=date (repository-wide; use the same expiry for preview and execution)" >&2; exit 2; \
	fi; \
	echo "Repository-wide stale registration cleanup; expiry: $$expiry"; \
	git worktree prune --verbose $(if $(filter worktree-prune-preview,$@),--dry-run) --expire="$$expiry"

.PHONY: worktree-create
worktree-create: ## create a prepared branch worktree; requires WORKTREE=/path BRANCH=work/name
	@set -eu; \
	source=$(call _SHELL_VALUE,$(CURDIR)); destination=$(call _SHELL_VALUE,$(WORKTREE)); branch=$(call _SHELL_VALUE,$(BRANCH)); \
	if [ -z "$$destination" ] || [ -z "$$branch" ]; then \
		echo "Usage: make worktree-create WORKTREE=/path BRANCH=work/name" >&2; exit 2; \
	fi; \
	case "$$destination" in /*) ;; *) destination="$$source/$$destination" ;; esac; \
	if [ -e "$$destination" ] || [ -L "$$destination" ]; then \
		echo "Worktree destination already exists: $$destination" >&2; exit 2; \
	fi; \
	if ! git check-ref-format --branch "$$branch" >/dev/null 2>&1; then \
		echo "Invalid branch name: $$branch" >&2; exit 2; \
	fi; \
	if git -C "$$source" show-ref --verify --quiet "refs/heads/$$branch"; then \
		echo "Branch already exists: $$branch" >&2; exit 2; \
	fi; \
	git -C "$$source" worktree add -b "$$branch" "$$destination" master || exit $$?; \
	if [ -d "$$source/.cache" ]; then \
		mkdir -p "$$destination/.cache"; \
		if ! cp -R "$$source/.cache/." "$$destination/.cache/"; then \
			echo "Cache copy failed; worktree retained at $$destination. Retry by copying .cache contents there, then run make ci-setup UV_OFFLINE=true and make verify-setup." >&2; exit 1; \
		fi; \
	fi; \
	if env -u UV_PROJECT_ENVIRONMENT -u VIRTUAL_ENV -u UV_NO_SYNC -u MAKEFLAGS -u MAKEOVERRIDES -u MFLAGS \
		$(MAKE) --no-print-directory -C "$$destination" ci-setup \
			UV_CACHE_DIR="$$destination/.cache/uv" PREK_HOME="$$destination/.cache/prek" \
			UV_PROJECT_ENVIRONMENT="$$destination/.venv" UV_OFFLINE=true UV_NO_SYNC=false; then \
		:; \
	else \
		status=$$?; echo "Offline setup failed (status $$status); worktree retained at $$destination. Repair its .cache or provide the missing cached artifact, then run make ci-setup UV_OFFLINE=true and make verify-setup." >&2; exit $$status; \
	fi; \
	if env -u UV_PROJECT_ENVIRONMENT -u VIRTUAL_ENV -u UV_NO_SYNC -u MAKEFLAGS -u MAKEOVERRIDES -u MFLAGS \
		$(MAKE) --no-print-directory -C "$$destination" verify-setup \
			UV_CACHE_DIR="$$destination/.cache/uv" PREK_HOME="$$destination/.cache/prek" \
			UV_PROJECT_ENVIRONMENT="$$destination/.venv" UV_OFFLINE=true UV_NO_SYNC=true; then \
		:; \
	else \
		status=$$?; echo "Environment check failed (status $$status); worktree retained at $$destination. Repair its environment, then run make verify-setup there." >&2; exit $$status; \
	fi; \
	echo "✓ Worktree ready: $$destination (branch $$branch)"
