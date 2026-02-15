FROM eclipse-temurin:11-jre-jammy

# Install required packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 python3-pip procps curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create HCD user and directories
RUN useradd -m -s /bin/bash hcd && \
    mkdir -p /var/lib/hcd/data \
             /var/lib/hcd/commitlog \
             /var/lib/hcd/saved_caches \
             /var/lib/hcd/hints \
             /var/log/hcd \
             /var/log/cassandra && \
    chown -R hcd:hcd /var/lib/hcd /var/log/hcd /var/log/cassandra

# Copy HCD tarball contents
COPY --chown=hcd:hcd hcd-1.2.3 /opt/hcd

# Set environment variables
ENV HCD_HOME=/opt/hcd \
    PATH=/opt/hcd/bin:$PATH \
    JAVA_HOME=/usr/local/openjdk-11 \
    HCD_DATA_DIR=/var/lib/hcd/data \
    HCD_COMMITLOG_DIR=/var/lib/hcd/commitlog \
    HCD_SAVED_CACHES_DIR=/var/lib/hcd/saved_caches \
    HCD_HINTS_DIR=/var/lib/hcd/hints

# Configure HCD for single-node containerized deployment
RUN sed -i \
        -e "s|^data_file_directories:.*|data_file_directories:\n    - /var/lib/hcd/data|" \
        -e "s|^commitlog_directory:.*|commitlog_directory: /var/lib/hcd/commitlog|" \
        -e "s|^saved_caches_directory:.*|saved_caches_directory: /var/lib/hcd/saved_caches|" \
        -e "s|^hints_directory:.*|hints_directory: /var/lib/hcd/hints|" \
        -e "s|^listen_address:.*|listen_address:|" \
        -e "s|^rpc_address:.*|rpc_address: 0.0.0.0|" \
        -e "s|^# broadcast_rpc_address:.*|broadcast_rpc_address: hcd-server|" \
        -e "s|^# num_tokens:.*|num_tokens: 16|" \
        -e "s|- seeds:.*|- seeds: \"hcd-server\"|" \
        -e "s|^auto_bootstrap:.*|auto_bootstrap: false|" \
        -e "/^auto_bootstrap:/! s|^endpoint_snitch:|auto_bootstrap: false\nendpoint_snitch:|" \
        /opt/hcd/resources/cassandra/conf/cassandra.yaml && \
    sed -i \
        -e 's/^# guardrails:/guardrails:/' \
        -e 's/^  # tombstone_failure_threshold: 100000/  tombstone_failure_threshold: 500000/' \
        /opt/hcd/resources/cassandra/conf/cassandra.yaml

# Expose ports
# 9042: CQL native transport
# 7000: Inter-node communication
# 7001: TLS inter-node communication
# 7199: JMX
# 9160: Thrift client API
EXPOSE 9042 7000 7001 7199 9160

# Switch to hcd user
USER hcd
WORKDIR /opt/hcd

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=5 \
    CMD /opt/hcd/bin/nodetool status || exit 1

# Start HCD
CMD ["/opt/hcd/bin/hcd", "cassandra", "-f"]
