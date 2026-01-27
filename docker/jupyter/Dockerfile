# Jupyter Lab with Conda-Forge for JanusGraph Analysis
# Platform: ARM64 (M1/M2/M3 Mac)

FROM --platform=linux/arm64 continuumio/miniconda3:latest

LABEL maintainer="JanusGraph Analysis Environment"
LABEL description="Jupyter Lab with conda-forge, gremlinpython, and graph visualization tools"

# Set working directory
WORKDIR /workspace

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
COPY environment.yml /tmp/environment.yml

# Create conda environment
RUN conda env create -f /tmp/environment.yml && \
    conda clean -afy

# Create workspace directories
RUN mkdir -p /workspace/notebooks /workspace/data /workspace/exports

# Copy sample notebooks (will be created separately)
COPY notebooks/ /workspace/notebooks/

# Set up JupyterLab configuration
RUN conda run -n janusgraph-analysis bash -c "mkdir -p /root/.jupyter && \
    echo \"c.ServerApp.token = ''\" >> /root/.jupyter/jupyter_lab_config.py && \
    echo \"c.ServerApp.password = ''\" >> /root/.jupyter/jupyter_lab_config.py && \
    echo \"c.ServerApp.allow_origin = '*'\" >> /root/.jupyter/jupyter_lab_config.py && \
    echo \"c.ServerApp.ip = '0.0.0.0'\" >> /root/.jupyter/jupyter_lab_config.py"

# Expose Jupyter port
EXPOSE 8888

# Set conda environment activation in bashrc
RUN echo "conda activate janusgraph-analysis" >> /root/.bashrc

# Default command: Start Jupyter Lab
CMD ["conda", "run", "--no-capture-output", "-n", "janusgraph-analysis", "jupyter", "lab", \
     "--ip=0.0.0.0", "--port=8888", "--no-browser", \
     "--allow-root", "--ServerApp.token=''", \
     "--ServerApp.password=''"]
