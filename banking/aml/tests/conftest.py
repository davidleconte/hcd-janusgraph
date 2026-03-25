"""
AML Test Fixtures

Pytest fixtures for AML module testing with reduced mocking.
These fixtures provide test data and lightweight implementations
to increase code coverage while maintaining test isolation.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest


# ============================================================
# TEST DATA FIXTURES
# ============================================================

@pytest.fixture
def reference_timestamp() -> datetime:
    """Reference timestamp for deterministic testing."""
    return datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def sample_transactions(reference_timestamp: datetime) -> List[Dict[str, Any]]:
    """Sample transaction data for structuring detection tests."""
    transactions = []
    
    # Create 5 transactions just below $10,000 threshold (classic structuring)
    for i in range(5):
        transactions.append({
            "transaction_id": f"TX-STRUCT-{i:04d}",
            "account_id": "ACC-001-STRUCTURING",
            "amount": 9800.00 + (i * 50),  # $9,800 - $10,000 range
            "currency": "USD",
            "timestamp": (reference_timestamp - timedelta(days=i)).isoformat(),
            "merchant": "Cash Deposit ATM",
            "merchant_category": "ATM",
            "type": "deposit",
        })
    
    # Create 3 rapid succession transactions
    for i in range(3):
        transactions.append({
            "transaction_id": f"TX-RAPID-{i:04d}",
            "account_id": "ACC-002-RAPID",
            "amount": 5000.00,
            "currency": "USD",
            "timestamp": (reference_timestamp - timedelta(hours=i)).isoformat(),
            "merchant": "Wire Transfer",
            "merchant_category": "Wire",
            "type": "transfer",
        })
    
    # Create layering chain
    for i in range(4):
        transactions.append({
            "transaction_id": f"TX-LAYER-{i:04d}",
            "account_id": f"ACC-LAYER-{i:03d}",
            "amount": 8500.00,
            "currency": "USD",
            "timestamp": (reference_timestamp - timedelta(days=i * 7)).isoformat(),
            "merchant": "International Wire",
            "merchant_category": "International",
            "type": "transfer",
            "destination_account": f"ACC-LAYER-{(i+1) % 4:03d}",
        })
    
    return transactions


@pytest.fixture
def sample_accounts() -> List[Dict[str, Any]]:
    """Sample account data for testing."""
    return [
        {
            "account_id": "ACC-001-STRUCTURING",
            "holder": "John Doe",
            "account_type": "checking",
            "opened_date": "2025-01-15",
            "balance": 50000.00,
            "risk_level": "medium",
        },
        {
            "account_id": "ACC-002-RAPID",
            "holder": "Jane Smith",
            "account_type": "savings",
            "opened_date": "2025-06-01",
            "balance": 25000.00,
            "risk_level": "high",
        },
        {
            "account_id": "ACC-LAYER-000",
            "holder": "Shell Company Alpha",
            "account_type": "business",
            "opened_date": "2024-03-15",
            "balance": 100000.00,
            "risk_level": "critical",
        },
    ]


@pytest.fixture
def sample_persons() -> List[Dict[str, Any]]:
    """Sample person data for sanctions screening tests."""
    return [
        {
            "person_id": "PERS-001",
            "first_name": "John",
            "last_name": "Smith",
            "full_name": "John Smith",
            "date_of_birth": "1985-03-15",
            "nationality": "US",
            "pep_status": False,
        },
        {
            "person_id": "PERS-002",
            "first_name": "Ahmed",
            "last_name": "Al-Rashid",
            "full_name": "Ahmed Al-Rashid",
            "date_of_birth": "1978-07-22",
            "nationality": "SA",
            "pep_status": True,
        },
        {
            "person_id": "PERS-003",
            "first_name": "Maria",
            "last_name": "Garcia",
            "full_name": "Maria Garcia",
            "date_of_birth": "1990-11-30",
            "nationality": "ES",
            "pep_status": False,
        },
    ]


@pytest.fixture
def sanctions_list_sample() -> List[Dict[str, Any]]:
    """Sample sanctions list entries for testing."""
    return [
        {
            "list": "ofac",
            "entity_id": "SDN-001",
            "name": "AHMED AL-RASHID",
            "name_aliases": ["A. Al-Rashid", "Ahmed Al Rashid"],
            "program": "SDGT",
            "sanctions_type": "individual",
        },
        {
            "list": "un",
            "entity_id": "UN-001",
            "name": "AL-RASHID, AHMED",
            "name_aliases": [],
            "program": "AQ",
            "sanctions_type": "individual",
        },
        {
            "list": "eu",
            "entity_id": "EU-001",
            "name": "Ahmed Al-Rashid",
            "name_aliases": [],
            "program": "TERRORISM",
            "sanctions_type": "individual",
        },
    ]


# ============================================================
# MOCK FIXTURES (Lightweight)
# ============================================================

@pytest.fixture
def mock_opensearch_client():
    """Mock OpenSearch client for vector search tests."""
    mock_client = MagicMock()
    mock_client.indices.exists.return_value = True
    mock_client.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_source": {
                        "name": "Test Entity",
                        "embedding": [0.1] * 384,
                    },
                    "_score": 0.95,
                }
            ]
        }
    }
    return mock_client


@pytest.fixture
def mock_embedding_generator():
    """Mock embedding generator with deterministic output."""
    mock_gen = MagicMock()
    # Return deterministic embeddings for reproducibility
    mock_gen.encode.return_value = [[0.1] * 384]
    mock_gen.encode_batch.return_value = [[0.1] * 384 for _ in range(10)]
    return mock_gen


@pytest.fixture
def mock_gremlin_connection():
    """Mock Gremlin connection for graph traversal tests."""
    mock_conn = MagicMock()
    
    # Mock traversal source
    mock_g = MagicMock()
    mock_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.return_value.__exit__ = MagicMock(return_value=False)
    
    return mock_conn


# ============================================================
# INTEGRATION FIXTURES (Requires Services)
# ============================================================

@pytest.fixture
def janusgraph_url() -> str:
    """JanusGraph Gremlin server URL."""
    return os.environ.get("JANUSGRAPH_URL", "ws://localhost:18182/gremlin")


@pytest.fixture
def opensearch_url() -> str:
    """OpenSearch URL."""
    return os.environ.get("OPENSEARCH_URL", "http://localhost:9200")


@pytest.fixture
def skip_if_no_services(janusgraph_url: str, opensearch_url: str):
    """Skip tests if services are not available."""
    import socket
    
    def check_port(url: str, default_port: int) -> bool:
        try:
            if "://" in url:
                host = url.split("://")[1].split(":")[0]
                port = int(url.split(":")[-1].split("/")[0])
            else:
                host = "localhost"
                port = default_port
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    janusgraph_available = check_port(janusgraph_url, 18182)
    opensearch_available = check_port(opensearch_url, 9200)
    
    if not (janusgraph_available and opensearch_available):
        pytest.skip("JanusGraph or OpenSearch not available")


# ============================================================
# TEST UTILITIES
# ============================================================

@pytest.fixture
def assert_valid_risk_score():
    """Helper to validate risk scores."""
    def _assert(score: float):
        assert 0.0 <= score <= 1.0, f"Risk score {score} not in [0, 1]"
    return _assert


@pytest.fixture
def assert_valid_structuring_pattern():
    """Helper to validate structuring patterns."""
    def _assert(pattern: Dict[str, Any]):
        required_fields = ["account_id", "pattern_type", "risk_score"]
        for field in required_fields:
            assert field in pattern, f"Missing required field: {field}"
    return _assert


# ============================================================
# PYTEST CONFIGURATION
# ============================================================

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as requiring live services"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "benchmark: mark test as performance benchmark"
    )
