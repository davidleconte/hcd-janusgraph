#!/bin/bash
# File: scripts/maintenance/rename_to_kebab_case.sh
# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS
# Purpose: Rename documentation files to kebab-case and update links
# Date: 2026-02-06

set -e

# Function to convert filename to kebab-case
to_kebab_case() {
    local filename="$1"
    # Simply: underscores to hyphens, then lowercase
    echo "$filename" | tr '_' '-' | tr '[:upper:]' '[:lower:]'
}

# Exceptions that should NOT be renamed
EXCEPTIONS="README.md|CHANGELOG.md|LICENSE|CONTRIBUTING.md|CODE_OF_CONDUCT.md|SECURITY.md|AGENTS.md"

# Find all markdown files with uppercase or underscores (excluding exceptions)
find docs -name "*.md" -type f | while read -r file; do
    filename=$(basename "$file")
    dirname=$(dirname "$file")

    # Skip exceptions
    if echo "$filename" | grep -qE "^($EXCEPTIONS)$"; then
        continue
    fi

    # Check if filename needs renaming (has uppercase or underscore)
    if echo "$filename" | grep -qE '[A-Z_]'; then
        new_filename=$(to_kebab_case "$filename")
        new_path="$dirname/$new_filename"

        if [ "$file" != "$new_path" ]; then
            echo "Renaming: $file -> $new_path"
            git mv "$file" "$new_path" 2>/dev/null || mv "$file" "$new_path"
        fi
    fi
done

echo "File renaming complete!"
echo ""
echo "Next step: Update all internal links manually or run link checker"
