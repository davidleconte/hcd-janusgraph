#!/bin/bash
# ==============================================================================
# Demo Quick Start Script
# ==============================================================================
#
# One-command demo deployment: generates passwords, creates .env, and deploys.
#
# ⚠️  WARNING: These are DEMO credentials only. Never use in production!
#
# Usage:
#   ./scripts/deployment/demo_quickstart.sh
#   ./scripts/deployment/demo_quickstart.sh --project my-demo
#
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "${PROJECT_ROOT}/scripts/utils/podman_connection.sh"

# Default values
PROJECT_NAME="janusgraph-demo"
PODMAN_CONNECTION="${PODMAN_CONNECTION:-}"
PODMAN_CONNECTION="$(resolve_podman_connection "${PODMAN_CONNECTION}")"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project)
            PROJECT_NAME="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "One-command demo deployment."
            echo ""
            echo "Options:"
            echo "  --project NAME      Set project name (default: janusgraph-demo)"
            echo "  --help, -h          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0"
            echo "  $0 --project my-demo-2026"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Change to project root
cd "$PROJECT_ROOT"

# Display header
echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    Demo Quick Start                                          ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${CYAN}🚀 Starting one-command demo deployment...${NC}"
echo ""

# Step 1: Generate passwords
echo -e "${BLUE}Step 1/4: Generating passwords...${NC}"
"$SCRIPT_DIR/setup_demo_env.sh" --project "$PROJECT_NAME" --no-clipboard

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Password generation failed${NC}"
    exit 1
fi

echo ""

# Step 2: Deploy services
echo -e "${BLUE}Step 2/4: Deploying services...${NC}"
cd "$PROJECT_ROOT/config/compose"
bash ../../scripts/deployment/deploy_full_stack.sh

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi

echo ""

# Step 3: Wait for services
echo -e "${BLUE}Step 3/4: Waiting for services to be ready...${NC}"
echo -e "${YELLOW}⏳ This will take approximately 90 seconds...${NC}"

for i in {1..90}; do
    echo -ne "\r   Progress: ["
    for ((j=0; j<i/3; j++)); do echo -n "="; done
    for ((j=i/3; j<30; j++)); do echo -n " "; done
    echo -ne "] $i/90 seconds"
    sleep 1
done
echo ""

echo ""

# Step 4: Display access information
echo -e "${BLUE}Step 4/4: Verifying services...${NC}"

podman_cmd() {
    podman --remote --connection "$PODMAN_CONNECTION" "$@"
}

# Check if services are running
cd "$PROJECT_ROOT"
SERVICES_RUNNING=true

if ! podman_cmd ps --filter "label=project=$PROJECT_NAME" | grep -q "hcd-server"; then
    echo -e "${YELLOW}⚠️  Warning: HCD server may not be running${NC}"
    SERVICES_RUNNING=false
fi

if ! podman_cmd ps --filter "label=project=$PROJECT_NAME" | grep -q "janusgraph"; then
    echo -e "${YELLOW}⚠️  Warning: JanusGraph may not be running${NC}"
    SERVICES_RUNNING=false
fi

echo ""

# Display completion message
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    Demo Environment Ready!                                   ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

if [ "$SERVICES_RUNNING" = true ]; then
    echo -e "${GREEN}✅ All services deployed successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Some services may still be starting${NC}"
    echo -e "   Check status: podman --remote --connection $PODMAN_CONNECTION ps --filter \"label=project=$PROJECT_NAME\""
fi

echo ""
echo "Access URLs:"
echo -e "  ${CYAN}JanusGraph:${NC}  http://localhost:8182"
echo -e "  ${CYAN}OpenSearch:${NC}  http://localhost:9200"
echo -e "  ${CYAN}Grafana:${NC}     http://localhost:3001"
echo -e "  ${CYAN}Jupyter:${NC}     http://localhost:8888"
echo ""
echo "Credentials:"
echo -e "  ${GREEN}📄 See: demo-credentials.txt${NC}"
echo -e "  ${GREEN}📋 Or: cat demo-credentials.txt${NC}"
echo ""
echo "Useful Commands:"
echo "  # View logs"
echo "  podman logs ${PROJECT_NAME}_janusgraph_1"
echo ""
echo "  # Check service status"
echo "  podman ps --filter \"label=project=$PROJECT_NAME\""
echo ""
echo "  # Stop services"
echo "  cd config/compose && bash ../../scripts/deployment/stop_full_stack.sh"
echo ""
echo -e "${YELLOW}⚠️  Remember: These are DEMO credentials only. Never use in production!${NC}"
echo ""

# Made with Bob
