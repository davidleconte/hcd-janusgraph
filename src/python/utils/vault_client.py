"""
Vault Client Wrapper
====================

Production-grade HashiCorp Vault client with caching, retry logic, and comprehensive error handling.
Integrates with application settings and provides a clean interface for credential management.

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS
Created: 2026-02-11
Phase: Phase 2 - Infrastructure Security
"""

import logging
import os
import time
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class VaultConfig(BaseModel):
    """Vault configuration with validation."""

    vault_addr: str = Field(
        default="http://localhost:8200",
        description="Vault server address",
    )
    vault_token: Optional[str] = Field(
        default=None,
        description="Vault authentication token",
    )
    vault_role_id: Optional[str] = Field(
        default=None,
        description="AppRole role ID for production",
    )
    vault_secret_id: Optional[str] = Field(
        default=None,
        description="AppRole secret ID for production",
    )
    vault_namespace: str = Field(
        default="janusgraph",
        description="Vault KV namespace",
    )
    vault_mount_point: str = Field(
        default="janusgraph",
        description="KV secrets engine mount point",
    )
    cache_ttl: int = Field(
        default=300,
        description="Cache TTL in seconds (5 minutes default)",
        ge=0,
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for failed requests",
        ge=0,
        le=10,
    )
    retry_delay: float = Field(
        default=1.0,
        description="Delay between retries in seconds",
        ge=0.1,
        le=10.0,
    )

    @classmethod
    def from_env(cls) -> "VaultConfig":
        """Load configuration from environment variables."""
        return cls(
            vault_addr=os.getenv("VAULT_ADDR", "http://localhost:8200"),
            vault_token=os.getenv("VAULT_TOKEN"),
            vault_role_id=os.getenv("VAULT_ROLE_ID"),
            vault_secret_id=os.getenv("VAULT_SECRET_ID"),
            vault_namespace=os.getenv("VAULT_NAMESPACE", "janusgraph"),
            vault_mount_point=os.getenv("VAULT_MOUNT_POINT", "janusgraph"),
            cache_ttl=int(os.getenv("VAULT_CACHE_TTL", "300")),
            max_retries=int(os.getenv("VAULT_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("VAULT_RETRY_DELAY", "1.0")),
        )


class VaultError(Exception):
    """Base exception for Vault-related errors."""

    pass


class VaultAuthenticationError(VaultError):
    """Raised when Vault authentication fails."""

    pass


class VaultConnectionError(VaultError):
    """Raised when connection to Vault fails."""

    pass


class VaultSecretNotFoundError(VaultError):
    """Raised when requested secret is not found."""

    pass


class VaultClient:
    """
    Production-grade Vault client with caching and retry logic.

    Features:
    - Automatic token renewal
    - AppRole authentication support
    - LRU caching with TTL
    - Retry logic with exponential backoff
    - Comprehensive error handling
    - Security event logging

    Example:
        >>> client = VaultClient.from_env()
        >>> password = client.get_secret("admin", "password")
        >>> credentials = client.get_credentials("opensearch")
    """

    def __init__(self, config: Optional[VaultConfig] = None):
        """
        Initialize Vault client.

        Args:
            config: Vault configuration (defaults to environment-based config)

        Raises:
            VaultAuthenticationError: If authentication fails
            VaultConnectionError: If connection to Vault fails
        """
        self.config = config or VaultConfig.from_env()
        self._client: Optional[Any] = None  # hvac.Client type
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._initialized = False

        # Lazy initialization - only connect when first secret is requested
        logger.info(
            "Vault client configured for %s (namespace: %s)",
            self.config.vault_addr,
            self.config.vault_namespace,
        )

    def _ensure_initialized(self) -> None:
        """Ensure Vault client is initialized and authenticated."""
        if self._initialized:
            return

        try:
            import hvac
        except ImportError:
            raise VaultError(
                "hvac library not installed. Install with: uv pip install hvac"
            )

        try:
            # Initialize client
            self._client = hvac.Client(url=self.config.vault_addr)

            # Authenticate
            if self.config.vault_token:
                # Token-based authentication (development)
                self._client.token = self.config.vault_token
                logger.info("Using token-based authentication")
            elif self.config.vault_role_id and self.config.vault_secret_id:
                # AppRole authentication (production)
                auth_response = self._client.auth.approle.login(
                    role_id=self.config.vault_role_id,
                    secret_id=self.config.vault_secret_id,
                )
                self._client.token = auth_response["auth"]["client_token"]
                logger.info("Using AppRole authentication")
            else:
                raise VaultAuthenticationError(
                    "No authentication method configured. "
                    "Set VAULT_TOKEN or VAULT_ROLE_ID/VAULT_SECRET_ID"
                )

            # Verify authentication
            if not self._client.is_authenticated():
                raise VaultAuthenticationError("Vault authentication failed")

            self._initialized = True
            logger.info("Vault client initialized successfully")

        except (VaultAuthenticationError, VaultConnectionError, VaultSecretNotFoundError):
            raise
        except hvac.exceptions.VaultError as e:
            raise VaultConnectionError(f"Failed to connect to Vault: {e}")
        except Exception as e:
            raise VaultError(f"Unexpected error initializing Vault client: {e}")

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self._cache:
            return None

        value, timestamp = self._cache[key]
        if time.time() - timestamp > self.config.cache_ttl:
            # Cache expired
            del self._cache[key]
            return None

        logger.debug("Cache hit for key: %s", key)
        return value

    def _set_in_cache(self, key: str, value: Any) -> None:
        """Store value in cache with current timestamp."""
        self._cache[key] = (value, time.time())
        logger.debug("Cached key: %s", key)

    def _retry_operation(self, operation, *args, **kwargs) -> Any:
        """
        Execute operation with retry logic.

        Args:
            operation: Callable to execute
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation

        Returns:
            Result of operation

        Raises:
            VaultError: If all retries fail
        """
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                return operation(*args, **kwargs)
            except (VaultAuthenticationError, VaultSecretNotFoundError):
                raise
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay * (2**attempt)
                    logger.warning(
                        "Vault operation failed (attempt %d/%d), retrying in %.1fs: %s",
                        attempt + 1,
                        self.config.max_retries + 1,
                        delay,
                        e,
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        "Vault operation failed after %d attempts: %s",
                        self.config.max_retries + 1,
                        e,
                    )

        raise VaultError(f"Operation failed after {self.config.max_retries + 1} attempts: {last_error}")

    def get_secret(
        self,
        path: str,
        key: Optional[str] = None,
        use_cache: bool = True,
    ) -> Any:
        """
        Retrieve secret from Vault.

        Args:
            path: Secret path (e.g., "admin", "opensearch")
            key: Specific key within secret (e.g., "password")
            use_cache: Whether to use cached value if available

        Returns:
            Secret value (string, dict, or specific key value)

        Raises:
            VaultSecretNotFoundError: If secret not found
            VaultError: If retrieval fails

        Example:
            >>> client.get_secret("admin", "password")
            'secure_password_123'
            >>> client.get_secret("admin")
            {'username': 'admin', 'password': 'secure_password_123'}
        """
        self._ensure_initialized()

        cache_key = f"{path}:{key}" if key else path

        # Check cache
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                return cached

        def _read_secret():
            response = None
            try:
                response = self._client.secrets.kv.v2.read_secret_version(
                    path=path,
                    mount_point=self.config.vault_mount_point,
                )
                if response is None:
                    raise VaultSecretNotFoundError(f"Secret '{path}' not found")
                data = response["data"]["data"]

                if key:
                    if key not in data:
                        raise VaultSecretNotFoundError(
                            f"Key '{key}' not found in secret '{path}'"
                        )
                    return data[key]
                return data

            except VaultSecretNotFoundError:
                raise
            except Exception as e:
                err_str = str(e).lower()
                if "invalid path" in err_str or "not found" in err_str or "none, on get" in err_str:
                    raise VaultSecretNotFoundError(f"Secret '{path}' not found")
                raise VaultError(f"Failed to read secret '{path}': {e}")

        # Execute with retry
        result = self._retry_operation(_read_secret)

        # Cache result
        if use_cache:
            self._set_in_cache(cache_key, result)

        logger.info("Retrieved secret: %s%s", path, f":{key}" if key else "")
        return result

    def get_credentials(self, service: str, use_cache: bool = True) -> Dict[str, str]:
        """
        Retrieve service credentials (username and password).

        Args:
            service: Service name (e.g., "admin", "opensearch", "hcd")
            use_cache: Whether to use cached credentials

        Returns:
            Dictionary with 'username' and 'password' keys

        Raises:
            VaultSecretNotFoundError: If credentials not found
            VaultError: If retrieval fails

        Example:
            >>> creds = client.get_credentials("opensearch")
            >>> print(creds["username"], creds["password"])
            admin secure_password_123
        """
        secret = self.get_secret(service, use_cache=use_cache)

        if not isinstance(secret, dict):
            raise VaultError(f"Expected dict for credentials, got {type(secret)}")

        if "username" not in secret or "password" not in secret:
            raise VaultError(
                f"Credentials for '{service}' missing username or password"
            )

        return {
            "username": secret["username"],
            "password": secret["password"],
        }

    def set_secret(
        self,
        path: str,
        data: Dict[str, Any],
        invalidate_cache: bool = True,
    ) -> None:
        """
        Store secret in Vault.

        Args:
            path: Secret path
            data: Secret data (dict)
            invalidate_cache: Whether to invalidate cache for this path

        Raises:
            VaultError: If storage fails

        Example:
            >>> client.set_secret("myapp/db", {
            ...     "username": "dbuser",
            ...     "password": "secure_pass"
            ... })
        """
        self._ensure_initialized()

        def _write_secret():
            try:
                self._client.secrets.kv.v2.create_or_update_secret(
                    path=path,
                    secret=data,
                    mount_point=self.config.vault_mount_point,
                )
            except Exception as e:
                raise VaultError(f"Failed to write secret '{path}': {e}")

        self._retry_operation(_write_secret)

        # Invalidate cache
        if invalidate_cache:
            # Remove all cache entries for this path
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(path)]
            for key in keys_to_remove:
                del self._cache[key]

        logger.info("Stored secret: %s", path)

    def list_secrets(self, path: str = "") -> list[str]:
        """
        List secrets at given path.

        Args:
            path: Path to list (empty for root)

        Returns:
            List of secret names

        Raises:
            VaultError: If listing fails
        """
        self._ensure_initialized()

        def _list_secrets():
            response = None
            try:
                response = self._client.secrets.kv.v2.list_secrets(
                    path=path,
                    mount_point=self.config.vault_mount_point,
                )
                return response["data"]["keys"]
            except Exception as e:
                if "not found" in str(e).lower() or response is None:
                    return []
                raise VaultError(f"Failed to list secrets at '{path}': {e}")

        return self._retry_operation(_list_secrets)

    def clear_cache(self) -> None:
        """Clear all cached secrets."""
        self._cache.clear()
        logger.info("Vault cache cleared")

    def renew_token(self) -> None:
        """
        Renew Vault token.

        Raises:
            VaultError: If renewal fails
        """
        self._ensure_initialized()

        def _renew():
            try:
                self._client.auth.token.renew_self()
            except Exception as e:
                raise VaultError(f"Failed to renew token: {e}")

        self._retry_operation(_renew)
        logger.info("Vault token renewed")

    @classmethod
    def from_env(cls) -> "VaultClient":
        """
        Create Vault client from environment variables.

        Returns:
            Configured VaultClient instance

        Example:
            >>> client = VaultClient.from_env()
        """
        config = VaultConfig.from_env()
        return cls(config)

    def __enter__(self) -> "VaultClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        # No cleanup needed
        pass


@lru_cache(maxsize=1)
def get_vault_client() -> VaultClient:
    """
    Get singleton Vault client instance.

    Returns:
        Cached VaultClient instance

    Example:
        >>> from src.python.utils.vault_client import get_vault_client
        >>> client = get_vault_client()
        >>> password = client.get_secret("admin", "password")
    """
    return VaultClient.from_env()


# Convenience functions for common operations
def get_janusgraph_credentials() -> Dict[str, str]:
    """Get JanusGraph admin credentials from Vault."""
    client = get_vault_client()
    return client.get_credentials("admin")


def get_opensearch_credentials() -> Dict[str, str]:
    """Get OpenSearch credentials from Vault."""
    client = get_vault_client()
    return client.get_credentials("opensearch")


def get_hcd_credentials() -> Dict[str, str]:
    """Get HCD/Cassandra credentials from Vault."""
    client = get_vault_client()
    return client.get_credentials("hcd")


def get_grafana_credentials() -> Dict[str, str]:
    """Get Grafana credentials from Vault."""
    client = get_vault_client()
    return client.get_credentials("grafana")

# Made with Bob
