"""Comprehensive tests for src.python.analytics.ubo_discovery — targets 60% → 85%+."""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from dataclasses import dataclass

from src.python.analytics.ubo_discovery import (
    OwnershipType,
    OwnershipLink,
    UBOResult,
    UBODiscovery,
)


class TestOwnershipType:
    def test_values(self):
        assert OwnershipType.DIRECT == "direct"
        assert OwnershipType.INDIRECT == "indirect"
        assert OwnershipType.NOMINEE == "nominee"
        assert OwnershipType.TRUST == "trust"
        assert OwnershipType.BEARER == "bearer"


class TestOwnershipLink:
    def test_fields(self):
        link = OwnershipLink(
            entity_id="p-1", entity_type="person", entity_name="Alice",
            ownership_percentage=30.0, ownership_type=OwnershipType.DIRECT,
            jurisdiction="US", is_pep=True, is_sanctioned=False,
        )
        assert link.entity_id == "p-1"
        assert link.is_pep is True
        assert link.jurisdiction == "US"

    def test_defaults(self):
        link = OwnershipLink(
            entity_id="c-1", entity_type="company", entity_name="Corp",
            ownership_percentage=100.0, ownership_type=OwnershipType.INDIRECT,
        )
        assert link.jurisdiction is None
        assert link.is_pep is False
        assert link.is_sanctioned is False


