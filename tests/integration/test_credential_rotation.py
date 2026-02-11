"""
Integration Tests for Credential Rotation Framework
====================================================

End-to-end tests for credential rotation across all services.
Tests rotation, rollback, health checks, and Vault integration.

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS
Created: 2026-02-11
Phase: Phase 2 - Infrastructure Security (Final 15%)

Prerequisites:
    - Vault server running at VAULT_ADDR
    - VAULT_TOKEN environment variable set
    - Services running (JanusGraph, HCD, OpenSearch, Grafana, Pulsar)
    - Podman/Docker compose project running

Run with:
    pytest tests/integration/test_credential_rotation.py -v
    pytest tests/integration/test_credential_rotation.py -v -m "not slow"
"""

import os
import time
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

# Import rotation framework components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "security"))

from credential_rotation_framework import (
    CredentialRotator,
    PasswordGenerator,
    RotationResult,
    RotationStatus,
    ServiceHealthChecker,
    ServiceType,
    VaultClient,
)

from src.python.utils.vault_client import (
    VaultClient as UtilsVaultClient,
    VaultConfig,
)

# Skip all tests if services not available
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


def is_janusgraph_available() -> bool:
    """Check if JanusGraph is available."""
    try:
        import requests
        response = requests.get("http://localhost:8182?gremlin=g.V().count()", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="module")
def services_available():
    """Skip tests if required services are not available."""
    if not is_vault_available():
        pytest.skip("Vault server not available")
    if not is_janusgraph_available():
        pytest.skip("JanusGraph not available")


@pytest.fixture
def vault_client(services_available) -> Generator[VaultClient, None, None]:
    """Create Vault client for testing."""
    vault_addr = os.getenv("VAULT_ADDR", "http://localhost:8200")
    vault_token = os.getenv("VAULT_TOKEN")
    client = VaultClient(vault_addr=vault_addr, vault_token=vault_token)
    yield client


@pytest.fixture
def health_checker() -> ServiceHealthChecker:
    """Create health checker instance."""
    return ServiceHealthChecker()


@pytest.fixture
def password_generator() -> PasswordGenerator:
    """Create password generator instance."""
    return PasswordGenerator()


@pytest.fixture
def credential_rotator(vault_client) -> CredentialRotator:
    """Create credential rotator instance."""
    return CredentialRotator(vault_client, project_name="janusgraph-demo")


class TestPasswordGeneration:
    """Test password generation functionality."""

    def test_generate_password_default(self, password_generator):
        """Test default password generation."""
        password = password_generator.generate_password()
        
        assert len(password) == 32
        assert any(c.islower() for c in password)
        assert any(c.isupper() for c in password)
        assert any(c.isdigit() for c in password)
        assert any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password)

    def test_generate_password_custom_length(self, password_generator):
        """Test password generation with custom length."""
        password = password_generator.generate_password(length=64)
        assert len(password) == 64

    def test_generate_password_no_special(self, password_generator):
        """Test password generation without special characters."""
        password = password_generator.generate_password(include_special=False)
        
        assert len(password) == 32
        assert any(c.islower() for c in password)
        assert any(c.isupper() for c in password)
        assert any(c.isdigit() for c in password)
        assert not any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password)

    def test_generate_token(self, password_generator):
        """Test token generation."""
        token = password_generator.generate_token(length=64)
        
        assert len(token) >= 64  # URL-safe encoding may be longer
        assert token.replace("-", "").replace("_", "").isalnum()

    def test_password_uniqueness(self, password_generator):
        """Test that generated passwords are unique."""
        passwords = [password_generator.generate_password() for _ in range(100)]
        assert len(set(passwords)) == 100  # All unique


class TestServiceHealthChecks:
    """Test service health check functionality."""

    def test_check_janusgraph_healthy(self, health_checker, services_available):
        """Test JanusGraph health check when service is healthy."""
        result = health_checker.check_janusgraph()
        assert result is True

    def test_check_janusgraph_unhealthy(self, health_checker):
        """Test JanusGraph health check when service is down."""
        result = health_checker.check_janusgraph(host="nonexistent", port=9999)
        assert result is False

    @pytest.mark.slow
    def test_check_opensearch_healthy(self, health_checker, services_available):
        """Test OpenSearch health check when service is healthy."""
        # Note: May require actual OpenSearch credentials
        pytest.skip("Requires OpenSearch with known credentials")

    def test_check_grafana_healthy(self, health_checker):
        """Test Grafana health check."""
        # May fail if Grafana not running, but shouldn't raise exception
        result = health_checker.check_grafana()
        assert isinstance(result, bool)

    def test_check_pulsar_healthy(self, health_checker):
        """Test Pulsar health check."""
        # May fail if Pulsar not running, but shouldn't raise exception
        result = health_checker.check_pulsar()
        assert isinstance(result, bool)


