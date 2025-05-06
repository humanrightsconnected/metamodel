.PHONY: setup clean test lint format help

# Use uv for venv management and package installation
PROJ := metamodel
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
UV := uv

# Windows-compatible commands
ifeq ($(OS),Windows_NT)
	PYTHON := $(VENV)\Scripts\python
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
	${ACTIVATE}

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
	@echo "Cleaning project..."
	ifeq ($(OS),Windows_NT)
		if (Test-Path -Path $(VENV)) { rd /s /q $(VENV) }
		if exist dist rd /s /q dist
		if exist build rd /s /q build
		if exist *.egg-info rd /s /q *.egg-info
		if exist .pytest_cache rd /s /q .pytest_cache
	else
		rm -rf $(VENV) dist build *.egg-info .pytest_cache
		find . -type d -name __pycache__ -exec rm -rf {} +
		find . -type f -name "*.pyc" -delete
	endif