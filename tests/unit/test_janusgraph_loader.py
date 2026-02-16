"""Tests for banking.data_generators.loaders.janusgraph_loader module."""

import pytest
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from unittest.mock import MagicMock, patch

from banking.data_generators.loaders.janusgraph_loader import (
    _serialize_value,
    _validate_entity,
    JanusGraphLoader,
    REQUIRED_PERSON_FIELDS,
    REQUIRED_ACCOUNT_FIELDS,
)


class TestSerializeValue:
    def test_none(self):
        assert _serialize_value(None) is None

    def test_int(self):
        assert _serialize_value(42) == 42

    def test_float(self):
        assert _serialize_value(3.14) == 3.14

    def test_bool(self):
        assert _serialize_value(True) is True

    def test_decimal(self):
        assert _serialize_value(Decimal("9.99")) == 9.99

    def test_enum(self):
        class Color(Enum):
            RED = "red"
        assert _serialize_value(Color.RED) == "red"

    def test_datetime(self):
        dt = datetime(2026, 1, 15, 12, 0, 0)
        result = _serialize_value(dt)
        assert isinstance(result, int)

    def test_date(self):
        d = date(2026, 1, 15)
        result = _serialize_value(d)
        assert isinstance(result, int)

    def test_list(self):
        result = _serialize_value([1, 2, 3])
        assert '"1"' not in result
        assert "[1, 2, 3]" == result

    def test_dict(self):
        result = _serialize_value({"key": "val"})
        assert "key" in result

    def test_string(self):
        assert _serialize_value("hello") == "hello"


class TestValidateEntity:
    def test_valid_entity(self):
        entity = {"person_id": "p1", "first_name": "John", "last_name": "Doe",
                   "full_name": "John Doe", "nationality": "US", "risk_level": "low"}
        missing = _validate_entity(entity, REQUIRED_PERSON_FIELDS, "person")
        assert missing == []

    def test_missing_fields(self):
        entity = {"person_id": "p1"}
        missing = _validate_entity(entity, REQUIRED_PERSON_FIELDS, "person")
        assert len(missing) > 0

    def test_empty_string_field(self):
        entity = {"person_id": "", "first_name": "John", "last_name": "Doe",
                   "full_name": "John Doe", "nationality": "US", "risk_level": "low"}
        missing = _validate_entity(entity, REQUIRED_PERSON_FIELDS, "person")
        assert "person_id" in missing


