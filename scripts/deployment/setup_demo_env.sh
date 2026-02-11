#!/bin/bash
# ==============================================================================
# Demo Environment Setup Script
# ==============================================================================
#
# Generates secure passwords and creates .env file for demo environments.
#
# ⚠️  WARNING: These are DEMO credentials only. Never use in production!
#
# Usage:
#   ./scripts/deployment/setup_demo_env.sh
#   ./scripts/deployment/setup_demo_env.sh --project my-demo
#   ./scripts/deployment/setup_demo_env.sh --no-clipboard
#
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Default values
PROJECT_NAME="janusgraph-demo"
USE_CLIPBOARD=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --project)
            PROJECT_NAME="$2"
            shift 2
            ;;
        --no-clipboard)
            USE_CLIPBOARD=false
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --project NAME      Set project name (default: janusgraph-demo)"
            echo "  --no-clipboard      Don't copy credentials to clipboard"
            echo "  --help, -h          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0"
            echo "  $0 --project my-demo-2026"
            echo "  $0 --no-clipboard"
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
echo "║                    Demo Environment Setup                                    ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if .env already exists
if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file already exists${NC}"
    read -p "   Overwrite? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ Aborted${NC}"
        exit 1
    fi
    echo ""
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: python3 is required but not installed${NC}"
    exit 1
fi

# Generate passwords using Python script
echo -e "${BLUE}🔐 Generating secure passwords...${NC}"
python3 "$SCRIPT_DIR/generate_demo_passwords.py" --project "$PROJECT_NAME"

# Check if generation was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Password generation failed${NC}"
    exit 1
fi

# Copy to clipboard if requested (macOS only)
if [ "$USE_CLIPBOARD" = true ]; then
    if command -v pbcopy &> /dev/null; then
        cat demo-credentials.txt | pbcopy
        echo ""
        echo -e "${GREEN}📋 Credentials copied to clipboard (paste with Cmd+V)${NC}"
    elif command -v xclip &> /dev/null; then
        cat demo-credentials.txt | xclip -selection clipboard
        echo ""
        echo -e "${GREEN}📋 Credentials copied to clipboard (paste with Ctrl+V)${NC}"
    else
        echo ""
        echo -e "${YELLOW}ℹ️  Clipboard utility not found (install pbcopy or xclip)${NC}"
    fi
fi

# Display completion message
echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    Setup Complete!                                           ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}✅ .env file created${NC}"
echo -e "${GREEN}✅ Credentials saved to demo-credentials.txt${NC}"
echo ""
echo "Next steps:"
echo "  1. Review credentials: cat demo-credentials.txt"
echo "  2. Deploy services:"
echo "     cd config/compose"
echo "     bash ../../scripts/deployment/deploy_full_stack.sh"
echo "  3. Wait for services to start (90 seconds)"
echo "  4. Access services with credentials from demo-credentials.txt"
echo ""
echo -e "${YELLOW}⚠️  Remember: These are DEMO credentials only. Never use in production!${NC}"
echo ""

# Made with Bob
