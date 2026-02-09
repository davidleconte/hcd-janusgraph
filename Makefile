# Makefile — unified dev commands
# Usage: make help

.PHONY: help build deploy stop test test-unit test-integration coverage lint format typecheck check clean

help:
	@echo "Available commands:"
	@echo ""
	@echo "  Development:"
	@echo "    make format      - Auto-format code (black + isort)"
	@echo "    make lint        - Run linters (ruff/flake8)"
	@echo "    make typecheck   - Run mypy type checker"
	@echo "    make check       - Run format + lint + typecheck"
	@echo ""
	@echo "  Testing:"
	@echo "    make test        - Run full test suite"
	@echo "    make test-unit   - Run unit tests only"
	@echo "    make test-int    - Run integration tests (requires services)"
	@echo "    make coverage    - Run tests with HTML coverage report"
	@echo ""
	@echo "  Deployment:"
	@echo "    make build       - Build all Docker images"
	@echo "    make deploy      - Deploy full stack"
	@echo "    make stop        - Stop full stack"
	@echo ""
	@echo "  Maintenance:"
	@echo "    make clean       - Remove containers, caches, temp files"
	@echo "    make deps        - Install all dependencies (uv)"

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

format:
	@black src/ tests/ banking/
	@isort src/ tests/ banking/

lint:
	@ruff check src/ tests/ banking/ || flake8 src/ tests/ banking/ --max-line-length=100

typecheck:
	@mypy src/ banking/ --ignore-missing-imports

check: format lint typecheck

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

test:
	@pytest -v -x

test-unit:
	@pytest tests/unit/ -v -x

test-int:
	@pytest tests/integration/ -v

coverage:
	@pytest --cov=src --cov=banking --cov-report=html --cov-report=term-missing -v
	@echo "HTML report: htmlcov/index.html"

# ---------------------------------------------------------------------------
# Deployment
# ---------------------------------------------------------------------------

build:
	@cd config/compose && podman-compose -f docker-compose.full.yml build

deploy:
	@cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh

stop:
	@cd config/compose && bash ../../scripts/deployment/stop_full_stack.sh

# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------

deps:
	@uv pip install -e ".[all]"

clean:
	@bash scripts/deployment/stop_full_stack.sh 2>/dev/null || true
	@rm -rf data/exports/* htmlcov/ .coverage
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
