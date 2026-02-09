"""
Root Test Configuration
=======================

Shared fixtures and configuration for all tests.

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "requires_janusgraph: Tests requiring JanusGraph")
    config.addinivalue_line("markers", "requires_vault: Tests requiring Vault")


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_janusgraph_client():
    """Mock JanusGraph client for testing"""
    client = Mock()
    client.submit = Mock()
    client.submit.return_value.all.return_value.result.return_value = []
    client.close = Mock()
    return client


@pytest.fixture
def mock_vault_client():
    """Mock Vault client for testing"""
    client = Mock()
    client.secrets = Mock()
    client.secrets.kv = Mock()
    client.secrets.kv.v2 = Mock()
    client.secrets.kv.v2.read_secret_version = Mock(return_value={
        'data': {
            'data': {
                'username': 'test_user',
                'password': 'test_password'
            }
        }
    })
    return client


# ============================================================================
# DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_person():
    """Sample person data for testing"""
    return {
        'id': 'P001',
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com',
        'phone': '+1-555-0100',
        'date_of_birth': '1980-01-01',
        'ssn': '123-45-6789',
        'address': {
            'street': '123 Main St',
            'city': 'New York',
            'state': 'NY',
            'zip': '10001',
            'country': 'USA'
        }
    }


@pytest.fixture
def sample_company():
    """Sample company data for testing"""
    return {
        'id': 'C001',
        'name': 'Acme Corporation',
        'industry': 'Technology',
        'country': 'USA',
        'employees': 1000,
        'revenue': Decimal('10000000.00'),
        'founded': '2000-01-01'
    }


@pytest.fixture
def sample_account():
    """Sample account data for testing"""
    return {
        'id': 'A001',
        'account_number': '1234567890',
        'account_type': 'checking',
        'balance': Decimal('10000.00'),
        'currency': 'USD',
        'status': 'active',
        'opened_date': '2020-01-01'
    }


@pytest.fixture
def sample_transaction():
    """Sample transaction data for testing"""
    return {
        'id': 'T001',
        'from_account': 'A001',
        'to_account': 'A002',
        'amount': Decimal('1000.00'),
        'currency': 'USD',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'type': 'transfer',
        'status': 'completed'
    }


# ============================================================================
# ENVIRONMENT FIXTURES
# ============================================================================

@pytest.fixture
def test_env_vars(monkeypatch):
    """Set test environment variables"""
    monkeypatch.setenv('JANUSGRAPH_HOST', 'localhost')
    monkeypatch.setenv('JANUSGRAPH_PORT', '8182')
    monkeypatch.setenv('JANUSGRAPH_USERNAME', 'test_user')
    monkeypatch.setenv('JANUSGRAPH_PASSWORD', 'test_password')
    monkeypatch.setenv('VAULT_ADDR', 'http://localhost:8200')
    monkeypatch.setenv('VAULT_TOKEN', 'test_token')


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests"""
    yield
    # Add singleton reset logic here if needed


@pytest.fixture(autouse=True)
def clear_janusgraph_env_vars(monkeypatch):
    """Clear JanusGraph environment variables to ensure tests use default values.
    
    This prevents the conda environment's JANUSGRAPH_PORT=18182 from interfering
    with unit tests that expect the default port 8182.
    """
    # Clear env vars that might interfere with default values in tests
    monkeypatch.delenv("JANUSGRAPH_PORT", raising=False)
    monkeypatch.delenv("JANUSGRAPH_USE_SSL", raising=False)
    monkeypatch.delenv("JANUSGRAPH_HOST", raising=False)


@pytest.fixture
def temp_directory(tmp_path):
    """Provide a temporary directory for tests"""
    return tmp_path

# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS | +33614126117
