"""
Unit Tests for Vault Client
============================

Tests for the VaultClient wrapper with mocking.

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS
Created: 2026-02-11
Phase: Phase 2 - Infrastructure Security
"""

import os
import time
from unittest.mock import MagicMock, Mock, patch

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


@pytest.fixture
def vault_config():
    """Create test Vault configuration."""
    return VaultConfig(
        vault_addr="http://test-vault:8200",
        vault_token="test-token",
        vault_namespace="test",
        vault_mount_point="test",
        cache_ttl=60,
        max_retries=2,
        retry_delay=0.1,
    )


@pytest.fixture
def mock_hvac_client():
    """Create mock hvac client."""
    mock_client = MagicMock()
    mock_client.is_authenticated.return_value = True
    mock_client.secrets.kv.v2.read_secret_version.return_value = {
        "data": {
            "data": {
                "username": "testuser",
                "password": "testpass",
            }
        }
    }
    return mock_client


class TestVaultConfig:
    """Test VaultConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = VaultConfig()
        assert config.vault_addr == "http://localhost:8200"
        assert config.vault_namespace == "janusgraph"
        assert config.cache_ttl == 300
        assert config.max_retries == 3

    def test_custom_config(self):
        """Test custom configuration."""
        config = VaultConfig(
            vault_addr="http://custom:8200",
            vault_token="custom-token",
            cache_ttl=600,
        )
        assert config.vault_addr == "http://custom:8200"
        assert config.vault_token == "custom-token"
        assert config.cache_ttl == 600

    def test_from_env(self, monkeypatch):
        """Test loading configuration from environment."""
        monkeypatch.setenv("VAULT_ADDR", "http://env-vault:8200")
        monkeypatch.setenv("VAULT_TOKEN", "env-token")
        monkeypatch.setenv("VAULT_NAMESPACE", "env-namespace")
        monkeypatch.setenv("VAULT_CACHE_TTL", "120")

        config = VaultConfig.from_env()
        assert config.vault_addr == "http://env-vault:8200"
        assert config.vault_token == "env-token"
        assert config.vault_namespace == "env-namespace"
        assert config.cache_ttl == 120

    def test_validation_cache_ttl(self):
        """Test cache_ttl validation."""
        with pytest.raises(ValueError):
            VaultConfig(cache_ttl=-1)

    def test_validation_max_retries(self):
        """Test max_retries validation."""
        with pytest.raises(ValueError):
            VaultConfig(max_retries=11)  # Max is 10


class TestVaultClient:
    """Test VaultClient functionality."""

    @patch("src.python.utils.vault_client.hvac")
    def test_initialization_with_token(self, mock_hvac, vault_config, mock_hvac_client):
        """Test client initialization with token authentication."""
        mock_hvac.Client.return_value = mock_hvac_client

        client = VaultClient(vault_config)
        assert not client._initialized

        # Trigger initialization
        client._ensure_initialized()
        assert client._initialized
        mock_hvac.Client.assert_called_once_with(url=vault_config.vault_addr)

    @patch("src.python.utils.vault_client.hvac")
    def test_initialization_with_approle(self, mock_hvac, mock_hvac_client):
        """Test client initialization with AppRole authentication."""
        config = VaultConfig(
            vault_addr="http://test:8200",
            vault_role_id="test-role",
            vault_secret_id="test-secret",
        )
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.auth.approle.login.return_value = {
            "auth": {"client_token": "approle-token"}
        }

        client = VaultClient(config)
        client._ensure_initialized()

        mock_hvac_client.auth.approle.login.assert_called_once_with(
            role_id="test-role",
            secret_id="test-secret",
        )

    @patch("src.python.utils.vault_client.hvac")
    def test_initialization_no_auth(self, mock_hvac, mock_hvac_client):
        """Test client initialization fails without authentication."""
        config = VaultConfig(vault_addr="http://test:8200")
        mock_hvac.Client.return_value = mock_hvac_client

        client = VaultClient(config)
        with pytest.raises(VaultAuthenticationError):
            client._ensure_initialized()

    @patch("src.python.utils.vault_client.hvac")
    def test_initialization_auth_failed(self, mock_hvac, vault_config, mock_hvac_client):
        """Test client initialization fails when authentication fails."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.is_authenticated.return_value = False

        client = VaultClient(vault_config)
        with pytest.raises(VaultAuthenticationError):
            client._ensure_initialized()

    @patch("src.python.utils.vault_client.hvac")
    def test_get_secret_success(self, mock_hvac, vault_config, mock_hvac_client):
        """Test successful secret retrieval."""
        mock_hvac.Client.return_value = mock_hvac_client

        client = VaultClient(vault_config)
        result = client.get_secret("test/secret")

        assert result == {"username": "testuser", "password": "testpass"}
        mock_hvac_client.secrets.kv.v2.read_secret_version.assert_called_once()

    @patch("src.python.utils.vault_client.hvac")
    def test_get_secret_with_key(self, mock_hvac, vault_config, mock_hvac_client):
        """Test secret retrieval with specific key."""
        mock_hvac.Client.return_value = mock_hvac_client

        client = VaultClient(vault_config)
        result = client.get_secret("test/secret", "password")

        assert result == "testpass"

    @patch("src.python.utils.vault_client.hvac")
    def test_get_secret_not_found(self, mock_hvac, vault_config, mock_hvac_client):
        """Test secret not found error."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.read_secret_version.side_effect = Exception(
            "Invalid path"
        )

        client = VaultClient(vault_config)
        with pytest.raises(VaultSecretNotFoundError):
            client.get_secret("nonexistent")

    @patch("src.python.utils.vault_client.hvac")
    def test_get_secret_key_not_found(self, mock_hvac, vault_config, mock_hvac_client):
        """Test key not found in secret."""
        mock_hvac.Client.return_value = mock_hvac_client

        client = VaultClient(vault_config)
        with pytest.raises(VaultSecretNotFoundError):
            client.get_secret("test/secret", "nonexistent_key")

    @patch("src.python.utils.vault_client.hvac")
    def test_get_secret_caching(self, mock_hvac, vault_config, mock_hvac_client):
        """Test secret caching."""
        mock_hvac.Client.return_value = mock_hvac_client

        client = VaultClient(vault_config)

        # First call - should hit Vault
        result1 = client.get_secret("test/secret")
        assert mock_hvac_client.secrets.kv.v2.read_secret_version.call_count == 1

        # Second call - should use cache
        result2 = client.get_secret("test/secret")
        assert mock_hvac_client.secrets.kv.v2.read_secret_version.call_count == 1
        assert result1 == result2

    @patch("src.python.utils.vault_client.hvac")
    def test_get_secret_cache_expiry(self, mock_hvac, vault_config, mock_hvac_client):
        """Test cache expiry."""
        vault_config.cache_ttl = 1  # 1 second TTL
        mock_hvac.Client.return_value = mock_hvac_client

        client = VaultClient(vault_config)

        # First call
        client.get_secret("test/secret")
        assert mock_hvac_client.secrets.kv.v2.read_secret_version.call_count == 1

        # Wait for cache to expire
        time.sleep(1.1)

        # Second call - should hit Vault again
        client.get_secret("test/secret")
        assert mock_hvac_client.secrets.kv.v2.read_secret_version.call_count == 2

    @patch("src.python.utils.vault_client.hvac")
    def test_get_secret_no_cache(self, mock_hvac, vault_config, mock_hvac_client):
        """Test secret retrieval without caching."""
        mock_hvac.Client.return_value = mock_hvac_client

        client = VaultClient(vault_config)

        # Both calls should hit Vault
        client.get_secret("test/secret", use_cache=False)
        client.get_secret("test/secret", use_cache=False)
        assert mock_hvac_client.secrets.kv.v2.read_secret_version.call_count == 2

    @patch("src.python.utils.vault_client.hvac")
    def test_get_credentials(self, mock_hvac, vault_config, mock_hvac_client):
        """Test credential retrieval."""
        mock_hvac.Client.return_value = mock_hvac_client

        client = VaultClient(vault_config)
        creds = client.get_credentials("test/service")

        assert creds["username"] == "testuser"
        assert creds["password"] == "testpass"

    @patch("src.python.utils.vault_client.hvac")
    def test_get_credentials_missing_fields(self, mock_hvac, vault_config, mock_hvac_client):
        """Test credential retrieval with missing fields."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"username": "testuser"}}  # Missing password
        }

        client = VaultClient(vault_config)
        with pytest.raises(VaultError, match="missing username or password"):
            client.get_credentials("test/service")

    @patch("src.python.utils.vault_client.hvac")
    def test_set_secret(self, mock_hvac, vault_config, mock_hvac_client):
        """Test secret storage."""
        mock_hvac.Client.return_value = mock_hvac_client

        client = VaultClient(vault_config)
        data = {"username": "newuser", "password": "newpass"}
        client.set_secret("test/new", data)

        mock_hvac_client.secrets.kv.v2.create_or_update_secret.assert_called_once_with(
            path="test/new",
            secret=data,
            mount_point="test",
        )

    @patch("src.python.utils.vault_client.hvac")
    def test_set_secret_invalidates_cache(self, mock_hvac, vault_config, mock_hvac_client):
        """Test that set_secret invalidates cache."""
        mock_hvac.Client.return_value = mock_hvac_client

        client = VaultClient(vault_config)

        # Get and cache secret
        client.get_secret("test/secret")
        assert len(client._cache) > 0

        # Set secret - should invalidate cache
        client.set_secret("test/secret", {"new": "data"})
        assert len(client._cache) == 0

    @patch("src.python.utils.vault_client.hvac")
    def test_list_secrets(self, mock_hvac, vault_config, mock_hvac_client):
        """Test listing secrets."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.list_secrets.return_value = {
            "data": {"keys": ["secret1", "secret2", "secret3"]}
        }

        client = VaultClient(vault_config)
        secrets = client.list_secrets("test/path")

        assert secrets == ["secret1", "secret2", "secret3"]

    @patch("src.python.utils.vault_client.hvac")
    def test_list_secrets_not_found(self, mock_hvac, vault_config, mock_hvac_client):
        """Test listing secrets when path not found."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.list_secrets.side_effect = Exception("not found")

        client = VaultClient(vault_config)
        secrets = client.list_secrets("nonexistent")

        assert secrets == []

    @patch("src.python.utils.vault_client.hvac")
    def test_clear_cache(self, mock_hvac, vault_config, mock_hvac_client):
        """Test cache clearing."""
        mock_hvac.Client.return_value = mock_hvac_client

        client = VaultClient(vault_config)
        client.get_secret("test/secret")
        assert len(client._cache) > 0

        client.clear_cache()
        assert len(client._cache) == 0

    @patch("src.python.utils.vault_client.hvac")
    def test_renew_token(self, mock_hvac, vault_config, mock_hvac_client):
        """Test token renewal."""
        mock_hvac.Client.return_value = mock_hvac_client

        client = VaultClient(vault_config)
        client.renew_token()

        mock_hvac_client.auth.token.renew_self.assert_called_once()

    @patch("src.python.utils.vault_client.hvac")
    def test_retry_logic(self, mock_hvac, vault_config, mock_hvac_client):
        """Test retry logic on failures."""
        vault_config.max_retries = 2
        vault_config.retry_delay = 0.1
        mock_hvac.Client.return_value = mock_hvac_client

        # Fail twice, succeed on third attempt
        mock_hvac_client.secrets.kv.v2.read_secret_version.side_effect = [
            Exception("Temporary error"),
            Exception("Temporary error"),
            {"data": {"data": {"key": "value"}}},
        ]

        client = VaultClient(vault_config)
        result = client.get_secret("test/secret")

        assert result == {"key": "value"}
        assert mock_hvac_client.secrets.kv.v2.read_secret_version.call_count == 3

    @patch("src.python.utils.vault_client.hvac")
    def test_retry_exhausted(self, mock_hvac, vault_config, mock_hvac_client):
        """Test retry exhaustion."""
        vault_config.max_retries = 2
        vault_config.retry_delay = 0.1
        mock_hvac.Client.return_value = mock_hvac_client

        # Always fail
        mock_hvac_client.secrets.kv.v2.read_secret_version.side_effect = Exception(
            "Persistent error"
        )

        client = VaultClient(vault_config)
        with pytest.raises(VaultError, match="failed after 3 attempts"):
            client.get_secret("test/secret")

    @patch("src.python.utils.vault_client.hvac")
    def test_context_manager(self, mock_hvac, vault_config, mock_hvac_client):
        """Test context manager usage."""
        mock_hvac.Client.return_value = mock_hvac_client

        with VaultClient(vault_config) as client:
            result = client.get_secret("test/secret")
            assert result is not None


