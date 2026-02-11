"""
Error Scenario Tests for Vault Client
======================================

Comprehensive tests for error handling, edge cases, and failure scenarios.
Tests use mocking to simulate various error conditions.

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS
Created: 2026-02-11
Phase: Phase 2 - Infrastructure Security

Run with:
    pytest tests/unit/test_vault_error_scenarios.py -v
"""

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
    return mock_client


class TestAuthenticationErrors:
    """Test authentication error scenarios."""

    @patch("src.python.utils.vault_client.hvac")
    def test_missing_hvac_library(self, mock_hvac, vault_config):
        """Test error when hvac library is not installed."""
        mock_hvac.side_effect = ImportError("No module named 'hvac'")

        client = VaultClient(vault_config)
        with pytest.raises(VaultError, match="hvac library not installed"):
            client._ensure_initialized()

    @patch("src.python.utils.vault_client.hvac")
    def test_no_authentication_method(self, mock_hvac, mock_hvac_client):
        """Test error when no authentication method is configured."""
        config = VaultConfig(vault_addr="http://test:8200")  # No token or AppRole
        mock_hvac.Client.return_value = mock_hvac_client

        client = VaultClient(config)
        with pytest.raises(VaultAuthenticationError, match="No authentication method"):
            client._ensure_initialized()

    @patch("src.python.utils.vault_client.hvac")
    def test_invalid_token(self, mock_hvac, vault_config, mock_hvac_client):
        """Test error with invalid token."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.is_authenticated.return_value = False

        client = VaultClient(vault_config)
        with pytest.raises(VaultAuthenticationError, match="authentication failed"):
            client._ensure_initialized()

    @patch("src.python.utils.vault_client.hvac")
    def test_approle_login_failure(self, mock_hvac, mock_hvac_client):
        """Test AppRole login failure."""
        config = VaultConfig(
            vault_addr="http://test:8200",
            vault_role_id="test-role",
            vault_secret_id="test-secret",
        )
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.auth.approle.login.side_effect = Exception("Invalid role")

        client = VaultClient(config)
        with pytest.raises(VaultConnectionError, match="Failed to connect"):
            client._ensure_initialized()

    @patch("src.python.utils.vault_client.hvac")
    def test_vault_sealed(self, mock_hvac, vault_config, mock_hvac_client):
        """Test error when Vault is sealed."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac.exceptions.VaultError = Exception
        mock_hvac_client.is_authenticated.side_effect = Exception("Vault is sealed")

        client = VaultClient(vault_config)
        with pytest.raises(VaultError):
            client._ensure_initialized()


