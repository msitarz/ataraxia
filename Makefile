.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Usage:"
	@echo "make setup     - setup for development"
	@echo "make test      - run pytest"
	@echo "make lint      - run ruff check"
	@echo "make format    - run ruff format"
	@echo "make typecheck - run pyrefly check"

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

.PHONY: test
test:
	uv run pytest --cov

.PHONY: ci
ci:
	uv run ruff check .
	uv run ruff format --check .
	uv run pyrefly check
	uv run pytest --cov

.PHONY: clean
clean:
	rm -rf .venv .ruff_cache .pytest_cache .coverage
