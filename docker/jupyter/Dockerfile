# Jupyter Lab with Conda-Forge for JanusGraph Analysis
# Platform: ARM64 (M1/M2/M3 Mac)
# Security: Use DEV_MODE=false for production (requires token/password)

ARG DEV_MODE=true

FROM --platform=linux/arm64 continuumio/miniconda3:latest

LABEL maintainer="JanusGraph Analysis Environment"
LABEL description="Jupyter Lab with conda-forge, gremlinpython, and graph visualization tools"

# CRITICAL: Set PYTHONPATH for banking modules (fixes notebook imports)
ENV PYTHONPATH="/workspace:/workspace/banking:/workspace/src/python:$PYTHONPATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    vim \
    curl \
    wget \
    graphviz \
    libgraphviz-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy environment file
COPY docker/jupyter/environment.yml /tmp/environment.yml

# Create conda environment
RUN conda env create -f /tmp/environment.yml && \
    conda clean -afy

# Copy deterministic dependency inputs
COPY pyproject.toml uv.lock requirements.txt /workspace/

# Install Python dependencies from lock-derived requirements
WORKDIR /workspace
RUN awk '!/^numpy==/ && !/^pandas==/ && !/^matplotlib==/' /workspace/requirements.txt > /tmp/requirements.jupyter.txt && \
    conda run -n janusgraph-analysis uv pip install --system -r /tmp/requirements.jupyter.txt && \
    conda run -n janusgraph-analysis uv pip install --system email-validator==2.3.0 && \
    conda run -n janusgraph-analysis python -c "import numpy, pandas, matplotlib, email_validator"

# Create workspace directories
RUN mkdir -p /workspace/notebooks /workspace/data /workspace/exports

# Copy sample notebooks
COPY notebooks/ /workspace/notebooks/

# Set up JupyterLab configuration (DEV_MODE controls security)
# DEV_MODE=true (default): No token/password required (DEVELOPMENT ONLY)
# DEV_MODE=false: Requires token/password (PRODUCTION)
RUN conda run -n janusgraph-analysis bash -c "mkdir -p /root/.jupyter"

# Configure based on DEV_MODE
RUN if [ "$DEV_MODE" = "true" ]; then \
        echo "c.ServerApp.token = ''" >> /root/.jupyter/jupyter_lab_config.py && \
        echo "c.ServerApp.password = ''" >> /root/.jupyter/jupyter_lab_config.py && \
        echo "c.ServerApp.allow_origin = '*'" >> /root/.jupyter/jupyter_lab_config.py; \
    else \
        echo "# Secure mode: token required" >> /root/.jupyter/jupyter_lab_config.py && \
        echo "c.ServerApp.allow_origin = ''" >> /root/.jupyter/jupyter_lab_config.py; \
    fi && \
    echo "c.ServerApp.ip = '0.0.0.0'" >> /root/.jupyter/jupyter_lab_config.py

# Expose Jupyter port
EXPOSE 8888

# Set conda environment activation in bashrc
RUN echo "conda activate janusgraph-analysis" >> /root/.bashrc

# Default command: Start Jupyter Lab
# In production, set JUPYTER_TOKEN env var or use --ServerApp.token=<secure_token>
CMD ["conda", "run", "--no-capture-output", "-n", "janusgraph-analysis", "jupyter", "lab", \
     "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
