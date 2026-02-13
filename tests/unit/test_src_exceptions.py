"""Tests for src.python.exceptions module."""
import pytest
from src.python.exceptions import (
    JanusGraphBaseException as JanusGraphException,
    ConnectionError as JGConnectionError,
    QueryError,
    ValidationError,
    ConfigurationError,
    DataError,
    QueryExecutionError,
    ConnectionFailedError,
    EntityNotFoundError,
)


class TestJanusGraphException:
    def test_basic(self):
        e = JanusGraphException("test")
        assert "test" in str(e)
        assert isinstance(e, Exception)

    def test_with_attributes(self):
        e = JanusGraphException("test", error_code="JG_001")
        assert e.error_code == "JG_001"

    def test_to_dict(self):
        e = JanusGraphException("msg", error_code="E1", details={"k": "v"})
        d = e.to_dict()
        assert d["error_code"] == "E1"
        assert d["message"] == "msg"

    def test_str_representation(self):
        e = JanusGraphException("msg", error_code="E1")
        assert "msg" in str(e)


class TestExceptionHierarchy:
    def test_connection_error(self):
        e = JGConnectionError("conn failed")
        assert isinstance(e, JanusGraphException)

    def test_query_error(self):
        e = QueryError("bad query")
        assert isinstance(e, JanusGraphException)

    def test_query_execution_error(self):
        e = QueryExecutionError("exec failed")
        assert isinstance(e, QueryError)

    def test_validation_error(self):
        e = ValidationError("invalid input")
        assert isinstance(e, DataError)
        assert isinstance(e, JanusGraphException)

    def test_configuration_error(self):
        e = ConfigurationError("bad config")
        assert isinstance(e, JanusGraphException)

    def test_data_error(self):
        e = DataError("bad data")
        assert isinstance(e, JanusGraphException)

    def test_connection_failed_error(self):
        e = ConnectionFailedError("failed")
        assert isinstance(e, JGConnectionError)

    def test_entity_not_found_error(self):
        e = EntityNotFoundError("not found")
        assert isinstance(e, DataError)


class TestErrorSerialization:
    def test_to_dict_basic(self):
        e = JanusGraphException("bad", error_code="Q001")
        d = e.to_dict()
        assert d["message"] == "bad"
        assert d["error_code"] == "Q001"
        assert "timestamp" in d

    def test_to_dict_with_details(self):
        e = JanusGraphException("err", details={"retry": 3})
        d = e.to_dict()
        assert d["details"] == {"retry": 3}

    def test_to_dict_with_cause(self):
        cause = ValueError("original")
        e = JanusGraphException("wrapped", cause=cause)
        d = e.to_dict()
        assert "cause" in d
