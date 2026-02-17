FROM python:3.11-slim

LABEL maintainer="IBM Bob <bob@ibm.com>"
LABEL description="Graph Analytics API Service"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    gremlinpython>=3.7.0 \
    pydantic>=2.0.0 \
    pydantic-settings>=2.1.0 \
    slowapi \
    python-json-logger>=2.0.7 \
    pyjwt>=2.8.0 \
    pyotp>=2.9.0 \
    qrcode[pil]>=7.4.2 \
    opentelemetry-api>=1.26.0 \
    opentelemetry-sdk>=1.26.0 \
    opentelemetry-exporter-jaeger-thrift>=1.21.0 \
    opentelemetry-exporter-otlp-proto-grpc>=1.26.0 \
    opentelemetry-instrumentation-requests>=0.47b0 \
    requests>=2.31.0 \
    python-multipart

# Copy application code
COPY src/python /app/src/python
COPY banking /app/banking

# Set Python path
ENV PYTHONPATH=/app/src/python:/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /var/log/janusgraph && \
    chown -R appuser:appuser /app /var/log/janusgraph

USER appuser

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "src.python.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
