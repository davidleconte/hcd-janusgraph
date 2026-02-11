#!/bin/bash
# Rename docs/implementation files to kebab-case

set -e

cd /Users/david.leconte/Documents/Work/Demos/hcd-tarball-janusgraph

echo "Renaming docs/implementation files to kebab-case..."

# Function to convert to kebab-case
to_kebab() {
    echo "$1" | sed 's/_/-/g' | tr '[:upper:]' '[:lower:]'
}

# Get all tracked files with uppercase/underscore in docs/implementation
git ls-files docs/implementation/ | grep -E "[A-Z_]" | while read -r file; do
    dir=$(dirname "$file")
    filename=$(basename "$file")
    new_filename=$(to_kebab "$filename")
    
    if [ "$filename" != "$new_filename" ]; then
        new_path="$dir/$new_filename"
        echo "  $file -> $new_path"
        git mv "$file" "$new_path"
    fi
done

echo "✅ Renaming complete"

# Made with Bob
