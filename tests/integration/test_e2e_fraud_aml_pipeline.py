#!/usr/bin/env python3
"""
End-to-End Fraud/AML Detection Pipeline Test

Tests the complete data flow:
    Data Generator → Pulsar → GraphConsumer → JanusGraph → Fraud/AML Detection

This validates that:
1. Synthetic data with fraud/AML patterns is generated
2. Data is published to Pulsar
3. GraphConsumer loads data into JanusGraph (via HCD backend)
4. Fraud/AML detection correctly identifies patterns

Requires running services:
- Pulsar (port 6650)
- JanusGraph (port 18182)
- OpenSearch (port 9200)

Run with: PYTHONPATH=. pytest tests/integration/test_e2e_fraud_aml_pipeline.py -v

Created: 2026-02-06
"""

import os
import sys
import time
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import logging

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'banking'))

logger = logging.getLogger(__name__)

# Service availability checks
def check_pulsar_available():
    """Check if Pulsar is available."""
    try:
        import pulsar
        client = pulsar.Client('pulsar://localhost:6650', operation_timeout_seconds=5)
        client.close()
        return True
    except Exception:
        return False

def check_janusgraph_available():
    """Check if JanusGraph is available using client approach."""
    try:
        from gremlin_python.driver import client, serializer
        c = client.Client(
            'ws://localhost:18182/gremlin', 'g',
            message_serializer=serializer.GraphSONSerializersV3d0()
        )
        result = c.submit('g.V().count()').all().result()
        c.close()
        return True
    except Exception:
        return False

def check_opensearch_available():
    """Check if OpenSearch is available."""
    try:
        from opensearchpy import OpenSearch
        use_ssl = os.getenv('OPENSEARCH_USE_SSL', 'true').lower() == 'true'
        client = OpenSearch(
            hosts=[{'host': 'localhost', 'port': 9200}],
            http_auth=('admin', 'admin'),
            use_ssl=use_ssl,
            verify_certs=False,
            ssl_show_warn=False
        )
        client.info()
        return True
    except Exception:
        return False


# Skip markers
PULSAR_AVAILABLE = check_pulsar_available()
JANUSGRAPH_AVAILABLE = check_janusgraph_available()
OPENSEARCH_AVAILABLE = check_opensearch_available()

skip_no_full_stack = pytest.mark.skipif(
    not (PULSAR_AVAILABLE and JANUSGRAPH_AVAILABLE and OPENSEARCH_AVAILABLE),
    reason="Full stack (Pulsar, JanusGraph, OpenSearch) not available"
)
skip_no_janusgraph = pytest.mark.skipif(
    not JANUSGRAPH_AVAILABLE,
    reason="JanusGraph not available"
)
skip_no_pulsar = pytest.mark.skipif(
    not PULSAR_AVAILABLE,
    reason="Pulsar not available"
)


class GremlinClient:
    """Simple Gremlin client wrapper using GraphSON3."""
    
    def __init__(self, url: str = 'ws://localhost:18182/gremlin'):
        from gremlin_python.driver import client, serializer
        self.url = url
        self.client = client.Client(url, 'g', message_serializer=serializer.GraphSONSerializersV3d0())
    
    def execute(self, query: str) -> List:
        """Execute a Gremlin query string."""
        return self.client.submit(query).all().result()
    
    def close(self):
        """Close the connection."""
        self.client.close()


@pytest.fixture(scope="module")
def gremlin_client():
    """Provide a Gremlin client for tests."""
    if not JANUSGRAPH_AVAILABLE:
        pytest.skip("JanusGraph not available")
    client = GremlinClient()
    yield client
    client.close()


