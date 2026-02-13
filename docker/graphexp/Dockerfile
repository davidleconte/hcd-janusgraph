# Graphexp - Lightweight Web-based Graph Explorer
# Platform: ARM64 (M1/M2/M3 Mac)

FROM --platform=linux/arm64 python:3.11-slim

LABEL maintainer="Graphexp Graph Explorer"
LABEL description="Lightweight web-based graph exploration for JanusGraph"

WORKDIR /app

# Install git
RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

# Clone Graphexp
RUN git clone https://github.com/bricaud/graphexp.git .

# No Python dependencies needed (pure HTML/JS client-side app)
# Just need HTTP server

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Start simple HTTP server
CMD ["python3", "-m", "http.server", "8080"]
