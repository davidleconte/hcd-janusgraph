"""
Unit Tests for Vault Client
============================
Tests for the VaultClient wrapper with mocking.
"""

import time
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from src.python.utils.vault_client import (
    VaultAuthenticationError,
    VaultClient,
    VaultConfig,
    VaultConnectionError,
    VaultError,
    VaultSecretNotFoundError,
)


class TestVaultConfig:
    def test_defaults(self):
        config = VaultConfig()
        assert config.vault_addr == "http://localhost:8200"
        assert config.vault_token is None
        assert config.vault_namespace == "janusgraph"
        assert config.vault_mount_point == "janusgraph"
        assert config.cache_ttl == 300
        assert config.max_retries == 3
        assert config.retry_delay == 1.0

    def test_custom_values(self):
        config = VaultConfig(
            vault_addr="http://vault:8200",
            vault_token="tok",
            vault_namespace="ns",
            vault_mount_point="mp",
            cache_ttl=60,
            max_retries=2,
            retry_delay=0.5,
        )
        assert config.vault_addr == "http://vault:8200"
        assert config.vault_token == "tok"
        assert config.cache_ttl == 60

    def test_from_env(self):
        with patch.dict("os.environ", {"VAULT_ADDR": "http://env:8200", "VAULT_TOKEN": "envtok"}):
            config = VaultConfig.from_env()
            assert config.vault_addr == "http://env:8200"
            assert config.vault_token == "envtok"


def _make_client(config=None, mock_hvac=None):
    """Helper to create a VaultClient with mocked hvac."""
    if config is None:
        config = VaultConfig(vault_token="test-token")
    client = VaultClient(config)
    if mock_hvac is not None:
        client._client = mock_hvac
        client._initialized = True
    return client


