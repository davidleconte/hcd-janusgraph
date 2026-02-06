#!/bin/bash
# File: scripts/docs/generate_api_docs.sh
# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS
# Purpose: Generate Python API documentation using pdoc
# Date: 2026-02-06

set -e

# Ensure pdoc is installed
if ! command -v pdoc &> /dev/null; then
    echo "Installing pdoc..."
    pip install pdoc
fi

# Output directory
OUTPUT_DIR="docs/api/generated"
mkdir -p "$OUTPUT_DIR"

echo "Generating API documentation..."

# Generate HTML documentation
pdoc --html --output-dir "$OUTPUT_DIR" --force \
    src/python/client \
    src/python/api \
    src/python/analytics \
    src/python/utils \
    banking/data_generators \
    banking/streaming \
    banking/compliance \
    banking/aml \
    banking/fraud

echo "Documentation generated in $OUTPUT_DIR"
echo "Open $OUTPUT_DIR/index.html in a browser to view"
