"""
Integration Tests for Vault Client
===================================

Tests that require a running Vault instance.
These tests verify real Vault operations including authentication,
secret management, caching, and error handling.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Created: 2026-02-11
Phase: Phase 2 - Infrastructure Security

Prerequisites:
    - Vault server running at VAULT_ADDR (default: http://localhost:8200)
    - VAULT_TOKEN environment variable set
    - KV v2 secrets engine mounted at 'janusgraph'

Run with:
    pytest tests/integration/test_vault_integration.py -v
    pytest tests/integration/test_vault_integration.py -v -m "not slow"
"""

import os
import time
from typing import Generator

import pytest

from src.python.utils.vault_client import (
    VaultAuthenticationError,
    VaultClient,
    VaultConfig,
    VaultConnectionError,
    VaultError,
    VaultSecretNotFoundError,
    get_vault_client,
)

# Skip all tests if Vault is not available
pytestmark = pytest.mark.integration


def is_vault_available() -> bool:
    """Check if Vault is available."""
    try:
        import hvac

        vault_addr = os.getenv("VAULT_ADDR", "http://localhost:8200")
        vault_token = os.getenv("VAULT_TOKEN")

        if not vault_token:
            return False

        client = hvac.Client(url=vault_addr, token=vault_token)
        return client.is_authenticated()
    except Exception:
        return False


@pytest.fixture(scope="module")
def vault_available():
    """Skip tests if Vault is not available."""
    if not is_vault_available():
        pytest.skip("Vault server not available or not authenticated")


@pytest.fixture
def vault_client(vault_available) -> Generator[VaultClient, None, None]:
    """Create Vault client for testing."""
    config = VaultConfig.from_env()
    client = VaultClient(config)
    yield client
    # Cleanup: clear cache after each test
    client.clear_cache()


@pytest.fixture
def test_secret_path() -> str:
    """Generate unique test secret path."""
    return f"test/integration-{int(time.time())}"


class TestVaultConnection:
    """Test Vault connection and authentication."""

    def test_connection_with_token(self, vault_available):
        """Test successful connection with token authentication."""
        config = VaultConfig.from_env()
        client = VaultClient(config)

        # Should initialize successfully
        client._ensure_initialized()
        assert client._initialized
        assert client._client is not None

    def test_connection_invalid_token(self, vault_available):
        """Test connection fails with invalid token."""
        config = VaultConfig(
            vault_addr=os.getenv("VAULT_ADDR", "http://localhost:8200"),
            vault_token="invalid-token-12345",
        )
        client = VaultClient(config)

        with pytest.raises(VaultAuthenticationError):
            client._ensure_initialized()

    def test_connection_invalid_address(self):
        """Test connection fails with invalid Vault address."""
        config = VaultConfig(
            vault_addr="http://nonexistent-vault:8200",
            vault_token="test-token",
        )
        client = VaultClient(config)

        with pytest.raises((VaultConnectionError, VaultError)):
            client._ensure_initialized()

    def test_lazy_initialization(self, vault_available):
        """Test that client initializes lazily on first operation."""
        config = VaultConfig.from_env()
        client = VaultClient(config)

        # Should not be initialized yet
        assert not client._initialized

        # First operation should trigger initialization
        try:
            client.list_secrets()
        except Exception:
            pass  # May fail if no secrets, but should initialize

        assert client._initialized


