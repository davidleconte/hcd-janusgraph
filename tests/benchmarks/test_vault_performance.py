"""
Performance Benchmarks for Vault Client
========================================

Benchmarks for Vault client caching, retry logic, and throughput.
Uses pytest-benchmark for accurate performance measurements.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Created: 2026-02-11
Phase: Phase 2 - Infrastructure Security

Prerequisites:
    - Vault server running at VAULT_ADDR
    - VAULT_TOKEN environment variable set
    - pytest-benchmark installed: uv pip install pytest-benchmark

Run with:
    pytest tests/benchmarks/test_vault_performance.py -v
    pytest tests/benchmarks/test_vault_performance.py -v --benchmark-only
    pytest tests/benchmarks/test_vault_performance.py -v --benchmark-save=vault_baseline
"""

import os
import time
from typing import Generator

import pytest

from src.python.utils.vault_client import VaultClient, VaultConfig

# Mark all tests as benchmarks
pytestmark = [pytest.mark.benchmark, pytest.mark.integration]


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


@pytest.fixture(scope="module")
def vault_available():
    """Skip benchmarks if Vault is not available."""
    if not is_vault_available():
        pytest.skip("Vault server not available or not authenticated")


@pytest.fixture
def vault_client(vault_available) -> Generator[VaultClient, None, None]:
    """Create Vault client for benchmarking."""
    config = VaultConfig.from_env()
    config.cache_ttl = 300  # 5 minutes
    config.max_retries = 3
    config.retry_delay = 0.1
    client = VaultClient(config)
    yield client
    client.clear_cache()


@pytest.fixture
def test_secret_path() -> str:
    """Generate unique test secret path."""
    return f"benchmark/test-{int(time.time())}"


@pytest.fixture
def populated_secrets(vault_client) -> dict:
    """Populate Vault with test secrets."""
    secrets = {}
    base_path = f"benchmark/populated-{int(time.time())}"

    for i in range(10):
        path = f"{base_path}/secret-{i}"
        data = {
            "username": f"user_{i}",
            "password": f"pass_{i}",
            "api_key": f"key_{i}" * 10,
        }
        vault_client.set_secret(path, data)
        secrets[path] = data

    return secrets


class TestReadPerformance:
    """Benchmark read operations."""

    def test_read_secret_cold_cache(self, benchmark, vault_client, test_secret_path):
        """Benchmark reading secret with cold cache (first read)."""
        test_data = {"username": "testuser", "password": "testpass123"}
        vault_client.set_secret(test_secret_path, test_data)

        def read_cold():
            vault_client.clear_cache()
            return vault_client.get_secret(test_secret_path)

        result = benchmark(read_cold)
        assert result == test_data

    def test_read_secret_warm_cache(self, benchmark, vault_client, test_secret_path):
        """Benchmark reading secret with warm cache (cached read)."""
        test_data = {"username": "testuser", "password": "testpass123"}
        vault_client.set_secret(test_secret_path, test_data)

        # Prime the cache
        vault_client.get_secret(test_secret_path)

        def read_warm():
            return vault_client.get_secret(test_secret_path)

        result = benchmark(read_warm)
        assert result == test_data

    def test_read_secret_with_key(self, benchmark, vault_client, test_secret_path):
        """Benchmark reading specific key from secret."""
        test_data = {"username": "testuser", "password": "testpass123"}
        vault_client.set_secret(test_secret_path, test_data)

        def read_key():
            vault_client.clear_cache()
            return vault_client.get_secret(test_secret_path, "password")

        result = benchmark(read_key)
        assert result == "testpass123"

    def test_read_multiple_secrets(self, benchmark, vault_client, populated_secrets):
        """Benchmark reading multiple secrets sequentially."""

        def read_multiple():
            vault_client.clear_cache()
            results = []
            for path in list(populated_secrets.keys())[:5]:
                results.append(vault_client.get_secret(path))
            return results

        results = benchmark(read_multiple)
        assert len(results) == 5


