"""Comprehensive tests for src.python.security.query_sanitizer — targets 28% → 90%+."""

import os
import time

import pytest

os.environ.setdefault("AUDIT_LOG_DIR", "/tmp/janusgraph-test-logs")

from unittest.mock import MagicMock, patch

with patch("banking.compliance.audit_logger.AuditLogger.__init__", lambda self, *a, **kw: None):
    with patch("banking.compliance.audit_logger.AuditLogger.log_event", MagicMock()):
        import banking.compliance.audit_logger as _al

        _al._audit_logger = MagicMock()

        from src.python.security.query_sanitizer import (
            GremlinQueryBuilder,
            QueryAllowlist,
            QueryComplexity,
            QueryPattern,
            QueryValidator,
            ValidationError,
            sanitize_gremlin_query,
        )


class TestQueryPattern:
    def test_matches_simple(self):
        p = QueryPattern(
            name="test",
            pattern=r"^g\.V\(\)\.count\(\)$",
            description="count",
            complexity=QueryComplexity.SIMPLE,
        )
        assert p.matches("g.V().count()")
        assert not p.matches("g.E().count()")

    def test_default_fields(self):
        p = QueryPattern(name="t", pattern=".*", description="d", complexity=QueryComplexity.SIMPLE)
        assert p.max_results == 1000
        assert p.timeout_seconds == 30
        assert p.parameters == []


class TestQueryAllowlist:
    def setup_method(self):
        self.al = QueryAllowlist()

    def test_default_patterns_loaded(self):
        names = self.al.list_patterns()
        assert "get_vertex_by_id" in names
        assert "find_transaction_chain" in names
        assert len(names) >= 8

    def test_add_and_remove_pattern(self):
        p = QueryPattern(
            name="custom", pattern=r"^custom$", description="c", complexity=QueryComplexity.SIMPLE
        )
        self.al.add_pattern(p)
        assert "custom" in self.al.list_patterns()
        self.al.remove_pattern("custom")
        assert "custom" not in self.al.list_patterns()

    def test_remove_nonexistent(self):
        self.al.remove_pattern("nope")

    def test_validate_query_match(self):
        valid, pattern = self.al.validate_query("g.V('abc-123').valueMap()")
        assert valid
        assert pattern.name == "get_vertex_by_id"

    def test_validate_query_no_match(self):
        valid, pattern = self.al.validate_query("g.V().drop()")
        assert not valid
        assert pattern is None

    def test_get_pattern(self):
        assert self.al.get_pattern("get_vertex_by_id") is not None
        assert self.al.get_pattern("nonexistent") is None


class TestGremlinQueryBuilder:
    def setup_method(self):
        self.builder = GremlinQueryBuilder()

    def test_get_vertex_by_id(self):
        q = self.builder.get_vertex_by_id("person-123")
        assert q == "g.V('person-123').valueMap()"

    def test_get_vertex_by_id_invalid(self):
        with pytest.raises(ValidationError):
            self.builder.get_vertex_by_id("DROP; --")

    def test_get_vertex_by_property_string(self):
        q = self.builder.get_vertex_by_property("name", "alice")
        assert "has('name', 'alice')" in q

    def test_get_vertex_by_property_not_in_allowlist(self):
        with pytest.raises(ValidationError):
            self.builder.get_vertex_by_property("name", "has spaces and stuff!!!")

    def test_get_outgoing_edges(self):
        q = self.builder.get_outgoing_edges("v-1", limit=10)
        assert "outE().limit(10)" in q

    def test_get_outgoing_edges_invalid_id(self):
        with pytest.raises(ValidationError):
            self.builder.get_outgoing_edges("bad id!")

    def test_get_incoming_edges(self):
        q = self.builder.get_incoming_edges("v-1", limit=5)
        assert "inE().limit(5)" in q

    def test_count_vertices_by_label(self):
        q = self.builder.count_vertices_by_label("Person")
        assert q == "g.V().hasLabel('Person').count()"

    def test_count_vertices_invalid_label(self):
        with pytest.raises(ValidationError):
            self.builder.count_vertices_by_label("Bad Label!")

    def test_find_connected_accounts(self):
        q = self.builder.find_connected_accounts("p-1", limit=10)
        assert "out('owns')" in q

    def test_find_transaction_chain(self):
        q = self.builder.find_transaction_chain("a-1", hops=2, limit=50)
        assert "repeat(out('transacted')).times(2)" in q

    def test_find_transaction_chain_invalid_hops(self):
        with pytest.raises(ValidationError):
            self.builder.find_transaction_chain("a-1", hops=0)
        with pytest.raises(ValidationError):
            self.builder.find_transaction_chain("a-1", hops=6)

    def test_sanitize_value_int(self):
        assert self.builder._sanitize_value(42) == "42"

    def test_sanitize_value_float(self):
        assert self.builder._sanitize_value(3.14) == "3.14"

    def test_sanitize_value_bool(self):
        assert self.builder._sanitize_value(True) == "True"

    def test_sanitize_value_unsupported(self):
        with pytest.raises(ValidationError):
            self.builder._sanitize_value([1, 2, 3])

    def test_sanitize_value_string_escapes(self):
        assert self.builder._sanitize_value("it's") == "it\\'s"

    def test_validate_limit_invalid(self):
        with pytest.raises(ValidationError):
            self.builder._validate_limit(-1)
        with pytest.raises(ValidationError):
            self.builder._validate_limit("abc")

    def test_validate_limit_capped(self):
        assert self.builder._validate_limit(9999, max_limit=100) == 100

    def test_sanitize_property_name_invalid(self):
        with pytest.raises(ValidationError):
            self.builder._sanitize_property_name("bad name!")


