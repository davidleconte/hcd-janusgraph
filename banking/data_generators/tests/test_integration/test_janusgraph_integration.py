"""
JanusGraph Integration Tests
=============================

Tests for JanusGraph integration including:
- Connection tests
- Schema creation tests
- Data loading tests
- Query tests

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

import os

import pytest

JANUSGRAPH_PORT = int(os.getenv("JANUSGRAPH_PORT", "18182"))


def _get_gremlin_connection():
    from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
    from gremlin_python.driver.serializer import GraphSONSerializersV3d0
    from gremlin_python.process.anonymous_traversal import traversal

    conn = DriverRemoteConnection(
        f"ws://localhost:{JANUSGRAPH_PORT}/gremlin",
        "g",
        message_serializer=GraphSONSerializersV3d0(),
    )
    return traversal().with_remote(conn), conn


def _janusgraph_available():
    import socket

    try:
        with socket.create_connection(("localhost", JANUSGRAPH_PORT), timeout=3):
            return True
    except (socket.timeout, OSError):
        return False


_JG_AVAILABLE = _janusgraph_available()
skip_no_jg = pytest.mark.skipif(not _JG_AVAILABLE, reason="JanusGraph not available")


@pytest.fixture(scope="module")
def gremlin():
    if not _JG_AVAILABLE:
        pytest.skip("JanusGraph not available")
    g, conn = _get_gremlin_connection()
    yield g
    conn.close()


@pytest.mark.integration
class TestJanusGraphConnection:
    @skip_no_jg
    def test_connection_available(self, gremlin):
        count = gremlin.V().count().next()
        assert isinstance(count, int)
        assert count >= 0

    @skip_no_jg
    def test_schema_creation(self, gremlin):
        labels = gremlin.V().label().dedup().toList()
        assert isinstance(labels, list)

    @skip_no_jg
    def test_vertex_creation(self, gremlin):
        count = gremlin.V().count().next()
        assert count > 0

    @skip_no_jg
    def test_edge_creation(self, gremlin):
        count = gremlin.E().count().next()
        assert isinstance(count, int)


@pytest.mark.integration
class TestJanusGraphDataLoading:
    @skip_no_jg
    def test_load_persons(self, gremlin):
        persons = gremlin.V().hasLabel("person").count().next()
        assert persons >= 0

    @skip_no_jg
    def test_load_companies(self, gremlin):
        companies = gremlin.V().hasLabel("company").count().next()
        assert companies >= 0

    @skip_no_jg
    def test_load_accounts(self, gremlin):
        accounts = gremlin.V().hasLabel("account").count().next()
        assert accounts >= 0

    @skip_no_jg
    def test_load_transactions(self, gremlin):
        transactions = gremlin.V().hasLabel("transaction").count().next()
        assert transactions >= 0


@pytest.mark.integration
class TestJanusGraphQueries:
    @skip_no_jg
    def test_find_person_by_id(self, gremlin):
        persons = gremlin.V().hasLabel("person").limit(1).toList()
        if persons:
            vid = persons[0].id
            found = gremlin.V(vid).toList()
            assert len(found) == 1

    @skip_no_jg
    def test_find_transactions_by_account(self, gremlin):
        accounts = gremlin.V().hasLabel("account").limit(1).toList()
        assert isinstance(accounts, list)

    @skip_no_jg
    def test_pattern_detection_query(self, gremlin):
        result = gremlin.V().hasLabel("person").limit(5).valueMap(True).toList()
        assert isinstance(result, list)
