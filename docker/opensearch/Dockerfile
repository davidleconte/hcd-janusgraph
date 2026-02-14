FROM opensearchproject/opensearch:latest

# Metadata
LABEL maintainer="JanusGraph Demo Team"
LABEL description="OpenSearch with JVector plugin for Vector Search capabilities"

# Use built-in k-NN plugin (already included in OpenSearch)
# No custom plugin installation needed - OpenSearch ships with opensearch-knn
RUN /usr/share/opensearch/bin/opensearch-plugin list
