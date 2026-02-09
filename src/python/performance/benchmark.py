"""
Performance Benchmarking Suite

Provides comprehensive benchmarking tools for JanusGraph queries,
including load testing, stress testing, and performance regression detection.
"""

import concurrent.futures
import json
import logging
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""

    name: str
    iterations: int
    total_time_seconds: float
    min_time_ms: float
    max_time_ms: float
    avg_time_ms: float
    median_time_ms: float
    p95_time_ms: float
    p99_time_ms: float
    std_dev_ms: float
    throughput_qps: float  # Queries per second
    success_count: int
    error_count: int
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "total_time_seconds": self.total_time_seconds,
            "avg_time_ms": self.avg_time_ms,
            "median_time_ms": self.median_time_ms,
            "p95_time_ms": self.p95_time_ms,
            "p99_time_ms": self.p99_time_ms,
            "throughput_qps": self.throughput_qps,
            "success_rate": f"{(self.success_count / self.iterations * 100):.2f}%",
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class LoadTestResult:
    """Result of a load test."""

    name: str
    concurrent_users: int
    duration_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    median_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    throughput_rps: float  # Requests per second
    error_rate: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class PerformanceBenchmark:
    """Performance benchmarking tool."""

    def __init__(self):
        """Initialize benchmark."""
        self.results: List[BenchmarkResult] = []
        logger.info("Performance Benchmark initialized")

    def run_benchmark(
        self,
        name: str,
        func: Callable,
        iterations: int = 100,
        warmup_iterations: int = 10,
        *args,
        **kwargs,
    ) -> BenchmarkResult:
        """
        Run performance benchmark.

        Args:
            name: Benchmark name
            func: Function to benchmark
            iterations: Number of iterations
            warmup_iterations: Number of warmup iterations
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Benchmark result
        """
        logger.info("Running benchmark: %s (%s iterations)", name, iterations)

        # Warmup
        logger.debug("Warmup: %s iterations", warmup_iterations)
        for _ in range(warmup_iterations):
            try:
                func(*args, **kwargs)
            except Exception as e:
                logger.warning("Warmup error: %s", e)

        # Benchmark
        execution_times = []
        success_count = 0
        error_count = 0

        start_time = time.perf_counter()

        for i in range(iterations):
            iter_start = time.perf_counter()
            try:
                func(*args, **kwargs)
                iter_end = time.perf_counter()
                execution_times.append((iter_end - iter_start) * 1000)  # ms
                success_count += 1
            except Exception as e:
                logger.error("Iteration %s failed: %s", i, e)
                error_count += 1

        end_time = time.perf_counter()
        total_time = end_time - start_time

        # Calculate statistics
        if execution_times:
            sorted_times = sorted(execution_times)
            result = BenchmarkResult(
                name=name,
                iterations=iterations,
                total_time_seconds=total_time,
                min_time_ms=min(execution_times),
                max_time_ms=max(execution_times),
                avg_time_ms=statistics.mean(execution_times),
                median_time_ms=statistics.median(execution_times),
                p95_time_ms=sorted_times[int(len(sorted_times) * 0.95)],
                p99_time_ms=sorted_times[int(len(sorted_times) * 0.99)],
                std_dev_ms=statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
                throughput_qps=success_count / total_time,
                success_count=success_count,
                error_count=error_count,
            )
        else:
            result = BenchmarkResult(
                name=name,
                iterations=iterations,
                total_time_seconds=total_time,
                min_time_ms=0,
                max_time_ms=0,
                avg_time_ms=0,
                median_time_ms=0,
                p95_time_ms=0,
                p99_time_ms=0,
                std_dev_ms=0,
                throughput_qps=0,
                success_count=success_count,
                error_count=error_count,
            )

        self.results.append(result)

        logger.info(
            f"Benchmark complete: {name} - "
            f"Avg: {result.avg_time_ms:.2f}ms, "
            f"P95: {result.p95_time_ms:.2f}ms, "
            f"Throughput: {result.throughput_qps:.2f} QPS"
        )

        return result

    def compare_benchmarks(
        self, baseline: BenchmarkResult, current: BenchmarkResult, threshold_percent: float = 10.0
    ) -> Dict[str, Any]:
        """
        Compare two benchmark results for regression detection.

        Args:
            baseline: Baseline benchmark result
            current: Current benchmark result
            threshold_percent: Regression threshold percentage

        Returns:
            Comparison report
        """
        avg_diff_percent = (current.avg_time_ms - baseline.avg_time_ms) / baseline.avg_time_ms * 100
        p95_diff_percent = (current.p95_time_ms - baseline.p95_time_ms) / baseline.p95_time_ms * 100
        throughput_diff_percent = (
            (current.throughput_qps - baseline.throughput_qps) / baseline.throughput_qps * 100
        )

        is_regression = (
            avg_diff_percent > threshold_percent
            or p95_diff_percent > threshold_percent
            or throughput_diff_percent < -threshold_percent
        )

        comparison = {
            "baseline": {
                "avg_time_ms": baseline.avg_time_ms,
                "p95_time_ms": baseline.p95_time_ms,
                "throughput_qps": baseline.throughput_qps,
            },
            "current": {
                "avg_time_ms": current.avg_time_ms,
                "p95_time_ms": current.p95_time_ms,
                "throughput_qps": current.throughput_qps,
            },
            "differences": {
                "avg_time_percent": f"{avg_diff_percent:+.2f}%",
                "p95_time_percent": f"{p95_diff_percent:+.2f}%",
                "throughput_percent": f"{throughput_diff_percent:+.2f}%",
            },
            "is_regression": is_regression,
            "threshold_percent": threshold_percent,
        }

        if is_regression:
            logger.warning("Performance regression detected for %s", current.name)
        else:
            logger.info("No regression detected for %s", current.name)

        return comparison

    def export_results(self, filepath: str):
        """
        Export benchmark results to JSON.

        Args:
            filepath: Output file path
        """
        data = {
            "benchmarks": [result.to_dict() for result in self.results],
            "summary": {
                "total_benchmarks": len(self.results),
                "avg_throughput_qps": (
                    statistics.mean(r.throughput_qps for r in self.results) if self.results else 0
                ),
            },
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.info("Results exported to %s", filepath)


class LoadTester:
    """Load testing tool for concurrent requests."""

    def __init__(self, max_workers: int = 10):
        """
        Initialize load tester.

        Args:
            max_workers: Maximum concurrent workers
        """
        self.max_workers = max_workers
        logger.info("Load Tester initialized with %s workers", max_workers)

    def run_load_test(
        self,
        name: str,
        func: Callable,
        concurrent_users: int,
        duration_seconds: float,
        *args,
        **kwargs,
    ) -> LoadTestResult:
        """
        Run load test with concurrent users.

        Args:
            name: Test name
            func: Function to test
            concurrent_users: Number of concurrent users
            duration_seconds: Test duration in seconds
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Load test result
        """
        logger.info(
            f"Running load test: {name} " f"({concurrent_users} users, {duration_seconds}s)"
        )

        response_times = []
        successful_requests = 0
        failed_requests = 0

        start_time = time.perf_counter()
        end_time = start_time + duration_seconds

        def execute_request():
            """Execute single request."""
            nonlocal successful_requests, failed_requests

            req_start = time.perf_counter()
            try:
                func(*args, **kwargs)
                req_end = time.perf_counter()
                response_times.append((req_end - req_start) * 1000)
                successful_requests += 1
            except Exception as e:
                logger.debug("Request failed: %s", e)
                failed_requests += 1

        # Execute concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []

            while time.perf_counter() < end_time:
                # Submit requests up to concurrent_users limit
                while len(futures) < concurrent_users and time.perf_counter() < end_time:
                    future = executor.submit(execute_request)
                    futures.append(future)

                # Wait for some to complete
                done, futures = concurrent.futures.wait(
                    futures, timeout=0.1, return_when=concurrent.futures.FIRST_COMPLETED
                )
                futures = list(futures)

            # Wait for remaining
            concurrent.futures.wait(futures)

        actual_duration = time.perf_counter() - start_time
        total_requests = successful_requests + failed_requests

        # Calculate statistics
        if response_times:
            sorted_times = sorted(response_times)
            result = LoadTestResult(
                name=name,
                concurrent_users=concurrent_users,
                duration_seconds=actual_duration,
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                avg_response_time_ms=statistics.mean(response_times),
                median_response_time_ms=statistics.median(response_times),
                p95_response_time_ms=sorted_times[int(len(sorted_times) * 0.95)],
                p99_response_time_ms=sorted_times[int(len(sorted_times) * 0.99)],
                throughput_rps=successful_requests / actual_duration,
                error_rate=failed_requests / total_requests * 100 if total_requests > 0 else 0,
            )
        else:
            result = LoadTestResult(
                name=name,
                concurrent_users=concurrent_users,
                duration_seconds=actual_duration,
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                avg_response_time_ms=0,
                median_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                throughput_rps=0,
                error_rate=100.0,
            )

        logger.info(
            f"Load test complete: {name} - "
            f"RPS: {result.throughput_rps:.2f}, "
            f"Avg: {result.avg_response_time_ms:.2f}ms, "
            f"Error rate: {result.error_rate:.2f}%"
        )

        return result


class QueryBenchmarkSuite:
    """Comprehensive query benchmark suite."""

    def __init__(self):
        """Initialize benchmark suite."""
        self.benchmark = PerformanceBenchmark()
        self.load_tester = LoadTester()
        self.test_queries: Dict[str, Callable] = {}

    def register_query(self, name: str, func: Callable):
        """
        Register query for benchmarking.

        Args:
            name: Query name
            func: Query function
        """
        self.test_queries[name] = func
        logger.info("Registered query: %s", name)

    def run_all_benchmarks(self, iterations: int = 100) -> List[BenchmarkResult]:
        """
        Run benchmarks for all registered queries.

        Args:
            iterations: Number of iterations per query

        Returns:
            List of benchmark results
        """
        results = []

        for name, func in self.test_queries.items():
            result = self.benchmark.run_benchmark(name, func, iterations=iterations)
            results.append(result)

        return results

    def run_load_tests(
        self, concurrent_users: List[int] = None, duration_seconds: float = 30.0
    ) -> List[LoadTestResult]:
        """
        Run load tests for all registered queries.

        Args:
            concurrent_users: List of concurrent user counts to test
            duration_seconds: Duration of each test

        Returns:
            List of load test results
        """
        if concurrent_users is None:
            concurrent_users = [1, 5, 10, 20]

        results = []

        for name, func in self.test_queries.items():
            for users in concurrent_users:
                result = self.load_tester.run_load_test(
                    f"{name}_users{users}", func, users, duration_seconds
                )
                results.append(result)

        return results

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive benchmark report.

        Returns:
            Report dictionary
        """
        if not self.benchmark.results:
            return {"error": "No benchmark results available"}

        report = {
            "summary": {
                "total_queries": len(self.test_queries),
                "total_benchmarks": len(self.benchmark.results),
                "avg_throughput_qps": statistics.mean(
                    r.throughput_qps for r in self.benchmark.results
                ),
                "fastest_query": min(self.benchmark.results, key=lambda r: r.avg_time_ms).name,
                "slowest_query": max(self.benchmark.results, key=lambda r: r.avg_time_ms).name,
            },
            "benchmarks": [r.to_dict() for r in self.benchmark.results],
        }

        return report


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Initialize suite
    suite = QueryBenchmarkSuite()

    # Example query functions
    def simple_query():
        time.sleep(0.01)  # Simulate 10ms query
        return [{"id": i} for i in range(10)]

    def complex_query():
        time.sleep(0.05)  # Simulate 50ms query
        return [{"id": i} for i in range(100)]

    # Register queries
    suite.register_query("simple_vertex_query", simple_query)
    suite.register_query("complex_traversal", complex_query)

    # Run benchmarks
    print("Running benchmarks...")
    benchmark_results = suite.run_all_benchmarks(iterations=50)

    # Run load tests
    print("\nRunning load tests...")
    load_results = suite.run_load_tests(concurrent_users=[1, 5, 10], duration_seconds=10.0)

    # Generate report
    report = suite.generate_report()
    print("\nBenchmark Report:")
    print(json.dumps(report, indent=2))
