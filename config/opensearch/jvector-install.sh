#!/bin/bash
# JVector Plugin Installation Script
# Installs JVector plugin from Maven Central into OpenSearch

set -e

echo "🔧 Installing JVector plugin..."

# JVector plugin version compatible with OpenSearch 3.0.0
# Check Maven Central for latest: https://central.sonatype.com/artifact/org.opensearch.jvector/jvector-plugin
JVECTOR_VERSION="0.1.0"  # Update to latest stable version
OPENSEARCH_VERSION="3.0.0"

# Download JVector plugin from Maven Central
PLUGIN_URL="https://repo1.maven.org/maven2/org/opensearch/jvector/jvector-plugin/${JVECTOR_VERSION}/jvector-plugin-${JVECTOR_VERSION}.zip"

echo "Downloading JVector plugin v${JVECTOR_VERSION}..."
curl -L -o /tmp/jvector-plugin.zip "${PLUGIN_URL}"

echo "Installing plugin..."
/usr/share/opensearch/bin/opensearch-plugin install file:///tmp/jvector-plugin.zip --batch

echo "✅ JVector plugin installed successfully"

# Clean up
rm /tmp/jvector-plugin.zip

echo "Plugin installation complete"
