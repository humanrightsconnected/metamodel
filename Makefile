.PHONY: setup clean test lint format help

# Use uv for venv management and package installation
PROJ := metamodel
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
UV := uv

# Windows-compatible commands
ifeq ($(OS),Windows_NT)
	VENV := .venv
	PYTHON := $(VENV)\Scripts\python
	PIP := $(VENV)\Scripts\pip
	ACTIVATE := $(VENV)\Scripts\activate
else
	ACTIVATE := source $(VENV)/bin/activate
endif

help:
	@echo "Available commands:"
	@echo "  make setup    - Create virtual environment and install dependencies"
	@echo "  make test     - Run tests"
	@echo "  make lint     - Run linting"
	@echo "  make format   - Format code"
	@echo "  make clean    - Remove virtual environment and build artifacts"

setup:
	$(UV) venv
	$(UV) pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest -v

lint:
	$(PYTHON) -m flake8 $(PROJ) tests
	$(PYTHON) -m black --check $(PROJ) tests
	$(PYTHON) -m isort --check $(PROJ) tests

format:
	$(PYTHON) -m black $(PROJ) tests
	$(PYTHON) -m isort $(PROJ) tests

clean:
	rm -rf $(VENV) dist build *.egg-info .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete