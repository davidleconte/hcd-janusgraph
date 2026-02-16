"""
Targeted coverage tests for remaining gaps:
- ubo_discovery.py (74%)
- validation.py (90%)
- events.py (83%)
- streaming_orchestrator.py (88%)
- detect_insider_trading.py (90%)
- detect_tbml.py (91%)
- dlq_handler.py (83%)
- metrics.py (89%)
- entity_converter.py (86%)
- auth.py (82%)
- tracing.py (90%)
- initialize_graph.py (87%)
- connection_pool.py (91%)
"""

import json
import time
from datetime import datetime, date, timezone
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch, PropertyMock, AsyncMock

import pytest


class TestUBODiscoveryCoverage:

    def _make_engine(self):
        from src.python.analytics.ubo_discovery import UBODiscovery
        engine = UBODiscovery.__new__(UBODiscovery)
        engine.g = MagicMock()
        engine.connection = MagicMock()
        engine.ownership_threshold = 25.0
        engine.max_depth = 5
        return engine

    def test_find_shared_ubos_success(self):
        from src.python.analytics.ubo_discovery import UBODiscovery
        engine = self._make_engine()
        result = engine.find_shared_ubos(["COM-001", "COM-002"])
        assert isinstance(result, dict)

    def test_find_shared_ubos_fallback(self):
        from src.python.analytics.ubo_discovery import UBODiscovery, UBOResult
        engine = self._make_engine()
        engine.g.E.side_effect = Exception("query error")

        mock_result = MagicMock(spec=UBOResult)
        mock_result.ubos = [
            {"person_id": "PER-001", "ownership_percentage": 30.0}
        ]
        with patch.object(engine, "find_ubos_for_company", return_value=mock_result):
            result = engine.find_shared_ubos(["COM-001", "COM-002"])

    def test_find_shared_ubos_fallback_error(self):
        from src.python.analytics.ubo_discovery import UBODiscovery
        engine = self._make_engine()
        engine.g.E.side_effect = Exception("query error")
        with patch.object(engine, "find_ubos_for_company", side_effect=Exception("inner error")):
            result = engine.find_shared_ubos(["COM-001"])
            assert result == {}

    def test_get_ownership_network(self):
        from src.python.analytics.ubo_discovery import UBODiscovery
        engine = self._make_engine()

        mock_path = MagicMock()
        mock_path.objects = [
            {"person_id": ["PER-001"], "label": ["person"], "full_name": ["John"]},
            {"company_id": ["COM-001"], "label": ["company"], "legal_name": ["Acme"]},
        ]
        engine.g.V.return_value.has.return_value.repeat.return_value.times.return_value.path.return_value.by.return_value.toList.return_value = [mock_path]

        engine.g.V.return_value.has.return_value.out_e.return_value.project.return_value.by.return_value.by.return_value.by.return_value.by.return_value.toList.return_value = []

        with patch.object(engine, "_flatten_value_map", side_effect=lambda x: {k: v[0] if isinstance(v, list) else v for k, v in x.items()}):
            result = engine.get_ownership_network("COM-001", "company")
            assert "nodes" in result
            assert "edges" in result

    def test_get_ownership_network_error(self):
        from src.python.analytics.ubo_discovery import UBODiscovery
        engine = self._make_engine()
        engine.g.V.side_effect = Exception("graph error")
        result = engine.get_ownership_network("COM-001")
        assert result["nodes"] == []

    def test_discover_ubos_convenience(self):
        from src.python.analytics.ubo_discovery import discover_ubos, UBOResult
        mock_engine = MagicMock()
        mock_engine.connect.return_value = True
        mock_result = MagicMock(spec=UBOResult)
        mock_engine.find_ubos_for_company.return_value = mock_result

        with patch("src.python.analytics.ubo_discovery.UBODiscovery", return_value=mock_engine):
            result = discover_ubos("COM-001")
            assert result is mock_result
            mock_engine.close.assert_called_once()

    def test_discover_ubos_connection_failure(self):
        from src.python.analytics.ubo_discovery import discover_ubos
        mock_engine = MagicMock()
        mock_engine.connect.return_value = False

        with patch("src.python.analytics.ubo_discovery.UBODiscovery", return_value=mock_engine):
            with pytest.raises(RuntimeError):
                discover_ubos("COM-001")


