# CQL Shell Client for HCD Access
# Platform: ARM64 (M1/M2/M3 Mac)
# No Apache Cassandra - HCD only via pip-installed cqlsh

FROM --platform=linux/arm64 eclipse-temurin:11-jre-jammy

LABEL maintainer="HCD CQL Client"
LABEL description="Standalone cqlsh client for HCD access (pip-based, no Cassandra binaries)"

# Install Python 3 and pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install cqlsh and cassandra-driver via pip (no Cassandra download needed)
RUN pip3 install --no-cache-dir cqlsh cassandra-driver

# Set default connection parameters (override at runtime)
ENV CQLSH_HOST=hcd-server
ENV CQLSH_PORT=9042

# Create entrypoint script
RUN echo '#!/bin/bash\n\
if [ $# -eq 0 ]; then\n\
    echo "Starting interactive cqlsh session..."\n\
    exec cqlsh "$CQLSH_HOST" "$CQLSH_PORT"\n\
else\n\
    exec "$@"\n\
fi' > /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["cqlsh"]
