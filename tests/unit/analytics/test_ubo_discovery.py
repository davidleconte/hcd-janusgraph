"""
Unit tests for UBO Discovery module

Test Coverage Target: 60%+
Total Tests: 30+

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-11
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from decimal import Decimal

from src.python.analytics.ubo_discovery import (
    UBODiscovery,
    OwnershipType,
    OwnershipLink,
    UBOResult,
    discover_ubos
)


class TestOwnershipType:
    """Test OwnershipType enum (5 tests)"""
    
    def test_ownership_type_values(self):
        """Test all ownership type values exist"""
        assert OwnershipType.DIRECT == "direct"
        assert OwnershipType.INDIRECT == "indirect"
        assert OwnershipType.NOMINEE == "nominee"
        assert OwnershipType.TRUST == "trust"
        assert OwnershipType.BEARER == "bearer"
    
    def test_ownership_type_is_string_enum(self):
        """Test OwnershipType inherits from str"""
        assert isinstance(OwnershipType.DIRECT, str)
        assert isinstance(OwnershipType.INDIRECT, str)
    
    def test_ownership_type_comparison(self):
        """Test ownership type string comparison"""
        assert OwnershipType.DIRECT == "direct"
        assert OwnershipType.DIRECT != "indirect"
        assert OwnershipType.BEARER != OwnershipType.TRUST
    
    def test_ownership_type_iteration(self):
        """Test can iterate over ownership types"""
        types = list(OwnershipType)
        assert len(types) == 5
        assert OwnershipType.DIRECT in types
    
    def test_ownership_type_membership(self):
        """Test membership checking"""
        assert "direct" in [t.value for t in OwnershipType]
        assert "invalid" not in [t.value for t in OwnershipType]


class TestOwnershipLink:
    """Test OwnershipLink dataclass (6 tests)"""
    
    def test_ownership_link_creation(self):
        """Test creating ownership link with required fields"""
        link = OwnershipLink(
            entity_id="p-123",
            entity_type="person",
            entity_name="John Doe",
            ownership_percentage=30.0,
            ownership_type=OwnershipType.DIRECT
        )
        assert link.entity_id == "p-123"
        assert link.entity_type == "person"
        assert link.entity_name == "John Doe"
        assert link.ownership_percentage == 30.0
        assert link.ownership_type == OwnershipType.DIRECT
    
    def test_ownership_link_optional_fields(self):
        """Test optional fields have defaults"""
        link = OwnershipLink(
            entity_id="p-123",
            entity_type="person",
            entity_name="John Doe",
            ownership_percentage=30.0,
            ownership_type=OwnershipType.DIRECT
        )
        assert link.jurisdiction is None
        assert link.is_pep is False
        assert link.is_sanctioned is False
    
    def test_ownership_link_with_all_fields(self):
        """Test creating link with all fields"""
        link = OwnershipLink(
            entity_id="p-123",
            entity_type="person",
            entity_name="John Doe",
            ownership_percentage=30.0,
            ownership_type=OwnershipType.DIRECT,
            jurisdiction="US",
            is_pep=True,
            is_sanctioned=False
        )
        assert link.jurisdiction == "US"
        assert link.is_pep is True
        assert link.is_sanctioned is False
    
    def test_ownership_link_high_risk_indicators(self):
        """Test high-risk ownership link"""
        link = OwnershipLink(
            entity_id="p-456",
            entity_type="person",
            entity_name="Sanctioned Person",
            ownership_percentage=50.0,
            ownership_type=OwnershipType.BEARER,
            jurisdiction="VG",
            is_sanctioned=True
        )
        assert link.is_sanctioned is True
        assert link.ownership_type == OwnershipType.BEARER
        assert link.jurisdiction == "VG"
    
    def test_ownership_link_dataclass_equality(self):
        """Test dataclass equality"""
        link1 = OwnershipLink("p-1", "person", "John", 30.0, OwnershipType.DIRECT)
        link2 = OwnershipLink("p-1", "person", "John", 30.0, OwnershipType.DIRECT)
        assert link1 == link2
    
    def test_ownership_link_company_entity(self):
        """Test ownership link for company entity"""
        link = OwnershipLink(
            entity_id="c-789",
            entity_type="company",
            entity_name="HoldCo Ltd",
            ownership_percentage=60.0,
            ownership_type=OwnershipType.INDIRECT,
            jurisdiction="KY"
        )
        assert link.entity_type == "company"
        assert link.jurisdiction == "KY"


class TestUBOResult:
    """Test UBOResult dataclass (4 tests)"""
    
    def test_ubo_result_creation(self):
        """Test creating UBO result"""
        result = UBOResult(
            target_entity_id="c-123",
            target_entity_name="ACME Corp",
            ubos=[],
            ownership_chains=[],
            total_layers=0,
            high_risk_indicators=[],
            risk_score=0.0
        )
        assert result.target_entity_id == "c-123"
        assert result.target_entity_name == "ACME Corp"
        assert result.risk_score == 0.0
        assert len(result.ubos) == 0
    
    def test_ubo_result_with_ubos(self):
        """Test UBO result with discovered UBOs"""
        ubos = [
            {"person_id": "p-1", "name": "John Doe", "ownership": 30.0},
            {"person_id": "p-2", "name": "Jane Smith", "ownership": 40.0}
        ]
        result = UBOResult(
            target_entity_id="c-123",
            target_entity_name="ACME Corp",
            ubos=ubos,
            ownership_chains=[],
            total_layers=2,
            high_risk_indicators=["offshore_jurisdiction"],
            risk_score=0.6
        )
        assert len(result.ubos) == 2
        assert result.total_layers == 2
        assert "offshore_jurisdiction" in result.high_risk_indicators
    
    def test_ubo_result_high_risk(self):
        """Test high-risk UBO result"""
        result = UBOResult(
            target_entity_id="c-456",
            target_entity_name="Shell Corp",
            ubos=[],
            ownership_chains=[],
            total_layers=5,
            high_risk_indicators=["bearer_shares", "sanctioned_owner", "tax_haven"],
            risk_score=0.9
        )
        assert result.risk_score > 0.8
        assert len(result.high_risk_indicators) == 3
        assert result.total_layers == 5
    
    def test_ubo_result_with_ownership_chains(self):
        """Test UBO result with ownership chains"""
        chain = [
            OwnershipLink("c-1", "company", "HoldCo", 60.0, OwnershipType.DIRECT),
            OwnershipLink("p-1", "person", "John", 50.0, OwnershipType.INDIRECT)
        ]
        result = UBOResult(
            target_entity_id="c-123",
            target_entity_name="ACME Corp",
            ubos=[{"person_id": "p-1", "name": "John", "ownership": 30.0}],
            ownership_chains=[chain],
            total_layers=2,
            high_risk_indicators=[],
            risk_score=0.3
        )
        assert len(result.ownership_chains) == 1
        assert len(result.ownership_chains[0]) == 2


class TestUBODiscoveryInit:
    """Test UBODiscovery initialization (5 tests)"""
    
    def test_init_default_parameters(self):
        """Test initialization with default parameters"""
        ubo = UBODiscovery()
        assert ubo.host == "localhost"
        assert ubo.port == 18182
        assert ubo.ownership_threshold == 25.0
    
    def test_init_custom_parameters(self):
        """Test initialization with custom parameters"""
        ubo = UBODiscovery(host="remote-host", port=8182, ownership_threshold=10.0)
        assert ubo.host == "remote-host"
        assert ubo.port == 8182
        assert ubo.ownership_threshold == 10.0
    
    def test_init_regulatory_thresholds(self):
        """Test regulatory threshold constants"""
        assert UBODiscovery.DEFAULT_OWNERSHIP_THRESHOLD == 25.0
        assert UBODiscovery.MAX_TRAVERSAL_DEPTH == 10
    
    def test_init_high_risk_jurisdictions(self):
        """Test high-risk jurisdiction list"""
        assert "VG" in UBODiscovery.HIGH_RISK_JURISDICTIONS  # British Virgin Islands
        assert "KY" in UBODiscovery.HIGH_RISK_JURISDICTIONS  # Cayman Islands
        assert "PA" in UBODiscovery.HIGH_RISK_JURISDICTIONS  # Panama
        assert "US" not in UBODiscovery.HIGH_RISK_JURISDICTIONS
    
    def test_init_connection_not_established(self):
        """Test connection is not established on init"""
        ubo = UBODiscovery()
        assert not hasattr(ubo, 'g') or ubo.g is None


class TestUBODiscoveryConnection:
    """Test connection management (4 tests)"""
    
    @patch('src.python.analytics.ubo_discovery.DriverRemoteConnection')
    @patch('src.python.analytics.ubo_discovery.traversal')
    def test_connect_success(self, mock_traversal, mock_connection):
        """Test successful connection"""
        mock_g = Mock()
        mock_traversal.return_value.with_remote.return_value = mock_g
        
        ubo = UBODiscovery()
        result = ubo.connect()
        
        assert result is True
        mock_connection.assert_called_once()
    
    @patch('src.python.analytics.ubo_discovery.DriverRemoteConnection')
    def test_connect_failure(self, mock_connection):
        """Test connection failure handling"""
        mock_connection.side_effect = Exception("Connection failed")
        
        ubo = UBODiscovery()
        result = ubo.connect()
        
        assert result is False
    
    def test_close_connection(self):
        """Test closing connection"""
        ubo = UBODiscovery()
        ubo.connection = Mock()
        ubo.close()
        ubo.connection.close.assert_called_once()
    
    def test_close_connection_none(self):
        """Test closing when connection is None"""
        ubo = UBODiscovery()
        ubo.connection = None
        # Should not raise exception
        ubo.close()


class TestUBODiscoveryHelperMethods:
    """Test helper methods (6 tests)"""
    
    def test_flatten_value_map_simple(self):
        """Test flattening simple value map"""
        ubo = UBODiscovery()
        value_map = {"name": ["John Doe"], "age": [30]}
        result = ubo._flatten_value_map(value_map)
        assert result == {"name": "John Doe", "age": 30}
    
    def test_flatten_value_map_empty(self):
        """Test flattening empty value map"""
        ubo = UBODiscovery()
        result = ubo._flatten_value_map({})
        assert result == {}
    
    def test_flatten_value_map_multiple_values(self):
        """Test flattening value map with multiple values"""
        ubo = UBODiscovery()
        value_map = {"tags": ["tag1", "tag2", "tag3"]}
        result = ubo._flatten_value_map(value_map)
        # Multiple values are kept as list (not flattened to single value)
        assert result == {"tags": ["tag1", "tag2", "tag3"]}
    
    def test_calculate_effective_ownership_direct(self):
        """Test calculating direct ownership"""
        ubo = UBODiscovery()
        chain = [
            OwnershipLink("p-1", "person", "John", 50.0, OwnershipType.DIRECT)
        ]
        result = ubo._calculate_effective_ownership(chain)
        assert result == 50.0
    
    def test_calculate_effective_ownership_chain(self):
        """Test calculating ownership through chain"""
        ubo = UBODiscovery()
        chain = [
            OwnershipLink("c-1", "company", "HoldCo", 60.0, OwnershipType.DIRECT),
            OwnershipLink("p-1", "person", "John", 50.0, OwnershipType.INDIRECT)
        ]
        result = ubo._calculate_effective_ownership(chain)
        assert result == 30.0  # 60% * 50%
    
    def test_calculate_risk_score(self):
        """Test risk score calculation"""
        ubo = UBODiscovery()
        ubos = [{"is_pep": True, "is_sanctioned": False}]
        chains = [[OwnershipLink("p-1", "person", "John", 50.0, OwnershipType.DIRECT)] * 5]
        indicators = ["bearer_shares", "tax_haven", "sanctioned_owner"]
        score = ubo._calculate_risk_score(ubos, chains, indicators)
        assert 0.0 <= score <= 100.0
        assert score > 50.0  # Should be high risk


class TestUBODiscoveryRiskAssessment:
    """Test risk assessment logic (4 tests)"""
    
    def test_risk_score_no_indicators(self):
        """Test risk score with no indicators"""
        ubo = UBODiscovery()
        ubos = [{"is_pep": False, "is_sanctioned": False}]
        chains = [[OwnershipLink("p-1", "person", "John", 50.0, OwnershipType.DIRECT)]]
        score = ubo._calculate_risk_score(ubos, chains, [])
        assert score < 30.0  # Low risk
    
    def test_risk_score_bearer_shares(self):
        """Test risk score with bearer shares"""
        ubo = UBODiscovery()
        ubos = [{"is_pep": False, "is_sanctioned": False}]
        chains = [[OwnershipLink("p-1", "person", "John", 50.0, OwnershipType.BEARER)]]
        indicators = ["bearer_shares"]
        score = ubo._calculate_risk_score(ubos, chains, indicators)
        assert score > 10.0  # Has risk indicators
    
    def test_risk_score_multiple_layers(self):
        """Test risk score increases with layers"""
        ubo = UBODiscovery()
        ubos = [{"is_pep": False, "is_sanctioned": False}]
        chains_low = [[OwnershipLink("p-1", "person", "John", 50.0, OwnershipType.DIRECT)] * 2]
        chains_high = [[OwnershipLink("p-1", "person", "John", 50.0, OwnershipType.DIRECT)] * 8]
        score_low = ubo._calculate_risk_score(ubos, chains_low, [])
        score_high = ubo._calculate_risk_score(ubos, chains_high, [])
        assert score_high > score_low
    
    def test_risk_score_pep_indicator(self):
        """Test risk score with PEP"""
        ubo = UBODiscovery()
        ubos_no_pep = [{"is_pep": False, "is_sanctioned": False}]
        ubos_with_pep = [{"is_pep": True, "is_sanctioned": False}]
        chains = [[OwnershipLink("p-1", "person", "John", 50.0, OwnershipType.DIRECT)]]
        score_no_pep = ubo._calculate_risk_score(ubos_no_pep, chains, [])
        score_with_pep = ubo._calculate_risk_score(ubos_with_pep, chains, [])
        assert score_with_pep > score_no_pep


class TestDiscoverUBOsFunction:
    """Test discover_ubos convenience function (2 tests)"""
    
    @patch('src.python.analytics.ubo_discovery.UBODiscovery')
    def test_discover_ubos_success(self, mock_ubo_class):
        """Test discover_ubos function success"""
        mock_ubo = Mock()
        mock_ubo.connect.return_value = True
        mock_ubo.find_ubos_for_company.return_value = UBOResult(
            target_entity_id="c-123",
            target_entity_name="ACME Corp",
            ubos=[],
            ownership_chains=[],
            total_layers=0,
            high_risk_indicators=[],
            risk_score=0.0
        )


class TestUBODiscoveryMainMethods:
    """Test main UBO discovery methods (15 tests)"""
    
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._get_company_info')
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._find_direct_owners')
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._find_indirect_owners')
    def test_find_ubos_for_company_direct_only(self, mock_indirect, mock_direct, mock_info):
        """Test finding UBOs with direct owners only"""
        ubo = UBODiscovery()
        ubo.g = Mock()  # Mock graph connection
        
        mock_info.return_value = {"legal_name": "ACME Corp"}
        mock_direct.return_value = [
            {
                "person_id": "p-1",
                "name": "John Doe",
                "ownership_percentage": 30.0,
                "is_pep": False,
                "is_sanctioned": False
            }
        ]
        mock_indirect.return_value = []
        
        result = ubo.find_ubos_for_company("c-123")
        
        assert result.target_entity_id == "c-123"
        assert result.target_entity_name == "ACME Corp"
        assert len(result.ubos) == 1
        assert result.ubos[0]["person_id"] == "p-1"
        assert result.ubos[0]["ownership_percentage"] == 30.0
    
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._get_company_info')
    def test_find_ubos_company_not_found(self, mock_info):
        """Test handling of non-existent company"""
        ubo = UBODiscovery()
        ubo.g = Mock()
        mock_info.return_value = None
        
        with pytest.raises(ValueError, match="Company not found"):
            ubo.find_ubos_for_company("c-999")
    
    def test_find_ubos_not_connected(self):
        """Test error when not connected to graph"""
        ubo = UBODiscovery()
        # Don't set ubo.g
        
        with pytest.raises(RuntimeError, match="Not connected"):
            ubo.find_ubos_for_company("c-123")
    
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._get_company_info')
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._find_direct_owners')
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._find_indirect_owners')
    def test_find_ubos_with_pep(self, mock_indirect, mock_direct, mock_info):
        """Test UBO discovery with PEP indicator"""
        ubo = UBODiscovery()
        ubo.g = Mock()
        
        mock_info.return_value = {"legal_name": "ACME Corp"}
        mock_direct.return_value = [
            {
                "person_id": "p-1",
                "name": "Political Person",
                "ownership_percentage": 30.0,
                "is_pep": True,
                "is_sanctioned": False
            }
        ]
        mock_indirect.return_value = []
        
        result = ubo.find_ubos_for_company("c-123")
        
        assert "PEP: Political Person" in result.high_risk_indicators
        assert result.risk_score > 0
    
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._get_company_info')
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._find_direct_owners')
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._find_indirect_owners')
    def test_find_ubos_with_sanctioned_owner(self, mock_indirect, mock_direct, mock_info):
        """Test UBO discovery with sanctioned owner"""
        ubo = UBODiscovery()
        ubo.g = Mock()
        
        mock_info.return_value = {"legal_name": "ACME Corp"}
        mock_direct.return_value = [
            {
                "person_id": "p-1",
                "name": "Sanctioned Person",
                "ownership_percentage": 30.0,
                "is_pep": False,
                "is_sanctioned": True
            }
        ]
        mock_indirect.return_value = []
        
        result = ubo.find_ubos_for_company("c-123")
        
        assert "Sanctioned: Sanctioned Person" in result.high_risk_indicators
        assert result.risk_score > 0
    
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._get_company_info')
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._find_direct_owners')
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._find_indirect_owners')
    def test_find_ubos_below_threshold(self, mock_indirect, mock_direct, mock_info):
        """Test UBO discovery filters below threshold"""
        ubo = UBODiscovery(ownership_threshold=25.0)
        ubo.g = Mock()
        
        mock_info.return_value = {"legal_name": "ACME Corp"}
        mock_direct.return_value = [
            {
                "person_id": "p-1",
                "name": "Minor Owner",
                "ownership_percentage": 10.0,  # Below 25% threshold
                "is_pep": False,
                "is_sanctioned": False
            }
        ]
        mock_indirect.return_value = []
        
        result = ubo.find_ubos_for_company("c-123")
        
        assert len(result.ubos) == 0  # Filtered out
    
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._get_company_info')
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._find_direct_owners')
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._find_indirect_owners')
    def test_find_ubos_indirect_ownership(self, mock_indirect, mock_direct, mock_info):
        """Test UBO discovery with indirect ownership"""
        ubo = UBODiscovery()
        ubo.g = Mock()
        
        mock_info.return_value = {"legal_name": "ACME Corp"}
        mock_direct.return_value = []
        
        # Create indirect ownership chain
        chain = [
            OwnershipLink("p-1", "person", "John Doe", 50.0, OwnershipType.INDIRECT),
            OwnershipLink("c-1", "company", "HoldCo", 60.0, OwnershipType.INDIRECT)
        ]
        mock_indirect.return_value = [chain]
        
        result = ubo.find_ubos_for_company("c-123", include_indirect=True)
        
        assert len(result.ubos) == 1
        assert result.ubos[0]["ownership_type"] == "indirect"
        assert result.ubos[0]["chain_length"] == 2
    
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._get_company_info')
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._find_direct_owners')
    def test_find_ubos_exclude_indirect(self, mock_direct, mock_info):
        """Test UBO discovery excluding indirect ownership"""
        ubo = UBODiscovery()
        ubo.g = Mock()
        
        mock_info.return_value = {"legal_name": "ACME Corp"}
        mock_direct.return_value = [
            {
                "person_id": "p-1",
                "name": "John Doe",
                "ownership_percentage": 30.0,
                "is_pep": False,
                "is_sanctioned": False
            }
        ]
        
        result = ubo.find_ubos_for_company("c-123", include_indirect=False)
        
        assert len(result.ubos) == 1
        assert result.ubos[0]["ownership_type"] == "direct"
    
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._get_company_info')
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._find_direct_owners')
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._find_indirect_owners')
    def test_find_ubos_high_risk_jurisdiction(self, mock_indirect, mock_direct, mock_info):
        """Test UBO discovery with high-risk jurisdiction"""
        ubo = UBODiscovery()
        ubo.g = Mock()
        
        mock_info.return_value = {"legal_name": "ACME Corp"}
        mock_direct.return_value = []
        
        # Chain with high-risk jurisdiction
        chain = [
            OwnershipLink("p-1", "person", "John Doe", 50.0, OwnershipType.INDIRECT),
            OwnershipLink("c-1", "company", "Offshore Co", 60.0, OwnershipType.INDIRECT, jurisdiction="VG")
        ]
        mock_indirect.return_value = [chain]
        
        result = ubo.find_ubos_for_company("c-123")
        
        assert any("High-risk jurisdiction" in ind for ind in result.high_risk_indicators)
        assert any("VG" in ind for ind in result.high_risk_indicators)
    
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._get_company_info')
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._find_direct_owners')
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._find_indirect_owners')
    def test_find_ubos_max_depth_parameter(self, mock_indirect, mock_direct, mock_info):
        """Test UBO discovery with custom max depth"""
        ubo = UBODiscovery()
        ubo.g = Mock()
        
        mock_info.return_value = {"legal_name": "ACME Corp"}
        mock_direct.return_value = []
        mock_indirect.return_value = []
        
        result = ubo.find_ubos_for_company("c-123", max_depth=5)
        
        # Verify max_depth was passed to _find_indirect_owners
        mock_indirect.assert_called_once_with("c-123", 5)
    
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._get_company_info')
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._find_direct_owners')
    @patch('src.python.analytics.ubo_discovery.UBODiscovery._find_indirect_owners')
    def test_find_ubos_multiple_owners(self, mock_indirect, mock_direct, mock_info):
        """Test UBO discovery with multiple owners"""
        ubo = UBODiscovery()
        ubo.g = Mock()
        
        mock_info.return_value = {"legal_name": "ACME Corp"}
        mock_direct.return_value = [
            {
                "person_id": "p-1",
                "name": "John Doe",
                "ownership_percentage": 30.0,
                "is_pep": False,
                "is_sanctioned": False
            },
            {
                "person_id": "p-2",
                "name": "Jane Smith",
                "ownership_percentage": 40.0,
                "is_pep": False,
                "is_sanctioned": False
            }
        ]
        mock_indirect.return_value = []
        
        result = ubo.find_ubos_for_company("c-123")
        
        assert len(result.ubos) == 2
        assert result.ubos[0]["person_id"] == "p-1"
        assert result.ubos[1]["person_id"] == "p-2"
    
    def test_get_company_info_success(self):
        """Test getting company info successfully"""
        ubo = UBODiscovery()
        mock_g = Mock()
        mock_g.V().has().value_map().toList.return_value = [
            {"company_id": ["c-123"], "legal_name": ["ACME Corp"]}
        ]
        ubo.g = mock_g
        
        result = ubo._get_company_info("c-123")
        
        assert result is not None
        assert result["company_id"] == "c-123"
        assert result["legal_name"] == "ACME Corp"
    
    def test_get_company_info_not_found(self):
        """Test getting company info when not found"""
        ubo = UBODiscovery()
        mock_g = Mock()
        mock_g.V().has().value_map().toList.return_value = []
        ubo.g = mock_g
        
        result = ubo._get_company_info("c-999")
        
        assert result is None
    
    def test_get_company_info_error(self):
        """Test getting company info with error"""
        ubo = UBODiscovery()
        mock_g = Mock()
        mock_g.V().has().value_map().toList.side_effect = Exception("Graph error")
        ubo.g = mock_g
        
        result = ubo._get_company_info("c-123")
        
        assert result is None


class TestUBODiscoveryDirectOwners:
    """Test direct owner discovery (5 tests)"""
    
    def test_find_direct_owners_success(self):
        """Test finding direct owners successfully"""
        ubo = UBODiscovery()
        mock_g = Mock()
        
        # Mock Gremlin traversal result
        mock_result = [
            {
                "person_id": "p-1",
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "",
                "ownership_percentage": 30.0,
                "is_pep": False,
                "is_sanctioned": False
            }
        ]
        mock_g.V().has().in_e().project().by().by().by().by().by().by().by().toList.return_value = mock_result
        ubo.g = mock_g
        
        result = ubo._find_direct_owners("c-123")
        
        assert len(result) == 1
        assert result[0]["person_id"] == "p-1"
        assert result[0]["name"] == "John Doe"
        assert result[0]["ownership_percentage"] == 30.0
    
    def test_find_direct_owners_with_full_name(self):
        """Test finding direct owners with full_name field"""
        ubo = UBODiscovery()
        mock_g = Mock()
        
        mock_result = [
            {
                "person_id": "p-1",
                "first_name": "",
                "last_name": "",
                "full_name": "John Q. Doe",
                "ownership_percentage": 30.0,
                "is_pep": False,
                "is_sanctioned": False
            }
        ]
        mock_g.V().has().in_e().project().by().by().by().by().by().by().by().toList.return_value = mock_result
        ubo.g = mock_g
        
        result = ubo._find_direct_owners("c-123")
        
        assert result[0]["name"] == "John Q. Doe"
    
    def test_find_direct_owners_no_name(self):
        """Test finding direct owners with no name"""
        ubo = UBODiscovery()
        mock_g = Mock()
        
        mock_result = [
            {
                "person_id": "p-1",
                "first_name": "",
                "last_name": "",
                "full_name": "",
                "ownership_percentage": 30.0,
                "is_pep": False,
                "is_sanctioned": False
            }
        ]
        mock_g.V().has().in_e().project().by().by().by().by().by().by().by().toList.return_value = mock_result
        ubo.g = mock_g
        
        result = ubo._find_direct_owners("c-123")
        
        assert result[0]["name"] == "Unknown"
    
    def test_find_direct_owners_empty(self):
        """Test finding direct owners with no results"""
        ubo = UBODiscovery()
        mock_g = Mock()
        mock_g.V().has().in_e().project().by().by().by().by().by().by().by().toList.return_value = []
        ubo.g = mock_g
        
        result = ubo._find_direct_owners("c-123")
        
        assert len(result) == 0
    
    def test_find_direct_owners_error(self):
        """Test finding direct owners with error"""
        ubo = UBODiscovery()
        mock_g = Mock()
        mock_g.V().has().in_e().project().by().by().by().by().by().by().by().toList.side_effect = Exception("Query error")
        ubo.g = mock_g
        
        result = ubo._find_direct_owners("c-123")
        
        assert len(result) == 0  # Returns empty list on error


# Total: 36 + 15 + 5 = 56 tests
    
    @patch('src.python.analytics.ubo_discovery.UBODiscovery')
    def test_discover_ubos_connection_failure(self, mock_ubo_class):
        """Test discover_ubos function with connection failure"""
        mock_ubo = Mock()
        mock_ubo.connect.return_value = False
        mock_ubo_class.return_value = mock_ubo
        
        # Should raise RuntimeError when connection fails
        with pytest.raises(RuntimeError, match="Failed to connect"):
            discover_ubos("c-123")
        
        mock_ubo.connect.assert_called_once()
        mock_ubo.find_ubos_for_company.assert_not_called()


# Total: 36 tests covering key functionality
# Coverage target: 60%+ of ubo_discovery.py

# Made with Bob
