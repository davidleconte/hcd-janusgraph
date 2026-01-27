# Graphexp - Lightweight Web-based Graph Explorer
# Platform: ARM64 (M1/M2/M3 Mac)

FROM --platform=linux/arm64 python:3.11-slim

LABEL maintainer="Graphexp Graph Explorer"
LABEL description="Lightweight web-based graph exploration for JanusGraph"

WORKDIR /app

# Install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Clone Graphexp
RUN git clone https://github.com/bricaud/graphexp.git .

# No Python dependencies needed (pure HTML/JS client-side app)
# Just need HTTP server

# Expose port
EXPOSE 8080

# Start simple HTTP server
CMD ["python3", "-m", "http.server", "8080"]
