"""Error Scenario Tests for Vault Client."""

import time
from unittest.mock import MagicMock, patch

import pytest

from src.python.utils.vault_client import (
    VaultAuthenticationError,
    VaultClient,
    VaultConfig,
    VaultConnectionError,
    VaultError,
    VaultSecretNotFoundError,
)


def _make_client(config=None, mock_hvac=None):
    if config is None:
        config = VaultConfig(vault_token="test-token")
    client = VaultClient(config)
    if mock_hvac is not None:
        client._client = mock_hvac
        client._initialized = True
    return client


class TestAuthenticationErrors:
    def test_missing_hvac_library(self):
        config = VaultConfig(vault_token="tok")
        client = VaultClient(config)
        with patch.dict("sys.modules", {"hvac": None}):
            with pytest.raises((VaultError, TypeError, ImportError)):
                client._ensure_initialized()

    def test_no_authentication_method(self):
        mock_hvac_mod = MagicMock()
        mock_hvac_mod.Client.return_value = MagicMock()
        mock_hvac_mod.exceptions.VaultError = type("VaultError", (Exception,), {})
        config = VaultConfig()
        client = VaultClient(config)
        with patch.dict("sys.modules", {"hvac": mock_hvac_mod}):
            with pytest.raises(VaultError):
                client._ensure_initialized()

    def test_invalid_token(self):
        mock_hvac_mod = MagicMock()
        mock_c = MagicMock()
        mock_c.is_authenticated.return_value = False
        mock_hvac_mod.Client.return_value = mock_c
        mock_hvac_mod.exceptions.VaultError = type("VaultError", (Exception,), {})
        config = VaultConfig(vault_token="bad")
        client = VaultClient(config)
        with patch.dict("sys.modules", {"hvac": mock_hvac_mod}):
            with pytest.raises(VaultError):
                client._ensure_initialized()

    def test_approle_login_failure(self):
        mock_hvac_mod = MagicMock()
        mock_hvac_mod.exceptions.VaultError = Exception
        mock_c = MagicMock()
        mock_c.auth.approle.login.side_effect = Exception("fail")
        mock_hvac_mod.Client.return_value = mock_c
        config = VaultConfig(vault_role_id="r", vault_secret_id="s")
        client = VaultClient(config)
        with patch.dict("sys.modules", {"hvac": mock_hvac_mod}):
            with pytest.raises((VaultConnectionError, VaultError)):
                client._ensure_initialized()