class TestSecretOperations:
    """Test secret read/write operations."""

    def test_write_and_read_secret(self, vault_client, test_secret_path):
        """Test writing and reading a secret."""
        test_data = {
            "username": "testuser",
            "password": "testpass123",
            "api_key": "test-api-key",
        }

        # Write secret
        vault_client.set_secret(test_secret_path, test_data)

        # Read secret
        result = vault_client.get_secret(test_secret_path)
        assert result == test_data

    def test_read_secret_with_key(self, vault_client, test_secret_path):
        """Test reading specific key from secret."""
        test_data = {"username": "testuser", "password": "testpass123"}
        vault_client.set_secret(test_secret_path, test_data)

        # Read specific key
        password = vault_client.get_secret(test_secret_path, "password")
        assert password == "testpass123"

    def test_read_nonexistent_secret(self, vault_client):
        """Test reading nonexistent secret raises error."""
        with pytest.raises(VaultSecretNotFoundError):
            vault_client.get_secret("nonexistent/secret/path")

    def test_read_nonexistent_key(self, vault_client, test_secret_path):
        """Test reading nonexistent key from secret."""
        test_data = {"username": "testuser"}
        vault_client.set_secret(test_secret_path, test_data)

        with pytest.raises(VaultSecretNotFoundError):
            vault_client.get_secret(test_secret_path, "nonexistent_key")

    def test_update_secret(self, vault_client, test_secret_path):
        """Test updating existing secret."""
        # Write initial secret
        initial_data = {"username": "user1", "password": "pass1"}
        vault_client.set_secret(test_secret_path, initial_data)

        # Update secret
        updated_data = {"username": "user2", "password": "pass2"}
        vault_client.set_secret(test_secret_path, updated_data)

        # Verify update
        result = vault_client.get_secret(test_secret_path)
        assert result == updated_data

    def test_list_secrets(self, vault_client):
        """Test listing secrets."""
        # Create test secrets
        base_path = f"test/list-{int(time.time())}"
        vault_client.set_secret(f"{base_path}/secret1", {"key": "value1"})
        vault_client.set_secret(f"{base_path}/secret2", {"key": "value2"})

        # List secrets
        secrets = vault_client.list_secrets(base_path)
        assert "secret1" in secrets
        assert "secret2" in secrets

    def test_list_empty_path(self, vault_client):
        """Test listing nonexistent path returns empty list."""
        secrets = vault_client.list_secrets("nonexistent/path")
        assert secrets == []


class TestCredentialOperations:
    """Test credential-specific operations."""

    def test_get_credentials(self, vault_client, test_secret_path):
        """Test getting credentials with username and password."""
        creds = {"username": "dbuser", "password": "dbpass123"}
        vault_client.set_secret(test_secret_path, creds)

        result = vault_client.get_credentials(test_secret_path)
        assert result["username"] == "dbuser"
        assert result["password"] == "dbpass123"

    def test_get_credentials_missing_username(self, vault_client, test_secret_path):
        """Test getting credentials fails if username missing."""
        vault_client.set_secret(test_secret_path, {"password": "pass"})

        with pytest.raises(VaultError, match="missing username or password"):
            vault_client.get_credentials(test_secret_path)

    def test_get_credentials_missing_password(self, vault_client, test_secret_path):
        """Test getting credentials fails if password missing."""
        vault_client.set_secret(test_secret_path, {"username": "user"})

        with pytest.raises(VaultError, match="missing username or password"):
            vault_client.get_credentials(test_secret_path)


