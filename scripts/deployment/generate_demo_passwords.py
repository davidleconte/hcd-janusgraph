#!/usr/bin/env python3
"""
Demo Password Generator
=======================

Generates secure passwords for demo environments and creates .env file.

⚠️  WARNING: These are DEMO credentials only. Never use in production!

Usage:
    python scripts/deployment/generate_demo_passwords.py
    python scripts/deployment/generate_demo_passwords.py --project my-demo
    python scripts/deployment/generate_demo_passwords.py --format json --output creds.json
"""

import argparse
import json
import secrets
import string
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict


def generate_secure_password(length: int = 32) -> str:
    """
    Generate cryptographically secure password.
    
    Requirements:
    - Minimum length (default 32 characters)
    - Contains uppercase letters
    - Contains lowercase letters
    - Contains digits
    - Contains special characters
    
    Args:
        length: Password length (minimum 12)
    
    Returns:
        Secure password string
    """
    if length < 12:
        raise ValueError("Password length must be at least 12 characters")
    
    # Define character sets
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    
    # Generate password
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # Ensure password meets all requirements
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(c in "!@#$%^&*" for c in password)
    
    if not (has_upper and has_lower and has_digit and has_symbol):
        # Regenerate if requirements not met
        return generate_secure_password(length)
    
    return password


def generate_all_passwords(length: int = 32) -> Dict[str, str]:
    """
    Generate passwords for all services.
    
    Args:
        length: Password length for all passwords
    
    Returns:
        Dictionary of service names to passwords
    """
    services = [
        "OPENSEARCH_INITIAL_ADMIN_PASSWORD",
        "OPENSEARCH_ADMIN_PASSWORD",
        "JANUSGRAPH_PASSWORD",
        "HCD_PASSWORD",
        "HCD_KEYSTORE_PASSWORD",
        "HCD_TRUSTSTORE_PASSWORD",
        "JANUSGRAPH_KEYSTORE_PASSWORD",
        "JANUSGRAPH_TRUSTSTORE_PASSWORD",
        "GRAFANA_ADMIN_PASSWORD",
        "SMTP_PASSWORD",
    ]
    
    return {service: generate_secure_password(length) for service in services}


def create_env_file(passwords: Dict[str, str], project_name: str = "janusgraph-demo") -> None:
    """
    Create .env file from template with generated passwords.
    
    Args:
        passwords: Dictionary of service names to passwords
        project_name: Project name for COMPOSE_PROJECT_NAME
    """
    env_example = Path(".env.example")
    if not env_example.exists():
        print("❌ Error: .env.example not found")
        print("   Run this script from the project root directory")
        sys.exit(1)
    
    env_template = env_example.read_text()
    
    # Replace placeholders with generated passwords
    env_content = env_template
    for key, value in passwords.items():
        # Replace various placeholder patterns
        patterns = [
            f"{key}=YOUR_SECURE_PASSWORD_HERE_MINIMUM_12_CHARACTERS",
            f"{key}=changeit",
            f"{key}=secure-password-here",
            f"{key}=your-smtp-password-here",
        ]
        for pattern in patterns:
            env_content = env_content.replace(pattern, f"{key}={value}")
    
    # Set project name
    env_content = env_content.replace(
        "COMPOSE_PROJECT_NAME=janusgraph-demo",
        f"COMPOSE_PROJECT_NAME={project_name}"
    )
    
    # Write .env file
    Path(".env").write_text(env_content)
    print(f"✅ Created .env file with project name: {project_name}")


