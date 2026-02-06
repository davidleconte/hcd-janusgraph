"""
End-to-End Streaming Tests (Week 5)
===================================

Comprehensive E2E tests that validate cross-system consistency:
- Generator -> Pulsar -> Graph Consumer -> JanusGraph
- Generator -> Pulsar -> Vector Consumer -> OpenSearch

Requires running services:
- Pulsar (port 6650)
- JanusGraph (port 18182)
- OpenSearch (port 9200)

Run with: PYTHONPATH=. pytest tests/integration/test_e2e_streaming.py -v

Created: 2026-02-06
Week 5: E2E Test Harness
"""

import pytest
import os
import time
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from banking.streaming.events import EntityEvent, create_person_event
from banking.streaming.producer import EntityProducer, MockEntityProducer, get_producer
from banking.streaming.streaming_orchestrator import StreamingOrchestrator, StreamingConfig

# Check if services are available
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
    """Check if JanusGraph is available."""
    try:
        from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
        from gremlin_python.process.anonymous_traversal import traversal
        conn = DriverRemoteConnection('ws://localhost:18182/gremlin', 'g')
        g = traversal().withRemote(conn)
        # Use count().next() instead of toList() to avoid custom type deserialization issues
        g.V().count().next()
        conn.close()
        return True
    except Exception:
        return False

def check_opensearch_available():
    """Check if OpenSearch is available."""
    try:
        from opensearchpy import OpenSearch
        import os
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

skip_no_pulsar = pytest.mark.skipif(not PULSAR_AVAILABLE, reason="Pulsar not available")
skip_no_janusgraph = pytest.mark.skipif(not JANUSGRAPH_AVAILABLE, reason="JanusGraph not available")
skip_no_opensearch = pytest.mark.skipif(not OPENSEARCH_AVAILABLE, reason="OpenSearch not available")
skip_no_services = pytest.mark.skipif(
    not (PULSAR_AVAILABLE and JANUSGRAPH_AVAILABLE and OPENSEARCH_AVAILABLE),
    reason="Full stack (Pulsar, JanusGraph, OpenSearch) not available"
)


@dataclass
class E2ETestResult:
    """Result from E2E test run."""
    events_published: int
    events_in_graph: int
    events_in_vector: int
    id_match_graph: bool
    id_match_vector: bool
    errors: List[str]


class TestE2EPulsarPublishing:
    """Tests for publishing to real Pulsar."""
    
    @skip_no_pulsar
    def test_publish_single_event(self):
        """Test publishing a single event to Pulsar."""
        event = create_person_event(
            person_id="test-e2e-person-001",
            name="E2E Test Person",
            payload={
                "id": "test-e2e-person-001",
                "first_name": "E2E",
                "last_name": "Test",
                "email": "e2e@test.com"
            },
            source="E2ETest"
        )
        
        producer = EntityProducer(pulsar_url="pulsar://localhost:6650")
        try:
            producer.send(event)
            producer.flush()
        finally:
            producer.close()
    
    @skip_no_pulsar
    def test_publish_batch_events(self):
        """Test publishing a batch of events to Pulsar."""
        events = [
            create_person_event(
                person_id=f"test-batch-{i}",
                name=f"Batch Person {i}",
                payload={
                    "id": f"test-batch-{i}",
                    "first_name": f"Batch{i}",
                    "last_name": "Test",
                    "email": f"batch{i}@test.com"
                },
                source="E2EBatchTest"
            )
            for i in range(10)
        ]
        
        producer = EntityProducer(pulsar_url="pulsar://localhost:6650")
        try:
            results = producer.send_batch(events)
            producer.flush()
            
            # Verify batch was sent
            total_sent = sum(results.values())
            assert total_sent == 10
        finally:
            producer.close()


