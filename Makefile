.PHONY: format format-check lint quality install-dev help

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install-dev: ## Install development dependencies
	uv pip install -e ".[dev]"

format: ## Auto-format code with black and isort
	uv run black src/
	uv run isort src/

format-check: ## Check formatting without making changes
	uv run black --check src/
	uv run isort --check-only src/

lint: ## Run flake8 linter
	uv run flake8 src/ --max-line-length 88 --extend-ignore E203,W503

quality: ## Run all quality checks (format-check + lint)
	@echo "=== Checking formatting (black) ==="
	uv run black --check src/
	@echo ""
	@echo "=== Checking import order (isort) ==="
	uv run isort --check-only src/
	@echo ""
	@echo "=== Running linter (flake8) ==="
	uv run flake8 src/ --max-line-length 88 --extend-ignore E203,W503
	@echo ""
	@echo "All quality checks passed!"