class TestJanusGraphLoader:
    @pytest.fixture
    def loader(self):
        return JanusGraphLoader()

    @pytest.fixture
    def connected_loader(self):
        loader = JanusGraphLoader()
        loader.client = MagicMock()
        loader.client.submit.return_value.all.return_value.result.return_value = [0]
        return loader

    def test_init(self, loader):
        assert loader.url == "ws://localhost:18182/gremlin"
        assert loader.client is None
        assert loader.stats["vertices_created"] == 0

    def test_connect(self):
        with patch("banking.data_generators.loaders.janusgraph_loader.client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.submit.return_value.all.return_value.result.return_value = [100]
            mock_client.Client.return_value = mock_instance
            loader = JanusGraphLoader()
            loader.connect()
            assert loader.client is not None

    def test_close(self, connected_loader):
        connected_loader.close()
        connected_loader.client.close.assert_called_once()

    def test_close_no_client(self, loader):
        loader.close()

    def test_submit_with_bindings(self, connected_loader):
        connected_loader.client.submit.return_value.all.return_value.result.return_value = [1]
        result = connected_loader._submit("g.V().count()", {"x": 1})
        assert result == [1]

    def test_submit_without_bindings(self, connected_loader):
        connected_loader.client.submit.return_value.all.return_value.result.return_value = [1]
        result = connected_loader._submit("g.V().count()")
        assert result == [1]

    def test_submit_error(self, connected_loader):
        connected_loader.client.submit.side_effect = Exception("query error")
        with pytest.raises(Exception):
            connected_loader._submit("bad query")
        assert len(connected_loader.stats["errors"]) == 1

    def test_clear_graph(self, connected_loader):
        connected_loader.client.submit.return_value.all.return_value.result.return_value = []
        connected_loader.clear_graph()

    def test_create_vertex_existing(self, connected_loader):
        connected_loader.client.submit.return_value.all.return_value.result.return_value = [42]
        result = connected_loader._create_vertex("person", "person_id", "p1", {"name": "test"})
        assert result == 42

    def test_create_vertex_new(self, connected_loader):
        call_count = [0]
        def mock_submit(*args, **kwargs):
            call_count[0] += 1
            mock_result = MagicMock()
            if call_count[0] == 1:
                mock_result.all.return_value.result.return_value = []
            else:
                mock_result.all.return_value.result.return_value = [99]
            return mock_result
        connected_loader.client.submit.side_effect = mock_submit
        result = connected_loader._create_vertex("person", "person_id", "p1", {"name": "John", "age": 30})
        assert result == 99

    def test_create_vertex_no_result(self, connected_loader):
        call_count = [0]
        def mock_submit(*args, **kwargs):
            call_count[0] += 1
            mock_result = MagicMock()
            mock_result.all.return_value.result.return_value = []
            return mock_result
        connected_loader.client.submit.side_effect = mock_submit
        result = connected_loader._create_vertex("person", "person_id", "p1", {"name": "John"})
        assert result is None

    def test_load_persons(self, connected_loader):
        person = MagicMock()
        person.model_dump.return_value = {
            "person_id": "p1", "first_name": "John", "last_name": "Doe",
            "full_name": "John Doe", "nationality": "US", "risk_level": "low",
        }
        call_count = [0]
        def mock_submit(*args, **kwargs):
            call_count[0] += 1
            mock_result = MagicMock()
            if call_count[0] == 1:
                mock_result.all.return_value.result.return_value = []
            else:
                mock_result.all.return_value.result.return_value = [1]
            return mock_result
        connected_loader.client.submit.side_effect = mock_submit
        result = connected_loader.load_persons([person])
        assert "p1" in result

    def test_load_persons_no_id(self, connected_loader):
        person = MagicMock()
        person.model_dump.return_value = {"first_name": "John"}
        result = connected_loader.load_persons([person])
        assert len(result) == 0

    def test_load_companies(self, connected_loader):
        company = MagicMock()
        company.model_dump.return_value = {
            "company_id": "c1", "legal_name": "Corp", "registration_country": "US",
        }
        call_count = [0]
        def mock_submit(*args, **kwargs):
            call_count[0] += 1
            mock_result = MagicMock()
            if call_count[0] == 1:
                mock_result.all.return_value.result.return_value = []
            else:
                mock_result.all.return_value.result.return_value = [2]
            return mock_result
        connected_loader.client.submit.side_effect = mock_submit
        result = connected_loader.load_companies([company])
        assert "c1" in result

    def test_load_accounts_with_person_owner(self, connected_loader):
        account = MagicMock()
        account.model_dump.return_value = {
            "account_id": "a1", "account_type": "checking", "currency": "USD",
            "owner_id": "p1", "owner_type": "person",
        }
        call_count = [0]
        def mock_submit(*args, **kwargs):
            call_count[0] += 1
            mock_result = MagicMock()
            if call_count[0] == 1:
                mock_result.all.return_value.result.return_value = []
            else:
                mock_result.all.return_value.result.return_value = [3]
            return mock_result
        connected_loader.client.submit.side_effect = mock_submit
        result = connected_loader.load_accounts([account], {"p1": 1}, {})
        assert "a1" in result

    def test_load_accounts_with_company_owner(self, connected_loader):
        account = MagicMock()
        account.model_dump.return_value = {
            "account_id": "a1", "account_type": "business", "currency": "USD",
            "owner_id": "c1", "owner_type": "company",
        }
        call_count = [0]
        def mock_submit(*args, **kwargs):
            call_count[0] += 1
            mock_result = MagicMock()
            if call_count[0] == 1:
                mock_result.all.return_value.result.return_value = []
            else:
                mock_result.all.return_value.result.return_value = [4]
            return mock_result
        connected_loader.client.submit.side_effect = mock_submit
        result = connected_loader.load_accounts([account], {}, {"c1": 2})
        assert "a1" in result

    def test_load_transactions(self, connected_loader):
        tx = MagicMock()
        tx.model_dump.return_value = {
            "transaction_id": "t1", "amount": Decimal("100"), "currency": "USD",
            "from_account_id": "a1", "to_account_id": "a2",
        }
        call_count = [0]
        def mock_submit(*args, **kwargs):
            call_count[0] += 1
            mock_result = MagicMock()
            if call_count[0] == 1:
                mock_result.all.return_value.result.return_value = []
            else:
                mock_result.all.return_value.result.return_value = [5]
            return mock_result
        connected_loader.client.submit.side_effect = mock_submit
        result = connected_loader.load_transactions([tx], {"a1": 1, "a2": 2})
        assert "t1" in result

    def test_load_trades(self, connected_loader):
        trade = MagicMock()
        trade.model_dump.return_value = {
            "trade_id": "tr1", "symbol": "AAPL", "side": "buy",
            "quantity": 100, "price": Decimal("150"), "total_value": Decimal("15000"),
            "account_id": "a1", "trader_id": "p1",
        }
        call_count = [0]
        def mock_submit(*args, **kwargs):
            call_count[0] += 1
            mock_result = MagicMock()
            if call_count[0] == 1:
                mock_result.all.return_value.result.return_value = []
            elif call_count[0] == 2:
                mock_result.all.return_value.result.return_value = [6]
            else:
                mock_result.all.return_value.result.return_value = []
            return mock_result
        connected_loader.client.submit.side_effect = mock_submit
        result = connected_loader.load_trades([trade], {"a1": 1}, {"p1": 2})
        assert result == 1

    def test_load_trades_existing(self, connected_loader):
        trade = MagicMock()
        trade.model_dump.return_value = {"trade_id": "tr1"}
        connected_loader.client.submit.return_value.all.return_value.result.return_value = [42]
        result = connected_loader.load_trades([trade], {}, {})
        assert result == 0

    def test_load_communications(self, connected_loader):
        comm = MagicMock()
        comm.model_dump.return_value = {
            "from_person_id": "p1", "to_person_id": "p2",
            "communication_type": "email",
        }
        connected_loader.client.submit.return_value.all.return_value.result.return_value = []
        result = connected_loader.load_communications([comm], {"p1": 1, "p2": 2})
        assert result == 1

    def test_load_communications_recipient_ids(self, connected_loader):
        comm = MagicMock()
        comm.model_dump.return_value = {
            "from_person_id": "p1", "recipient_ids": ["p2"],
            "communication_type": "email",
        }
        connected_loader.client.submit.return_value.all.return_value.result.return_value = []
        result = connected_loader.load_communications([comm], {"p1": 1, "p2": 2})
        assert result == 1

    def test_load_communications_no_vertices(self, connected_loader):
        comm = MagicMock()
        comm.model_dump.return_value = {"from_person_id": "p1", "to_person_id": "p2"}
        result = connected_loader.load_communications([comm], {})
        assert result == 0

    def test_load_from_orchestrator(self):
        with patch("banking.data_generators.loaders.janusgraph_loader.client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.submit.return_value.all.return_value.result.return_value = [0]
            mock_client.Client.return_value = mock_instance

            loader = JanusGraphLoader()
            orch = MagicMock()
            orch.persons = []
            orch.companies = []
            orch.accounts = []
            orch.transactions = []
            orch.communications = []
            orch.trades = []

            stats = loader.load_from_orchestrator(orch, clear_first=True)
            assert stats["vertices_created"] == 0
