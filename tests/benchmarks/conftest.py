"""
Benchmark Test Configuration
=============================

Shared fixtures for performance benchmarks.
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest


@pytest.fixture(scope="session")
def benchmark_seed():
    """Fixed seed for reproducible benchmarks."""
    return 12345


@pytest.fixture
def large_transaction_batch():
    """Generate a batch of 1000 transactions for benchmarking."""
    return [
        {
            "id": f"T-BENCH-{i:05d}",
            "from_account": "A001",
            "to_account": "A002",
            "amount": Decimal(str(100 + i)),
            "currency": "USD",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "transfer",
            "status": "completed",
        }
        for i in range(1000)
    ]
