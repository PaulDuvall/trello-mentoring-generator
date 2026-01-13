# Trello Career Planner - Development Makefile
#
# Usage: make [target]
# Run 'make help' to see available commands

.DEFAULT_GOAL := help
SHELL := /bin/bash

# Paths
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest

# Colors
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m

.PHONY: help install test test-cov lint format clean run dry-run setup verify

##@ General

help: ## Show this help message
	@echo ""
	@echo "$(CYAN)Trello Career Planner$(NC) - Development Commands"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make $(GREEN)<target>$(NC)\n\n"} \
		/^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2 } \
		/^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) }' $(MAKEFILE_LIST)
	@echo ""

##@ Setup

install: $(VENV)/bin/activate ## Create venv and install dependencies
	@echo "$(GREEN)[+]$(NC) Environment ready"

$(VENV)/bin/activate: requirements.txt requirements-dev.txt
	@echo "$(CYAN)==>$(NC) Creating virtual environment..."
	python3 -m venv $(VENV)
	$(PIP) install --quiet --upgrade pip
	$(PIP) install --quiet -r requirements-dev.txt
	$(PIP) install --quiet -e .
	touch $(VENV)/bin/activate

##@ Testing

test: install ## Run tests
	@echo "$(CYAN)==>$(NC) Running tests..."
	$(PYTEST) tests/ -v --tb=short

test-cov: install ## Run tests with coverage report
	@echo "$(CYAN)==>$(NC) Running tests with coverage..."
	$(PYTEST) tests/ -v --cov=trello_career_planner --cov-report=term-missing --cov-report=html
	@echo ""
	@echo "$(GREEN)[+]$(NC) Coverage report: htmlcov/index.html"

##@ Code Quality

lint: install ## Run linters (ruff)
	@echo "$(CYAN)==>$(NC) Running linters..."
	$(VENV)/bin/pip install --quiet ruff
	$(VENV)/bin/ruff check src/ tests/

format: install ## Auto-format code (ruff)
	@echo "$(CYAN)==>$(NC) Formatting code..."
	$(VENV)/bin/pip install --quiet ruff
	$(VENV)/bin/ruff format src/ tests/
	$(VENV)/bin/ruff check --fix src/ tests/
	@echo "$(GREEN)[+]$(NC) Code formatted"

##@ Running

run: ## Run the application (use: make run ARGS="--name MyBoard")
	@./run.sh $(ARGS)

dry-run: ## Preview board without creating (no credentials needed)
	@./run.sh --dry-run

setup: ## Show credential setup instructions
	@./run.sh --setup-help

verify: install ## Verify credentials are valid
	@./run.sh --verify-only

##@ Maintenance

clean: ## Remove build artifacts and caches
	@echo "$(CYAN)==>$(NC) Cleaning..."
	rm -rf $(VENV)
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf *.egg-info
	rm -rf dist build
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)[+]$(NC) Clean complete"

clean-all: clean ## Remove everything including .env
	rm -f .env
	@echo "$(YELLOW)[!]$(NC) Removed .env file"
