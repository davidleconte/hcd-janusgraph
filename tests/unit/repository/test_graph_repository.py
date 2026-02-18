"""Tests for GraphRepository."""

from unittest.mock import MagicMock

import pytest
from gremlin_python.process.traversal import T

from src.python.repository.graph_repository import GraphRepository, _flatten_value_map


@pytest.fixture()
def mock_g():
    g = MagicMock()
    g.V.return_value = g
    g.E.return_value = g
    g.hasLabel.return_value = g
    g.has_label.return_value = g
    g.has.return_value = g
    g.count.return_value = g
    g.limit.return_value = g
    g.next.return_value = 42
    g.hasNext.return_value = True
    g.toList.return_value = []
    g.where.return_value = g
    g.project.return_value = g
    g.by.return_value = g
    g.values.return_value = g
    g.inE.return_value = g
    g.in_e.return_value = g
    g.outE.return_value = g
    g.out_e.return_value = g
    g.outV.return_value = g
    g.out_v.return_value = g
    g.inV.return_value = g
    g.in_v.return_value = g
    g.in_.return_value = g
    g.coalesce.return_value = g
    g.constant.return_value = g
    g.fold.return_value = g
    g.sum.return_value = g
    g.valueMap.return_value = g
    g.value_map.return_value = g
    return g


@pytest.fixture()
def repo(mock_g):
    return GraphRepository(mock_g)


class TestFlattenValueMap:
    def test_flattens_single_element_lists(self):
        assert _flatten_value_map({"name": ["Alice"], "age": [30]}) == {"name": "Alice", "age": 30}

    def test_preserves_multi_element_lists(self):
        assert _flatten_value_map({"tags": ["a", "b"]}) == {"tags": ["a", "b"]}

    def test_handles_t_id_and_label(self):
        result = _flatten_value_map({T.id: 123, T.label: "person", "name": ["Bob"]})
        assert result == {"id": 123, "label": "person", "name": "Bob"}

    def test_empty_dict(self):
        assert _flatten_value_map({}) == {}

    def test_scalar_values_pass_through(self):
        assert _flatten_value_map({"count": 5}) == {"count": 5}


class TestHealthAndStats:
    def test_vertex_count(self, repo, mock_g):
        mock_g.next.return_value = 100
        assert repo.vertex_count() == 100

    def test_edge_count(self, repo, mock_g):
        mock_g.next.return_value = 200
        assert repo.edge_count() == 200

    def test_vertex_count_by_label(self, repo, mock_g):
        mock_g.next.return_value = 50
        assert repo.vertex_count_by_label("person") == 50

    def test_graph_stats_keys(self, repo, mock_g):
        mock_g.next.return_value = 10
        stats = repo.graph_stats()
        assert set(stats.keys()) == {
            "vertex_count",
            "edge_count",
            "person_count",
            "company_count",
            "account_count",
            "transaction_count",
        }

    def test_health_check_success(self, repo):
        assert repo.health_check() is True

    def test_health_check_failure(self, repo, mock_g):
        mock_g.next.side_effect = Exception("connection lost")
        assert repo.health_check() is False


class TestFraudDetection:
    def test_find_shared_addresses_empty(self, repo, mock_g):
        mock_g.toList.return_value = []
        assert repo.find_shared_addresses(min_members=3) == []

    def test_find_shared_addresses_formats_results(self, repo, mock_g):
        mock_g.toList.return_value = [
            {"address_id": "ADDR-1", "city": "New York", "persons": ["P1", "P2", "P3"]}
        ]
        result = repo.find_shared_addresses(min_members=3)
        assert len(result) == 1
        assert result[0]["type"] == "shared_address"
        assert result[0]["member_count"] == 3

    def test_find_shared_addresses_with_accounts(self, repo, mock_g):
        mock_g.toList.return_value = [
            {
                "address_id": "ADDR-2",
                "city": "Zurich",
                "members": [
                    {"person_id": "P1", "account_ids": ["ACC-1", "ACC-2"]},
                    {"person_id": "P2", "account_ids": ["ACC-3"]},
                ],
            }
        ]
        result = repo.find_shared_addresses_with_accounts(min_members=2, include_accounts=True)
        assert len(result) == 1
        assert result[0]["members"][0]["person_id"] == "P1"
        assert result[0]["member_accounts"][0] == ["ACC-1", "ACC-2"]
        assert result[0]["member_count"] == 2