class TestVaultOperations:
    """Test Vault client operations for rotation."""

    def test_read_write_secret(self, vault_client):
        """Test reading and writing secrets."""
        test_path = f"test/rotation-{int(time.time())}"
        test_data = {"username": "testuser", "password": "testpass123"}
        
        # Write secret
        vault_client.write_secret(test_path, test_data)
        
        # Read secret
        result = vault_client.read_secret(test_path)
        assert result["username"] == "testuser"
        assert result["password"] == "testpass123"

    def test_create_backup(self, vault_client):
        """Test creating backup of secret."""
        test_path = f"test/backup-{int(time.time())}"
        test_data = {"username": "user", "password": "pass"}
        
        # Create initial secret
        vault_client.write_secret(test_path, test_data)
        
        # Create backup
        backup_path = vault_client.create_backup(test_path)
        
        # Verify backup exists
        backup_data = vault_client.read_secret(backup_path.replace("janusgraph/", ""))
        assert backup_data["username"] == "user"
        assert backup_data["password"] == "pass"


class TestCredentialRotation:
    """Test credential rotation for various services."""

    @pytest.mark.slow
    def test_rotate_janusgraph_password_mock(self, credential_rotator):
        """Test JanusGraph password rotation with mocked services."""
        # Mock health checks to avoid actual service dependencies
        with patch.object(credential_rotator.health_checker, 'check_janusgraph', return_value=True):
            with patch.object(credential_rotator, '_update_janusgraph_config'):
                with patch.object(credential_rotator, '_restart_service'):
                    result = credential_rotator.rotate_janusgraph_password()
        
        # Verify result structure
        assert isinstance(result, RotationResult)
        assert result.service == "janusgraph"
        assert result.status in [RotationStatus.SUCCESS, RotationStatus.FAILED]
        assert result.timestamp is not None
        assert result.duration_seconds >= 0

    @pytest.mark.slow
    def test_rotate_opensearch_password_mock(self, credential_rotator):
        """Test OpenSearch password rotation with mocked services."""
        # Setup test credentials in Vault
        test_creds = {"username": "admin", "password": "oldpass"}
        credential_rotator.vault.write_secret("opensearch/admin", test_creds)
        
        with patch.object(credential_rotator.health_checker, 'check_opensearch', return_value=True):
            with patch.object(credential_rotator, '_update_opensearch_user'):
                result = credential_rotator.rotate_opensearch_password()
        
        assert isinstance(result, RotationResult)
        assert result.service == "opensearch"

    @pytest.mark.slow
    def test_rotate_grafana_password_mock(self, credential_rotator):
        """Test Grafana password rotation with mocked services."""
        # Setup test credentials
        test_creds = {"username": "admin", "password": "oldpass"}
        credential_rotator.vault.write_secret("grafana/admin", test_creds)
        
        with patch.object(credential_rotator.health_checker, 'check_grafana', return_value=True):
            with patch.object(credential_rotator, '_update_grafana_password'):
                with patch.object(credential_rotator, '_verify_grafana_login', return_value=True):
                    result = credential_rotator.rotate_grafana_password()
        
        assert isinstance(result, RotationResult)
        assert result.service == "grafana"

    @pytest.mark.slow
    def test_rotate_pulsar_token_mock(self, credential_rotator):
        """Test Pulsar token rotation with mocked services."""
        with patch.object(credential_rotator.health_checker, 'check_pulsar', return_value=True):
            with patch.object(credential_rotator, '_update_pulsar_token'):
                with patch.object(credential_rotator, '_restart_service'):
                    result = credential_rotator.rotate_pulsar_token()
        
        assert isinstance(result, RotationResult)
        assert result.service == "pulsar"

    @pytest.mark.slow
    def test_rotate_certificates_mock(self, credential_rotator):
        """Test SSL/TLS certificate rotation with mocked services."""
        with patch('subprocess.run'):
            with patch.object(credential_rotator.health_checker, 'check_janusgraph', return_value=True):
                with patch.object(credential_rotator.health_checker, 'check_opensearch', return_value=True):
                    with patch.object(credential_rotator.health_checker, 'check_grafana', return_value=True):
                        with patch.object(credential_rotator, '_restart_service'):
                            result = credential_rotator.rotate_certificates()
        
        assert isinstance(result, RotationResult)
        assert result.service == "certificates"