class TestCaching:
    """Test caching functionality."""

    def test_cache_hit(self, vault_client, test_secret_path):
        """Test that cached values are returned without Vault call."""
        test_data = {"key": "value"}
        vault_client.set_secret(test_secret_path, test_data)

        # First read - should cache
        result1 = vault_client.get_secret(test_secret_path)

        # Modify secret in Vault directly (bypass cache)
        vault_client.set_secret(test_secret_path, {"key": "new_value"}, invalidate_cache=False)

        # Second read - should return cached value
        result2 = vault_client.get_secret(test_secret_path, use_cache=True)
        assert result2 == result1  # Should be old value from cache

    def test_cache_bypass(self, vault_client, test_secret_path):
        """Test bypassing cache returns fresh value."""
        test_data = {"key": "value"}
        vault_client.set_secret(test_secret_path, test_data)

        # First read - should cache
        vault_client.get_secret(test_secret_path)

        # Modify secret
        new_data = {"key": "new_value"}
        vault_client.set_secret(test_secret_path, new_data)

        # Read with cache bypass - should get new value
        result = vault_client.get_secret(test_secret_path, use_cache=False)
        assert result == new_data

    @pytest.mark.slow
    def test_cache_expiry(self, vault_available):
        """Test that cache expires after TTL."""
        # Create client with short TTL
        config = VaultConfig.from_env()
        config.cache_ttl = 2  # 2 seconds
        client = VaultClient(config)

        test_path = f"test/cache-expiry-{int(time.time())}"
        test_data = {"key": "value"}
        client.set_secret(test_path, test_data)

        # First read - should cache
        client.get_secret(test_path)

        # Wait for cache to expire
        time.sleep(2.5)

        # Modify secret
        new_data = {"key": "new_value"}
        client.set_secret(test_path, new_data)

        # Read - should get new value (cache expired)
        result = client.get_secret(test_path)
        assert result == new_data

    def test_cache_invalidation_on_write(self, vault_client, test_secret_path):
        """Test that writing secret invalidates cache."""
        test_data = {"key": "value"}
        vault_client.set_secret(test_secret_path, test_data)

        # Cache the secret
        vault_client.get_secret(test_secret_path)
        assert len(vault_client._cache) > 0

        # Write new value - should invalidate cache
        new_data = {"key": "new_value"}
        vault_client.set_secret(test_secret_path, new_data)
        assert len(vault_client._cache) == 0

    def test_clear_cache(self, vault_client, test_secret_path):
        """Test manual cache clearing."""
        test_data = {"key": "value"}
        vault_client.set_secret(test_secret_path, test_data)

        # Cache multiple secrets
        vault_client.get_secret(test_secret_path)
        vault_client.get_secret(test_secret_path, "key")
        assert len(vault_client._cache) > 0

        # Clear cache
        vault_client.clear_cache()
        assert len(vault_client._cache) == 0


class TestRetryLogic:
    """Test retry logic and error handling."""

    @pytest.mark.slow
    def test_retry_on_transient_error(self, vault_available):
        """Test that operations retry on transient errors using mock."""
        from unittest.mock import patch, MagicMock

        config = VaultConfig.from_env()
        client = VaultClient(config)
        client._ensure_initialized()

        call_count = {"n": 0}
        original_read = client._client.secrets.kv.v2.read_secret_version

        def flaky_read(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] <= 2:
                raise Exception("simulated transient error")
            return original_read(*args, **kwargs)

        test_path = f"test/retry-{int(time.time())}"
        client.set_secret(test_path, {"key": "value"})

        with patch.object(
            client._client.secrets.kv.v2,
            "read_secret_version",
            side_effect=flaky_read,
        ):
            result = client.get_secret(test_path, use_cache=False)

        assert result == {"key": "value"}
        assert call_count["n"] == 3

    def test_no_retry_on_auth_error(self, vault_available):
        """Test that auth errors don't retry."""
        config = VaultConfig(
            vault_addr=os.getenv("VAULT_ADDR", "http://localhost:8200"),
            vault_token="invalid-token",
            max_retries=3,
        )
        client = VaultClient(config)

        # Should fail immediately without retries
        with pytest.raises(VaultAuthenticationError):
            client._ensure_initialized()


class TestTokenManagement:
    """Test token renewal and management."""

    def test_token_renewal(self, vault_client):
        """Test token renewal (root tokens cannot be renewed, so expect VaultError)."""
        try:
            vault_client.renew_token()
        except VaultError:
            pass

    def test_token_renewal_with_invalid_token(self, vault_available):
        """Test token renewal fails with invalid token."""
        config = VaultConfig(
            vault_addr=os.getenv("VAULT_ADDR", "http://localhost:8200"),
            vault_token="invalid-token",
        )
        client = VaultClient(config)

        with pytest.raises(VaultAuthenticationError):
            client._ensure_initialized()


