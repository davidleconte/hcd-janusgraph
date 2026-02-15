# JanusGraph Visualizer - Web-based Graph Visualization
# Platform: ARM64 (M1/M2/M3 Mac)

FROM --platform=linux/arm64 node:20-alpine

LABEL maintainer="JanusGraph Visualizer"
LABEL description="Web-based interactive graph visualization for JanusGraph"

WORKDIR /app

# Install git (needed for npm install from GitHub)
RUN apk add --no-cache git curl

# Clone JanusGraph Visualizer
RUN git clone https://github.com/JanusGraph/janusgraph-visualizer.git .

# Install dependencies and build production assets
RUN npm install
RUN npm run build

# Configure connection to JanusGraph server
# The visualizer reads configuration from environment variables
ENV GREMLIN_URL=ws://janusgraph-server:8182/gremlin

# Create non-root user
RUN adduser -D appuser && chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

# Start visualizer
CMD ["npm", "start"]