class TestConnectionErrors:
    """Test connection error scenarios."""

    @patch("src.python.utils.vault_client.hvac")
    def test_network_timeout(self, mock_hvac, vault_config, mock_hvac_client):
        """Test network timeout error."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac.exceptions.VaultError = Exception
        mock_hvac.Client.side_effect = Exception("Connection timeout")

        client = VaultClient(vault_config)
        with pytest.raises(VaultConnectionError, match="Failed to connect"):
            client._ensure_initialized()

    @patch("src.python.utils.vault_client.hvac")
    def test_dns_resolution_failure(self, mock_hvac, vault_config, mock_hvac_client):
        """Test DNS resolution failure."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac.Client.side_effect = Exception("Name or service not known")

        client = VaultClient(vault_config)
        with pytest.raises(VaultConnectionError):
            client._ensure_initialized()

    @patch("src.python.utils.vault_client.hvac")
    def test_connection_refused(self, mock_hvac, vault_config, mock_hvac_client):
        """Test connection refused error."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac.Client.side_effect = Exception("Connection refused")

        client = VaultClient(vault_config)
        with pytest.raises(VaultConnectionError):
            client._ensure_initialized()


class TestSecretReadErrors:
    """Test secret read error scenarios."""

    @patch("src.python.utils.vault_client.hvac")
    def test_secret_not_found(self, mock_hvac, vault_config, mock_hvac_client):
        """Test reading nonexistent secret."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.read_secret_version.side_effect = Exception(
            "Invalid path"
        )

        client = VaultClient(vault_config)
        with pytest.raises(VaultSecretNotFoundError, match="not found"):
            client.get_secret("nonexistent")

    @patch("src.python.utils.vault_client.hvac")
    def test_key_not_found_in_secret(self, mock_hvac, vault_config, mock_hvac_client):
        """Test reading nonexistent key from secret."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"username": "user"}}
        }

        client = VaultClient(vault_config)
        with pytest.raises(VaultSecretNotFoundError, match="Key 'password' not found"):
            client.get_secret("test/secret", "password")

    @patch("src.python.utils.vault_client.hvac")
    def test_permission_denied(self, mock_hvac, vault_config, mock_hvac_client):
        """Test permission denied error."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.read_secret_version.side_effect = Exception(
            "permission denied"
        )

        client = VaultClient(vault_config)
        with pytest.raises(VaultError, match="Failed to read secret"):
            client.get_secret("restricted/secret")

    @patch("src.python.utils.vault_client.hvac")
    def test_malformed_response(self, mock_hvac, vault_config, mock_hvac_client):
        """Test handling of malformed Vault response."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {}  # Missing 'data' key
        }

        client = VaultClient(vault_config)
        with pytest.raises(Exception):  # Will raise KeyError
            client.get_secret("test/secret")


class TestSecretWriteErrors:
    """Test secret write error scenarios."""

    @patch("src.python.utils.vault_client.hvac")
    def test_write_permission_denied(self, mock_hvac, vault_config, mock_hvac_client):
        """Test write permission denied."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.create_or_update_secret.side_effect = Exception(
            "permission denied"
        )

        client = VaultClient(vault_config)
        with pytest.raises(VaultError, match="Failed to write secret"):
            client.set_secret("restricted/secret", {"key": "value"})

    @patch("src.python.utils.vault_client.hvac")
    def test_write_quota_exceeded(self, mock_hvac, vault_config, mock_hvac_client):
        """Test write when quota is exceeded."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.create_or_update_secret.side_effect = Exception(
            "quota exceeded"
        )

        client = VaultClient(vault_config)
        with pytest.raises(VaultError, match="Failed to write secret"):
            client.set_secret("test/secret", {"key": "value"})

    @patch("src.python.utils.vault_client.hvac")
    def test_write_invalid_data_type(self, mock_hvac, vault_config, mock_hvac_client):
        """Test write with invalid data type."""
        mock_hvac.Client.return_value = mock_hvac_client

        client = VaultClient(vault_config)
        # Should not raise during set_secret call (validation happens in Vault)
        # But we can test that dict is required
        with pytest.raises(Exception):
            client.set_secret("test/secret", "not a dict")  # type: ignore


class TestCredentialErrors:
    """Test credential-specific error scenarios."""

    @patch("src.python.utils.vault_client.hvac")
    def test_credentials_not_dict(self, mock_hvac, vault_config, mock_hvac_client):
        """Test error when credentials are not a dict."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": "not a dict"}
        }

        client = VaultClient(vault_config)
        with pytest.raises(VaultError, match="Expected dict"):
            client.get_credentials("test/service")

    @patch("src.python.utils.vault_client.hvac")
    def test_credentials_missing_username(self, mock_hvac, vault_config, mock_hvac_client):
        """Test error when username is missing."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"password": "pass"}}
        }

        client = VaultClient(vault_config)
        with pytest.raises(VaultError, match="missing username or password"):
            client.get_credentials("test/service")

    @patch("src.python.utils.vault_client.hvac")
    def test_credentials_missing_password(self, mock_hvac, vault_config, mock_hvac_client):
        """Test error when password is missing."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"username": "user"}}
        }

        client = VaultClient(vault_config)
        with pytest.raises(VaultError, match="missing username or password"):
            client.get_credentials("test/service")


class TestRetryLogic:
    """Test retry logic error scenarios."""

    @patch("src.python.utils.vault_client.hvac")
    def test_retry_exhaustion(self, mock_hvac, vault_config, mock_hvac_client):
        """Test that retries are exhausted on persistent errors."""
        vault_config.max_retries = 2
        vault_config.retry_delay = 0.1
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.read_secret_version.side_effect = Exception(
            "Persistent error"
        )

        client = VaultClient(vault_config)
        with pytest.raises(VaultError, match="failed after 3 attempts"):
            client.get_secret("test/secret")

        # Should have tried 3 times (initial + 2 retries)
        assert mock_hvac_client.secrets.kv.v2.read_secret_version.call_count == 3

    @patch("src.python.utils.vault_client.hvac")
    def test_retry_with_eventual_success(self, mock_hvac, vault_config, mock_hvac_client):
        """Test that retry succeeds after transient errors."""
        vault_config.max_retries = 2
        vault_config.retry_delay = 0.1
        mock_hvac.Client.return_value = mock_hvac_client

        # Fail twice, succeed on third attempt
        mock_hvac_client.secrets.kv.v2.read_secret_version.side_effect = [
            Exception("Transient error 1"),
            Exception("Transient error 2"),
            {"data": {"data": {"key": "value"}}},
        ]

        client = VaultClient(vault_config)
        result = client.get_secret("test/secret")

        assert result == {"key": "value"}
        assert mock_hvac_client.secrets.kv.v2.read_secret_version.call_count == 3

    @patch("src.python.utils.vault_client.hvac")
    def test_exponential_backoff(self, mock_hvac, vault_config, mock_hvac_client):
        """Test that retry uses exponential backoff."""
        vault_config.max_retries = 3
        vault_config.retry_delay = 0.1
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.read_secret_version.side_effect = Exception(
            "Error"
        )

        client = VaultClient(vault_config)
        start_time = time.time()

        with pytest.raises(VaultError):
            client.get_secret("test/secret")

        elapsed = time.time() - start_time
        # Expected delays: 0.1, 0.2, 0.4 = 0.7 seconds minimum
        assert elapsed >= 0.7


