# Demo Setup Guide - Quick Password Generation

**Date:** 2026-02-11  
**Purpose:** Streamline demo setup with automated password generation  
**Status:** Implementation Plan

---

## Problem Statement

The Phase 1 security fixes require explicit password configuration, which creates friction for demo scenarios. We need a streamlined process that:

1. Generates secure passwords automatically
2. Populates them in all required locations
3. Displays them clearly for copy/paste during demos
4. Maintains security while being demo-friendly

---

## Solution Design

### 1. Demo Setup Script

**File:** `scripts/deployment/setup_demo_env.sh`

**Features:**
- Generates cryptographically secure passwords
- Creates `.env` file from template
- Populates all password fields automatically
- Displays passwords in formatted table
- Saves passwords to `demo-credentials.txt` (gitignored)
- Optional: Copies passwords to clipboard

**Usage:**
```bash
# Quick demo setup (generates all passwords)
./scripts/deployment/setup_demo_env.sh

# Custom project name
./scripts/deployment/setup_demo_env.sh --project janusgraph-demo-2026

# Skip clipboard copy
./scripts/deployment/setup_demo_env.sh --no-clipboard
```

**Output:**
```
╔══════════════════════════════════════════════════════════════╗
║          Demo Environment Setup Complete                      ║
╚══════════════════════════════════════════════════════════════╝

Generated Passwords (saved to demo-credentials.txt):

┌─────────────────────────────────────┬──────────────────────────────────┐
│ Service                             │ Password                         │
├─────────────────────────────────────┼──────────────────────────────────┤
│ OPENSEARCH_INITIAL_ADMIN_PASSWORD   │ Xy9#mK2$pL4@nQ8!vR3%wT7&zU1^aB5  │
│ JANUSGRAPH_PASSWORD                 │ Cd6*fG8@hJ2#kL4$mN9!pQ3%rS7&tU1  │
│ HCD_KEYSTORE_PASSWORD               │ Vw5^xY9*zA3@bC7#dE1$fG5!hJ9%kL3  │
│ GRAFANA_ADMIN_PASSWORD              │ Mn2&pQ6*rS0@tU4#vW8$xY2!zA6%bC0  │
└─────────────────────────────────────┴──────────────────────────────────┘

✅ .env file created and configured
✅ Passwords saved to demo-credentials.txt
✅ Passwords copied to clipboard (paste with Cmd+V)

Next steps:
1. Review demo-credentials.txt
2. Deploy: cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh
3. Access services with credentials above
```

### 2. Python Password Generator

**File:** `scripts/deployment/generate_demo_passwords.py`

**Features:**
- Generates passwords meeting security requirements (12+ chars, mixed case, numbers, symbols)
- Validates against forbidden patterns
- Creates `.env` file from template
- Generates `demo-credentials.txt` with formatted output
- Optional JSON export for automation

**Usage:**
```bash
# Generate passwords and create .env
python scripts/deployment/generate_demo_passwords.py

# Generate and export to JSON
python scripts/deployment/generate_demo_passwords.py --format json --output demo-creds.json

# Custom password length
python scripts/deployment/generate_demo_passwords.py --length 24
```

### 3. Quick Start Script

**File:** `scripts/deployment/demo_quickstart.sh`

**Features:**
- One-command demo setup
- Generates passwords
- Creates .env file
- Deploys full stack
- Displays access URLs and credentials

**Usage:**
```bash
# Complete demo setup in one command
./scripts/deployment/demo_quickstart.sh

# Output:
# 1. Generating passwords...
# 2. Creating .env file...
# 3. Deploying services...
# 4. Waiting for services to be ready...
# 5. Demo environment ready!
```

---

## Implementation Plan

### Step 1: Create Password Generator Script (Python)

