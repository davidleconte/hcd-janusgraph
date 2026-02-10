"""Tests for JanusGraphLoader."""

from unittest.mock import MagicMock, patch

import pytest

from banking.data_generators.loaders.janusgraph_loader import JanusGraphLoader


@pytest.fixture()
def mock_gremlin_client():
    with patch("banking.data_generators.loaders.janusgraph_loader.client.Client") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        mock_instance.submit.return_value.all.return_value.result.return_value = [0]
        yield mock_instance


@pytest.fixture()
def loader(mock_gremlin_client):
    loader = JanusGraphLoader(url="ws://localhost:18182/gremlin")
    loader.connect()
    return loader


class TestLoaderInit:
    def test_default_url(self):
        loader = JanusGraphLoader()
        assert loader.url == "ws://localhost:18182/gremlin"
        assert loader.traversal_source == "g"

    def test_custom_url(self):
        loader = JanusGraphLoader(url="ws://custom:9999/gremlin", traversal_source="g2")
        assert loader.url == "ws://custom:9999/gremlin"
        assert loader.traversal_source == "g2"

    def test_initial_stats(self):
        loader = JanusGraphLoader()
        assert loader.stats["vertices_created"] == 0
        assert loader.stats["edges_created"] == 0
        assert loader.stats["errors"] == []


class TestConnect:
    def test_connect_success(self, mock_gremlin_client):
        loader = JanusGraphLoader()
        loader.connect()
        assert loader.client is not None

    @patch("banking.data_generators.loaders.janusgraph_loader.client.Client")
    def test_connect_failure(self, mock_cls):
        mock_cls.side_effect = Exception("connection refused")
        loader = JanusGraphLoader()
        with pytest.raises(Exception, match="connection refused"):
            loader.connect()


class TestClose:
    def test_close_with_client(self, loader, mock_gremlin_client):
        loader.close()
        mock_gremlin_client.close.assert_called_once()

    def test_close_without_client(self):
        loader = JanusGraphLoader()
        loader.close()


class TestSubmit:
    def test_submit_success(self, loader, mock_gremlin_client):
        mock_gremlin_client.submit.return_value.all.return_value.result.return_value = [42]
        result = loader._submit("g.V().count()")
        assert result == [42]

    def test_submit_with_bindings(self, loader, mock_gremlin_client):
        mock_gremlin_client.submit.return_value.all.return_value.result.return_value = [1]
        result = loader._submit("g.V().has('name', n)", {"n": "Alice"})
        assert result == [1]
        mock_gremlin_client.submit.assert_called_with("g.V().has('name', n)", {"n": "Alice"})

    def test_submit_error_tracks_stats(self, loader, mock_gremlin_client):
        mock_gremlin_client.submit.side_effect = Exception("query failed")
        with pytest.raises(Exception):
            loader._submit("bad query")
        assert len(loader.stats["errors"]) == 1


class TestClearGraph:
    def test_clear_graph(self, loader):
        loader._submit = MagicMock(return_value=[])
        loader.clear_graph()
        loader._submit.assert_called_with("g.V().drop().iterate()")


class TestLoadPersons:
    def _make_person(self, person_id="P-1"):
        p = MagicMock()
        p.model_dump.return_value = {
            "person_id": person_id,
            "first_name": "Alice",
            "last_name": "Smith",
            "date_of_birth": "1990-01-01",
            "nationality": "US",
            "risk_score": 0.5,
        }
        return p

    def test_load_new_person(self, loader):
        loader._submit = MagicMock(side_effect=[[], [100]])
        person_map = loader.load_persons([self._make_person()])
        assert "P-1" in person_map
        assert loader.stats["vertices_created"] == 1

    def test_skip_existing_person(self, loader):
        loader._submit = MagicMock(side_effect=[[99]])
        person_map = loader.load_persons([self._make_person()])
        assert person_map["P-1"] == 99
        assert loader.stats["vertices_created"] == 0


class TestLoadCompanies:
    def _make_company(self, company_id="C-1"):
        c = MagicMock()
        c.model_dump.return_value = {
            "company_id": company_id,
            "name": "Acme Corp",
            "industry": "Finance",
            "country": "US",
            "risk_score": 0.2,
        }
        return c

    def test_load_new_company(self, loader):
        loader._submit = MagicMock(side_effect=[[], [200]])
        company_map = loader.load_companies([self._make_company()])
        assert "C-1" in company_map
        assert loader.stats["vertices_created"] == 1

    def test_skip_existing_company(self, loader):
        loader._submit = MagicMock(side_effect=[[199]])
        company_map = loader.load_companies([self._make_company()])
        assert company_map["C-1"] == 199


class TestLoadAccounts:
    def _make_account(self, account_id="A-1", owner_id="P-1", owner_type="person"):
        a = MagicMock()
        a.model_dump.return_value = {
            "account_id": account_id,
            "account_type": "checking",
            "currency": "USD",
            "balance": 1000.0,
            "status": "active",
            "opened_date": "2024-01-01",
            "owner_id": owner_id,
            "owner_type": owner_type,
        }
        return a

    def test_load_account_with_person_owner(self, loader):
        loader._submit = MagicMock(side_effect=[[], [300], []])
        acc_map = loader.load_accounts(
            [self._make_account()], person_id_map={"P-1": 100}, company_id_map={}
        )
        assert "A-1" in acc_map
        assert loader.stats["vertices_created"] == 1
        assert loader.stats["edges_created"] == 1

    def test_load_account_with_company_owner(self, loader):
        loader._submit = MagicMock(side_effect=[[], [301], []])
        acc_map = loader.load_accounts(
            [self._make_account(owner_id="C-1", owner_type="company")],
            person_id_map={},
            company_id_map={"C-1": 200},
        )
        assert "A-1" in acc_map
        assert loader.stats["edges_created"] == 1


class TestLoadTransactions:
    def _make_tx(self, tx_id="TX-1"):
        t = MagicMock()
        t.model_dump.return_value = {
            "transaction_id": tx_id,
            "amount": 500.0,
            "currency": "USD",
            "transaction_type": "transfer",
            "timestamp": "2024-06-01T12:00:00",
            "status": "completed",
            "is_suspicious": False,
            "from_account_id": "A-1",
            "to_account_id": "A-2",
        }
        return t

    def test_load_transaction_with_edges(self, loader):
        loader._submit = MagicMock(side_effect=[[], [400], [], []])
        tx_map = loader.load_transactions(
            [self._make_tx()], account_id_map={"A-1": 300, "A-2": 301}
        )
        assert "TX-1" in tx_map
        assert loader.stats["vertices_created"] == 1
        assert loader.stats["edges_created"] == 2


class TestLoadCommunications:
    def _make_comm(self):
        c = MagicMock()
        c.model_dump.return_value = {
            "from_person_id": "P-1",
            "to_person_id": "P-2",
            "communication_type": "email",
            "timestamp": "2024-06-01",
            "is_suspicious": False,
        }
        return c

    def test_load_communication_edge(self, loader):
        loader._submit = MagicMock(return_value=[])
        count = loader.load_communications(
            [self._make_comm()], person_id_map={"P-1": 100, "P-2": 101}
        )
        assert count == 1
        assert loader.stats["edges_created"] == 1

    def test_skip_when_person_not_in_map(self, loader):
        count = loader.load_communications(
            [self._make_comm()], person_id_map={"P-1": 100}
        )
        assert count == 0
