"""Tests for initialize_graph module."""

from unittest.mock import MagicMock, patch

import pytest

from src.python.init.initialize_graph import (
    initialize_schema,
    load_sample_data,
    main,
    verify_initialization,
)


@pytest.fixture()
def mock_client():
    return MagicMock()


class TestInitializeSchema:
    def test_success(self, mock_client):
        mock_client.execute.return_value = ["Schema created"]
        assert initialize_schema(mock_client) is True

    def test_query_error_returns_true(self, mock_client):
        from src.python.client.exceptions import QueryError

        mock_client.execute.side_effect = QueryError("already exists")
        assert initialize_schema(mock_client) is True

    def test_unexpected_error_returns_false(self, mock_client):
        mock_client.execute.side_effect = RuntimeError("unexpected")
        assert initialize_schema(mock_client) is False


class TestLoadSampleData:
    def test_success(self, mock_client):
        mock_client.execute.return_value = ["Sample data loaded"]
        assert load_sample_data(mock_client) is True

    def test_query_error_returns_false(self, mock_client):
        from src.python.client.exceptions import QueryError

        mock_client.execute.side_effect = QueryError("syntax error")
        assert load_sample_data(mock_client) is False

    def test_unexpected_error_returns_false(self, mock_client):
        mock_client.execute.side_effect = RuntimeError("boom")
        assert load_sample_data(mock_client) is False


class TestVerifyInitialization:
    def test_success_correct_counts(self, mock_client):
        mock_client.execute.side_effect = [
            [11],
            [19],
            ["Alice", "Bob", "Carol"],
            ["TechCorp", "DataLabs"],
            ["GraphDB Pro", "Analytics Suite"],
        ]
        assert verify_initialization(mock_client) is True

    def test_wrong_vertex_count(self, mock_client):
        mock_client.execute.side_effect = [
            [5],
            [19],
            ["Alice"],
            ["TechCorp"],
            ["GraphDB Pro"],
        ]
        assert verify_initialization(mock_client) is False

    def test_wrong_edge_count(self, mock_client):
        mock_client.execute.side_effect = [
            [11],
            [10],
            ["Alice"],
            ["TechCorp"],
            ["GraphDB Pro"],
        ]
        assert verify_initialization(mock_client) is False

    def test_query_error(self, mock_client):
        from src.python.client.exceptions import QueryError

        mock_client.execute.side_effect = QueryError("fail")
        assert verify_initialization(mock_client) is False

    def test_index_error(self, mock_client):
        mock_client.execute.return_value = []
        mock_client.execute.side_effect = IndexError("empty")
        assert verify_initialization(mock_client) is False

    def test_unexpected_error(self, mock_client):
        mock_client.execute.side_effect = RuntimeError("boom")
        assert verify_initialization(mock_client) is False


class TestMain:
    @patch("src.python.init.initialize_graph.JanusGraphClient")
    @patch("src.python.init.initialize_graph.time.sleep")
    def test_success(self, mock_sleep, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.execute.side_effect = [
            ["Schema created"],
            ["Data loaded"],
            [11],
            [19],
            ["Alice", "Bob", "Carol"],
            ["TechCorp", "DataLabs"],
            ["GraphDB Pro", "Analytics Suite"],
        ]
        assert main() == 0

    @patch("src.python.init.initialize_graph.JanusGraphClient")
    def test_connection_error(self, mock_client_cls):
        from src.python.client.exceptions import ConnectionError

        mock_client_cls.return_value.__enter__ = MagicMock(side_effect=ConnectionError("refused"))
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        assert main() == 1

    @patch("src.python.init.initialize_graph.JanusGraphClient")
    @patch("src.python.init.initialize_graph.time.sleep")
    def test_schema_failure(self, mock_sleep, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.execute.side_effect = RuntimeError("schema fail")
        assert main() == 1