class TestAMLStructuring:
    @pytest.fixture(autouse=True)
    def _patch_anon(self, monkeypatch):
        """Patch anonymous traversal __ so .outE/.inV etc. return chainable mocks."""
        mock_anon = MagicMock()
        mock_anon.return_value = mock_anon
        for attr in (
            "outE",
            "inV",
            "in_",
            "outV",
            "values",
            "coalesce",
            "constant",
            "count",
            "sum",
            "fold",
            "is_",
        ):
            setattr(mock_anon, attr, MagicMock(return_value=mock_anon))
        monkeypatch.setattr("src.python.repository.graph_repository.__", mock_anon)

    def test_get_account_transaction_summaries(self, repo, mock_g):
        mock_g.toList.return_value = [
            {"account_id": "ACC-1", "holder": "Alice", "txn_count": 15, "total": 140000}
        ]
        result = repo.get_account_transaction_summaries()
        assert len(result) == 1
        assert result[0]["account_id"] == "ACC-1"

    def test_get_account_transaction_summaries_filtered(self, repo, mock_g):
        mock_g.toList.return_value = []
        result = repo.get_account_transaction_summaries(account_id="ACC-001")
        assert len(result) == 0
        mock_g.has.assert_called_with("account_id", "ACC-001")


class TestUBODiscovery:
    def test_get_company_found(self, repo, mock_g):
        mock_g.toList.return_value = [
            {T.id: 1, T.label: "company", "company_id": ["COMP-1"], "legal_name": ["Acme Corp"]}
        ]
        result = repo.get_company("COMP-1")
        assert result is not None
        assert result["legal_name"] == "Acme Corp"

    def test_get_company_not_found(self, repo, mock_g):
        mock_g.toList.return_value = []
        assert repo.get_company("COMP-MISSING") is None

    def test_company_exists(self, repo, mock_g):
        mock_g.hasNext.return_value = True
        assert repo.company_exists("COMP-1") is True

    def test_company_not_exists(self, repo, mock_g):
        mock_g.hasNext.return_value = False
        assert repo.company_exists("COMP-MISSING") is False

    def test_find_direct_owners(self, repo, mock_g):
        mock_g.toList.return_value = [
            {"person_id": "P-1", "name": "Alice", "ownership_percentage": 60.0}
        ]
        result = repo.find_direct_owners("COMP-1")
        assert len(result) == 1
        assert result[0]["person_id"] == "P-1"

    def test_find_ubo_owners_direct_only(self, repo, mock_g):
        mock_g.toList.return_value = [
            {"person_id": "P-1", "name": "Alice", "ownership_percentage": 60.0}
        ]
        result, layers = repo.find_ubo_owners("COMP-1", include_indirect=False)
        assert layers == 1
        assert len(result) == 1
        assert result[0]["ownership_type"] == "direct"

    def test_get_owner_vertices(self, repo, mock_g):
        mock_g.toList.return_value = [
            {T.id: 10, T.label: "person", "person_id": ["P-1"], "full_name": ["Alice"]}
        ]
        result = repo.get_owner_vertices("COMP-1")
        assert len(result) == 1
        assert result[0]["full_name"] == "Alice"


class TestGenericHelpers:
    def test_get_vertex_found(self, repo, mock_g):
        mock_g.toList.return_value = [
            {T.id: 5, T.label: "person", "person_id": ["P-1"], "full_name": ["Bob"]}
        ]
        result = repo.get_vertex("person_id", "P-1")
        assert result is not None
        assert result["full_name"] == "Bob"

    def test_get_vertex_not_found(self, repo, mock_g):
        mock_g.toList.return_value = []
        assert repo.get_vertex("person_id", "P-MISSING") is None

    def test_vertex_exists(self, repo, mock_g):
        mock_g.hasNext.return_value = True
        assert repo.vertex_exists("person_id", "P-1") is True

    def test_static_flatten(self):
        assert GraphRepository.flatten_value_map({"x": [1]}) == {"x": 1}

    def test_g_property(self, repo, mock_g):
        assert repo.g is mock_g