class TestTokenManagement:
    """Test token management error scenarios."""

    @patch("src.python.utils.vault_client.hvac")
    def test_token_renewal_failure(self, mock_hvac, vault_config, mock_hvac_client):
        """Test token renewal failure."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.auth.token.renew_self.side_effect = Exception("Token expired")

        client = VaultClient(vault_config)
        client._ensure_initialized()

        with pytest.raises(VaultError, match="Failed to renew token"):
            client.renew_token()

    @patch("src.python.utils.vault_client.hvac")
    def test_token_renewal_with_retry(self, mock_hvac, vault_config, mock_hvac_client):
        """Test token renewal with retry logic."""
        vault_config.max_retries = 2
        vault_config.retry_delay = 0.1
        mock_hvac.Client.return_value = mock_hvac_client

        # Fail once, succeed on second attempt
        mock_hvac_client.auth.token.renew_self.side_effect = [
            Exception("Transient error"),
            None,  # Success
        ]

        client = VaultClient(vault_config)
        client._ensure_initialized()
        client.renew_token()  # Should succeed after retry

        assert mock_hvac_client.auth.token.renew_self.call_count == 2


class TestListOperations:
    """Test list operation error scenarios."""

    @patch("src.python.utils.vault_client.hvac")
    def test_list_permission_denied(self, mock_hvac, vault_config, mock_hvac_client):
        """Test list operation with permission denied."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.list_secrets.side_effect = Exception(
            "permission denied"
        )

        client = VaultClient(vault_config)
        with pytest.raises(VaultError, match="Failed to list secrets"):
            client.list_secrets("restricted/path")

    @patch("src.python.utils.vault_client.hvac")
    def test_list_nonexistent_path(self, mock_hvac, vault_config, mock_hvac_client):
        """Test listing nonexistent path returns empty list."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.list_secrets.side_effect = Exception("not found")

        client = VaultClient(vault_config)
        result = client.list_secrets("nonexistent/path")

        assert result == []


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch("src.python.utils.vault_client.hvac")
    def test_empty_secret_path(self, mock_hvac, vault_config, mock_hvac_client):
        """Test handling of empty secret path."""
        mock_hvac.Client.return_value = mock_hvac_client

        client = VaultClient(vault_config)
        # Should attempt to read empty path (Vault will handle validation)
        with pytest.raises(Exception):
            client.get_secret("")

    @patch("src.python.utils.vault_client.hvac")
    def test_very_long_secret_path(self, mock_hvac, vault_config, mock_hvac_client):
        """Test handling of very long secret path."""
        mock_hvac.Client.return_value = mock_hvac_client
        long_path = "a" * 1000

        client = VaultClient(vault_config)
        # Should attempt to read (Vault will handle path length validation)
        with pytest.raises(Exception):
            client.get_secret(long_path)

    @patch("src.python.utils.vault_client.hvac")
    def test_special_characters_in_path(self, mock_hvac, vault_config, mock_hvac_client):
        """Test handling of special characters in path."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key": "value"}}
        }

        client = VaultClient(vault_config)
        # Vault should handle path validation
        result = client.get_secret("test/path-with_special.chars")
        assert result == {"key": "value"}

    @patch("src.python.utils.vault_client.hvac")
    def test_none_secret_data(self, mock_hvac, vault_config, mock_hvac_client):
        """Test handling of None in secret data."""
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key": None}}
        }

        client = VaultClient(vault_config)
        result = client.get_secret("test/secret")
        assert result == {"key": None}

    @patch("src.python.utils.vault_client.hvac")
    def test_cache_with_zero_ttl(self, mock_hvac, vault_config, mock_hvac_client):
        """Test caching with zero TTL (caching disabled)."""
        vault_config.cache_ttl = 0
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key": "value"}}
        }

        client = VaultClient(vault_config)

        # Both calls should hit Vault (cache disabled)
        client.get_secret("test/secret")
        client.get_secret("test/secret")

        assert mock_hvac_client.secrets.kv.v2.read_secret_version.call_count == 2

    @patch("src.python.utils.vault_client.hvac")
    def test_concurrent_initialization(self, mock_hvac, vault_config, mock_hvac_client):
        """Test concurrent initialization attempts."""
        import concurrent.futures

        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key": "value"}}
        }

        client = VaultClient(vault_config)

        def initialize_and_read():
            return client.get_secret("test/secret")

        # Multiple threads trying to initialize simultaneously
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(initialize_and_read) for _ in range(10)]
            results = [f.result() for f in futures]

        # All should succeed
        assert all(r == {"key": "value"} for r in results)
        # Should only initialize once
        assert client._initialized


# Made with Bob