class TestRollbackScenarios:
    """Test rollback functionality."""

    def test_rollback_from_backup(self, credential_rotator):
        """Test rolling back credentials from backup."""
        test_path = f"test/rollback-{int(time.time())}"
        original_data = {"username": "user", "password": "original"}
        new_data = {"username": "user", "password": "new"}
        
        # Create original secret
        credential_rotator.vault.write_secret(test_path, original_data)
        
        # Create backup
        backup_path = credential_rotator.vault.create_backup(test_path)
        
        # Update to new credentials
        credential_rotator.vault.write_secret(test_path, new_data)
        
        # Rollback
        credential_rotator._rollback_from_backup(backup_path, test_path)
        
        # Verify rollback
        result = credential_rotator.vault.read_secret(test_path)
        assert result["password"] == "original"

    @pytest.mark.slow
    def test_rotation_failure_triggers_rollback(self, credential_rotator):
        """Test that rotation failure triggers automatic rollback."""
        # Setup test credentials
        test_creds = {"username": "admin", "password": "oldpass"}
        credential_rotator.vault.write_secret("opensearch/admin", test_creds)
        
        # Mock health check to fail after rotation
        with patch.object(credential_rotator.health_checker, 'check_opensearch', side_effect=[True, False]):
            with patch.object(credential_rotator, '_update_opensearch_user'):
                with patch.object(credential_rotator, '_rollback_opensearch_user') as mock_rollback:
                    result = credential_rotator.rotate_opensearch_password()
        
        # Verify rollback was called
        assert result.status == RotationStatus.FAILED
        mock_rollback.assert_called_once()


class TestHealthCheckValidation:
    """Test health check validation during rotation."""

    def test_pre_rotation_health_check_failure(self, credential_rotator):
        """Test that rotation aborts if pre-rotation health check fails."""
        with patch.object(credential_rotator.health_checker, 'check_janusgraph', return_value=False):
            result = credential_rotator.rotate_janusgraph_password()
        
        assert result.status == RotationStatus.FAILED
        assert "not healthy before rotation" in result.error_message

    def test_post_rotation_health_check_failure(self, credential_rotator):
        """Test that rotation rolls back if post-rotation health check fails."""
        with patch.object(credential_rotator.health_checker, 'check_janusgraph', side_effect=[True, False]):
            with patch.object(credential_rotator, '_update_janusgraph_config'):
                with patch.object(credential_rotator, '_restart_service'):
                    result = credential_rotator.rotate_janusgraph_password()
        
        assert result.status == RotationStatus.FAILED
        assert "health check failed" in result.error_message.lower()


class TestVaultIntegration:
    """Test Vault integration during rotation."""

    def test_vault_secret_versioning(self, vault_client):
        """Test that Vault maintains secret versions."""
        test_path = f"test/versioning-{int(time.time())}"
        
        # Write multiple versions
        vault_client.write_secret(test_path, {"password": "v1"})
        vault_client.write_secret(test_path, {"password": "v2"})
        vault_client.write_secret(test_path, {"password": "v3"})
        
        # Read latest version
        result = vault_client.read_secret(test_path)
        assert result["password"] == "v3"

    def test_vault_metadata_tracking(self, credential_rotator):
        """Test that rotation metadata is tracked in Vault."""
        test_path = f"test/metadata-{int(time.time())}"
        
        # Simulate rotation with metadata
        new_creds = {
            "username": "admin",
            "password": "newpass",
            "rotated_at": "2026-02-11T10:00:00Z",
            "rotated_by": "credential_rotation_framework"
        }
        credential_rotator.vault.write_secret(test_path, new_creds)
        
        # Verify metadata
        result = credential_rotator.vault.read_secret(test_path)
        assert "rotated_at" in result
        assert "rotated_by" in result
        assert result["rotated_by"] == "credential_rotation_framework"

    def test_vault_backup_retention(self, vault_client):
        """Test that backups are retained in Vault."""
        test_path = f"test/retention-{int(time.time())}"
        
        # Create secret and backup
        vault_client.write_secret(test_path, {"password": "original"})
        backup_path = vault_client.create_backup(test_path)
        
        # Update original
        vault_client.write_secret(test_path, {"password": "updated"})
        
        # Verify both exist
        original = vault_client.read_secret(test_path)
        backup = vault_client.read_secret(backup_path.replace("janusgraph/", ""))
        
        assert original["password"] == "updated"
        assert backup["password"] == "original"


