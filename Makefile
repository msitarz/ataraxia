.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Usage:"
	@echo "make setup     - setup for development"
	@echo "make test      - run pytest"
	@echo "make lint      - run ruff check"
	@echo "make format    - run ruff format"
	@echo "make typecheck - run pyrefly check"
	@echo "make ci        - run all CI checks, including audit, examples, and wheel smoke test"

.PHONY: setup
setup:
	uv sync
	uv run prek install --hook-type pre-commit --hook-type commit-msg
	@echo "✓ Dev environment ready. Run 'make test' to verify."

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

.PHONY: test
test:
	uv run pytest --cov

.PHONY: ci ci-setup ci-check ci-test ci-examples ci-package
# Setup validates the lockfile; subsequent commands use that exact environment.
ci ci-check ci-test ci-examples ci-package: export UV_NO_SYNC := true
ci: ci-check ci-test ci-examples ci-package

ci-setup:
	uv sync --locked --group dev

ci-check: ci-setup
	uv audit --frozen --preview-features audit
	uv run prek run --all-files check-yaml check-merge-conflict detect-private-key
	uv run ruff check .
	uv run ruff format --check .
	$(MAKE) typecheck

ci-test: ci-setup
	$(MAKE) test

ci-examples: ci-setup
	uv run pytest example/

ci-package: ci-setup
	uv run python script/smoke_installed_package.py

.PHONY: clean
clean:
	rm -rf .venv .ruff_cache .pytest_cache .coverage