```python
#!/usr/bin/env python3
"""
Demo Password Generator
Generates secure passwords for demo environments.
"""

import secrets
import string
from pathlib import Path
from typing import Dict

def generate_secure_password(length: int = 32) -> str:
    """Generate cryptographically secure password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # Ensure password meets requirements
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(c in "!@#$%^&*" for c in password)
    
    if not (has_upper and has_lower and has_digit and has_symbol):
        return generate_secure_password(length)  # Regenerate
    
    return password

def generate_all_passwords() -> Dict[str, str]:
    """Generate passwords for all services."""
    return {
        "OPENSEARCH_INITIAL_ADMIN_PASSWORD": generate_secure_password(32),
        "JANUSGRAPH_PASSWORD": generate_secure_password(32),
        "HCD_KEYSTORE_PASSWORD": generate_secure_password(32),
        "HCD_TRUSTSTORE_PASSWORD": generate_secure_password(32),
        "JANUSGRAPH_KEYSTORE_PASSWORD": generate_secure_password(32),
        "JANUSGRAPH_TRUSTSTORE_PASSWORD": generate_secure_password(32),
        "GRAFANA_ADMIN_PASSWORD": generate_secure_password(32),
        "SMTP_PASSWORD": generate_secure_password(32),
    }

def create_env_file(passwords: Dict[str, str], project_name: str = "janusgraph-demo"):
    """Create .env file from template with generated passwords."""
    env_template = Path(".env.example").read_text()
    
    # Replace placeholders with generated passwords
    env_content = env_template
    for key, value in passwords.items():
        # Replace placeholder patterns
        env_content = env_content.replace(
            f"{key}=YOUR_SECURE_PASSWORD_HERE_MINIMUM_12_CHARACTERS",
            f"{key}={value}"
        )
        env_content = env_content.replace(
            f"{key}=changeit",
            f"{key}={value}"
        )
    
    # Set project name
    env_content = env_content.replace(
        "COMPOSE_PROJECT_NAME=janusgraph-demo",
        f"COMPOSE_PROJECT_NAME={project_name}"
    )
    
    Path(".env").write_text(env_content)

def save_credentials_file(passwords: Dict[str, str]):
    """Save passwords to demo-credentials.txt."""
    output = []
    output.append("=" * 70)
    output.append("DEMO CREDENTIALS - GENERATED " + datetime.now().isoformat())
    output.append("=" * 70)
    output.append("")
    output.append("⚠️  WARNING: These are demo credentials. Do not use in production!")
    output.append("")
    
    for key, value in passwords.items():
        output.append(f"{key:40s} = {value}")
    
    output.append("")
    output.append("=" * 70)
    
    Path("demo-credentials.txt").write_text("\n".join(output))

def display_credentials(passwords: Dict[str, str]):
    """Display credentials in formatted table."""
    print("\n" + "=" * 70)
    print("DEMO CREDENTIALS GENERATED")
    print("=" * 70)
    print("")
    
    for key, value in passwords.items():
        print(f"{key:40s} : {value}")
    
    print("")
    print("✅ Saved to: demo-credentials.txt")
    print("=" * 70)

if __name__ == "__main__":
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Generate demo passwords")
    parser.add_argument("--project", default="janusgraph-demo", help="Project name")
    parser.add_argument("--length", type=int, default=32, help="Password length")
    args = parser.parse_args()
    
    print("Generating secure passwords...")
    passwords = generate_all_passwords()
    
    print("Creating .env file...")
    create_env_file(passwords, args.project)
    
    print("Saving credentials...")
    save_credentials_file(passwords)
    
    display_credentials(passwords)
    
    print("\nNext steps:")
    print("1. Review demo-credentials.txt")
    print("2. Deploy: cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh")
```

### Step 2: Create Bash Wrapper Script

```bash
#!/bin/bash
# Demo Environment Setup Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          Demo Environment Setup                               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if .env already exists
if [ -f ".env" ]; then
    read -p "⚠️  .env file exists. Overwrite? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Generate passwords
python3 scripts/deployment/generate_demo_passwords.py "$@"

# Copy to clipboard (macOS)
if command -v pbcopy &> /dev/null; then
    cat demo-credentials.txt | pbcopy
    echo "✅ Credentials copied to clipboard"
fi

echo ""
echo "Demo environment ready!"
```

