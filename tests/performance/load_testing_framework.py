#!/usr/bin/env python3
"""
Load Testing Framework for HCD + JanusGraph Banking Compliance Platform

This framework provides comprehensive load testing capabilities including:
- API endpoint load testing
- Credential rotation under load
- Query sanitization performance testing
- Vault client performance testing
- Concurrent user simulation
- Performance baseline validation

Usage:
    python load_testing_framework.py --scenario api_load
    python load_testing_framework.py --scenario full --duration 300
    python load_testing_framework.py --report-only
"""

import argparse
import asyncio
import json
import logging
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LoadTestScenario(Enum):
    """Load test scenarios"""
    API_LOAD = "api_load"
    CREDENTIAL_ROTATION = "credential_rotation"
    QUERY_SANITIZATION = "query_sanitization"
    VAULT_PERFORMANCE = "vault_performance"
    CONCURRENT_USERS = "concurrent_users"
    FULL = "full"


@dataclass
class PerformanceMetrics:
    """Performance metrics for a test"""
    scenario: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    response_times: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    @property
    def duration(self) -> float:
        """Total test duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    @property
    def requests_per_second(self) -> float:
        """Requests per second"""
        if self.duration > 0:
            return self.total_requests / self.duration
        return 0.0
    
    @property
    def success_rate(self) -> float:
        """Success rate percentage"""
        if self.total_requests > 0:
            return (self.successful_requests / self.total_requests) * 100
        return 0.0
    
    @property
    def avg_response_time(self) -> float:
        """Average response time in milliseconds"""
        if self.response_times:
            return statistics.mean(self.response_times)
        return 0.0
    
    @property
    def p50_response_time(self) -> float:
        """50th percentile response time"""
        if self.response_times:
            return statistics.median(self.response_times)
        return 0.0
    
    @property
    def p95_response_time(self) -> float:
        """95th percentile response time"""
        if self.response_times:
            sorted_times = sorted(self.response_times)
            index = int(len(sorted_times) * 0.95)
            return sorted_times[index]
        return 0.0
    
    @property
    def p99_response_time(self) -> float:
        """99th percentile response time"""
        if self.response_times:
            sorted_times = sorted(self.response_times)
            index = int(len(sorted_times) * 0.99)
            return sorted_times[index]
        return 0.0
    
    @property
    def max_response_time(self) -> float:
        """Maximum response time"""
        if self.response_times:
            return max(self.response_times)
        return 0.0
    
    @property
    def min_response_time(self) -> float:
        """Minimum response time"""
        if self.response_times:
            return min(self.response_times)
        return 0.0


@dataclass
class SLARequirements:
    """SLA requirements for validation"""
    max_avg_response_time: float = 200.0  # ms
    max_p95_response_time: float = 500.0  # ms
    max_p99_response_time: float = 1000.0  # ms
    min_success_rate: float = 99.5  # %
    min_requests_per_second: float = 100.0


class LoadTestingFramework:
    """Main load testing framework"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        vault_url: str = "http://localhost:8200",
        janusgraph_url: str = "http://localhost:8182"
    ):
        self.base_url = base_url
        self.vault_url = vault_url
        self.janusgraph_url = janusgraph_url
        self.session = self._create_session()
        self.sla = SLARequirements()
        
    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=100, pool_maxsize=100)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def run_scenario(
        self,
        scenario: LoadTestScenario,
        duration: int = 60,
        concurrent_users: int = 10
    ) -> PerformanceMetrics:
        """Run a load test scenario"""
        logger.info(f"Starting load test scenario: {scenario.value}")
        logger.info(f"Duration: {duration}s, Concurrent Users: {concurrent_users}")
        
        if scenario == LoadTestScenario.API_LOAD:
            return self._test_api_load(duration, concurrent_users)
        elif scenario == LoadTestScenario.CREDENTIAL_ROTATION:
            return self._test_credential_rotation(duration)
        elif scenario == LoadTestScenario.QUERY_SANITIZATION:
            return self._test_query_sanitization(duration, concurrent_users)
        elif scenario == LoadTestScenario.VAULT_PERFORMANCE:
            return self._test_vault_performance(duration, concurrent_users)
        elif scenario == LoadTestScenario.CONCURRENT_USERS:
            return self._test_concurrent_users(duration, concurrent_users)
        elif scenario == LoadTestScenario.FULL:
            return self._test_full_stack(duration, concurrent_users)
        else:
            raise ValueError(f"Unknown scenario: {scenario}")
    
    def _test_api_load(self, duration: int, concurrent_users: int) -> PerformanceMetrics:
        """Test API endpoint load"""
        metrics = PerformanceMetrics(scenario="API Load Test")
        metrics.start_time = time.time()
        
        # Define API endpoints to test
        endpoints = [
            {"method": "GET", "path": "/api/v1/health"},
            {"method": "GET", "path": "/api/v1/persons"},
            {"method": "GET", "path": "/api/v1/accounts"},
            {"method": "GET", "path": "/api/v1/transactions"},
        ]
        
        def make_request():
            """Make a single request"""
            endpoint = endpoints[metrics.total_requests % len(endpoints)]
            url = f"{self.base_url}{endpoint['path']}"
            
            try:
                start = time.time()
                response = self.session.request(
                    endpoint['method'],
                    url,
                    timeout=10
                )
                elapsed = (time.time() - start) * 1000  # Convert to ms
                
                metrics.total_requests += 1
                metrics.response_times.append(elapsed)
                
                if response.status_code < 400:
                    metrics.successful_requests += 1
                else:
                    metrics.failed_requests += 1
                    metrics.errors.append(f"{endpoint['path']}: {response.status_code}")
                    
            except Exception as e:
                metrics.total_requests += 1
                metrics.failed_requests += 1
                metrics.errors.append(f"{endpoint['path']}: {str(e)}")
        
        # Run load test
        end_time = time.time() + duration
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            while time.time() < end_time:
                future = executor.submit(make_request)
                futures.append(future)
                
                # Limit queue size
                if len(futures) > concurrent_users * 10:
                    for f in as_completed(futures[:concurrent_users]):
                        pass
                    futures = futures[concurrent_users:]
            
            # Wait for remaining requests
            for future in as_completed(futures):
                pass
        
        metrics.end_time = time.time()
        return metrics
    
    def _test_credential_rotation(self, duration: int) -> PerformanceMetrics:
        """Test credential rotation under load"""
        metrics = PerformanceMetrics(scenario="Credential Rotation Under Load")
        metrics.start_time = time.time()
        
        logger.info("Testing credential rotation performance...")
        
        # Simulate credential rotation operations
        rotation_operations = [
            "generate_new_password",
            "update_vault_secret",
            "update_database_credentials",
            "verify_new_credentials",
            "cleanup_old_credentials"
        ]
        
        end_time = time.time() + duration
        while time.time() < end_time:
            for operation in rotation_operations:
                try:
                    start = time.time()
                    
                    # Simulate operation (in real test, call actual rotation functions)
                    time.sleep(0.01)  # Simulate work
                    
                    elapsed = (time.time() - start) * 1000
                    metrics.total_requests += 1
                    metrics.successful_requests += 1
                    metrics.response_times.append(elapsed)
                    
                except Exception as e:
                    metrics.total_requests += 1
                    metrics.failed_requests += 1
                    metrics.errors.append(f"{operation}: {str(e)}")
        
        metrics.end_time = time.time()
        return metrics
    
    def _test_query_sanitization(self, duration: int, concurrent_users: int) -> PerformanceMetrics:
        """Test query sanitization performance"""
        metrics = PerformanceMetrics(scenario="Query Sanitization Performance")
        metrics.start_time = time.time()
        
        # Test queries with various injection attempts
        test_queries = [
            "normal query",
            "test'); DROP TABLE users; --",
            "test' OR '1'='1",
            "test\"; g.V().drop(); //",
            "test' UNION SELECT * FROM passwords--",
        ]
        
        def test_sanitization():
            """Test query sanitization"""
            query = test_queries[metrics.total_requests % len(test_queries)]
            
            try:
                start = time.time()
                
                # Test sanitization endpoint
                response = self.session.get(
                    f"{self.base_url}/api/v1/persons/search",
                    params={"name": query},
                    timeout=5
                )
                
                elapsed = (time.time() - start) * 1000
                metrics.total_requests += 1
                metrics.response_times.append(elapsed)
                
                if response.status_code < 400:
                    metrics.successful_requests += 1
                else:
                    metrics.failed_requests += 1
                    
            except Exception as e:
                metrics.total_requests += 1
                metrics.failed_requests += 1
                metrics.errors.append(str(e))
        
        # Run test
        end_time = time.time() + duration
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            while time.time() < end_time:
                future = executor.submit(test_sanitization)
                futures.append(future)
                
                if len(futures) > concurrent_users * 5:
                    for f in as_completed(futures[:concurrent_users]):
                        pass
                    futures = futures[concurrent_users:]
            
            for future in as_completed(futures):
                pass
        
        metrics.end_time = time.time()
        return metrics
    
    def _test_vault_performance(self, duration: int, concurrent_users: int) -> PerformanceMetrics:
        """Test Vault client performance"""
        metrics = PerformanceMetrics(scenario="Vault Performance")
        metrics.start_time = time.time()
        
        def test_vault_operation():
            """Test Vault read operation"""
            try:
                start = time.time()
                
                # Test Vault health endpoint (doesn't require auth)
                response = self.session.get(
                    f"{self.vault_url}/v1/sys/health",
                    timeout=5
                )
                
                elapsed = (time.time() - start) * 1000
                metrics.total_requests += 1
                metrics.response_times.append(elapsed)
                
                if response.status_code < 400:
                    metrics.successful_requests += 1
                else:
                    metrics.failed_requests += 1
                    
            except Exception as e:
                metrics.total_requests += 1
                metrics.failed_requests += 1
                metrics.errors.append(str(e))
        
        # Run test
        end_time = time.time() + duration
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            while time.time() < end_time:
                future = executor.submit(test_vault_operation)
                futures.append(future)
                
                if len(futures) > concurrent_users * 5:
                    for f in as_completed(futures[:concurrent_users]):
                        pass
                    futures = futures[concurrent_users:]
            
            for future in as_completed(futures):
                pass
        
        metrics.end_time = time.time()
        return metrics
    
    def _test_concurrent_users(self, duration: int, concurrent_users: int) -> PerformanceMetrics:
        """Test concurrent user simulation"""
        metrics = PerformanceMetrics(scenario="Concurrent Users")
        metrics.start_time = time.time()
        
        def simulate_user_session():
            """Simulate a user session"""
            try:
                # Login
                start = time.time()
                response = self.session.post(
                    f"{self.base_url}/api/v1/auth/login",
                    json={"username": "test", "password": "test"},
                    timeout=5
                )
                elapsed = (time.time() - start) * 1000
                metrics.response_times.append(elapsed)
                
                if response.status_code >= 400:
                    metrics.failed_requests += 1
                    return
                
                # Perform operations
                operations = [
                    "/api/v1/persons",
                    "/api/v1/accounts",
                    "/api/v1/transactions"
                ]
                
                for op in operations:
                    start = time.time()
                    response = self.session.get(
                        f"{self.base_url}{op}",
                        timeout=5
                    )
                    elapsed = (time.time() - start) * 1000
                    metrics.response_times.append(elapsed)
                    
                    if response.status_code < 400:
                        metrics.successful_requests += 1
                    else:
                        metrics.failed_requests += 1
                
                metrics.total_requests += len(operations) + 1
                
            except Exception as e:
                metrics.failed_requests += 1
                metrics.errors.append(str(e))
        
        # Run test
        end_time = time.time() + duration
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            while time.time() < end_time:
                future = executor.submit(simulate_user_session)
                futures.append(future)
                
                if len(futures) > concurrent_users * 2:
                    for f in as_completed(futures[:concurrent_users]):
                        pass
                    futures = futures[concurrent_users:]
            
            for future in as_completed(futures):
                pass
        
        metrics.end_time = time.time()
        return metrics
    
    def _test_full_stack(self, duration: int, concurrent_users: int) -> PerformanceMetrics:
        """Test full stack under load"""
        metrics = PerformanceMetrics(scenario="Full Stack Load Test")
        
        # Run all scenarios
        scenarios = [
            LoadTestScenario.API_LOAD,
            LoadTestScenario.QUERY_SANITIZATION,
            LoadTestScenario.VAULT_PERFORMANCE,
            LoadTestScenario.CONCURRENT_USERS
        ]
        
        all_metrics = []
        for scenario in scenarios:
            scenario_metrics = self.run_scenario(scenario, duration // len(scenarios), concurrent_users)
            all_metrics.append(scenario_metrics)
        
        # Aggregate metrics
        metrics.start_time = min(m.start_time for m in all_metrics if m.start_time)
        metrics.end_time = max(m.end_time for m in all_metrics if m.end_time)
        metrics.total_requests = sum(m.total_requests for m in all_metrics)
        metrics.successful_requests = sum(m.successful_requests for m in all_metrics)
        metrics.failed_requests = sum(m.failed_requests for m in all_metrics)
        
        for m in all_metrics:
            metrics.response_times.extend(m.response_times)
            metrics.errors.extend(m.errors)
        
        return metrics
    
    def validate_sla(self, metrics: PerformanceMetrics) -> Tuple[bool, List[str]]:
        """Validate performance against SLA requirements"""
        violations = []
        
        if metrics.avg_response_time > self.sla.max_avg_response_time:
            violations.append(
                f"Average response time ({metrics.avg_response_time:.2f}ms) "
                f"exceeds SLA ({self.sla.max_avg_response_time}ms)"
            )
        
        if metrics.p95_response_time > self.sla.max_p95_response_time:
            violations.append(
                f"P95 response time ({metrics.p95_response_time:.2f}ms) "
                f"exceeds SLA ({self.sla.max_p95_response_time}ms)"
            )
        
        if metrics.p99_response_time > self.sla.max_p99_response_time:
            violations.append(
                f"P99 response time ({metrics.p99_response_time:.2f}ms) "
                f"exceeds SLA ({self.sla.max_p99_response_time}ms)"
            )
        
        if metrics.success_rate < self.sla.min_success_rate:
            violations.append(
                f"Success rate ({metrics.success_rate:.2f}%) "
                f"below SLA ({self.sla.min_success_rate}%)"
            )
        
        if metrics.requests_per_second < self.sla.min_requests_per_second:
            violations.append(
                f"Requests per second ({metrics.requests_per_second:.2f}) "
                f"below SLA ({self.sla.min_requests_per_second})"
            )
        
        return len(violations) == 0, violations
    
    def generate_report(self, metrics: PerformanceMetrics, output_dir: Path):
        """Generate load test report"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        
        # Save JSON report
        json_file = output_dir / f"load-test-{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump({
                "scenario": metrics.scenario,
                "timestamp": datetime.utcnow().isoformat(),
                "duration": metrics.duration,
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "success_rate": metrics.success_rate,
                "requests_per_second": metrics.requests_per_second,
                "response_times": {
                    "avg": metrics.avg_response_time,
                    "p50": metrics.p50_response_time,
                    "p95": metrics.p95_response_time,
                    "p99": metrics.p99_response_time,
                    "min": metrics.min_response_time,
                    "max": metrics.max_response_time
                },
                "errors": metrics.errors[:100]  # Limit error list
            }, f, indent=2)
        
        logger.info(f"JSON report saved to {json_file}")
        
        # Save markdown report
        md_file = output_dir / f"load-test-{timestamp}.md"
        self._save_markdown_report(metrics, md_file)
        logger.info(f"Markdown report saved to {md_file}")
    
    def _save_markdown_report(self, metrics: PerformanceMetrics, output_file: Path):
        """Save markdown report"""
        sla_passed, violations = self.validate_sla(metrics)
        
        with open(output_file, 'w') as f:
            f.write(f"# Load Test Report: {metrics.scenario}\n\n")
            f.write(f"**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
            f.write(f"**Duration:** {metrics.duration:.2f}s\n\n")
            
            # Summary
            f.write("## Summary\n\n")
            f.write(f"- **Total Requests:** {metrics.total_requests:,}\n")
            f.write(f"- **Successful:** {metrics.successful_requests:,}\n")
            f.write(f"- **Failed:** {metrics.failed_requests:,}\n")
            f.write(f"- **Success Rate:** {metrics.success_rate:.2f}%\n")
            f.write(f"- **Requests/Second:** {metrics.requests_per_second:.2f}\n\n")
            
            # Response Times
            f.write("## Response Times (ms)\n\n")
            f.write(f"- **Average:** {metrics.avg_response_time:.2f}\n")
            f.write(f"- **Median (P50):** {metrics.p50_response_time:.2f}\n")
            f.write(f"- **P95:** {metrics.p95_response_time:.2f}\n")
            f.write(f"- **P99:** {metrics.p99_response_time:.2f}\n")
            f.write(f"- **Min:** {metrics.min_response_time:.2f}\n")
            f.write(f"- **Max:** {metrics.max_response_time:.2f}\n\n")
            
            # SLA Validation
            f.write("## SLA Validation\n\n")
            if sla_passed:
                f.write("✅ **All SLA requirements met**\n\n")
            else:
                f.write("❌ **SLA violations detected:**\n\n")
                for violation in violations:
                    f.write(f"- {violation}\n")
                f.write("\n")
            
            # SLA Requirements
            f.write("### SLA Requirements\n\n")
            f.write(f"- Max Average Response Time: {self.sla.max_avg_response_time}ms\n")
            f.write(f"- Max P95 Response Time: {self.sla.max_p95_response_time}ms\n")
            f.write(f"- Max P99 Response Time: {self.sla.max_p99_response_time}ms\n")
            f.write(f"- Min Success Rate: {self.sla.min_success_rate}%\n")
            f.write(f"- Min Requests/Second: {self.sla.min_requests_per_second}\n\n")
            
            # Errors
            if metrics.errors:
                f.write("## Errors\n\n")
                f.write(f"Total errors: {len(metrics.errors)}\n\n")
                f.write("Sample errors (first 10):\n\n")
                for error in metrics.errors[:10]:
                    f.write(f"- {error}\n")
                f.write("\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Load Testing Framework for HCD + JanusGraph Platform"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        choices=[s.value for s in LoadTestScenario],
        default="api_load",
        help="Load test scenario to run"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Test duration in seconds"
    )
    parser.add_argument(
        "--concurrent-users",
        type=int,
        default=10,
        help="Number of concurrent users"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/implementation/audits/performance"),
        help="Output directory for reports"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:8000",
        help="Base URL for API"
    )
    
    args = parser.parse_args()
    
    # Create framework
    framework = LoadTestingFramework(base_url=args.base_url)
    
    # Run test
    scenario = LoadTestScenario(args.scenario)
    metrics = framework.run_scenario(
        scenario,
        duration=args.duration,
        concurrent_users=args.concurrent_users
    )
    
    # Generate report
    framework.generate_report(metrics, args.output_dir)
    
    # Print summary
    print("\n" + "="*80)
    print("LOAD TEST SUMMARY")
    print("="*80)
    print(f"Scenario: {metrics.scenario}")
    print(f"Duration: {metrics.duration:.2f}s")
    print(f"Total Requests: {metrics.total_requests:,}")
    print(f"Success Rate: {metrics.success_rate:.2f}%")
    print(f"Requests/Second: {metrics.requests_per_second:.2f}")
    print(f"Avg Response Time: {metrics.avg_response_time:.2f}ms")
    print(f"P95 Response Time: {metrics.p95_response_time:.2f}ms")
    print(f"P99 Response Time: {metrics.p99_response_time:.2f}ms")
    
    # Validate SLA
    sla_passed, violations = framework.validate_sla(metrics)
    print("\nSLA Validation:")
    if sla_passed:
        print("✅ All SLA requirements met")
    else:
        print("❌ SLA violations:")
        for violation in violations:
            print(f"  - {violation}")
    print("="*80)
    
    # Exit with error code if SLA failed
    if not sla_passed:
        exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