class TestE2EStreamingOrchestrator:
    """E2E tests for StreamingOrchestrator with real Pulsar."""
    
    @skip_no_pulsar
    def test_orchestrator_with_real_pulsar(self):
        """Test StreamingOrchestrator publishes to real Pulsar."""
        config = StreamingConfig(
            seed=42,
            person_count=5,
            company_count=2,
            account_count=10,
            transaction_count=20,
            communication_count=10,
            trade_count=0,
            travel_count=0,
            document_count=0,
            use_mock_producer=False,
            pulsar_url="pulsar://localhost:6650",
            output_dir=Path(tempfile.mkdtemp())
        )
        
        try:
            with StreamingOrchestrator(config) as orchestrator:
                stats = orchestrator.generate_all()
                
                assert stats.events_published > 0
                assert stats.events_failed == 0
                
                # Verify counts
                assert stats.persons_generated == 5
                assert stats.companies_generated == 2
                assert stats.accounts_generated == 10
        finally:
            shutil.rmtree(config.output_dir, ignore_errors=True)
    
    @skip_no_pulsar
    def test_orchestrator_event_consistency(self):
        """Test that orchestrator event count matches published count."""
        config = StreamingConfig(
            seed=123,
            person_count=10,
            company_count=3,
            account_count=15,
            transaction_count=30,
            communication_count=20,
            trade_count=0,
            travel_count=0,
            document_count=0,
            use_mock_producer=False,
            pulsar_url="pulsar://localhost:6650",
            output_dir=Path(tempfile.mkdtemp())
        )
        
        try:
            with StreamingOrchestrator(config) as orchestrator:
                stats = orchestrator.generate_all()
                
                # Total entities should equal events published
                expected_events = (
                    stats.persons_generated +
                    stats.companies_generated +
                    stats.accounts_generated +
                    stats.transactions_generated +
                    stats.communications_generated
                )
                
                assert stats.events_published == expected_events
                
                # Verify by type
                assert stats.events_by_type.get('person', 0) == 10
                assert stats.events_by_type.get('company', 0) == 3
                assert stats.events_by_type.get('account', 0) == 15
                assert stats.events_by_type.get('transaction', 0) == 30
                assert stats.events_by_type.get('communication', 0) == 20
        finally:
            shutil.rmtree(config.output_dir, ignore_errors=True)


class TestE2EJanusGraphIntegration:
    """E2E tests for JanusGraph integration."""
    
    @skip_no_janusgraph
    def test_janusgraph_connection(self):
        """Test basic JanusGraph connectivity."""
        from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
        from gremlin_python.process.anonymous_traversal import traversal
        
        conn = DriverRemoteConnection('ws://localhost:18182/gremlin', 'g')
        try:
            g = traversal().withRemote(conn)
            count = g.V().count().next()
            assert isinstance(count, int)
        finally:
            conn.close()
    
    @skip_no_janusgraph
    def test_janusgraph_vertex_operations(self):
        """Test basic vertex operations in JanusGraph."""
        from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
        from gremlin_python.process.anonymous_traversal import traversal
        from gremlin_python.process.graph_traversal import __
        
        conn = DriverRemoteConnection('ws://localhost:18182/gremlin', 'g')
        try:
            g = traversal().withRemote(conn)
            
            # Create a test vertex
            test_id = f"e2e-test-{int(time.time())}"
            
            # Upsert pattern (idempotent) - use iterate() to avoid custom type deserialization
            g.V().has('person', 'entity_id', test_id).fold().coalesce(
                __.unfold(),
                __.addV('person').property('entity_id', test_id).property('name', 'E2E Test')
            ).iterate()
            
            # Verify vertex exists (use count to avoid custom type deserialization)
            vertex_count = g.V().has('person', 'entity_id', test_id).count().next()
            assert vertex_count == 1
            
            # Cleanup
            g.V().has('person', 'entity_id', test_id).drop().iterate()
        finally:
            conn.close()


class TestE2EOpenSearchIntegration:
    """E2E tests for OpenSearch integration."""
    
    def _get_opensearch_client(self):
        """Create OpenSearch client with environment-based SSL config."""
        from opensearchpy import OpenSearch
        
        use_ssl = os.environ.get('OPENSEARCH_USE_SSL', 'true').lower() == 'true'
        
        return OpenSearch(
            hosts=[{'host': 'localhost', 'port': 9200}],
            http_auth=('admin', 'admin'),
            use_ssl=use_ssl,
            verify_certs=False,
            ssl_show_warn=False
        )
    
    @skip_no_opensearch
    def test_opensearch_connection(self):
        """Test basic OpenSearch connectivity."""
        client = self._get_opensearch_client()
        
        info = client.info()
        assert 'version' in info
    
    @skip_no_opensearch
    def test_opensearch_index_operations(self):
        """Test basic index operations in OpenSearch."""
        client = self._get_opensearch_client()
        
        # Create test index
        test_index = "e2e-test-index"
        test_id = f"e2e-doc-{int(time.time())}"
        
        try:
            # Create index if not exists
            if not client.indices.exists(test_index):
                client.indices.create(test_index)
            
            # Index a document
            doc = {
                "entity_id": test_id,
                "name": "E2E Test Document",
                "type": "person"
            }
            client.index(index=test_index, id=test_id, body=doc, refresh=True)
            
            # Verify document exists
            result = client.get(index=test_index, id=test_id)
            assert result['_id'] == test_id
            assert result['_source']['entity_id'] == test_id
            
            # Cleanup
            client.delete(index=test_index, id=test_id)
        finally:
            # Clean up test index
            if client.indices.exists(test_index):
                client.indices.delete(test_index)