### Step 3: Create Quick Start Script

```bash
#!/bin/bash
# One-command demo deployment

set -e

echo "🚀 Starting demo deployment..."

# Step 1: Generate passwords
./scripts/deployment/setup_demo_env.sh

# Step 2: Deploy services
cd config/compose
bash ../../scripts/deployment/deploy_full_stack.sh

# Step 3: Wait for services
echo "⏳ Waiting for services to be ready (90 seconds)..."
sleep 90

# Step 4: Display access information
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          Demo Environment Ready!                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Access URLs:"
echo "  JanusGraph:  http://localhost:8182"
echo "  OpenSearch:  http://localhost:9200"
echo "  Grafana:     http://localhost:3001"
echo "  Jupyter:     http://localhost:8888"
echo ""
echo "Credentials: See demo-credentials.txt"
echo ""
```

### Step 4: Update .gitignore

```gitignore
# Demo credentials (never commit)
demo-credentials.txt
demo-creds.json
.env
```

### Step 5: Update Documentation

Add to `README.md`:

```markdown
## Quick Demo Setup

For demo environments, use the automated setup script:

```bash
# One-command setup
./scripts/deployment/demo_quickstart.sh

# Or step-by-step:
./scripts/deployment/setup_demo_env.sh  # Generate passwords
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh  # Deploy
```

Credentials will be saved to `demo-credentials.txt` (gitignored).

⚠️ **WARNING:** Demo credentials are for demonstration only. Never use in production!
```

---

## Security Considerations

### Demo vs Production

| Aspect | Demo | Production |
|--------|------|------------|
| Password Generation | Automated | Manual + Vault |
| Password Storage | demo-credentials.txt | HashiCorp Vault |
| Password Rotation | Manual | Automated (90 days) |
| Credential Sharing | File/Clipboard | Vault access control |
| Audit Logging | Basic | Comprehensive |

### Demo Safety Measures

1. **Clear Labeling:** All demo files clearly marked as "DEMO ONLY"
2. **Gitignore:** demo-credentials.txt never committed
3. **Warnings:** Scripts display warnings about production use
4. **Separate Workflow:** Demo scripts separate from production deployment
5. **Documentation:** Clear distinction between demo and production setup

---

## Implementation Checklist

- [ ] Create `scripts/deployment/generate_demo_passwords.py`
- [ ] Create `scripts/deployment/setup_demo_env.sh`
- [ ] Create `scripts/deployment/demo_quickstart.sh`
- [ ] Update `.gitignore` with demo credential files
- [ ] Update `README.md` with demo setup instructions
- [ ] Update `AGENTS.md` with demo workflow
- [ ] Test demo setup end-to-end
- [ ] Document demo vs production differences
- [ ] Add demo credentials to startup validation exceptions
- [ ] Create demo teardown script

---

## Usage Examples

### Scenario 1: Quick Demo for Client

```bash
# Setup (2 minutes)
./scripts/deployment/demo_quickstart.sh

# Present demo
# - Show JanusGraph queries
# - Demonstrate fraud detection
# - Display Grafana dashboards

# Teardown
./scripts/deployment/stop_full_stack.sh
```

### Scenario 2: Training Session

```bash
# Setup with custom project name
./scripts/deployment/setup_demo_env.sh --project training-2026-02-11

# Deploy
cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh

# Share credentials
cat demo-credentials.txt  # Display on screen for participants
```

### Scenario 3: Development Testing

```bash
# Generate passwords only
python scripts/deployment/generate_demo_passwords.py

# Review .env file
cat .env

# Deploy manually
cd config/compose && podman-compose -p janusgraph-demo -f docker-compose.full.yml up -d
```

---

## Next Steps

1. **Switch to Code Mode:** Implement the scripts
2. **Test End-to-End:** Verify demo setup works
3. **Update Documentation:** Add demo instructions to README
4. **Create Demo Video:** Record demo setup walkthrough

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-11  
**Status:** Ready for Implementation