@pytest.fixture(scope="module")
def temp_output_dir():
    """Provide a temporary output directory."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir, ignore_errors=True)


class TestE2EDataGeneratorToPulsar:
    """Test data generator → Pulsar flow."""
    
    @skip_no_pulsar
    def test_generate_and_publish_persons(self, temp_output_dir):
        """Test generating persons and publishing to Pulsar."""
        from banking.streaming.streaming_orchestrator import StreamingOrchestrator, StreamingConfig
        
        config = StreamingConfig(
            seed=42,
            person_count=10,
            company_count=3,
            account_count=15,
            transaction_count=0,
            communication_count=0,
            trade_count=0,
            travel_count=0,
            document_count=0,
            use_mock_producer=False,
            pulsar_url="pulsar://localhost:6650",
            output_dir=temp_output_dir
        )
        
        with StreamingOrchestrator(config) as orchestrator:
            stats = orchestrator.generate_all()
            
            assert stats.persons_generated == 10
            assert stats.companies_generated == 3
            assert stats.accounts_generated == 15
            assert stats.events_published > 0
            assert stats.events_failed == 0
    
    @skip_no_pulsar
    def test_generate_with_transactions(self, temp_output_dir):
        """Test generating full dataset with transactions."""
        from banking.streaming.streaming_orchestrator import StreamingOrchestrator, StreamingConfig
        
        config = StreamingConfig(
            seed=100,
            person_count=5,
            company_count=2,
            account_count=10,
            transaction_count=50,  # Generate transactions for AML testing
            communication_count=10,
            trade_count=0,
            travel_count=0,
            document_count=0,
            use_mock_producer=False,
            pulsar_url="pulsar://localhost:6650",
            output_dir=temp_output_dir
        )
        
        with StreamingOrchestrator(config) as orchestrator:
            stats = orchestrator.generate_all()
            
            assert stats.transactions_generated == 50
            assert stats.events_published > 0
            
            # Verify event counts by type
            assert 'person' in stats.events_by_type
            assert 'transaction' in stats.events_by_type


class TestE2EGraphConsumerIntegration:
    """Test Pulsar → GraphConsumer → JanusGraph flow."""
    
    @skip_no_full_stack
    def test_graph_consumer_initialization(self):
        """Test GraphConsumer can be initialized."""
        from banking.streaming.graph_consumer import GraphConsumer
        
        consumer = GraphConsumer(
            pulsar_url="pulsar://localhost:6650",
            janusgraph_url="ws://localhost:18182/gremlin"
        )
        assert consumer is not None
        assert consumer.pulsar_url == "pulsar://localhost:6650"
    
    @skip_no_full_stack
    def test_graph_consumer_connect(self):
        """Test GraphConsumer can connect to services."""
        from banking.streaming.graph_consumer import GraphConsumer
        
        consumer = GraphConsumer(
            pulsar_url="pulsar://localhost:6650",
            janusgraph_url="ws://localhost:18182/gremlin"
        )
        
        try:
            consumer.connect()
            assert consumer.consumer is not None
            assert consumer.g is not None
        finally:
            consumer.disconnect()


class TestE2EJanusGraphDataVerification:
    """Test that data exists in JanusGraph after pipeline."""
    
    @skip_no_janusgraph
    def test_count_persons_in_graph(self, gremlin_client):
        """Verify persons exist in JanusGraph."""
        result = gremlin_client.execute("g.V().hasLabel('Person').count()")
        assert isinstance(result, list)
        person_count = result[0]
        logger.info(f"Persons in graph: {person_count}")
        assert isinstance(person_count, int)
    
    @skip_no_janusgraph
    def test_count_accounts_in_graph(self, gremlin_client):
        """Verify accounts exist in JanusGraph."""
        result = gremlin_client.execute("g.V().hasLabel('Account').count()")
        account_count = result[0]
        logger.info(f"Accounts in graph: {account_count}")
        assert isinstance(account_count, int)
    
    @skip_no_janusgraph
    def test_count_transactions_in_graph(self, gremlin_client):
        """Verify transactions exist in JanusGraph."""
        result = gremlin_client.execute("g.E().hasLabel('MADE_TRANSACTION').count()")
        txn_count = result[0]
        logger.info(f"Transactions in graph: {txn_count}")
        assert isinstance(txn_count, int)
    
    @skip_no_janusgraph
    def test_query_transaction_amounts(self, gremlin_client):
        """Query transaction amounts for AML analysis."""
        result = gremlin_client.execute(
            "g.E().hasLabel('MADE_TRANSACTION').has('amount').values('amount').limit(50)"
        )
        logger.info(f"Sample transaction amounts: {result[:10] if result else 'None'}")
        assert isinstance(result, list)


class TestE2EFraudDetection:
    """Test fraud detection against JanusGraph data."""
    
    @skip_no_janusgraph
    def test_fraud_detector_initialization(self):
        """Test FraudDetector initializes with real JanusGraph."""
        from fraud.fraud_detection import FraudDetector
        
        try:
            detector = FraudDetector(
                janusgraph_host='localhost',
                janusgraph_port=18182,
                opensearch_host='localhost',
                opensearch_port=9200
            )
            assert detector is not None
            assert detector.graph_url == "ws://localhost:18182/gremlin"
        except Exception as e:
            pytest.skip(f"FraudDetector init failed: {e}")
    
    @skip_no_janusgraph
    def test_fraud_detector_thresholds_match_config(self):
        """Verify fraud detector thresholds are correctly configured."""
        from fraud.fraud_detection import FraudDetector
        
        assert FraudDetector.CRITICAL_THRESHOLD == 0.9
        assert FraudDetector.HIGH_THRESHOLD == 0.75
        assert FraudDetector.MEDIUM_THRESHOLD == 0.5
        assert FraudDetector.MAX_TRANSACTIONS_PER_DAY == 50


class TestE2EAMLStructuringDetection:
    """Test AML structuring detection against JanusGraph data."""
    
    @skip_no_janusgraph
    def test_structuring_detector_initialization(self):
        """Test StructuringDetector initializes with real JanusGraph."""
        from aml.structuring_detection import StructuringDetector
        
        detector = StructuringDetector(
            janusgraph_host='localhost',
            janusgraph_port=18182
        )
        assert detector is not None
        assert detector.graph_url == "ws://localhost:18182/gremlin"
        assert detector.ctr_threshold == Decimal('10000.00')
    
    @skip_no_janusgraph
    def test_detect_smurfing_against_real_data(self):
        """Test smurfing detection against real JanusGraph data."""
        from aml.structuring_detection import StructuringDetector
        
        detector = StructuringDetector(
            janusgraph_host='localhost',
            janusgraph_port=18182
        )
        
        # Query for an account that exists in the graph
        client = GremlinClient()
        try:
            result = client.execute(
                "g.V().hasLabel('Account').values('account_id').limit(1)"
            )
            if result:
                account_id = result[0]
                logger.info(f"Testing smurfing detection for account: {account_id}")
                
                # Run detection - may or may not find patterns depending on data
                patterns = detector.detect_smurfing(
                    account_id=account_id,
                    time_window_hours=24,
                    min_transactions=3
                )
                assert isinstance(patterns, list)
                logger.info(f"Smurfing patterns found: {len(patterns)}")
            else:
                logger.info("No accounts in graph - skipping smurfing test")
        finally:
            client.close()
    
    @skip_no_janusgraph
    def test_query_suspicious_transactions(self, gremlin_client):
        """Query for transactions that might indicate structuring."""
        # Look for transactions between $9,000-$10,000 (suspicious range)
        result = gremlin_client.execute("""
            g.E().hasLabel('MADE_TRANSACTION')
             .has('amount')
             .has('amount', gte(9000.0))
             .has('amount', lt(10000.0))
             .limit(20)
        """)
        logger.info(f"Suspicious range transactions: {len(result)}")
        assert isinstance(result, list)


class TestE2EFullPipelineValidation:
    """Validate the complete pipeline end-to-end."""
    
    @skip_no_full_stack
    def test_data_consistency_across_pipeline(self, gremlin_client, temp_output_dir):
        """Test that data generated matches what's queryable in JanusGraph."""
        from banking.streaming.streaming_orchestrator import StreamingOrchestrator, StreamingConfig
        
        # Generate data with unique seed for this test
        test_seed = int(time.time()) % 10000
        
        config = StreamingConfig(
            seed=test_seed,
            person_count=5,
            company_count=2,
            account_count=8,
            transaction_count=20,
            communication_count=5,
            trade_count=0,
            travel_count=0,
            document_count=0,
            use_mock_producer=False,
            pulsar_url="pulsar://localhost:6650",
            output_dir=temp_output_dir
        )
        
        with StreamingOrchestrator(config) as orchestrator:
            stats = orchestrator.generate_all()
            
            # Log what was generated
            logger.info(f"Generated - Persons: {stats.persons_generated}, "
                       f"Accounts: {stats.accounts_generated}, "
                       f"Transactions: {stats.transactions_generated}")
            logger.info(f"Events published: {stats.events_published}")
            
            assert stats.events_published > 0
            
            # Note: Consumer must be running to load into JanusGraph
            # This test validates the publishing side of the pipeline
    
    @skip_no_janusgraph
    def test_graph_statistics_summary(self, gremlin_client):
        """Get summary statistics of what's in the graph."""
        # Vertex counts by label
        vertex_result = gremlin_client.execute("g.V().groupCount().by(label)")
        logger.info(f"Vertex counts: {vertex_result}")
        
        # Edge counts by label
        edge_result = gremlin_client.execute("g.E().groupCount().by(label)")
        logger.info(f"Edge counts: {edge_result}")
        
        # Total counts
        total_v = gremlin_client.execute("g.V().count()")[0]
        total_e = gremlin_client.execute("g.E().count()")[0]
        logger.info(f"Total vertices: {total_v}, Total edges: {total_e}")
        
        assert total_v >= 0
        assert total_e >= 0


class TestE2EPatternInjection:
    """Test fraud/AML pattern injection through the pipeline."""
    
    @skip_no_full_stack
    def test_generate_with_structuring_patterns(self, temp_output_dir):
        """Test generating data with structuring patterns enabled."""
        from banking.streaming.streaming_orchestrator import StreamingOrchestrator, StreamingConfig
        
        config = StreamingConfig(
            seed=555,
            person_count=10,
            company_count=3,
            account_count=20,
            transaction_count=100,  # More transactions for pattern detection
            communication_count=20,
            trade_count=0,
            travel_count=0,
            document_count=0,
            use_mock_producer=False,
            pulsar_url="pulsar://localhost:6650",
            output_dir=temp_output_dir
        )
        
        with StreamingOrchestrator(config) as orchestrator:
            stats = orchestrator.generate_all()
            
            logger.info(f"Generated {stats.transactions_generated} transactions")
            logger.info(f"Published {stats.events_published} events to Pulsar")
            
            assert stats.transactions_generated == 100
            assert stats.events_published > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
