"""
Pytest Configuration and Fixtures
==================================

Shared fixtures and configuration for all tests.

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path (go up 3 levels: tests -> data_generators -> banking -> root)
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from banking.data_generators.core.person_generator import PersonGenerator
from banking.data_generators.core.company_generator import CompanyGenerator
from banking.data_generators.core.account_generator import AccountGenerator
from banking.data_generators.events.transaction_generator import TransactionGenerator
from banking.data_generators.events.communication_generator import CommunicationGenerator
from banking.data_generators.patterns.insider_trading_pattern_generator import InsiderTradingPatternGenerator
from banking.data_generators.patterns.tbml_pattern_generator import TBMLPatternGenerator
from banking.data_generators.patterns.fraud_ring_pattern_generator import FraudRingPatternGenerator
from banking.data_generators.patterns.structuring_pattern_generator import StructuringPatternGenerator
from banking.data_generators.patterns.cato_pattern_generator import CATOPatternGenerator
from banking.data_generators.orchestration import MasterOrchestrator, GenerationConfig


# ============================================================================
# GENERATOR FIXTURES
# ============================================================================

@pytest.fixture
def person_generator():
    """Fixture for PersonGenerator with fixed seed"""
    return PersonGenerator(seed=42)


@pytest.fixture
def company_generator():
    """Fixture for CompanyGenerator with fixed seed"""
    return CompanyGenerator(seed=42)


@pytest.fixture
def account_generator():
    """Fixture for AccountGenerator with fixed seed"""
    return AccountGenerator(seed=42)


@pytest.fixture
def transaction_generator():
    """Fixture for TransactionGenerator with fixed seed"""
    return TransactionGenerator(seed=42)


@pytest.fixture
def communication_generator():
    """Fixture for CommunicationGenerator with fixed seed"""
    return CommunicationGenerator(seed=42)


@pytest.fixture
def insider_trading_generator():
    """Fixture for InsiderTradingPatternGenerator with fixed seed"""
    return InsiderTradingPatternGenerator(seed=42)


@pytest.fixture
def tbml_generator():
    """Fixture for TBMLPatternGenerator with fixed seed"""
    return TBMLPatternGenerator(seed=42)


@pytest.fixture
def fraud_ring_generator():
    """Fixture for FraudRingPatternGenerator with fixed seed"""
    return FraudRingPatternGenerator(seed=42)


@pytest.fixture
def structuring_generator():
    """Fixture for StructuringPatternGenerator with fixed seed"""
    return StructuringPatternGenerator(seed=42)


@pytest.fixture
def cato_generator():
    """Fixture for CATOPatternGenerator with fixed seed"""
    return CATOPatternGenerator(seed=42)


# ============================================================================
# ENTITY FIXTURES
# ============================================================================

@pytest.fixture
def sample_person(person_generator):
    """Generate a sample person"""
    return person_generator.generate()


@pytest.fixture
def sample_persons(person_generator):
    """Generate multiple sample persons"""
    return [person_generator.generate() for _ in range(10)]


@pytest.fixture
def sample_company(company_generator):
    """Generate a sample company"""
    return company_generator.generate()


@pytest.fixture
def sample_companies(company_generator):
    """Generate multiple sample companies"""
    return [company_generator.generate() for _ in range(5)]


@pytest.fixture
def sample_account(account_generator, sample_person):
    """Generate a sample account"""
    return account_generator.generate(
        owner_id=sample_person.id,
        owner_type="person"
    )


@pytest.fixture
def sample_accounts(account_generator, sample_persons):
    """Generate multiple sample accounts"""
    return [
        account_generator.generate(
            owner_id=person.id,
            owner_type="person"
        )
        for person in sample_persons
    ]


@pytest.fixture
def sample_transaction(transaction_generator, sample_accounts):
    """Generate a sample transaction"""
    return transaction_generator.generate(
        from_account_id=sample_accounts[0].id,
        to_account_id=sample_accounts[1].id
    )


@pytest.fixture
def sample_transactions(transaction_generator, sample_accounts):
    """
    Generate multiple sample transactions.
    
    Note: Generates min(20, len(sample_accounts)) transactions to prevent IndexError.
    Requires at least 2 accounts. If you need exactly 20 transactions, ensure
    sample_accounts fixture provides at least 20 accounts.
    """
    assert len(sample_accounts) >= 2, "Need at least 2 accounts for sample_transactions fixture"
    
    # Generate transactions using available accounts
    num_transactions = min(20, len(sample_accounts))
    return [
        transaction_generator.generate(
            from_account_id=sample_accounts[i % len(sample_accounts)].id,
            to_account_id=sample_accounts[(i + 1) % len(sample_accounts)].id
        )
        for i in range(num_transactions)
    ]


# ============================================================================
# ORCHESTRATOR FIXTURES
# ============================================================================

@pytest.fixture
def small_config():
    """Small configuration for quick tests"""
    return GenerationConfig(
        seed=42,
        person_count=10,
        company_count=2,
        account_count=15,
        transaction_count=50,
        communication_count=20,
        output_dir=Path("/tmp/test_output")
    )


@pytest.fixture
def medium_config():
    """Medium configuration for integration tests"""
    return GenerationConfig(
        seed=42,
        person_count=100,
        company_count=20,
        account_count=200,
        transaction_count=1000,
        communication_count=500,
        insider_trading_patterns=2,
        tbml_patterns=1,
        fraud_ring_patterns=2,
        structuring_patterns=3,
        cato_patterns=2,
        output_dir=Path("/tmp/test_output")
    )


@pytest.fixture
def orchestrator(small_config):
    """Fixture for MasterOrchestrator with small config"""
    return MasterOrchestrator(small_config)

@pytest.fixture
def small_orchestrator(small_config):
    """
    Alias for orchestrator with small config.
    
    This fixture provides backward compatibility with existing tests that
    reference 'small_orchestrator' instead of 'orchestrator'. Both fixtures
    use the same small_config and return identical MasterOrchestrator instances.
    
    Use this fixture when:
    - Maintaining existing tests that use small_orchestrator
    - You need explicit naming to distinguish from other orchestrator sizes
    
    For new tests, prefer using 'orchestrator' fixture for consistency.
    """
    return MasterOrchestrator(small_config)


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory for tests"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_datetime():
    """
    Sample datetime for testing with specific time component.
    
    Returns datetime(2024, 1, 15, 10, 30, 0) for tests requiring
    full datetime objects with time information.
    """
    return datetime(2024, 1, 15, 10, 30, 0)


@pytest.fixture
def sample_date():
    """
    Sample date for testing without time component.
    
    Returns date(2024, 1, 15) for tests requiring only date information.
    """
    return datetime(2024, 1, 15).date()


@pytest.fixture
def date_range():
    """
    Date range for testing temporal queries.
    
    Returns tuple of (start_date, end_date) covering full year 2024.
    Both are datetime objects for compatibility with datetime operations.
    """
    start = datetime(2024, 1, 1)
    end = datetime(2024, 12, 31)
    return start, end


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "benchmark: marks tests as performance benchmarks"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Mark benchmark tests
        if "benchmark" in item.nodeid or "performance" in item.nodeid:
            item.add_marker(pytest.mark.benchmark)
        
        # Mark slow tests
        if any(keyword in item.nodeid for keyword in ["large", "stress", "load"]):
            item.add_marker(pytest.mark.slow)