class TestConvenienceFunctions:
    """Test convenience functions."""

    @patch("src.python.utils.vault_client.VaultClient")
    def test_get_janusgraph_credentials(self, mock_client_class):
        """Test JanusGraph credentials helper."""
        from src.python.utils.vault_client import get_janusgraph_credentials

        mock_instance = Mock()
        mock_instance.get_credentials.return_value = {
            "username": "admin",
            "password": "pass",
        }
        mock_client_class.from_env.return_value = mock_instance

        # Clear cache first
        get_vault_client.cache_clear()

        creds = get_janusgraph_credentials()
        assert creds["username"] == "admin"
        mock_instance.get_credentials.assert_called_with("admin")

    @patch("src.python.utils.vault_client.VaultClient")
    def test_get_opensearch_credentials(self, mock_client_class):
        """Test OpenSearch credentials helper."""
        from src.python.utils.vault_client import get_opensearch_credentials

        mock_instance = Mock()
        mock_instance.get_credentials.return_value = {
            "username": "admin",
            "password": "pass",
        }
        mock_client_class.from_env.return_value = mock_instance

        get_vault_client.cache_clear()

        creds = get_opensearch_credentials()
        assert creds["username"] == "admin"
        mock_instance.get_credentials.assert_called_with("opensearch")

# Made with Bob