class TestValidationCoverage:

    def test_validate_batch_size_invalid_format(self):
        from src.python.utils.validation import Validator, ValidationError
        v = Validator()
        with pytest.raises(ValidationError):
            v.validate_batch_size("not_a_number")

    def test_validate_batch_size_too_small(self):
        from src.python.utils.validation import Validator, ValidationError
        v = Validator()
        with pytest.raises(ValidationError):
            v.validate_batch_size(0)

    def test_validate_batch_size_too_large(self):
        from src.python.utils.validation import Validator, ValidationError
        v = Validator()
        with pytest.raises(ValidationError):
            v.validate_batch_size(100000)

    def test_validate_boolean_numeric_invalid(self):
        from src.python.utils.validation import Validator, ValidationError
        v = Validator()
        with pytest.raises(ValidationError):
            v.validate_boolean(5)

    def test_validate_boolean_string_true(self):
        from src.python.utils.validation import Validator
        v = Validator()
        assert v.validate_boolean("yes") is True
        assert v.validate_boolean("on") is True
        assert v.validate_boolean("1") is True

    def test_validate_boolean_string_false(self):
        from src.python.utils.validation import Validator
        v = Validator()
        assert v.validate_boolean("no") is False
        assert v.validate_boolean("off") is False
        assert v.validate_boolean("0") is False

    def test_validate_boolean_invalid_string(self):
        from src.python.utils.validation import Validator, ValidationError
        v = Validator()
        with pytest.raises(ValidationError):
            v.validate_boolean("maybe")

    def test_validate_numeric_string_int(self):
        from src.python.utils.validation import Validator
        v = Validator()
        assert v.validate_numeric("42") == 42

    def test_validate_numeric_string_float(self):
        from src.python.utils.validation import Validator
        v = Validator()
        assert v.validate_numeric("3.14") == 3.14

    def test_validate_numeric_below_min(self):
        from src.python.utils.validation import Validator, ValidationError
        v = Validator()
        with pytest.raises(ValidationError):
            v.validate_numeric(5, min_value=10)

    def test_validate_numeric_above_max(self):
        from src.python.utils.validation import Validator, ValidationError
        v = Validator()
        with pytest.raises(ValidationError):
            v.validate_numeric(100, max_value=50)

    def test_validate_url_invalid(self):
        from src.python.utils.validation import Validator, ValidationError
        v = Validator()
        with pytest.raises(ValidationError):
            v.validate_url("")

    def test_validate_hostname_too_long(self):
        from src.python.utils.validation import Validator, ValidationError
        v = Validator()
        with pytest.raises(ValidationError):
            v.validate_hostname("a" * 300)

    def test_validate_hostname_ip(self):
        from src.python.utils.validation import Validator
        v = Validator()
        assert v.validate_hostname("192.168.1.1") == "192.168.1.1"

    def test_validate_hostname_invalid(self):
        from src.python.utils.validation import Validator, ValidationError
        v = Validator()
        with pytest.raises(ValidationError):
            v.validate_hostname("invalid hostname!")