class TestWritePerformance:
    """Benchmark write operations."""

    def test_write_secret_small(self, benchmark, vault_client):
        """Benchmark writing small secret."""
        test_data = {"username": "user", "password": "pass"}

        def write_small():
            path = f"benchmark/write-small-{time.time()}"
            vault_client.set_secret(path, test_data)

        benchmark(write_small)

    def test_write_secret_medium(self, benchmark, vault_client):
        """Benchmark writing medium-sized secret."""
        test_data = {f"key_{i}": f"value_{i}" * 10 for i in range(20)}

        def write_medium():
            path = f"benchmark/write-medium-{time.time()}"
            vault_client.set_secret(path, test_data)

        benchmark(write_medium)

    def test_write_secret_large(self, benchmark, vault_client):
        """Benchmark writing large secret."""
        test_data = {f"key_{i}": f"value_{i}" * 100 for i in range(50)}

        def write_large():
            path = f"benchmark/write-large-{time.time()}"
            vault_client.set_secret(path, test_data)

        benchmark(write_large)

    def test_update_secret(self, benchmark, vault_client, test_secret_path):
        """Benchmark updating existing secret."""
        initial_data = {"username": "user1", "password": "pass1"}
        vault_client.set_secret(test_secret_path, initial_data)

        updated_data = {"username": "user2", "password": "pass2"}

        def update():
            vault_client.set_secret(test_secret_path, updated_data)

        benchmark(update)


class TestCachePerformance:
    """Benchmark caching performance."""

    def test_cache_hit_rate(self, benchmark, vault_client, test_secret_path):
        """Benchmark cache hit performance vs cold reads."""
        test_data = {"username": "testuser", "password": "testpass123"}
        vault_client.set_secret(test_secret_path, test_data)

        # Prime cache
        vault_client.get_secret(test_secret_path)

        def cached_reads():
            results = []
            for _ in range(100):
                results.append(vault_client.get_secret(test_secret_path))
            return results

        results = benchmark(cached_reads)
        assert len(results) == 100

    def test_cache_with_different_keys(self, benchmark, vault_client, test_secret_path):
        """Benchmark cache performance with different key access patterns."""
        test_data = {
            "username": "user",
            "password": "pass",
            "api_key": "key",
            "token": "token",
        }
        vault_client.set_secret(test_secret_path, test_data)

        def mixed_access():
            vault_client.clear_cache()
            results = []
            # Access different keys
            for key in ["username", "password", "api_key", "token"]:
                results.append(vault_client.get_secret(test_secret_path, key))
            # Access full secret
            results.append(vault_client.get_secret(test_secret_path))
            return results

        results = benchmark(mixed_access)
        assert len(results) == 5

    def test_cache_invalidation(self, benchmark, vault_client, test_secret_path):
        """Benchmark cache invalidation on write."""
        test_data = {"username": "user", "password": "pass"}
        vault_client.set_secret(test_secret_path, test_data)

        def write_and_invalidate():
            # Prime cache
            vault_client.get_secret(test_secret_path)
            # Write (invalidates cache)
            vault_client.set_secret(test_secret_path, {"username": "new", "password": "new"})
            # Read (cold)
            return vault_client.get_secret(test_secret_path)

        benchmark(write_and_invalidate)


class TestCredentialOperations:
    """Benchmark credential-specific operations."""

    def test_get_credentials_cold(self, benchmark, vault_client, test_secret_path):
        """Benchmark getting credentials with cold cache."""
        creds = {"username": "dbuser", "password": "dbpass123"}
        vault_client.set_secret(test_secret_path, creds)

        def get_creds_cold():
            vault_client.clear_cache()
            return vault_client.get_credentials(test_secret_path)

        result = benchmark(get_creds_cold)
        assert result["username"] == "dbuser"

    def test_get_credentials_warm(self, benchmark, vault_client, test_secret_path):
        """Benchmark getting credentials with warm cache."""
        creds = {"username": "dbuser", "password": "dbpass123"}
        vault_client.set_secret(test_secret_path, creds)

        # Prime cache
        vault_client.get_credentials(test_secret_path)

        def get_creds_warm():
            return vault_client.get_credentials(test_secret_path)

        result = benchmark(get_creds_warm)
        assert result["username"] == "dbuser"


