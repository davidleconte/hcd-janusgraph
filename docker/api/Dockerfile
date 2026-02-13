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
    python-multipart

# Copy application code
COPY src/python /app/src/python

# Set Python path
ENV PYTHONPATH=/app/src/python:/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "src.python.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
