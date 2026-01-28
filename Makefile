# File: Makefile
# Created: 2026-01-28T10:37:00.123
# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117
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
	@bash scripts/deployment/build_images.sh

deploy:
	@cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh

test:
	@bash scripts/testing/run_tests.sh

lint:
	@black --check src/ tests/
	@flake8 src/ tests/
	@isort --check-only src/ tests/

clean:
	@bash scripts/deployment/stop_full_stack.sh
	@rm -rf data/exports/*
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