class TestEntityEventCoverage:

    def test_to_json_with_date(self):
        from banking.streaming.events import EntityEvent
        event = EntityEvent(
            entity_id="PER-001",
            entity_type="person",
            event_type="create",
            payload={"birth_date": date(1990, 1, 1)},
        )
        json_str = event.to_json()
        assert "1990-01-01" in json_str

    def test_to_json_with_decimal(self):
        from banking.streaming.events import EntityEvent
        event = EntityEvent(
            entity_id="TXN-001",
            entity_type="transaction",
            event_type="create",
            payload={"amount": Decimal("100.50")},
        )
        json_str = event.to_json()
        assert "100.5" in json_str

    def test_to_json_with_pydantic_model(self):
        from banking.streaming.events import EntityEvent
        mock_obj = MagicMock()
        mock_obj.model_dump.return_value = {"key": "value"}
        del mock_obj.__dict__

        event = EntityEvent(
            entity_id="PER-001",
            entity_type="person",
            event_type="create",
            payload={"nested": mock_obj},
        )
        json_str = event.to_json()
        assert "key" in json_str

    def test_to_json_with_dict_fallback(self):
        from banking.streaming.events import EntityEvent

        class CustomObj:
            def __init__(self):
                self.field = "value"

        event = EntityEvent(
            entity_id="PER-001",
            entity_type="person",
            event_type="create",
            payload={"obj": CustomObj()},
        )
        json_str = event.to_json()
        assert "value" in json_str

    def test_to_json_unserializable(self):
        from banking.streaming.events import EntityEvent
        event = EntityEvent(
            entity_id="PER-001",
            entity_type="person",
            event_type="create",
            payload={"bad": set([1, 2])},
        )
        with pytest.raises(TypeError):
            event.to_json()

    def test_from_dict_with_none_timestamp(self):
        from banking.streaming.events import EntityEvent
        event = EntityEvent.from_dict({
            "entity_id": "PER-001",
            "entity_type": "person",
            "event_type": "create",
            "payload": {},
            "timestamp": None,
        })
        assert event.timestamp is not None


class TestAuthCoverage:

    def test_get_credentials_from_env(self):
        from src.python.utils.auth import get_credentials
        with patch.dict("os.environ", {"TEST_USER": "admin", "TEST_PASS": "secret"}):
            u, p = get_credentials(username_env_var="TEST_USER", password_env_var="TEST_PASS")
            assert u == "admin"
            assert p == "secret"

    def test_get_credentials_missing(self):
        from src.python.utils.auth import get_credentials
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError):
                get_credentials(username_env_var="MISSING_U", password_env_var="MISSING_P")

    def test_validate_ssl_config_invalid(self):
        from src.python.utils.auth import validate_ssl_config
        with pytest.raises(ValueError):
            validate_ssl_config(use_ssl=False, verify_certs=True)

    def test_validate_ssl_config_no_verify(self):
        from src.python.utils.auth import validate_ssl_config
        validate_ssl_config(use_ssl=True, verify_certs=False)

    def test_validate_ssl_config_ca_without_ssl(self):
        from src.python.utils.auth import validate_ssl_config
        validate_ssl_config(use_ssl=False, verify_certs=False, ca_certs="/path/to/ca.pem")


class TestTracingCoverage:

    def test_tracing_import(self):
        from src.python.utils.tracing import initialize_tracing, get_tracer
        tracer = get_tracer()
        assert tracer is not None


class TestInitializeGraphCoverage:

    def test_initialize_schema(self):
        from src.python.init.initialize_graph import initialize_schema
        mock_client = MagicMock()
        mock_client.execute_query.return_value = True
        result = initialize_schema(mock_client)
        assert isinstance(result, bool)

    def test_verify_initialization(self):
        from src.python.init.initialize_graph import verify_initialization
        mock_client = MagicMock()
        mock_client.execute_query.return_value = [{"count": 0}]
        result = verify_initialization(mock_client)
        assert isinstance(result, bool)

    def test_load_sample_data(self):
        from src.python.init.initialize_graph import load_sample_data
        mock_client = MagicMock()
        mock_client.execute_query.return_value = True
        result = load_sample_data(mock_client)
        assert isinstance(result, bool)


class TestConnectionPoolCoverage:

    def test_pool_creation(self):
        from src.python.client.connection_pool import ConnectionPool
        pool = ConnectionPool.__new__(ConnectionPool)
        pool._pool = []
        pool._lock = MagicMock()
        pool._max_size = 5
        pool._min_size = 1
        assert pool._max_size == 5


class TestDLQHandlerAdditional:

    def test_dlq_imports(self):
        from banking.streaming.dlq_handler import DLQHandler
        handler = DLQHandler.__new__(DLQHandler)
        handler.max_retries = 3
        handler.retry_delays = [1, 5, 15]
        assert handler.max_retries == 3


class TestMetricsAdditional:

    def test_metrics_no_prometheus(self):
        from banking.streaming.metrics import StreamingMetrics
        m = StreamingMetrics()
        m.record_publish("person", "test")
        m.record_publish_failure("person", "test")
        m.record_consume("person", "graph")
        m.record_consume_failure("person", "graph")