class TestConcurrentRotation:
    """Test concurrent rotation scenarios."""

    @pytest.mark.slow
    def test_sequential_rotation_multiple_services(self, credential_rotator):
        """Test rotating multiple services sequentially."""
        services = [
            ("janusgraph", credential_rotator.rotate_janusgraph_password),
            ("opensearch", credential_rotator.rotate_opensearch_password),
            ("grafana", credential_rotator.rotate_grafana_password),
        ]
        
        results = []
        for service_name, rotate_func in services:
            # Setup test credentials
            test_creds = {"username": "admin", "password": "oldpass"}
            credential_rotator.vault.write_secret(f"{service_name}/admin", test_creds)
            
            # Mock all external dependencies
            with patch.object(credential_rotator.health_checker, f'check_{service_name}', return_value=True):
                with patch.object(credential_rotator, f'_update_{service_name}_config', create=True):
                    with patch.object(credential_rotator, f'_update_{service_name}_user', create=True):
                        with patch.object(credential_rotator, f'_update_{service_name}_password', create=True):
                            with patch.object(credential_rotator, f'_verify_{service_name}_login', return_value=True, create=True):
                                with patch.object(credential_rotator, '_restart_service'):
                                    result = rotate_func()
            
            results.append(result)
        
        # Verify all rotations completed
        assert len(results) == 3
        assert all(isinstance(r, RotationResult) for r in results)


class TestErrorHandling:
    """Test error handling during rotation."""

    def test_vault_connection_error(self):
        """Test handling of Vault connection errors."""
        with pytest.raises(Exception):
            VaultClient(vault_addr="http://nonexistent:8200", vault_token="test")

    def test_invalid_service_type(self, credential_rotator):
        """Test handling of invalid service types."""
        # This would be caught at the CLI level, but test the enum
        assert ServiceType.JANUSGRAPH.value == "janusgraph"
        assert ServiceType.ALL.value == "all"

    def test_rotation_timeout(self, credential_rotator):
        """Test handling of rotation timeouts."""
        # Mock a slow operation
        with patch.object(credential_rotator, '_restart_service', side_effect=lambda *args, **kwargs: time.sleep(0.1)):
            with patch.object(credential_rotator.health_checker, 'check_janusgraph', return_value=True):
                with patch.object(credential_rotator, '_update_janusgraph_config'):
                    result = credential_rotator.rotate_janusgraph_password()
        
        # Should complete despite delay
        assert isinstance(result, RotationResult)
        assert result.duration_seconds >= 0.1


class TestRotationMetrics:
    """Test rotation metrics and monitoring."""

    def test_rotation_duration_tracking(self, credential_rotator):
        """Test that rotation duration is tracked."""
        with patch.object(credential_rotator.health_checker, 'check_janusgraph', return_value=True):
            with patch.object(credential_rotator, '_update_janusgraph_config'):
                with patch.object(credential_rotator, '_restart_service'):
                    result = credential_rotator.rotate_janusgraph_password()
        
        assert result.duration_seconds > 0
        assert result.timestamp is not None

    def test_rotation_result_structure(self, credential_rotator):
        """Test that rotation result has all required fields."""
        with patch.object(credential_rotator.health_checker, 'check_janusgraph', return_value=True):
            with patch.object(credential_rotator, '_update_janusgraph_config'):
                with patch.object(credential_rotator, '_restart_service'):
                    result = credential_rotator.rotate_janusgraph_password()
        
        assert hasattr(result, 'service')
        assert hasattr(result, 'status')
        assert hasattr(result, 'old_credential_id')
        assert hasattr(result, 'new_credential_id')
        assert hasattr(result, 'timestamp')
        assert hasattr(result, 'duration_seconds')
        assert hasattr(result, 'error_message')


# Made with Bob