class TestVaultClient:
    def test_init_lazy(self):
        client = VaultClient(VaultConfig(vault_token="tok"))
        assert client._initialized is False
        assert client._client is None

    def test_ensure_initialized_token_auth(self):
        mock_hvac_mod = MagicMock()
        mock_hvac_client = MagicMock()
        mock_hvac_client.is_authenticated.return_value = True
        mock_hvac_mod.Client.return_value = mock_hvac_client

        config = VaultConfig(vault_token="test-token")
        client = VaultClient(config)

        with patch.dict("sys.modules", {"hvac": mock_hvac_mod}):
            client._ensure_initialized()

        assert client._initialized is True
        assert mock_hvac_client.token == "test-token"

    def test_ensure_initialized_approle_auth(self):
        mock_hvac_mod = MagicMock()
        mock_hvac_client = MagicMock()
        mock_hvac_client.is_authenticated.return_value = True
        mock_hvac_client.auth.approle.login.return_value = {"auth": {"client_token": "new-tok"}}
        mock_hvac_mod.Client.return_value = mock_hvac_client

        config = VaultConfig(vault_role_id="role", vault_secret_id="secret")
        client = VaultClient(config)

        with patch.dict("sys.modules", {"hvac": mock_hvac_mod}):
            client._ensure_initialized()

        assert client._initialized is True

    def test_ensure_initialized_no_auth(self):
        mock_hvac_mod = MagicMock()
        mock_hvac_mod.Client.return_value = MagicMock()
        mock_hvac_mod.exceptions.VaultError = type("VaultError", (Exception,), {})

        config = VaultConfig()
        client = VaultClient(config)

        with patch.dict("sys.modules", {"hvac": mock_hvac_mod}):
            with pytest.raises(VaultError):
                client._ensure_initialized()

    def test_ensure_initialized_auth_failed(self):
        mock_hvac_mod = MagicMock()
        mock_hvac_client = MagicMock()
        mock_hvac_client.is_authenticated.return_value = False
        mock_hvac_mod.Client.return_value = mock_hvac_client
        mock_hvac_mod.exceptions.VaultError = type("VaultError", (Exception,), {})

        config = VaultConfig(vault_token="bad")
        client = VaultClient(config)

        with patch.dict("sys.modules", {"hvac": mock_hvac_mod}):
            with pytest.raises(VaultError):
                client._ensure_initialized()

    def test_get_secret_success(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"username": "admin", "password": "secret"}}
        }
        client = _make_client(mock_hvac=mock_hvac)
        result = client.get_secret("admin")
        assert result == {"username": "admin", "password": "secret"}

    def test_get_secret_with_key(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"username": "admin", "password": "secret"}}
        }
        client = _make_client(mock_hvac=mock_hvac)
        assert client.get_secret("admin", "password") == "secret"

    def test_get_secret_key_not_found(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"username": "admin"}}
        }
        client = _make_client(mock_hvac=mock_hvac)
        with pytest.raises(VaultError):
            client.get_secret("admin", "missing_key")

    def test_get_secret_caching(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"val": "cached"}}
        }
        client = _make_client(mock_hvac=mock_hvac)
        client.get_secret("path1")
        client.get_secret("path1")
        assert mock_hvac.secrets.kv.v2.read_secret_version.call_count == 1

    def test_get_secret_no_cache(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"val": "x"}}
        }
        client = _make_client(mock_hvac=mock_hvac)
        client.get_secret("p", use_cache=False)
        client.get_secret("p", use_cache=False)
        assert mock_hvac.secrets.kv.v2.read_secret_version.call_count == 2

    def test_get_secret_cache_expiry(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"val": "x"}}
        }
        config = VaultConfig(vault_token="tok", cache_ttl=0)
        client = _make_client(config=config, mock_hvac=mock_hvac)
        client.get_secret("p")
        time.sleep(0.01)
        client.get_secret("p")
        assert mock_hvac.secrets.kv.v2.read_secret_version.call_count == 2

    def test_get_credentials(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"username": "u", "password": "p"}}
        }
        client = _make_client(mock_hvac=mock_hvac)
        creds = client.get_credentials("svc")
        assert creds == {"username": "u", "password": "p"}

    def test_get_credentials_missing_fields(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"username": "u"}}
        }
        client = _make_client(mock_hvac=mock_hvac)
        with pytest.raises(VaultError, match="missing username or password"):
            client.get_credentials("svc")

    def test_set_secret(self):
        mock_hvac = MagicMock()
        client = _make_client(mock_hvac=mock_hvac)
        client.set_secret("path", {"key": "val"})
        mock_hvac.secrets.kv.v2.create_or_update_secret.assert_called_once()

    def test_set_secret_invalidates_cache(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"val": "x"}}
        }
        client = _make_client(mock_hvac=mock_hvac)
        client.get_secret("mypath")
        assert "mypath" in client._cache
        client.set_secret("mypath", {"val": "y"})
        assert "mypath" not in client._cache

    def test_list_secrets(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.list_secrets.return_value = {
            "data": {"keys": ["a", "b"]}
        }
        client = _make_client(mock_hvac=mock_hvac)
        assert client.list_secrets() == ["a", "b"]

    def test_list_secrets_not_found(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.list_secrets.side_effect = Exception("not found")
        client = _make_client(mock_hvac=mock_hvac)
        assert client.list_secrets() == []

    def test_clear_cache(self):
        mock_hvac = MagicMock()
        client = _make_client(mock_hvac=mock_hvac)
        client._cache["key"] = ("val", time.time())
        client.clear_cache()
        assert len(client._cache) == 0

    def test_renew_token(self):
        mock_hvac = MagicMock()
        client = _make_client(mock_hvac=mock_hvac)
        client.renew_token()
        mock_hvac.auth.token.renew_self.assert_called_once()

    def test_retry_logic(self):
        mock_hvac = MagicMock()
        call_count = 0
        def failing_read(*a, **kw):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("transient")
            return {"data": {"data": {"val": "ok"}}}
        mock_hvac.secrets.kv.v2.read_secret_version.side_effect = failing_read
        config = VaultConfig(vault_token="tok", max_retries=3, retry_delay=0.1)
        client = _make_client(config=config, mock_hvac=mock_hvac)
        result = client.get_secret("p", use_cache=False)
        assert result == {"val": "ok"}

    def test_retry_exhausted(self):
        mock_hvac = MagicMock()
        mock_hvac.secrets.kv.v2.read_secret_version.side_effect = Exception("permanent")
        config = VaultConfig(vault_token="tok", max_retries=1, retry_delay=0.1)
        client = _make_client(config=config, mock_hvac=mock_hvac)
        with pytest.raises(VaultError, match="Operation failed"):
            client.get_secret("p", use_cache=False)

    def test_context_manager(self):
        config = VaultConfig(vault_token="tok")
        with VaultClient(config) as client:
            assert client is not None

    def test_from_env(self):
        with patch.dict("os.environ", {"VAULT_TOKEN": "envtok"}):
            client = VaultClient.from_env()
            assert client.config.vault_token == "envtok"


class TestVaultExceptions:
    def test_hierarchy(self):
        assert issubclass(VaultAuthenticationError, VaultError)
        assert issubclass(VaultConnectionError, VaultError)
        assert issubclass(VaultSecretNotFoundError, VaultError)

    def test_messages(self):
        e = VaultError("test")
        assert str(e) == "test"
        e2 = VaultSecretNotFoundError("not found")
        assert "not found" in str(e2)
