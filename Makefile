.PHONY: help install install-dev lint lint-fix format test test-cov test-fast clean clean-all migrate makemigrations shell security coverage pre-commit-install pre-commit-run docs build

# Default target
help:
	@echo "Available commands:"
	@echo "  install         - Install production dependencies"
	@echo "  install-dev     - Install development dependencies"
	@echo "  lint            - Run ruff linter"
	@echo "  lint-fix        - Run ruff linter and fix issues"
	@echo "  format          - Format code with ruff"
	@echo "  test            - Run all tests"
	@echo "  test-cov        - Run tests with coverage report"
	@echo "  test-fast       - Run tests without coverage (faster)"
	@echo "  clean           - Remove Python cache files"
	@echo "  clean-all       - Remove all cache and build files"
	@echo "  migrate         - Run Django migrations"
	@echo "  makemigrations  - Create Django migrations"
	@echo "  shell           - Open Django shell"
	@echo "  security        - Run security checks with bandit"
	@echo "  coverage        - Generate coverage report"
	@echo "  pre-commit-install - Install pre-commit hooks"
	@echo "  pre-commit-run  - Run pre-commit on all files"
	@echo "  docs            - Generate documentation (if configured)"
	@echo "  build           - Build the project"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

# Code Quality
lint:
	ruff check .

lint-fix:
	ruff check --fix .

format:
	ruff format .

# Testing
test:
	pytest

test-cov:
	pytest --cov=. --cov-report=html --cov-report=term-missing

test-fast:
	pytest -q --tb=short

# Django
migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

shell:
	python manage.py shell

# Security & Quality
security:
	bandit -r . -c pyproject.toml

coverage:
	coverage run -m pytest
	coverage report
	coverage html

# Pre-commit
pre-commit-install:
	pre-commit install

pre-commit-run:
	pre-commit run --all-files

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".ruff_cache" -delete
	find . -type d -name ".mypy_cache" -delete

clean-all: clean
	rm -rf .coverage htmlcov/ .tox/ dist/ build/ *.egg-info/

# Documentation (placeholder - configure as needed)
docs:
	@echo "Documentation generation not yet configured"
	@echo "Consider using Sphinx: pip install sphinx sphinx-rtd-theme"

# Build (placeholder - configure as needed)
build:
	@echo "Build process not yet configured"
	@echo "For packaging: pip install build && python -m build"
