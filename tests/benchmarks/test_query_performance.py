#!/usr/bin/env python3
"""
Query Performance Benchmarks

Uses pytest-benchmark to measure query performance for critical operations.
Run with: pytest tests/benchmarks/ -v --benchmark-only

Requires: pip install pytest-benchmark
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import pytest_benchmark  # noqa: F401

    BENCHMARK_AVAILABLE = True
except ImportError:
    BENCHMARK_AVAILABLE = False

pytestmark = [
    pytest.mark.benchmark,
    pytest.mark.skipif(not BENCHMARK_AVAILABLE, reason="pytest-benchmark not installed"),
]


def check_janusgraph() -> bool:
    try:
        from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
        from gremlin_python.process.anonymous_traversal import traversal

        conn = DriverRemoteConnection(
            f"ws://localhost:{os.getenv('JANUSGRAPH_PORT', '18182')}/gremlin", "g"
        )
        g = traversal().withRemote(conn)
        g.V().limit(1).toList()
        conn.close()
        return True
    except Exception:
        return False


JG_AVAILABLE = check_janusgraph()
skip_no_jg = pytest.mark.skipif(not JG_AVAILABLE, reason="JanusGraph unavailable")


@pytest.fixture(scope="module")
def jg_connection():
    if not JG_AVAILABLE:
        pytest.skip("JanusGraph unavailable")
    from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
    from gremlin_python.process.anonymous_traversal import traversal

    conn = DriverRemoteConnection(
        f"ws://localhost:{os.getenv('JANUSGRAPH_PORT', '18182')}/gremlin", "g"
    )
    yield traversal().withRemote(conn)
    conn.close()


class TestJanusGraphBenchmarks:
    """Benchmarks for JanusGraph operations."""

    @skip_no_jg
    def test_vertex_count(self, benchmark, jg_connection):
        """Benchmark: Count all vertices."""
        result = benchmark(lambda: jg_connection.V().count().next())
        assert result >= 0

    @skip_no_jg
    def test_vertex_lookup_by_label(self, benchmark, jg_connection):
        """Benchmark: Lookup vertices by label."""
        result = benchmark(lambda: jg_connection.V().hasLabel("person").limit(100).toList())
        assert isinstance(result, list)

    @skip_no_jg
    def test_single_hop_traversal(self, benchmark, jg_connection):
        """Benchmark: Single-hop traversal."""
        result = benchmark(
            lambda: jg_connection.V().hasLabel("person").limit(10).out().limit(50).toList()
        )
        assert isinstance(result, list)

    @skip_no_jg
    def test_two_hop_traversal(self, benchmark, jg_connection):
        """Benchmark: Two-hop traversal."""
        result = benchmark(
            lambda: jg_connection.V().hasLabel("person").limit(5).out().out().limit(100).toList()
        )
        assert isinstance(result, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])
