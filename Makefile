# File: Makefile
# Created: 2026-01-28T10:37:00.123
# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
#

.PHONY: help build deploy test clean lint

help:
	@echo "Available commands:"
	@echo "  make build     - Build all Docker images"
	@echo "  make deploy    - Deploy full stack"
	@echo "  make test      - Run test suite"
	@echo "  make lint      - Run code linters"
	@echo "  make clean     - Clean up containers and temp files"

build:
	@cd config/compose && podman-compose -f docker-compose.full.yml build

deploy:
	@cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh

test:
	@bash scripts/testing/run_tests.sh

lint:
	@black --check src/ tests/ banking/ scripts/
	@flake8 src/ tests/ banking/ scripts/ --max-line-length=100
	@isort --check-only src/ tests/ banking/ scripts/

clean:
	@bash scripts/deployment/stop_full_stack.sh
	@rm -rf data/exports/*
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
