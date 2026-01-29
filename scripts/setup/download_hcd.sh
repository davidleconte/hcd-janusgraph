#!/bin/bash
# Download HCD on-demand instead of storing in repo
VERSION="${1:-1.2.3}"
URL="https://downloads.datastax.com/hcd/${VERSION}/hcd-${VERSION}-bin.tar.gz"

echo "Downloading HCD ${VERSION}..."
if command -v wget &> /dev/null; then
    wget "$URL" -O "hcd-${VERSION}-bin.tar.gz"
elif command -v curl &> /dev/null; then
    curl -L "$URL" -o "hcd-${VERSION}-bin.tar.gz"
else
    echo "Error: Neither wget nor curl found"
    exit 1
fi

echo "Extracting..."
tar xzf "hcd-${VERSION}-bin.tar.gz"
echo "✓ HCD extracted to hcd-${VERSION}/"