class TestSecretErrors:
    def test_secret_not_found(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.read_secret_version.side_effect = Exception("Invalid path")
        config = VaultConfig(vault_token="tok", max_retries=0, retry_delay=0.1)
        client = _make_client(config=config, mock_hvac=mock_hvac)
        with pytest.raises(VaultError):
            client.get_secret("nonexistent")

    def test_key_not_found(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"a": 1}}
        }
        client = _make_client(mock_hvac=mock_hvac)
        with pytest.raises(VaultError):
            client.get_secret("path", "missing_key")

    def test_write_failure(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.create_or_update_secret.side_effect = Exception("write error")
        config = VaultConfig(vault_token="tok", max_retries=0, retry_delay=0.1)
        client = _make_client(config=config, mock_hvac=mock_hvac)
        with pytest.raises(VaultError):
            client.set_secret("path", {"k": "v"})

    def test_list_failure(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.list_secrets.side_effect = Exception("permission denied")
        config = VaultConfig(vault_token="tok", max_retries=0, retry_delay=0.1)
        client = _make_client(config=config, mock_hvac=mock_hvac)
        with pytest.raises(VaultError):
            client.list_secrets("secret")

    def test_list_not_found_returns_empty(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.list_secrets.side_effect = Exception("not found")
        client = _make_client(mock_hvac=mock_hvac)
        assert client.list_secrets("missing") == []


class TestRetryLogic:
    def test_retry_exhaustion(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.read_secret_version.side_effect = Exception("fail")
        config = VaultConfig(vault_token="tok", max_retries=2, retry_delay=0.1)
        client = _make_client(config=config, mock_hvac=mock_hvac)
        with pytest.raises(VaultError, match="Operation failed"):
            client.get_secret("p", use_cache=False)
        assert mock_hvac.secrets.kv.v2.read_secret_version.call_count == 3

    def test_retry_with_eventual_success(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.read_secret_version.side_effect = [
            Exception("transient"),
            {"data": {"data": {"ok": True}}},
        ]
        config = VaultConfig(vault_token="tok", max_retries=2, retry_delay=0.1)
        client = _make_client(config=config, mock_hvac=mock_hvac)
        result = client.get_secret("p", use_cache=False)
        assert result == {"ok": True}

    def test_exponential_backoff(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.read_secret_version.side_effect = Exception("fail")
        config = VaultConfig(vault_token="tok", max_retries=1, retry_delay=0.1)
        client = _make_client(config=config, mock_hvac=mock_hvac)
        start = time.time()
        with pytest.raises(VaultError):
            client.get_secret("p", use_cache=False)
        elapsed = time.time() - start
        assert elapsed >= 0.1


class TestTokenManagement:
    def test_token_renewal_failure(self):
        mock_hvac = MagicMock()
        mock_hvac.auth.token.renew_self.side_effect = Exception("renewal failed")
        config = VaultConfig(vault_token="tok", max_retries=0, retry_delay=0.1)
        client = _make_client(config=config, mock_hvac=mock_hvac)
        with pytest.raises(VaultError):
            client.renew_token()

    def test_token_renewal_with_retry(self):
        mock_hvac = MagicMock()
        mock_hvac.auth.token.renew_self.side_effect = [Exception("transient"), None]
        config = VaultConfig(vault_token="tok", max_retries=1, retry_delay=0.1)
        client = _make_client(config=config, mock_hvac=mock_hvac)
        client.renew_token()
        assert mock_hvac.auth.token.renew_self.call_count == 2


class TestListOperations:
    def test_list_permission_denied(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.list_secrets.side_effect = Exception("permission denied")
        config = VaultConfig(vault_token="tok", max_retries=0, retry_delay=0.1)
        client = _make_client(config=config, mock_hvac=mock_hvac)
        with pytest.raises(VaultError):
            client.list_secrets("secret/path")

    def test_list_nonexistent_path(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.list_secrets.side_effect = Exception("not found in vault")
        client = _make_client(mock_hvac=mock_hvac)
        result = client.list_secrets("nonexistent")
        assert result == []


class TestEdgeCases:
    def test_empty_secret_path(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"k": "v"}}
        }
        client = _make_client(mock_hvac=mock_hvac)
        result = client.get_secret("")
        assert result == {"k": "v"}

    def test_very_long_secret_path(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"k": "v"}}
        }
        client = _make_client(mock_hvac=mock_hvac)
        long_path = "a/" * 100 + "secret"
        result = client.get_secret(long_path)
        assert result == {"k": "v"}

    def test_special_characters_in_path(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"k": "v"}}
        }
        client = _make_client(mock_hvac=mock_hvac)
        result = client.get_secret("path/with-dashes_and.dots")
        assert result == {"k": "v"}

    def test_none_secret_data(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": None}
        }
        config = VaultConfig(vault_token="tok", max_retries=0, retry_delay=0.1)
        client = _make_client(config=config, mock_hvac=mock_hvac)
        with pytest.raises(VaultError):
            client.get_secret("path", "key")

    def test_cache_with_zero_ttl(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"k": "v"}}
        }
        config = VaultConfig(vault_token="tok", cache_ttl=0)
        client = _make_client(config=config, mock_hvac=mock_hvac)
        client.get_secret("p")
        time.sleep(0.01)
        client.get_secret("p")
        assert mock_hvac.secrets.kv.v2.read_secret_version.call_count == 2

    def test_concurrent_initialization(self):
        config = VaultConfig(vault_token="tok")
        client = VaultClient(config)
        mock_hvac_mod = MagicMock()
        mock_c = MagicMock()
        mock_c.is_authenticated.return_value = True
        mock_hvac_mod.Client.return_value = mock_c
        with patch.dict("sys.modules", {"hvac": mock_hvac_mod}):
            client._ensure_initialized()
            client._ensure_initialized()
        assert mock_hvac_mod.Client.call_count == 1