class TestUBODiscovery:
    def setup_method(self):
        self.engine = UBODiscovery(host="localhost", port=18182, ownership_threshold=25.0)

    def test_init(self):
        assert self.engine.host == "localhost"
        assert self.engine.port == 18182
        assert self.engine.ownership_threshold == 25.0
        assert self.engine.g is None

    def test_connect_success(self):
        with patch("src.python.analytics.ubo_discovery.DriverRemoteConnection") as mock_conn:
            with patch("src.python.analytics.ubo_discovery.traversal") as mock_trav:
                mock_trav.return_value.with_remote.return_value = MagicMock()
                assert self.engine.connect() is True
                assert self.engine.g is not None

    def test_connect_failure(self):
        with patch("src.python.analytics.ubo_discovery.DriverRemoteConnection", side_effect=Exception("fail")):
            assert self.engine.connect() is False

    def test_close(self):
        mock_conn = MagicMock()
        self.engine.connection = mock_conn
        self.engine.close()
        mock_conn.close.assert_called_once()

    def test_close_no_connection(self):
        self.engine.close()

    def test_find_ubos_not_connected(self):
        with pytest.raises(RuntimeError, match="Not connected"):
            self.engine.find_ubos_for_company("COMP-1")

    def test_find_ubos_company_not_found(self):
        self.engine.g = MagicMock()
        self.engine.g.V.return_value.has.return_value.value_map.return_value.toList.return_value = []
        with pytest.raises(ValueError, match="Company not found"):
            self.engine.find_ubos_for_company("COMP-MISSING")

    def test_find_ubos_direct_owners(self):
        mock_g = MagicMock()
        self.engine.g = mock_g

        mock_g.V.return_value.has.return_value.value_map.return_value.toList.return_value = [
            {"legal_name": ["Acme Corp"]}
        ]
        mock_g.V.return_value.has.return_value.value_map.return_value.toList.return_value = [
            {"legal_name": ["Acme Corp"]}
        ]

        chain = mock_g.V.return_value.has.return_value.in_e.return_value
        chain.project.return_value.by.return_value.by.return_value.by.return_value \
            .by.return_value.by.return_value.by.return_value.by.return_value \
            .toList.return_value = [
            {
                "person_id": "p-1",
                "first_name": "Alice",
                "last_name": "Smith",
                "full_name": "Alice Smith",
                "ownership_percentage": 30.0,
                "is_pep": False,
                "is_sanctioned": False,
            }
        ]

        mock_g.V.return_value.has.return_value.repeat.return_value \
            .until.return_value.has_label.return_value.path.return_value \
            .by.return_value.toList.return_value = []

        result = self.engine.find_ubos_for_company("COMP-1", include_indirect=False)
        assert isinstance(result, UBOResult)
        assert len(result.ubos) == 1
        assert result.ubos[0]["name"] == "Alice Smith"

    def test_calculate_effective_ownership(self):
        chain = [
            OwnershipLink("p-1", "person", "Alice", 60.0, OwnershipType.INDIRECT),
            OwnershipLink("c-1", "company", "Holding", 80.0, OwnershipType.INDIRECT),
        ]
        eff = self.engine._calculate_effective_ownership(chain)
        assert abs(eff - 48.0) < 0.01

    def test_calculate_effective_ownership_empty(self):
        assert self.engine._calculate_effective_ownership([]) == 0.0

    def test_calculate_risk_score_no_ubos(self):
        score = self.engine._calculate_risk_score([], [], [])
        assert score == 20.0

    def test_calculate_risk_score_with_indicators(self):
        ubos = [{"is_pep": True, "is_sanctioned": True}]
        chains = [[
            OwnershipLink("p-1", "person", "A", 100.0, OwnershipType.DIRECT),
            OwnershipLink("c-1", "company", "B", 100.0, OwnershipType.INDIRECT),
            OwnershipLink("c-2", "company", "C", 100.0, OwnershipType.INDIRECT),
        ]]
        indicators = ["risk1", "risk2", "risk3"]
        score = self.engine._calculate_risk_score(ubos, chains, indicators)
        assert score > 0

    def test_flatten_value_map(self):
        from gremlin_python.process.traversal import T
        vm = {T.id: 123, T.label: "person", "name": ["Alice"], "age": [30]}
        flat = self.engine._flatten_value_map(vm)
        assert flat["id"] == 123
        assert flat["label"] == "person"
        assert flat["name"] == "Alice"
        assert flat["age"] == 30

    def test_convert_path_to_chain_person(self):
        path = [{"person_id": "p-1", "full_name": "Alice", "ownership_percentage": 50.0}]
        chain = self.engine._convert_path_to_chain(path)
        assert len(chain) == 1
        assert chain[0].entity_type == "person"

    def test_convert_path_to_chain_company(self):
        path = [{"company_id": "c-1", "legal_name": "Corp", "registration_country": "VG"}]
        chain = self.engine._convert_path_to_chain(path)
        assert len(chain) == 1
        assert chain[0].entity_type == "company"
        assert chain[0].jurisdiction == "VG"

    def test_convert_path_to_chain_with_path_objects(self):
        mock_path = MagicMock()
        mock_path.objects = [{"person_id": "p-1", "full_name": "Bob"}]
        chain = self.engine._convert_path_to_chain(mock_path)
        assert len(chain) == 1

    def test_get_company_info_error(self):
        mock_g = MagicMock()
        mock_g.V.return_value.has.return_value.value_map.return_value.toList.side_effect = Exception("err")
        self.engine.g = mock_g
        assert self.engine._get_company_info("X") is None

    def test_find_direct_owners_error(self):
        mock_g = MagicMock()
        mock_g.V.return_value.has.return_value.inE.side_effect = Exception("err")
        self.engine.g = mock_g
        assert self.engine._find_direct_owners("X") == []

    def test_find_indirect_owners_error(self):
        mock_g = MagicMock()
        mock_g.V.return_value.has.return_value.repeat.side_effect = Exception("err")
        self.engine.g = mock_g
        assert self.engine._find_indirect_owners("X", 5) == []

    def test_find_shared_ubos_empty(self):
        mock_g = MagicMock()
        mock_g.V.return_value.has.return_value.inE.return_value \
            .where.return_value.project.return_value \
            .by.return_value.by.return_value.toList.return_value = []
        self.engine.g = mock_g
        result = self.engine.find_shared_ubos(["C1", "C2"])
        assert result == {}

    def test_get_ownership_network_error(self):
        mock_g = MagicMock()
        mock_g.V.return_value.has.return_value.repeat.side_effect = Exception("err")
        self.engine.g = mock_g
        result = self.engine.get_ownership_network("C1")
        assert result["nodes"] == []
        assert result["edges"] == []