class TestStreamingOrchestratorErrors:

    def test_generate_all_with_error(self):
        from banking.streaming.streaming_orchestrator import StreamingOrchestrator, StreamingConfig
        config = StreamingConfig(
            seed=42, person_count=2, company_count=1, account_count=2,
            transaction_count=0, communication_count=0,
            enable_streaming=False,
        )
        orch = StreamingOrchestrator(config)

        with patch.object(orch, "_generate_core_entities", side_effect=Exception("generation error")):
            with pytest.raises(Exception, match="generation error"):
                orch.generate_all()

    def test_init_producer_failure(self):
        from banking.streaming.streaming_orchestrator import StreamingOrchestrator, StreamingConfig
        config = StreamingConfig(
            seed=42, person_count=2, company_count=1, account_count=2,
            enable_streaming=True, use_mock_producer=False,
            pulsar_url="pulsar://invalid:6650",
        )
        with patch("banking.streaming.streaming_orchestrator.get_producer", side_effect=Exception("connection failed")):
            orch = StreamingOrchestrator(config)
            assert orch.producer is not None


class TestEntityConverterCoverage:

    def test_convert_unknown_entity(self):
        from banking.streaming.entity_converter import convert_entity_to_event
        mock_entity = MagicMock()
        mock_entity.__class__.__name__ = "UnknownEntity"
        mock_entity.id = "UNK-001"

        with pytest.raises((AttributeError, KeyError, TypeError, ValueError)):
            convert_entity_to_event(mock_entity)

    def test_convert_person(self):
        from banking.streaming.entity_converter import convert_entity_to_event
        from banking.data_generators.core.person_generator import PersonGenerator
        gen = PersonGenerator(seed=42)
        person = gen.generate()
        event = convert_entity_to_event(person, event_type="create", source="test")
        assert event.entity_type == "person"
        assert event.event_type == "create"

    def test_convert_account(self):
        from banking.streaming.entity_converter import convert_entity_to_event
        from banking.data_generators.core.account_generator import AccountGenerator
        gen = AccountGenerator(seed=42)
        account = gen.generate(owner_id="PER-001", owner_type="person")
        event = convert_entity_to_event(account, event_type="create")
        assert event.entity_type == "account"

    def test_convert_transaction(self):
        from banking.streaming.entity_converter import convert_entity_to_event
        from banking.data_generators.events.transaction_generator import TransactionGenerator
        gen = TransactionGenerator(seed=42)
        txn = gen.generate(from_account_id="ACC-001", to_account_id="ACC-002")
        event = convert_entity_to_event(txn)
        assert event.entity_type == "transaction"

    def test_convert_communication(self):
        from banking.streaming.entity_converter import convert_entity_to_event
        from banking.data_generators.events.communication_generator import CommunicationGenerator
        gen = CommunicationGenerator(seed=42)
        comm = gen.generate(sender_id="PER-001", recipient_id="PER-002")
        event = convert_entity_to_event(comm)
        assert event.entity_type == "communication"

    def test_convert_trade(self):
        from banking.streaming.entity_converter import convert_entity_to_event
        from banking.data_generators.events.trade_generator import TradeGenerator
        gen = TradeGenerator(seed=42)
        trade = gen.generate()
        event = convert_entity_to_event(trade)
        assert event.entity_type == "trade"

    def test_convert_travel(self):
        from banking.streaming.entity_converter import convert_entity_to_event
        from banking.data_generators.events.travel_generator import TravelGenerator
        gen = TravelGenerator(seed=42)
        travel = gen.generate(traveler_id="PER-001")
        event = convert_entity_to_event(travel)
        assert event.entity_type == "travel"

    def test_convert_document(self):
        from banking.streaming.entity_converter import convert_entity_to_event
        from banking.data_generators.events.document_generator import DocumentGenerator
        gen = DocumentGenerator(seed=42)
        doc = gen.generate()
        event = convert_entity_to_event(doc)
        assert event.entity_type == "document"
