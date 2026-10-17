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
	@echo "Run project tools through Make targets; ARGS narrows target-specific checks."
	@echo "doc-check always checks every active Work, regardless of ARGS."
	@echo "Managed sandbox usage and supported limits: doc/evaluation-sandboxes.md"

singlequote := $(shell echo "'")
# Quote caller selectors as literal, whitespace-separated shell words.
_SHELL_WORDS = $(foreach arg,$(1),'$(subst $(singlequote),'"'"',$(arg))')
# Quote one shell value while preserving embedded spaces and apostrophes.
_SHELL_VALUE = '$(subst $(singlequote),'"'"',$(1))'
# Prevent automatic recursive evaluation of raw commit inputs in child Make processes.
unexport SUBJECT BODY
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

.PHONY: lint lint-check
lint: ## lint and apply fixes; ARGS=paths narrows the files
	uv run ruff check $(_TARGET_PATHS) --fix
	uv run complexipy $(_TARGET_PATHS) --output-format sarif --output .cache/complexipy.sarif

lint-check: ## check lint without fixes; ARGS=paths narrows the files
	uv run ruff check $(_TARGET_PATHS)
	uv run complexipy $(_TARGET_PATHS) --output-format sarif --output .cache/complexipy.sarif
	@printf '%s\n' 'During implementation and before handoff, apply the design questions to changed code and tests. doc/engineering-review.md'

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
	uv run pyrefly check --expectations $(if $(strip $(ARGS)),$(_ARGS),test/*/typecheck/*.py)

.PHONY: arch-check
arch-check: ## check architecture boundaries
	uv run tach check
	uv run tach check-external

.PHONY: doc-check doc-check-mermaid doc-format
doc-check doc-check-mermaid doc-format: export UV_OFFLINE := true
doc-check doc-check-mermaid doc-format: export UV_NO_SYNC := true

_DOC_PATHS = $(_TARGET_PATHS)
_DOC_GRAPH_PATHS = $(if $(strip $(ARGS)),$(_ARGS) . ,.)

doc-check: ## check docs and all Work contracts (read only)
	@uv run rumdl check --no-code-block-tools $(_DOC_GRAPH_PATHS) && \
	  uv run rumdl fmt --check --no-code-block-tools $(_DOC_PATHS) && \
	  $(MAKE) --no-print-directory doc-check-mermaid ARGS=$(call _SHELL_VALUE,$(ARGS)) && \
	  $(MAKE) --no-print-directory work-check ARGS= && \
	  if [ "$(MAKELEVEL)" -eq 0 ]; then printf '%s\n' 'Was the whole affected section reviewed at its owner for duplication and accuracy? doc/README.md#review'; fi

doc-check-mermaid: ## validate selected Mermaid fences; ARGS selects files or directories
	@uv run rumdl check --only-code-block-tools --no-cache $(_DOC_PATHS) && \
	  if [ "$(MAKELEVEL)" -eq 0 ]; then printf '%s\n' 'For meaningful changes: would a Mermaid diagram or before/after visual clarify what changes? doc/work-contract-template.md#visuals'; fi

doc-format: ## format Markdown; ARGS selects files or directories
	@uv run rumdl fmt --no-code-block-tools --config pyproject.toml $(_DOC_PATHS) && \
	  if [ "$(MAKELEVEL)" -eq 0 ]; then printf '%s\n' 'If defining a Work: does its contract solve the underlying problem using inspected existing commands/APIs/helpers? doc/change-rules.md#fix-the-underlying-problem'; fi

.PHONY: work-check
work-check: export UV_OFFLINE := true
work-check: export UV_NO_SYNC := true
work-check: ## check active Work contract structure; ARGS=repo paths selects README files or subtrees
	@uv run python -m script.work_check $(_ARGS)

_TEST_QUALITY_QUESTIONS = Are tests in the right layer/layout? At Work closure, are retained tests project regressions rather than temporary adoption probes? doc/testing.md\#layout-ownership-and-adoption doc/test-ownership.md\#test-ownership\nAre reviewed static fixtures treated as data without redundant validation? doc/testing.md\#treat-test-data-as-data\nDo assertions catch the named defect with independent expectations at the real boundary? doc/testing.md\#what-a-test-proves doc/testing.md\#make-expectations-independent

.PHONY: test
test: ## run full tests with coverage; ARGS=paths runs a focused selection
ifeq ($(strip $(ARGS)),)
	uv run pytest --cov
	@if [ "$(MAKELEVEL)" -eq 0 ]; then printf '%b\n' '$(_TEST_QUALITY_QUESTIONS)'; fi
else
	uv run pytest $(_ARGS)
	@if [ "$(MAKELEVEL)" -eq 0 ]; then printf '%b\n' '$(_TEST_QUALITY_QUESTIONS)'; fi
endif

.PHONY: run deps-lock
run: ## run the project CLI; CLI_ARGS='options and values'
ifeq ($(strip $(CLI_ARGS)),)
	@echo "Set CLI_ARGS to the CLI options to run." >&2
	@exit 2
else
	uv run ataraxia $(_CLI_ARGS)
endif

.PHONY: commit
commit: export ATARAXIA_COMMIT_SUBJECT := $(value SUBJECT)
commit: export ATARAXIA_COMMIT_BODY := $(value BODY)
commit: ## commit staged changes; requires SUBJECT=... [BODY=...]
	@uv run python script/commit_command.py && \
	  if [ "$(MAKELEVEL)" -eq 0 ]; then printf '%s\n' 'If a fundamentally wrong approach was discarded: were it and compensating changes reverted before reimplementation? doc/change-rules.md#fix-the-underlying-problem'; fi

deps-lock: ## update uv.lock after dependency changes
	uv lock

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
	@if [ "$(MAKELEVEL)" -eq 0 ]; then printf '%b\n' '$(_TEST_QUALITY_QUESTIONS)'; fi

verify-examples: ## run example tests offline
	$(MAKE) test ARGS=example/
	@if [ "$(MAKELEVEL)" -eq 0 ]; then printf '%b\n' '$(_TEST_QUALITY_QUESTIONS)'; fi

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
	$(MAKE) verify-setup
	$(MAKE) verify-test
	@if [ "$(MAKELEVEL)" -eq 0 ]; then printf '%b\n' '$(_TEST_QUALITY_QUESTIONS)'; fi

ci-examples: ci-setup ## run CI example tests
	$(MAKE) verify-examples
	@if [ "$(MAKELEVEL)" -eq 0 ]; then printf '%b\n' '$(_TEST_QUALITY_QUESTIONS)'; fi

ci-package: ci-package-setup ## build and smoke-test the installed package
	$(MAKE) verify-package

ci-package-setup:
	uv python install
	uv build --wheel --out-dir .cache/build

##@ Worktrees
# Cleanup selectors are literal values, not recursively expanded Make expressions.
unexport WORKTREE EXPIRE NAME SANDBOX_ROOT
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
	printf '%s\n' 'Before dispatch: does the complete expected leaf change fit a maintainer review in about five minutes? If not, pause to split it or get an explicit larger-review decision from the maintainer. doc/workflow.md#scope-and-sizing doc/workflow.md#decisions-and-new-splits'; \
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

##@ Work review
.PHONY: work-review
work-review: ## review Work sizing and remind owner to publish and deliver PR
	@printf '%s\n' 'Before publication: does the complete leaf diff fit review in about five minutes? If not, pause and ask the maintainer to split it or explicitly approve a larger review. For code or test changes, independently review design judgment on the exact final revision before publication. Then complete reviewed publication via the normal publisher flow and return the PR to the maintainer. doc/workflow.md#scope-and-sizing doc/workflow.md#decisions-and-new-splits doc/engineering-review.md doc/orchestrator.md#review-and-return'

.PHONY: sandbox-create
##@ Evaluation sandboxes
sandbox-create: ## create an independent prepared evaluation sandbox; requires NAME=name [SANDBOX_ROOT=/path]
	@uv run --no-sync python script/sandbox.py create $(call _SHELL_VALUE,$(value NAME)) \
		$(call _SHELL_VALUE,$(CURDIR)) $(call _SHELL_VALUE,$(value SANDBOX_ROOT))
