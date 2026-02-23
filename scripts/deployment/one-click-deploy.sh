#!/bin/bash
# =============================================================================
# One-Click Deterministic Deployment Script
# =============================================================================
# Purpose: Deploy the project with one command, handling all setup automatically
# Usage:   bash scripts/deployment/one-click-deploy.sh
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== One-Click Deterministic Deployment ===${NC}"
echo ""

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo -e "${RED}Error: Conda not found. Install Miniconda first.${NC}"
    exit 1
fi

# Activate conda environment
source "$(conda info --base)/etc/profile.d/conda.sh" 2>/dev/null || true
conda activate janusgraph-analysis 2>/dev/null || {
    echo -e "${YELLOW}Creating janusgraph-analysis environment...${NC}"
    conda env create -f "${PROJECT_ROOT}/environment.yml"
    conda activate janusgraph-analysis
}

echo -e "${GREEN}Conda environment activated${NC}"

# Check Podman machine
echo -e "${GREEN}Checking Podman machine...${NC}"
MACHINE_STATUS=$(podman machine list 2>/dev/null | grep "podman-machine-default" | awk '{print $4}')
if [ "$MACHINE_STATUS" != "Running" ]; then
    if [ -n "$MACHINE_STATUS" ]; then
        echo -e "${YELLOW}Starting existing Podman machine...${NC}"
        podman machine start || true
    else
        echo -e "${YELLOW}Initializing Podman machine...${NC}"
        podman machine init --cpus 12 --memory 24576 --disk-size 250 --now
    fi
else
    echo -e "${GREEN}Podman machine already running${NC}"
fi

# Get podman connection
PODMAN_CONNECTION="${PODMAN_CONNECTION:-podman-machine-default}"
export PODMAN_CONNECTION
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-janusgraph-demo}"

# Check for port 7000 conflict
if lsof -i :7000 &>/dev/null; then
    echo -e "${YELLOW}Port 7000 in use. Attempting to free...${NC}"
    # Try to kill the process
    PID=$(lsof -ti :7000 2>/dev/null)
    if [ -n "$PID" ]; then
        kill -9 $PID 2>/dev/null || echo "Could not kill process on port 7000"
    fi
fi

# Check and set passwords in .env
echo -e "${GREEN}Setting up environment variables...${NC}"
cd "${PROJECT_ROOT}"

# Update .env with passwords if needed
if grep -q "CHANGE_ME" .env 2>/dev/null; then
    sed -i '' 's/CHANGE_ME_TO_SECURE_PASSWORD_MIN_16_CHARS/JanusGraph2026/g' .env
fi

# Ensure required passwords exist
if ! grep -q "HCD_KEYSTORE_PASSWORD" .env 2>/dev/null; then
    echo "HCD_KEYSTORE_PASSWORD=SecurePass123!Janus" >> .env
fi

# Update config/compose/.env
cd "${PROJECT_ROOT}/config/compose"
if grep -q "CHANGE_ME" .env 2>/dev/null; then
    sed -i '' 's/CHANGE_ME_TO_SECURE_PASSWORD_MIN_16_CHARS/JanusGraph2026/g' .env
fi

# Add required passwords if missing
if ! grep -q "HCD_KEYSTORE_PASSWORD" .env 2>/dev/null; then
    cat >> .env << 'EOF'

# Required for deployment
HCD_KEYSTORE_PASSWORD=SecurePass123!Janus
HCD_TRUSTSTORE_PASSWORD=SecurePass123!Janus
HCD_PASSWORD=JanusGraph2026
JANUSGRAPH_PASSWORD=JanusGraph2026
JANUSGRAPH_TRUSTSTORE_PASSWORD=SecurePass123!Janus
OPENSEARCH_PASSWORD=JanusGraph2026
EOF
fi

cd "${PROJECT_ROOT}"

# Run deterministic deployment
echo -e "${GREEN}Running deterministic deployment...${NC}"
export DEMO_SEED=42
export PYTHONHASHSEED=0

bash scripts/deployment/deterministic_setup_and_proof_wrapper.sh \
    --status-report exports/deterministic-status.json

echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo "Access URLs:"
echo "  Jupyter:     http://localhost:8888"
echo "  JanusGraph: ws://localhost:18182/gremlin"
echo "  OpenSearch: http://localhost:9200"
echo "  Grafana:    http://localhost:3001"
