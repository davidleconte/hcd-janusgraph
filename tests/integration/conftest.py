"""
Integration Test Configuration and Fixtures
============================================

Shared fixtures and utilities for integration tests.
Provides service health checks and automatic test skipping.

Author: IBM Bob
Created: 2026-01-29
Phase: Week 3 Day 5 - Integration Test Improvements
"""

import pytest
import requests
import socket
import time
import logging
from typing import Dict, Optional
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal

logger = logging.getLogger(__name__)


# Service configuration
SERVICES = {
    'hcd': {
        'host': 'localhost',
        'port': 9042,
        'name': 'HCD/Cassandra',
        'check_type': 'tcp'
    },
    'janusgraph': {
        'host': 'localhost',
        'port': 8182,
        'name': 'JanusGraph',
        'check_type': 'http',
        'url': 'http://localhost:8182?gremlin=g.V().count()'
    },
    'prometheus': {
        'host': 'localhost',
        'port': 9090,
        'name': 'Prometheus',
        'check_type': 'http',
        'url': 'http://localhost:9090/-/healthy'
    },
    'grafana': {
        'host': 'localhost',
        'port': 3001,
        'name': 'Grafana',
        'check_type': 'http',
        'url': 'http://localhost:3001/api/health'
    },
    'alertmanager': {
        'host': 'localhost',
        'port': 9093,
        'name': 'AlertManager',
        'check_type': 'http',
        'url': 'http://localhost:9093/-/healthy'
    },
}


def check_port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    """
    Check if a TCP port is open.
    
    Args:
        host: Hostname or IP address
        port: Port number
        timeout: Connection timeout in seconds
    
    Returns:
        True if port is open, False otherwise
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((host, port))
        return result == 0
    except socket.error:
        return False
    finally:
        sock.close()


def check_http_endpoint(url: str, timeout: float = 5.0) -> bool:
    """
    Check if an HTTP endpoint is accessible.
    
    Args:
        url: URL to check
        timeout: Request timeout in seconds
    
    Returns:
        True if endpoint returns 200, False otherwise
    """
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except requests.RequestException:
        return False


def check_service_health(service_name: str) -> Dict[str, any]:
    """
    Check if a service is healthy.
    
    Args:
        service_name: Name of service to check (from SERVICES dict)
    
    Returns:
        Dict with 'available', 'message', and 'details' keys
    """
    if service_name not in SERVICES:
        return {
            'available': False,
            'message': f"Unknown service: {service_name}",
            'details': None
        }
    
    service = SERVICES[service_name]
    check_type = service.get('check_type', 'tcp')
    
    if check_type == 'tcp':
        available = check_port_open(service['host'], service['port'])
        message = (
            f"{service['name']} is available on {service['host']}:{service['port']}"
            if available else
            f"{service['name']} is not available on {service['host']}:{service['port']}"
        )
    elif check_type == 'http':
        available = check_http_endpoint(service['url'])
        message = (
            f"{service['name']} is healthy at {service['url']}"
            if available else
            f"{service['name']} is not responding at {service['url']}"
        )
    else:
        available = False
        message = f"Unknown check type: {check_type}"
    
    return {
        'available': available,
        'message': message,
        'details': service
    }


def get_deployment_instructions() -> str:
    """Get instructions for deploying the full stack"""
    return """
To run integration tests, deploy the full stack:

1. Deploy services:
   cd config/compose
   bash ../../scripts/deployment/deploy_full_stack.sh

2. Wait for services to be ready (60-90 seconds):
   sleep 90

3. Run integration tests:
   cd ../..
   pytest tests/integration/ -v

4. To stop services:
   cd config/compose
   bash ../../scripts/deployment/stop_full_stack.sh