class TestQueryValidator:
    def setup_method(self):
        self.validator = QueryValidator()

    def test_dangerous_pattern_system(self):
        ok, err = self.validator.validate("system()", user="u1")
        assert not ok
        assert "Dangerous" in err

    def test_dangerous_pattern_exec(self):
        ok, err = self.validator.validate("exec('x')", user="u1")
        assert not ok

    def test_dangerous_pattern_eval(self):
        ok, err = self.validator.validate("eval('x')", user="u1")
        assert not ok

    def test_dangerous_pattern_import(self):
        ok, err = self.validator.validate("__import__('os')", user="u1")
        assert not ok

    def test_dangerous_pattern_path_traversal(self):
        ok, err = self.validator.validate("../../etc/passwd", user="u1")
        assert not ok

    def test_dangerous_pattern_drop(self):
        ok, err = self.validator.validate("g.V().drop()", user="u1")
        assert not ok

    def test_dangerous_pattern_addV(self):
        ok, err = self.validator.validate("g.addV('x')", user="u1")
        assert not ok

    def test_dangerous_pattern_addE(self):
        ok, err = self.validator.validate("g.addE('x')", user="u1")
        assert not ok

    def test_dangerous_pattern_chaining(self):
        ok, err = self.validator.validate(";g.V().count()", user="u1")
        assert not ok

    def test_dangerous_pattern_comments(self):
        ok, err = self.validator.validate("g.V()/* hidden */", user="u1")
        assert not ok

    def test_not_in_allowlist(self):
        ok, err = self.validator.validate("g.V().toList()", user="u1")
        assert not ok
        assert "allowlist" in err.lower()

    def test_valid_query(self):
        ok, err = self.validator.validate("g.V('abc').valueMap()", user="u1")
        assert ok
        assert err is None

    def test_rate_limit(self):
        self.validator._max_queries_per_minute = 3
        for i in range(3):
            ok, _ = self.validator.validate("g.V('abc').valueMap()", user="limited")
            assert ok
        ok, err = self.validator.validate("g.V('abc').valueMap()", user="limited")
        assert not ok
        assert "Rate limit" in err

    def test_rate_limit_different_users(self):
        self.validator._max_queries_per_minute = 1
        ok1, _ = self.validator.validate("g.V('abc').valueMap()", user="u1")
        ok2, _ = self.validator.validate("g.V('abc').valueMap()", user="u2")
        assert ok1
        assert ok2

    def test_rate_limit_expiry(self):
        self.validator._max_queries_per_minute = 1
        self.validator._rate_limiter["u1"] = [time.time() - 120]
        ok, _ = self.validator.validate("g.V('abc').valueMap()", user="u1")
        assert ok


class TestSanitizeGremlinQuery:
    def test_valid(self):
        ok, query, err = sanitize_gremlin_query("g.V('x').valueMap()")
        assert ok
        assert query == "g.V('x').valueMap()"
        assert err is None

    def test_invalid(self):
        ok, query, err = sanitize_gremlin_query("g.V().drop()")
        assert not ok
        assert query == ""
        assert err is not None
