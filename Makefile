.PHONY: install dev test lint format clean run help

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install the package in production mode
	pip install -e .

dev: ## Install the package in development mode with dev dependencies
	pip install -e ".[dev]"
	pre-commit install

test: ## Run tests with coverage
	pytest

test-verbose: ## Run tests with verbose output
	pytest -vv

test-fast: ## Run tests in parallel
	pytest -n auto

lint: ## Run linters (flake8, mypy)
	flake8 src/ tests/
	mypy src/

format: ## Format code with black and isort
	black src/ tests/
	isort src/ tests/

format-check: ## Check if code is formatted correctly
	black --check src/ tests/
	isort --check-only src/ tests/

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean ## Build the package
	python -m build

run: ## Run the application (example: make run DOMAIN=example.com)
	d $(DOMAIN)

release: clean build ## Build and upload to PyPI
	twine upload dist/*

release-test: clean build ## Build and upload to TestPyPI
	twine upload --repository testpypi dist/*