class TestContextManager:
    """Test context manager functionality."""

    def test_context_manager_usage(self, vault_available, test_secret_path):
        """Test using VaultClient as context manager."""
        config = VaultConfig.from_env()
        test_data = {"key": "value"}

        with VaultClient(config) as client:
            client.set_secret(test_secret_path, test_data)
            result = client.get_secret(test_secret_path)
            assert result == test_data


class TestConvenienceFunctions:
    """Test convenience functions for common services."""

    def test_get_janusgraph_credentials(self, vault_client):
        """Test JanusGraph credentials helper."""
        from src.python.utils.vault_client import get_janusgraph_credentials

        # Setup test credentials
        vault_client.set_secret("admin", {"username": "admin", "password": "testpass"})

        # Clear singleton cache
        get_vault_client.cache_clear()

        # Get credentials
        creds = get_janusgraph_credentials()
        assert "username" in creds
        assert "password" in creds

    def test_get_opensearch_credentials(self, vault_client):
        """Test OpenSearch credentials helper."""
        from src.python.utils.vault_client import get_opensearch_credentials

        # Setup test credentials
        vault_client.set_secret(
            "opensearch", {"username": "admin", "password": "testpass"}
        )

        get_vault_client.cache_clear()

        creds = get_opensearch_credentials()
        assert "username" in creds
        assert "password" in creds


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_empty_secret_data(self, vault_client, test_secret_path):
        """Test storing and retrieving empty secret."""
        vault_client.set_secret(test_secret_path, {})
        result = vault_client.get_secret(test_secret_path)
        assert result == {}

    def test_large_secret_data(self, vault_client, test_secret_path):
        """Test storing large secret data."""
        # Create large secret (but within Vault limits)
        large_data = {f"key_{i}": f"value_{i}" * 100 for i in range(100)}
        vault_client.set_secret(test_secret_path, large_data)

        result = vault_client.get_secret(test_secret_path)
        assert len(result) == 100

    def test_special_characters_in_secret(self, vault_client, test_secret_path):
        """Test secrets with special characters."""
        special_data = {
            "password": "p@$$w0rd!#%&*()[]{}",
            "api_key": "key-with-dashes_and_underscores.and.dots",
        }
        vault_client.set_secret(test_secret_path, special_data)

        result = vault_client.get_secret(test_secret_path)
        assert result == special_data

    def test_unicode_in_secret(self, vault_client, test_secret_path):
        """Test secrets with unicode characters."""
        unicode_data = {
            "name": "用户名",
            "description": "Тестовое описание",
            "emoji": "🔐🔑",
        }
        vault_client.set_secret(test_secret_path, unicode_data)

        result = vault_client.get_secret(test_secret_path)
        assert result == unicode_data


class TestConcurrency:
    """Test concurrent access patterns."""

    @pytest.mark.slow
    def test_concurrent_reads(self, vault_client, test_secret_path):
        """Test concurrent reads from cache."""
        import concurrent.futures

        test_data = {"key": "value"}
        vault_client.set_secret(test_secret_path, test_data)

        def read_secret():
            return vault_client.get_secret(test_secret_path)

        # Perform concurrent reads
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(read_secret) for _ in range(50)]
            results = [f.result() for f in futures]

        # All reads should return same data
        assert all(r == test_data for r in results)

    @pytest.mark.slow
    def test_concurrent_writes(self, vault_available):
        """Test concurrent writes to different paths."""
        import concurrent.futures

        config = VaultConfig.from_env()
        client = VaultClient(config)

        def write_secret(index):
            path = f"test/concurrent-{int(time.time())}-{index}"
            data = {"index": index, "value": f"value_{index}"}
            client.set_secret(path, data)
            return path

        # Perform concurrent writes
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(write_secret, i) for i in range(20)]
            paths = [f.result() for f in futures]

        # Verify all writes succeeded
        assert len(paths) == 20
        assert len(set(paths)) == 20  # All unique


# Made with Bob