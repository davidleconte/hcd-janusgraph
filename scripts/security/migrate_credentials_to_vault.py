#!/usr/bin/env python3
"""
Credential Migration Script
===========================

Migrate credentials from environment variables and config files to HashiCorp Vault.
This script securely populates Vault with all necessary credentials for the platform.

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS
Created: 2026-02-11
Phase: Phase 2 - Infrastructure Security

Prerequisites:
    - Vault server running and unsealed
    - VAULT_ADDR and VAULT_TOKEN environment variables set
    - KV v2 secrets engine mounted at 'janusgraph'

Usage:
    # Dry run (show what would be migrated)
    python scripts/security/migrate_credentials_to_vault.py --dry-run

    # Migrate all credentials
    python scripts/security/migrate_credentials_to_vault.py

    # Migrate specific service
    python scripts/security/migrate_credentials_to_vault.py --service janusgraph

    # Generate strong passwords
    python scripts/security/migrate_credentials_to_vault.py --generate-passwords

    # Backup existing secrets before migration
    python scripts/security/migrate_credentials_to_vault.py --backup
"""

import argparse
import json
import logging
import os
import secrets
import string
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.python.utils.vault_client import VaultClient, VaultConfig, VaultError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class CredentialMigrator:
    """Migrate credentials to Vault."""

    def __init__(
        self,
        vault_client: VaultClient,
        dry_run: bool = False,
        generate_passwords: bool = False,
    ):
        """
        Initialize credential migrator.

        Args:
            vault_client: VaultClient instance
            dry_run: If True, only show what would be migrated
            generate_passwords: If True, generate strong passwords
        """
        self.vault = vault_client
        self.dry_run = dry_run
        self.generate_passwords = generate_passwords
        self.migrated_count = 0
        self.skipped_count = 0
        self.error_count = 0

    def generate_strong_password(self, length: int = 24) -> str:
        """
        Generate a strong random password.

        Args:
            length: Password length (minimum 12)

        Returns:
            Strong random password
        """
        if length < 12:
            length = 12

        # Character sets
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = "!@#$%^&*()-_=+[]{}|;:,.<>?"

        # Ensure at least one character from each set
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special),
        ]

        # Fill remaining length
        all_chars = lowercase + uppercase + digits + special
        password.extend(secrets.choice(all_chars) for _ in range(length - 4))

        # Shuffle
        secrets.SystemRandom().shuffle(password)

        return "".join(password)

    def migrate_secret(
        self,
        path: str,
        data: Dict[str, str],
        description: str = "",
        overwrite: bool = False,
    ) -> bool:
        """
        Migrate a secret to Vault.

        Args:
            path: Secret path in Vault
            data: Secret data (dict)
            description: Human-readable description
            overwrite: If True, overwrite existing secret

        Returns:
            True if migrated, False if skipped
        """
        try:
            # Check if secret already exists
            try:
                existing = self.vault.get_secret(path, use_cache=False)
                if existing and not overwrite:
                    logger.info(f"⏭️  Skipping {path} (already exists)")
                    self.skipped_count += 1
                    return False
            except Exception:
                # Secret doesn't exist, proceed with migration
                pass

            if self.dry_run:
                logger.info(f"🔍 [DRY RUN] Would migrate: {path}")
                logger.info(f"   Description: {description}")
                logger.info(f"   Keys: {list(data.keys())}")
                self.migrated_count += 1
                return True

            # Migrate secret
            self.vault.set_secret(path, data)
            logger.info(f"✅ Migrated: {path}")
            if description:
                logger.info(f"   Description: {description}")
            self.migrated_count += 1
            return True

        except VaultError as e:
            logger.error(f"❌ Failed to migrate {path}: {e}")
            self.error_count += 1
            return False

    def migrate_janusgraph_credentials(self) -> None:
        """Migrate JanusGraph/HCD credentials."""
        logger.info("\n📊 Migrating JanusGraph/HCD Credentials...")

        # Admin credentials
        admin_password = (
            self.generate_strong_password()
            if self.generate_passwords
            else os.getenv("JANUSGRAPH_PASSWORD", "CHANGE_ME_ADMIN_PASSWORD")
        )

        self.migrate_secret(
            path="admin",
            data={
                "username": "admin",
                "password": admin_password,
                "description": "JanusGraph admin user",
            },
            description="JanusGraph admin credentials",
        )

        # HCD/Cassandra credentials
        hcd_password = (
            self.generate_strong_password()
            if self.generate_passwords
            else os.getenv("HCD_PASSWORD", "CHANGE_ME_HCD_PASSWORD")
        )

        self.migrate_secret(
            path="hcd",
            data={
                "username": "cassandra",
                "password": hcd_password,
                "description": "HCD/Cassandra superuser",
            },
            description="HCD/Cassandra credentials",
        )

        # JMX credentials
        jmx_password = (
            self.generate_strong_password()
            if self.generate_passwords
            else os.getenv("JMX_PASSWORD", "CHANGE_ME_JMX_PASSWORD")
        )

        self.migrate_secret(
            path="hcd/jmx",
            data={
                "username": "jmxuser",
                "password": jmx_password,
                "description": "JMX monitoring user",
            },
            description="JMX monitoring credentials",
        )

    def migrate_opensearch_credentials(self) -> None:
        """Migrate OpenSearch credentials."""
        logger.info("\n🔍 Migrating OpenSearch Credentials...")

        # Admin credentials
        admin_password = (
            self.generate_strong_password()
            if self.generate_passwords
            else os.getenv("OPENSEARCH_PASSWORD", "CHANGE_ME_OPENSEARCH_PASSWORD")
        )

        self.migrate_secret(
            path="opensearch",
            data={
                "username": "admin",
                "password": admin_password,
                "description": "OpenSearch admin user",
            },
            description="OpenSearch admin credentials",
        )

        # API key for applications
        api_key = (
            self.generate_strong_password(32)
            if self.generate_passwords
            else os.getenv("OPENSEARCH_API_KEY", "CHANGE_ME_API_KEY")
        )

        self.migrate_secret(
            path="opensearch/api",
            data={
                "api_key": api_key,
                "description": "OpenSearch API key for applications",
            },
            description="OpenSearch API credentials",
        )

    def migrate_monitoring_credentials(self) -> None:
        """Migrate monitoring stack credentials."""
        logger.info("\n📈 Migrating Monitoring Credentials...")

        # Grafana credentials
        grafana_password = (
            self.generate_strong_password()
            if self.generate_passwords
            else os.getenv("GRAFANA_PASSWORD", "CHANGE_ME_GRAFANA_PASSWORD")
        )

        self.migrate_secret(
            path="grafana",
            data={
                "username": "admin",
                "password": grafana_password,
                "description": "Grafana admin user",
            },
            description="Grafana admin credentials",
        )

        # Prometheus credentials (if basic auth enabled)
        prometheus_password = (
            self.generate_strong_password()
            if self.generate_passwords
            else os.getenv("PROMETHEUS_PASSWORD", "CHANGE_ME_PROMETHEUS_PASSWORD")
        )

        self.migrate_secret(
            path="prometheus",
            data={
                "username": "prometheus",
                "password": prometheus_password,
                "description": "Prometheus basic auth",
            },
            description="Prometheus credentials",
        )

        # AlertManager credentials
        alertmanager_password = (
            self.generate_strong_password()
            if self.generate_passwords
            else os.getenv("ALERTMANAGER_PASSWORD", "CHANGE_ME_ALERTMANAGER_PASSWORD")
        )

        self.migrate_secret(
            path="alertmanager",
            data={
                "username": "alertmanager",
                "password": alertmanager_password,
                "description": "AlertManager basic auth",
            },
            description="AlertManager credentials",
        )

    def migrate_pulsar_credentials(self) -> None:
        """Migrate Apache Pulsar credentials."""
        logger.info("\n📨 Migrating Pulsar Credentials...")

        # Pulsar admin credentials
        admin_password = (
            self.generate_strong_password()
            if self.generate_passwords
            else os.getenv("PULSAR_ADMIN_PASSWORD", "CHANGE_ME_PULSAR_PASSWORD")
        )

        self.migrate_secret(
            path="pulsar/admin",
            data={
                "username": "admin",
                "password": admin_password,
                "description": "Pulsar admin user",
            },
            description="Pulsar admin credentials",
        )

        # Pulsar token for applications
        token = (
            self.generate_strong_password(64)
            if self.generate_passwords
            else os.getenv("PULSAR_TOKEN", "CHANGE_ME_PULSAR_TOKEN")
        )

        self.migrate_secret(
            path="pulsar/token",
            data={
                "token": token,
                "description": "Pulsar authentication token",
            },
            description="Pulsar authentication token",
        )

    def migrate_ssl_certificates(self) -> None:
        """Migrate SSL/TLS certificate passwords."""
        logger.info("\n🔐 Migrating SSL/TLS Certificate Passwords...")

        # Keystore password
        keystore_password = (
            self.generate_strong_password()
            if self.generate_passwords
            else os.getenv("HCD_KEYSTORE_PASSWORD", "changeit")
        )

        self.migrate_secret(
            path="ssl/keystore",
            data={
                "password": keystore_password,
                "description": "Java keystore password",
            },
            description="Keystore password",
        )

        # Truststore password
        truststore_password = (
            self.generate_strong_password()
            if self.generate_passwords
            else os.getenv("HCD_TRUSTSTORE_PASSWORD", "changeit")
        )

        self.migrate_secret(
            path="ssl/truststore",
            data={
                "password": truststore_password,
                "description": "Java truststore password",
            },
            description="Truststore password",
        )

    def migrate_api_keys(self) -> None:
        """Migrate API keys and tokens."""
        logger.info("\n🔑 Migrating API Keys...")

        # JanusGraph API key
        api_key = (
            self.generate_strong_password(32)
            if self.generate_passwords
            else os.getenv("JANUSGRAPH_API_KEY", "CHANGE_ME_API_KEY")
        )

        self.migrate_secret(
            path="api/janusgraph",
            data={
                "api_key": api_key,
                "description": "JanusGraph REST API key",
            },
            description="JanusGraph API key",
        )

        # Webhook secret
        webhook_secret = (
            self.generate_strong_password(32)
            if self.generate_passwords
            else os.getenv("WEBHOOK_SECRET", "CHANGE_ME_WEBHOOK_SECRET")
        )

        self.migrate_secret(
            path="api/webhook",
            data={
                "secret": webhook_secret,
                "description": "Webhook signature secret",
            },
            description="Webhook secret",
        )

    def backup_existing_secrets(self, backup_dir: Path) -> None:
        """
        Backup existing secrets from Vault.

        Args:
            backup_dir: Directory to store backups
        """
        logger.info(f"\n💾 Backing up existing secrets to {backup_dir}...")

        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"vault_backup_{timestamp}.json"

        try:
            # List all secrets
            secrets = self.vault.list_secrets("")
            backup_data = {}

            for secret_name in secrets:
                try:
                    data = self.vault.get_secret(secret_name, use_cache=False)
                    backup_data[secret_name] = data
                    logger.info(f"   Backed up: {secret_name}")
                except Exception as e:
                    logger.warning(f"   Failed to backup {secret_name}: {e}")

            # Write backup file
            with open(backup_file, "w") as f:
                json.dump(backup_data, f, indent=2)

            logger.info(f"✅ Backup saved to: {backup_file}")

        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")

    def print_summary(self) -> None:
        """Print migration summary."""
        logger.info("\n" + "=" * 60)
        logger.info("📊 Migration Summary")
        logger.info("=" * 60)
        logger.info(f"✅ Migrated: {self.migrated_count}")
        logger.info(f"⏭️  Skipped:  {self.skipped_count}")
        logger.info(f"❌ Errors:   {self.error_count}")
        logger.info("=" * 60)

        if self.dry_run:
            logger.info("\n🔍 This was a DRY RUN - no changes were made")
            logger.info("   Run without --dry-run to perform actual migration")

        if self.generate_passwords:
            logger.info("\n⚠️  IMPORTANT: Strong passwords were generated")
            logger.info("   Make sure to update your .env files and docker-compose")
            logger.info("   with the new passwords from Vault")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate credentials to HashiCorp Vault",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without making changes",
    )
    parser.add_argument(
        "--generate-passwords",
        action="store_true",
        help="Generate strong random passwords instead of using env vars",
    )
    parser.add_argument(
        "--service",
        choices=["janusgraph", "opensearch", "monitoring", "pulsar", "ssl", "api", "all"],
        default="all",
        help="Migrate specific service credentials (default: all)",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Backup existing secrets before migration",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=Path("./backups/vault"),
        help="Directory for backups (default: ./backups/vault)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing secrets",
    )

    args = parser.parse_args()

    # Validate environment
    if not os.getenv("VAULT_ADDR"):
        logger.error("❌ VAULT_ADDR environment variable not set")
        sys.exit(1)

    if not os.getenv("VAULT_TOKEN"):
        logger.error("❌ VAULT_TOKEN environment variable not set")
        sys.exit(1)

    try:
        # Initialize Vault client
        logger.info("🔐 Connecting to Vault...")
        config = VaultConfig.from_env()
        vault_client = VaultClient(config)

        # Test connection
        vault_client._ensure_initialized()
        logger.info(f"✅ Connected to Vault at {config.vault_addr}")

        # Initialize migrator
        migrator = CredentialMigrator(
            vault_client=vault_client,
            dry_run=args.dry_run,
            generate_passwords=args.generate_passwords,
        )

        # Backup if requested
        if args.backup:
            migrator.backup_existing_secrets(args.backup_dir)

        # Migrate credentials
        logger.info("\n🚀 Starting credential migration...")

        if args.service in ["janusgraph", "all"]:
            migrator.migrate_janusgraph_credentials()

        if args.service in ["opensearch", "all"]:
            migrator.migrate_opensearch_credentials()

        if args.service in ["monitoring", "all"]:
            migrator.migrate_monitoring_credentials()

        if args.service in ["pulsar", "all"]:
            migrator.migrate_pulsar_credentials()

        if args.service in ["ssl", "all"]:
            migrator.migrate_ssl_certificates()

        if args.service in ["api", "all"]:
            migrator.migrate_api_keys()

        # Print summary
        migrator.print_summary()

        # Exit with error if any migrations failed
        if migrator.error_count > 0:
            sys.exit(1)

    except VaultError as e:
        logger.error(f"❌ Vault error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob