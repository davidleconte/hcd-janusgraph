FROM opensearchproject/opensearch:latest

# Metadata
LABEL maintainer="JanusGraph Demo Team"
LABEL description="OpenSearch with JVector plugin for Vector Search capabilities"

# Remove conflicting plugins in dependency order
# 1. Remove neural-search (depends on knn)
RUN /usr/share/opensearch/bin/opensearch-plugin remove opensearch-neural-search
# 2. Remove knn (conflicts with jvector)
RUN /usr/share/opensearch/bin/opensearch-plugin remove opensearch-knn

# Install JVector Plugin via Maven Coordinates
# Version 3.4.0.0 matches OpenSearch 3.4.0 (latest)
RUN /usr/share/opensearch/bin/opensearch-plugin install --batch org.opensearch.plugin:opensearch-jvector-plugin:3.4.0.0

# Verify installation
RUN /usr/share/opensearch/bin/opensearch-plugin list