"""


# Pytest fixtures

@pytest.fixture(scope="session")
def service_health_check():
    """
    Session-scoped fixture that checks service health once.
    Returns a function to check specific services.
    """
    health_cache = {}
    
    def check(service_name: str) -> Dict[str, any]:
        if service_name not in health_cache:
            health_cache[service_name] = check_service_health(service_name)
        return health_cache[service_name]
    
    return check


@pytest.fixture(scope="session")
def require_janusgraph(service_health_check):
    """
    Fixture that skips test if JanusGraph is not available.
    """
    health = service_health_check('janusgraph')
    if not health['available']:
        pytest.skip(
            f"JanusGraph not available: {health['message']}\n"
            f"{get_deployment_instructions()}"
        )
    return health


@pytest.fixture(scope="session")
def require_hcd(service_health_check):
    """
    Fixture that skips test if HCD is not available.
    """
    health = service_health_check('hcd')
    if not health['available']:
        pytest.skip(
            f"HCD not available: {health['message']}\n"
            f"{get_deployment_instructions()}"
        )
    return health


@pytest.fixture(scope="session")
def require_prometheus(service_health_check):
    """
    Fixture that skips test if Prometheus is not available.
    """
    health = service_health_check('prometheus')
    if not health['available']:
        pytest.skip(
            f"Prometheus not available: {health['message']}\n"
            "Prometheus is optional for basic tests."
        )
    return health


@pytest.fixture(scope="session")
def require_grafana(service_health_check):
    """
    Fixture that skips test if Grafana is not available.
    """
    health = service_health_check('grafana')
    if not health['available']:
        pytest.skip(
            f"Grafana not available: {health['message']}\n"
            "Grafana is optional for basic tests."
        )
    return health


@pytest.fixture(scope="session")
def require_full_stack(require_janusgraph, require_hcd, require_prometheus, require_grafana):
    """
    Fixture that requires all services to be available.
    """
    return {
        'janusgraph': require_janusgraph,
        'hcd': require_hcd,
        'prometheus': require_prometheus,
        'grafana': require_grafana
    }


@pytest.fixture(scope="class")
def hcd_session(require_hcd):
    """
    Fixture providing HCD/Cassandra session.
    """
    auth_provider = PlainTextAuthProvider(
        username='cassandra',
        password='cassandra'
    )
    cluster = Cluster(
        ['localhost'],
        port=9042,
        auth_provider=auth_provider
    )
    session = cluster.connect()
    yield session
    cluster.shutdown()


@pytest.fixture(scope="class")
def janusgraph_connection(require_janusgraph):
    """
    Fixture providing JanusGraph graph traversal connection.
    """
    connection = DriverRemoteConnection('ws://localhost:8182/gremlin', 'g')
    g = traversal().withRemote(connection)
    yield g
    connection.close()


@pytest.fixture(scope="function")
def test_data_cleanup(janusgraph_connection):
    """
    Fixture that cleans up test data after each test.
    """
    yield
    
    # Cleanup test data
    g = janusgraph_connection
    test_labels = [
        'test_person', 'test_entity', 'test_temp',
        'perf_test', 'query_test', 'persistence_test'
    ]
    
    for label in test_labels:
        try:
            count = g.V().hasLabel(label).count().next()
            if count > 0:
                g.V().hasLabel(label).drop().iterate()
                logger.info(f"Cleaned up {count} vertices with label: {label}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {label}: {e}")


@pytest.fixture(scope="session", autouse=True)
def log_test_environment():
    """
    Automatically log test environment information at session start.
    """
    logger.info("="*60)
    logger.info("Integration Test Environment Check")
    logger.info("="*60)
    
    for service_name, service_config in SERVICES.items():
        health = check_service_health(service_name)
        status = "✅ AVAILABLE" if health['available'] else "❌ NOT AVAILABLE"
        logger.info(f"{service_config['name']}: {status}")
    
    logger.info("="*60)
    
    # Check if any required services are missing
    required_services = ['hcd', 'janusgraph']
    missing_services = [
        SERVICES[s]['name'] 
        for s in required_services 
        if not check_service_health(s)['available']
    ]
    
    if missing_services:
        logger.warning(
            f"\n⚠️  Required services not available: {', '.join(missing_services)}\n"
            f"{get_deployment_instructions()}"
        )


# Made with Bob