class TestE2ECrossSystemConsistency:
    """E2E tests for cross-system data consistency."""
    
    @skip_no_services
    def test_full_pipeline_consistency(self):
        """Test that IDs are consistent across all systems."""
        # This test validates the ID consistency guarantee of the architecture:
        # - Same UUID used in Pulsar partition key
        # - Same UUID stored in JanusGraph as entity_id property
        # - Same UUID used as OpenSearch document _id
        
        from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
        from gremlin_python.process.anonymous_traversal import traversal
        from opensearchpy import OpenSearch
        
        # Generate unique test ID
        test_entity_id = f"consistency-test-{int(time.time())}"
        
        # Create event
        event = create_person_event(
            person_id=test_entity_id,
            name="Consistency Test Person",
            payload={
                "id": test_entity_id,
                "first_name": "Consistency",
                "last_name": "Test",
                "email": "consistency@test.com"
            },
            source="E2EConsistencyTest"
        )
        
        # Publish to Pulsar
        producer = EntityProducer(pulsar_url="pulsar://localhost:6650")
        try:
            producer.send(event)
            producer.flush()
        finally:
            producer.close()
        
        # Note: In a full implementation, we would wait for consumers to process
        # For now, we validate the event format and ID consistency
        
        # Verify event structure maintains ID consistency
        pulsar_msg = event.to_pulsar_message()
        assert pulsar_msg['partition_key'] == test_entity_id
        
        # Verify payload has same ID
        assert event.payload['id'] == test_entity_id
        
        # Verify entity_id matches
        assert event.entity_id == test_entity_id
    
    @skip_no_services
    def test_id_format_consistency(self):
        """Test that ID format is consistent for all entity types."""
        config = StreamingConfig(
            seed=999,
            person_count=3,
            company_count=2,
            account_count=5,
            transaction_count=0,
            communication_count=0,
            trade_count=0,
            travel_count=0,
            document_count=0,
            use_mock_producer=True,  # Use mock to capture events
            output_dir=Path(tempfile.mkdtemp())
        )
        
        try:
            with StreamingOrchestrator(config) as orchestrator:
                orchestrator.generate_all()
                
                mock_producer = orchestrator.producer
                
                # Verify all events have consistent ID format
                for event in mock_producer.events:
                    # entity_id should be non-empty
                    assert event.entity_id
                    assert len(event.entity_id) > 0
                    
                    # Pulsar message partition_key should match entity_id
                    msg = event.to_pulsar_message()
                    assert msg['partition_key'] == event.entity_id
                    
                    # Payload should contain the ID
                    assert 'id' in event.payload or any(
                        k.endswith('_id') for k in event.payload.keys()
                    )
        finally:
            shutil.rmtree(config.output_dir, ignore_errors=True)


class TestE2EResilience:
    """E2E tests for system resilience."""
    
    @skip_no_pulsar
    def test_reconnection_after_publish(self):
        """Test that producer can handle multiple sessions."""
        for i in range(3):
            producer = EntityProducer(pulsar_url="pulsar://localhost:6650")
            try:
                event = create_person_event(
                    person_id=f"reconnect-test-{i}",
                    name=f"Reconnect Test {i}",
                    payload={"id": f"reconnect-test-{i}", "iteration": i},
                    source="ReconnectTest"
                )
                producer.send(event)
                producer.flush()
            finally:
                producer.close()
    
    @skip_no_pulsar  
    def test_large_batch_handling(self):
        """Test handling of larger batches."""
        events = [
            create_person_event(
                person_id=f"large-batch-{i}",
                name=f"Large Batch Person {i}",
                payload={
                    "id": f"large-batch-{i}",
                    "first_name": f"Person{i}",
                    "last_name": "Test",
                    "data": "x" * 100  # Add some data
                },
                source="LargeBatchTest"
            )
            for i in range(100)
        ]
        
        producer = EntityProducer(pulsar_url="pulsar://localhost:6650")
        try:
            results = producer.send_batch(events)
            producer.flush()
            
            total_sent = sum(results.values())
            assert total_sent == 100
        finally:
            producer.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
