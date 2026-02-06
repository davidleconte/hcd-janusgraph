#!/usr/bin/env python3
"""
Secrets Management Utility
Provides interface to retrieve secrets from various backends (Vault, AWS Secrets Manager, env vars)

File: scripts/utils/secrets_manager.py
Created: 2026-01-28
Author: Security Remediation Team
"""

import os
import sys
from typing import Optional, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Unified interface for secrets management.
    Supports multiple backends: environment variables, HashiCorp Vault, AWS Secrets Manager
    """

    def __init__(self, backend: str = "env"):
        """
        Initialize secrets manager with specified backend.
        
        Args:
            backend: One of 'env', 'vault', 'aws' (default: 'env')
        """
        self.backend = backend.lower()
        self._client = None
        
        if self.backend == "vault":
            self._init_vault()
        elif self.backend == "aws":
            self._init_aws()
        elif self.backend != "env":
            raise ValueError(f"Unsupported backend: {backend}")
        
        logger.info(f"Secrets manager initialized with backend: {self.backend}")

    def _init_vault(self) -> None:
        """Initialize HashiCorp Vault client"""
        try:
            import hvac
            
            vault_addr = os.getenv("VAULT_ADDR", "http://localhost:8200")
            vault_token = os.getenv("VAULT_TOKEN")
            
            if not vault_token:
                raise ValueError("VAULT_TOKEN environment variable not set")
            
            self._client = hvac.Client(url=vault_addr, token=vault_token)
            
            if not self._client.is_authenticated():
                raise ValueError("Vault authentication failed")
            
            logger.info(f"Connected to Vault at {vault_addr}")
            
        except ImportError:
            logger.error("hvac library not installed. Install with: pip install hvac")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Vault: {e}")
            raise

    def _init_aws(self) -> None:
        """Initialize AWS Secrets Manager client"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            region = os.getenv("AWS_REGION", "us-east-1")
            self._client = boto3.client("secretsmanager", region_name=region)
            
            logger.info(f"Connected to AWS Secrets Manager in {region}")
            
        except ImportError:
            logger.error("boto3 library not installed. Install with: pip install boto3")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize AWS Secrets Manager: {e}")
            raise

    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieve secret value from configured backend.
        
        Args:
            secret_name: Name/path of the secret
            default: Default value if secret not found
            
        Returns:
            Secret value or default
            
        Raises:
            ValueError: If secret not found and no default provided
        """
        try:
            if self.backend == "env":
                return self._get_from_env(secret_name, default)
            elif self.backend == "vault":
                return self._get_from_vault(secret_name, default)
            elif self.backend == "aws":
                return self._get_from_aws(secret_name, default)
        except Exception as e:
            logger.error(f"Failed to retrieve secret '{secret_name}': {e}")
            if default is not None:
                logger.warning(f"Using default value for '{secret_name}'")
                return default
            raise

    def _get_from_env(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret from environment variable"""
        value = os.getenv(secret_name, default)
        if value is None:
            raise ValueError(f"Environment variable '{secret_name}' not set")
        return value

    def _get_from_vault(self, secret_path: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret from HashiCorp Vault"""
        try:
            # Vault path format: secret/data/path/to/secret
            response = self._client.secrets.kv.v2.read_secret_version(path=secret_path)
            data = response["data"]["data"]
            
            # If secret_path contains a key (e.g., "myapp/db:password"), extract it
            if ":" in secret_path:
                path, key = secret_path.rsplit(":", 1)
                return data.get(key)
            
            # Otherwise return the whole secret data
            return data.get("value") or str(data)
            
        except Exception as e:
            logger.error(f"Failed to read from Vault: {e}")
            if default is not None:
                return default
            raise ValueError(f"Secret '{secret_path}' not found in Vault")

    def _get_from_aws(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret from AWS Secrets Manager"""
        try:
            from botocore.exceptions import ClientError
            
            response = self._client.get_secret_value(SecretId=secret_name)
            
            # Secrets can be string or binary
            if "SecretString" in response:
                return response["SecretString"]
            else:
                import base64
                return base64.b64decode(response["SecretBinary"]).decode("utf-8")
                
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ResourceNotFoundException":
                logger.error(f"Secret '{secret_name}' not found in AWS Secrets Manager")
            else:
                logger.error(f"AWS Secrets Manager error: {e}")
            
            if default is not None:
                return default
            raise ValueError(f"Secret '{secret_name}' not found in AWS Secrets Manager")

    def set_secret(self, secret_name: str, secret_value: str) -> bool:
        """
        Store secret in configured backend.
        
        Args:
            secret_name: Name/path of the secret
            secret_value: Secret value to store
            
        Returns:
            True if successful
            
        Note:
            Not supported for 'env' backend
        """
        if self.backend == "env":
            raise NotImplementedError("Cannot set secrets in environment backend")
        
        try:
            if self.backend == "vault":
                return self._set_in_vault(secret_name, secret_value)
            elif self.backend == "aws":
                return self._set_in_aws(secret_name, secret_value)
        except Exception as e:
            logger.error(f"Failed to store secret '{secret_name}': {e}")
            raise

    def _set_in_vault(self, secret_path: str, secret_value: str) -> bool:
        """Store secret in HashiCorp Vault"""
        try:
            self._client.secrets.kv.v2.create_or_update_secret(
                path=secret_path,
                secret={"value": secret_value}
            )
            logger.info(f"Secret '{secret_path}' stored in Vault")
            return True
        except Exception as e:
            logger.error(f"Failed to store in Vault: {e}")
            raise

    def _set_in_aws(self, secret_name: str, secret_value: str) -> bool:
        """Store secret in AWS Secrets Manager"""
        try:
            from botocore.exceptions import ClientError
            
            try:
                # Try to update existing secret
                self._client.update_secret(
                    SecretId=secret_name,
                    SecretString=secret_value
                )
                logger.info(f"Secret '{secret_name}' updated in AWS Secrets Manager")
            except ClientError as e:
                if e.response["Error"]["Code"] == "ResourceNotFoundException":
                    # Create new secret
                    self._client.create_secret(
                        Name=secret_name,
                        SecretString=secret_value
                    )
                    logger.info(f"Secret '{secret_name}' created in AWS Secrets Manager")
                else:
                    raise
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store in AWS Secrets Manager: {e}")
            raise

    def get_all_secrets(self, prefix: str = "") -> Dict[str, str]:
        """
        Retrieve all secrets with optional prefix.
        
        Args:
            prefix: Filter secrets by prefix
            
        Returns:
            Dictionary of secret names and values
        """
        if self.backend == "env":
            # Return all environment variables matching prefix
            return {
                k: v for k, v in os.environ.items()
                if k.startswith(prefix)
            }
        elif self.backend == "vault":
            # List and retrieve all secrets under path
            try:
                secrets = {}
                response = self._client.secrets.kv.v2.list_secrets(path=prefix)
                for key in response["data"]["keys"]:
                    full_path = f"{prefix}/{key}" if prefix else key
                    secrets[key] = self.get_secret(full_path)
                return secrets
            except Exception as e:
                logger.error(f"Failed to list Vault secrets: {e}")
                return {}
        elif self.backend == "aws":
            # List and retrieve all secrets
            try:
                secrets = {}
                paginator = self._client.get_paginator("list_secrets")
                for page in paginator.paginate():
                    for secret in page["SecretList"]:
                        name = secret["Name"]
                        if name.startswith(prefix):
                            secrets[name] = self.get_secret(name)
                return secrets
            except Exception as e:
                logger.error(f"Failed to list AWS secrets: {e}")
                return {}


def main():
    """CLI interface for secrets management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Secrets Management Utility")
    parser.add_argument("--backend", choices=["env", "vault", "aws"], default="env",
                       help="Secrets backend to use")
    parser.add_argument("--get", metavar="SECRET_NAME",
                       help="Retrieve a secret")
    parser.add_argument("--set", nargs=2, metavar=("SECRET_NAME", "SECRET_VALUE"),
                       help="Store a secret")
    parser.add_argument("--list", metavar="PREFIX", nargs="?", const="",
                       help="List all secrets (optionally with prefix)")
    
    args = parser.parse_args()
    
    try:
        sm = SecretsManager(backend=args.backend)
        
        if args.get:
            value = sm.get_secret(args.get)
            print(value)
        elif args.set:
            sm.set_secret(args.set[0], args.set[1])
            print(f"Secret '{args.set[0]}' stored successfully")
        elif args.list is not None:
            secrets = sm.get_all_secrets(prefix=args.list)
            for name in sorted(secrets.keys()):
                print(f"{name}: {'*' * 8}")  # Don't print actual values
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS | +33614126117