class TestListOperations:
    """Benchmark list operations."""

    def test_list_secrets_small(self, benchmark, vault_client):
        """Benchmark listing small number of secrets."""
        base_path = f"benchmark/list-small-{int(time.time())}"

        # Create 5 secrets
        for i in range(5):
            vault_client.set_secret(f"{base_path}/secret-{i}", {"key": f"value-{i}"})

        def list_small():
            return vault_client.list_secrets(base_path)

        result = benchmark(list_small)
        assert len(result) == 5

    def test_list_secrets_medium(self, benchmark, vault_client):
        """Benchmark listing medium number of secrets."""
        base_path = f"benchmark/list-medium-{int(time.time())}"

        # Create 25 secrets
        for i in range(25):
            vault_client.set_secret(f"{base_path}/secret-{i}", {"key": f"value-{i}"})

        def list_medium():
            return vault_client.list_secrets(base_path)

        result = benchmark(list_medium)
        assert len(result) == 25


class TestRetryPerformance:
    """Benchmark retry logic performance."""

    def test_successful_operation_no_retry(self, benchmark, vault_client, test_secret_path):
        """Benchmark successful operation (no retries needed)."""
        test_data = {"username": "user", "password": "pass"}
        vault_client.set_secret(test_secret_path, test_data)

        def successful_read():
            return vault_client.get_secret(test_secret_path, use_cache=False)

        result = benchmark(successful_read)
        assert result == test_data


class TestConcurrentAccess:
    """Benchmark concurrent access patterns."""

    @pytest.mark.slow
    def test_concurrent_reads_cached(self, benchmark, vault_client, test_secret_path):
        """Benchmark concurrent reads from cache."""
        import concurrent.futures

        test_data = {"username": "user", "password": "pass"}
        vault_client.set_secret(test_secret_path, test_data)

        # Prime cache
        vault_client.get_secret(test_secret_path)

        def concurrent_cached_reads():
            def read():
                return vault_client.get_secret(test_secret_path)

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(read) for _ in range(50)]
                return [f.result() for f in futures]

        results = benchmark(concurrent_cached_reads)
        assert len(results) == 50

    @pytest.mark.slow
    def test_concurrent_reads_cold(self, benchmark, vault_client, populated_secrets):
        """Benchmark concurrent reads with cold cache."""
        import concurrent.futures

        paths = list(populated_secrets.keys())[:10]

        def concurrent_cold_reads():
            vault_client.clear_cache()

            def read(path):
                return vault_client.get_secret(path)

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(read, path) for path in paths]
                return [f.result() for f in futures]

        results = benchmark(concurrent_cold_reads)
        assert len(results) == 10


class TestMemoryEfficiency:
    """Benchmark memory usage patterns."""

    def test_cache_memory_growth(self, benchmark, vault_client):
        """Benchmark cache memory growth with many secrets."""
        base_path = f"benchmark/memory-{int(time.time())}"

        # Create secrets
        for i in range(20):
            vault_client.set_secret(f"{base_path}/secret-{i}", {"key": f"value-{i}"})

        def cache_many_secrets():
            vault_client.clear_cache()
            for i in range(20):
                vault_client.get_secret(f"{base_path}/secret-{i}")
            return len(vault_client._cache)

        cache_size = benchmark(cache_many_secrets)
        assert cache_size > 0


class TestEndToEndScenarios:
    """Benchmark realistic end-to-end scenarios."""

    def test_application_startup_scenario(self, benchmark, vault_client):
        """Benchmark typical application startup credential loading."""
        # Setup credentials for multiple services
        services = ["janusgraph", "opensearch", "hcd", "grafana", "prometheus"]
        base_path = f"benchmark/startup-{int(time.time())}"

        for service in services:
            vault_client.set_secret(
                f"{base_path}/{service}",
                {"username": f"{service}_user", "password": f"{service}_pass"},
            )

        def startup_load():
            vault_client.clear_cache()
            creds = {}
            for service in services:
                creds[service] = vault_client.get_credentials(f"{base_path}/{service}")
            return creds

        result = benchmark(startup_load)
        assert len(result) == 5

    def test_request_handling_scenario(self, benchmark, vault_client, test_secret_path):
        """Benchmark typical request handling with cached credentials."""
        vault_client.set_secret(
            test_secret_path, {"username": "api_user", "password": "api_pass"}
        )

        # Prime cache (simulating previous requests)
        vault_client.get_credentials(test_secret_path)

        def handle_requests():
            results = []
            for _ in range(100):
                # Each request gets credentials from cache
                creds = vault_client.get_credentials(test_secret_path)
                results.append(creds)
            return results

        results = benchmark(handle_requests)
        assert len(results) == 100


# Made with Bob