def save_credentials_file(passwords: Dict[str, str]) -> None:
    """
    Save passwords to demo-credentials.txt.
    
    Args:
        passwords: Dictionary of service names to passwords
    """
    output = []
    output.append("=" * 80)
    output.append(f"DEMO CREDENTIALS - GENERATED {datetime.now().isoformat()}")
    output.append("=" * 80)
    output.append("")
    output.append("⚠️  WARNING: These are DEMO credentials only. Never use in production!")
    output.append("")
    output.append("Service Passwords:")
    output.append("-" * 80)
    
    for key, value in sorted(passwords.items()):
        output.append(f"{key:45s} = {value}")
    
    output.append("")
    output.append("=" * 80)
    output.append("")
    output.append("Usage:")
    output.append("  1. Review these credentials")
    output.append("  2. Deploy: cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh")
    output.append("  3. Access services with credentials above")
    output.append("")
    output.append("Access URLs:")
    output.append("  JanusGraph:  http://localhost:8182")
    output.append("  OpenSearch:  http://localhost:9200")
    output.append("  Grafana:     http://localhost:3001 (admin / GRAFANA_ADMIN_PASSWORD)")
    output.append("  Jupyter:     http://localhost:8888")
    output.append("")
    output.append("=" * 80)
    
    credentials_file = Path("demo-credentials.txt")
    credentials_file.write_text("\n".join(output))
    print(f"✅ Saved credentials to: {credentials_file.absolute()}")


def save_json_file(passwords: Dict[str, str], output_file: str) -> None:
    """
    Save passwords to JSON file.
    
    Args:
        passwords: Dictionary of service names to passwords
        output_file: Output JSON file path
    """
    data = {
        "generated_at": datetime.now().isoformat(),
        "warning": "DEMO credentials only - never use in production",
        "passwords": passwords
    }
    
    output_path = Path(output_file)
    output_path.write_text(json.dumps(data, indent=2))
    print(f"✅ Saved JSON to: {output_path.absolute()}")


def display_credentials(passwords: Dict[str, str]) -> None:
    """
    Display credentials in formatted table.
    
    Args:
        passwords: Dictionary of service names to passwords
    """
    print("\n" + "=" * 80)
    print("DEMO CREDENTIALS GENERATED")
    print("=" * 80)
    print("")
    print("⚠️  WARNING: These are DEMO credentials only. Never use in production!")
    print("")
    print(f"{'Service':<45s}   Password")
    print("-" * 80)
    
    for key, value in sorted(passwords.items()):
        print(f"{key:<45s} : {value}")
    
    print("")
    print("=" * 80)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate secure passwords for demo environment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate passwords and create .env file
  python scripts/deployment/generate_demo_passwords.py
  
  # Custom project name
  python scripts/deployment/generate_demo_passwords.py --project my-demo-2026
  
  # Export to JSON
  python scripts/deployment/generate_demo_passwords.py --format json --output demo-creds.json
  
  # Custom password length
  python scripts/deployment/generate_demo_passwords.py --length 24
        """
    )
    
    parser.add_argument(
        "--project",
        default="janusgraph-demo",
        help="Project name for COMPOSE_PROJECT_NAME (default: janusgraph-demo)"
    )
    parser.add_argument(
        "--length",
        type=int,
        default=32,
        help="Password length (default: 32, minimum: 12)"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--output",
        help="Output file for JSON format (default: demo-credentials.json)"
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Don't display passwords on screen"
    )
    
    args = parser.parse_args()
    
    # Validate password length
    if args.length < 12:
        print("❌ Error: Password length must be at least 12 characters")
        sys.exit(1)
    
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                    Demo Password Generator                                   ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print("")
    
    # Generate passwords
    print(f"🔐 Generating secure passwords ({args.length} characters each)...")
    passwords = generate_all_passwords(args.length)
    
    # Create .env file
    print("📝 Creating .env file from template...")
    create_env_file(passwords, args.project)
    
    # Save credentials
    print("💾 Saving credentials...")
    save_credentials_file(passwords)
    
    # Save JSON if requested
    if args.format == "json":
        output_file = args.output or "demo-credentials.json"
        save_json_file(passwords, output_file)
    
    # Display credentials
    if not args.no_display:
        display_credentials(passwords)
    
    print("\n✅ Demo environment setup complete!")
    print("")
    print("Next steps:")
    print("  1. Review demo-credentials.txt")
    print("  2. Deploy: cd config/compose && bash ../../scripts/deployment/deploy_full_stack.sh")
    print("  3. Access services with credentials above")
    print("")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Aborted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

# Made with Bob
