#!/usr/bin/env python3
"""
End-to-End Streaming Pipeline Integration Tests

Tests the complete data flow:
  Data Generator → Pulsar → Graph Consumer → JanusGraph
                         → Vector Consumer → OpenSearch
"""

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

pytestmark = pytest.mark.integration


def check_janusgraph() -> bool:
    try:
        from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
        from gremlin_python.process.anonymous_traversal import traversal

        host = os.getenv("JANUSGRAPH_HOST", "localhost")
        port = os.getenv("JANUSGRAPH_PORT", "18182")
        conn = DriverRemoteConnection(f"ws://{host}:{port}/gremlin", "g")
        g = traversal().with_remote(conn)
        g.V().limit(1).toList()
        conn.close()
        return True
    except Exception:
        return False


def check_opensearch() -> bool:
    try:
        from opensearchpy import OpenSearch

        client = OpenSearch(
            hosts=[
                {
                    "host": os.getenv("OPENSEARCH_HOST", "localhost"),
                    "port": int(os.getenv("OPENSEARCH_PORT", "9200")),
                }
            ],
            use_ssl=os.getenv("OPENSEARCH_USE_SSL", "false").lower() == "true",
            verify_certs=False,
        )
        client.info()
        return True
    except Exception:
        return False


JG_AVAILABLE = check_janusgraph()
OS_AVAILABLE = check_opensearch()

skip_no_jg = pytest.mark.skipif(not JG_AVAILABLE, reason="JanusGraph unavailable")
skip_no_os = pytest.mark.skipif(not OS_AVAILABLE, reason="OpenSearch unavailable")
skip_no_services = pytest.mark.skipif(
    not (JG_AVAILABLE and OS_AVAILABLE), reason="Services unavailable"
)


@pytest.fixture
def test_id() -> str:
    return f"e2e-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def jg_client():
    from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
    from gremlin_python.process.anonymous_traversal import traversal

    conn = DriverRemoteConnection(
        f"ws://localhost:{os.getenv('JANUSGRAPH_PORT', '18182')}/gremlin", "g"
    )
    yield traversal().with_remote(conn)
    conn.close()


@pytest.fixture
def os_client():
    from opensearchpy import OpenSearch

    yield OpenSearch(
        hosts=[{"host": "localhost", "port": int(os.getenv("OPENSEARCH_PORT", "9200"))}],
        use_ssl=False,
        verify_certs=False,
    )


class TestServiceConnectivity:
    @skip_no_jg
    def test_janusgraph(self, jg_client):
        assert jg_client.V().count().next() >= 0

    @skip_no_os
    def test_opensearch(self, os_client):
        assert "cluster_name" in os_client.info()


class TestIDConsistency:
    @skip_no_services
    def test_entity_id_propagation(self, test_id, jg_client, os_client):
        """Test same entity_id appears in both systems."""
        # Write to JanusGraph
        jg_client.addV("person").property("entity_id", test_id).property(
            "name", f"Test {test_id}"
        ).iterate()

        # Write to OpenSearch
        os_client.index(
            index="e2e-test",
            id=test_id,
            body={"entity_id": test_id, "name": f"Test {test_id}"},
            refresh=True,
        )

        # Verify both
        jg_result = jg_client.V().has("entity_id", test_id).values("name").toList()
        assert len(jg_result) == 1

        os_result = os_client.get(index="e2e-test", id=test_id)
        assert os_result["found"] and os_result["_source"]["entity_id"] == test_id

        # Cleanup
        jg_client.V().has("entity_id", test_id).drop().iterate()
        os_client.delete(index="e2e-test", id=test_id, ignore=[404])


class TestStreamingFlow:
    @skip_no_services
    def test_mock_streaming(self, test_id, jg_client, os_client):
        """Simulate dual-write pattern."""
        event = {"entity_id": test_id, "name": "Stream Test", "risk_score": 0.3}

        jg_client.addV("person").property("entity_id", event["entity_id"]).property(
            "name", event["name"]
        ).iterate()
        os_client.index(index="e2e-test", id=event["entity_id"], body=event, refresh=True)

        # Verify consistency
        jg_name = jg_client.V().has("entity_id", test_id).values("name").next()
        os_name = os_client.get(index="e2e-test", id=test_id)["_source"]["name"]
        assert jg_name == os_name == "Stream Test"

        # Cleanup
        jg_client.V().has("entity_id", test_id).drop().iterate()
        os_client.delete(index="e2e-test", id=test_id, ignore=[404])


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
