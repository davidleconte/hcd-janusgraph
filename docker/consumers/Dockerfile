FROM python:3.11-slim

LABEL maintainer="David Leconte"
LABEL description="Pulsar Event Consumers for JanusGraph and OpenSearch"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    gremlinpython>=3.6.0,<3.8.0 \
    pulsar-client>=3.0.0 \
    opensearch-py>=2.4.0 \
    sentence-transformers>=2.2.2 \
    pydantic>=2.0.0 \
    python-dotenv>=1.0.0

# Copy application code
COPY banking /app/banking
COPY src /app/src

# Set Python path
ENV PYTHONPATH=/app

# Default command (override in compose)
CMD ["python", "-m", "banking.streaming.graph_consumer"]
