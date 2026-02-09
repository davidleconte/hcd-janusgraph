"""Tests for VectorSearchClient (mocked OpenSearch)."""

from unittest.mock import MagicMock, call, patch

import numpy as np
import pytest

from src.python.utils.vector_search import (
    VectorSearchClient,
    create_person_name_index,
    create_transaction_description_index,
)


@pytest.fixture
def mock_os_client():
    with patch("src.python.utils.vector_search.OpenSearch") as mock_cls:
        instance = MagicMock()
        instance.info.return_value = {"version": {"number": "3.3.4"}}
        mock_cls.return_value = instance
        yield instance


@pytest.fixture
def client(mock_os_client):
    return VectorSearchClient(host="localhost", port=9200)


class TestVectorSearchClientInit:
    def test_unauthenticated(self, mock_os_client):
        c = VectorSearchClient()
        mock_os_client.info.assert_called_once()

    def test_authenticated(self, mock_os_client):
        c = VectorSearchClient(username="admin", password="secret")
        mock_os_client.info.assert_called_once()

    def test_env_credentials(self, mock_os_client, monkeypatch):
        monkeypatch.setenv("OPENSEARCH_USERNAME", "u")
        monkeypatch.setenv("OPENSEARCH_PASSWORD", "p")
        c = VectorSearchClient()
        mock_os_client.info.assert_called_once()

    def test_ssl_options(self, mock_os_client):
        c = VectorSearchClient(use_ssl=True, ca_certs="/path/ca.pem")
        mock_os_client.info.assert_called_once()


class TestCreateVectorIndex:
    def test_creates_index(self, client, mock_os_client):
        mock_os_client.indices.exists.return_value = False
        mock_os_client.indices.create.return_value = {"acknowledged": True}
        result = client.create_vector_index("test_idx", 384)
        assert result is True
        mock_os_client.indices.create.assert_called_once()

    def test_index_already_exists(self, client, mock_os_client):
        mock_os_client.indices.exists.return_value = True
        result = client.create_vector_index("test_idx", 384)
        assert result is False

    def test_additional_fields(self, client, mock_os_client):
        mock_os_client.indices.exists.return_value = False
        mock_os_client.indices.create.return_value = {"acknowledged": True}
        result = client.create_vector_index(
            "test_idx", 384, additional_fields={"name": {"type": "text"}}
        )
        assert result is True


class TestIndexDocument:
    def test_index_single(self, client, mock_os_client):
        mock_os_client.index.return_value = {"result": "created"}
        embedding = np.random.rand(384)
        result = client.index_document("idx", "doc-1", embedding, metadata={"name": "test"})
        assert result is True

    def test_index_updated(self, client, mock_os_client):
        mock_os_client.index.return_value = {"result": "updated"}
        result = client.index_document("idx", "doc-1", np.zeros(384))
        assert result is True


class TestBulkIndex:
    def test_bulk_index(self, client, mock_os_client):
        with patch("src.python.utils.vector_search.helpers") as mock_helpers:
            mock_helpers.bulk.return_value = (2, [])
            docs = [
                {"id": "1", "embedding": np.random.rand(384), "text": "a"},
                {"id": "2", "embedding": [0.1] * 384, "text": "b"},
            ]
            success, errors = client.bulk_index_documents("idx", docs)
            assert success == 2
            assert errors == []

    def test_skips_incomplete_docs(self, client, mock_os_client):
        with patch("src.python.utils.vector_search.helpers") as mock_helpers:
            mock_helpers.bulk.return_value = (0, [])
            docs = [{"id": "1"}]
            client.bulk_index_documents("idx", docs)
            args = mock_helpers.bulk.call_args
            assert args[0][1] == []


class TestSearch:
    def test_knn_search(self, client, mock_os_client):
        mock_os_client.search.return_value = {
            "hits": {
                "hits": [
                    {"_id": "1", "_score": 0.95, "_source": {"text": "match"}},
                    {"_id": "2", "_score": 0.80, "_source": {"text": "ok"}},
                ]
            }
        }
        results = client.search("idx", np.random.rand(384), k=2)
        assert len(results) == 2
        assert results[0]["score"] == 0.95

    def test_knn_search_with_min_score(self, client, mock_os_client):
        mock_os_client.search.return_value = {
            "hits": {
                "hits": [
                    {"_id": "1", "_score": 0.95, "_source": {}},
                    {"_id": "2", "_score": 0.50, "_source": {}},
                ]
            }
        }
        results = client.search("idx", np.random.rand(384), min_score=0.8)
        assert len(results) == 1

    def test_knn_search_with_filters(self, client, mock_os_client):
        mock_os_client.search.return_value = {"hits": {"hits": []}}
        client.search("idx", np.random.rand(384), filters={"term": {"type": "person"}})
        body = mock_os_client.search.call_args[1]["body"]
        assert "bool" in body["query"]


class TestDeleteIndex:
    def test_delete_existing(self, client, mock_os_client):
        mock_os_client.indices.exists.return_value = True
        assert client.delete_index("idx") is True

    def test_delete_nonexistent(self, client, mock_os_client):
        mock_os_client.indices.exists.return_value = False
        assert client.delete_index("idx") is False


class TestGetIndexStats:
    def test_stats(self, client, mock_os_client):
        mock_os_client.indices.stats.return_value = {"indices": {"idx": {"total": {}}}}
        stats = client.get_index_stats("idx")
        assert "total" in stats


class TestHelperFunctions:
    def test_create_person_name_index(self, client, mock_os_client):
        mock_os_client.indices.exists.return_value = False
        mock_os_client.indices.create.return_value = {"acknowledged": True}
        assert create_person_name_index(client) is True

    def test_create_transaction_description_index(self, client, mock_os_client):
        mock_os_client.indices.exists.return_value = False
        mock_os_client.indices.create.return_value = {"acknowledged": True}
        assert create_transaction_description_index(client) is True
