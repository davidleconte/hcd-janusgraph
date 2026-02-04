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

# Install dependencies
RUN npm install

# Configure connection to JanusGraph server
# The visualizer reads configuration from environment variables
ENV GREMLIN_URL=ws://janusgraph-server:8182/gremlin

# Expose port
EXPOSE 3000

# Start visualizer
CMD ["npm", "start"]
