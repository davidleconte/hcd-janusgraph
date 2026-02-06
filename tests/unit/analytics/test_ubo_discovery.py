"""
Unit Tests for UBO Discovery Module
====================================

Tests for Ultimate Beneficial Owner discovery functionality
including ownership chain traversal, effective ownership calculation,
and risk scoring.

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-04
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from dataclasses import asdict

# Import the module under test
import sys
from pathlib import Path
src_path = str(Path(__file__).parent.parent.parent.parent / 'src' / 'python')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from src.python.analytics.ubo_discovery import (
    UBODiscovery,
    UBOResult,
    OwnershipLink,
    OwnershipType,
    discover_ubos
)


class TestOwnershipLink:
    """Tests for OwnershipLink dataclass"""
    
    def test_create_direct_ownership_link(self):
        """Test creating a direct ownership link"""
        link = OwnershipLink(
            entity_id="PERSON-001",
            entity_type="person",
            entity_name="John Doe",
            ownership_percentage=50.0,
            ownership_type=OwnershipType.DIRECT
        )
        
        assert link.entity_id == "PERSON-001"
        assert link.entity_type == "person"
        assert link.entity_name == "John Doe"
        assert link.ownership_percentage == 50.0
        assert link.ownership_type == OwnershipType.DIRECT
        assert link.jurisdiction is None
        assert link.is_pep is False
        assert link.is_sanctioned is False
    
    def test_create_indirect_ownership_link_with_jurisdiction(self):
        """Test creating an indirect ownership link with jurisdiction"""
        link = OwnershipLink(
            entity_id="COMP-001",
            entity_type="company",
            entity_name="Holding Corp",
            ownership_percentage=80.0,
            ownership_type=OwnershipType.INDIRECT,
            jurisdiction="VG"  # British Virgin Islands - high risk
        )
        
        assert link.jurisdiction == "VG"
        assert link.ownership_type == OwnershipType.INDIRECT
    
    def test_create_pep_sanctioned_link(self):
        """Test creating link for PEP/sanctioned individual"""
        link = OwnershipLink(
            entity_id="PERSON-PEP",
            entity_type="person",
            entity_name="Political Figure",
            ownership_percentage=30.0,
            ownership_type=OwnershipType.DIRECT,
            is_pep=True,
            is_sanctioned=True
        )
        
        assert link.is_pep is True
        assert link.is_sanctioned is True


class TestUBOResult:
    """Tests for UBOResult dataclass"""
    
    def test_create_ubo_result(self):
        """Test creating UBO result"""
        result = UBOResult(
            target_entity_id="COMP-TARGET",
            target_entity_name="Target Corp",
            ubos=[{"person_id": "P1", "name": "Owner", "ownership_percentage": 60.0}],
            ownership_chains=[],
            total_layers=1,
            high_risk_indicators=["PEP: Political Figure"],
            risk_score=35.0
        )
        
        assert result.target_entity_id == "COMP-TARGET"
        assert len(result.ubos) == 1
        assert result.risk_score == 35.0


class TestUBODiscoveryInit:
    """Tests for UBODiscovery initialization"""
    
    def test_default_initialization(self):
        """Test default initialization parameters"""
        ubo = UBODiscovery()
        
        assert ubo.host == 'localhost'
        assert ubo.port == 18182
        assert ubo.ownership_threshold == 25.0  # EU 5AMLD default
        assert ubo.g is None
        assert ubo.connection is None
    
    def test_custom_initialization(self):
        """Test custom initialization parameters"""
        ubo = UBODiscovery(
            host='janusgraph.example.com',
            port=8182,
            ownership_threshold=10.0
        )
        
        assert ubo.host == 'janusgraph.example.com'
        assert ubo.port == 8182
        assert ubo.ownership_threshold == 10.0
    
    def test_high_risk_jurisdictions(self):
        """Test high-risk jurisdiction list"""
        ubo = UBODiscovery()
        
        # Tax havens
        assert 'VG' in ubo.HIGH_RISK_JURISDICTIONS  # BVI
        assert 'KY' in ubo.HIGH_RISK_JURISDICTIONS  # Cayman
        assert 'PA' in ubo.HIGH_RISK_JURISDICTIONS  # Panama
        
        # Sanctioned countries
        assert 'RU' in ubo.HIGH_RISK_JURISDICTIONS  # Russia
        assert 'KP' in ubo.HIGH_RISK_JURISDICTIONS  # North Korea
        assert 'IR' in ubo.HIGH_RISK_JURISDICTIONS  # Iran


class TestEffectiveOwnershipCalculation:
    """Tests for effective ownership calculation"""
    
    def test_calculate_single_link_ownership(self):
        """Test effective ownership with single link"""
        ubo = UBODiscovery()
        
        chain = [
            OwnershipLink("P1", "person", "Owner", 60.0, OwnershipType.DIRECT)
        ]
        
        effective = ubo._calculate_effective_ownership(chain)
        assert effective == 60.0
    
    def test_calculate_two_layer_ownership(self):
        """Test effective ownership through two layers"""
        ubo = UBODiscovery()
        
        # Person owns 60% of Holding Co, Holding Co owns 80% of Target
        # Effective: 60% * 80% = 48%
        chain = [
            OwnershipLink("P1", "person", "Owner", 60.0, OwnershipType.INDIRECT),
            OwnershipLink("C1", "company", "Holding Co", 80.0, OwnershipType.INDIRECT)
        ]
        
        effective = ubo._calculate_effective_ownership(chain)
        assert effective == pytest.approx(48.0, rel=0.01)
    
    def test_calculate_three_layer_ownership(self):
        """Test effective ownership through three layers"""
        ubo = UBODiscovery()
        
        # Person owns 50% of A, A owns 60% of B, B owns 80% of Target
        # Effective: 50% * 60% * 80% = 24%
        chain = [
            OwnershipLink("P1", "person", "Owner", 50.0, OwnershipType.INDIRECT),
            OwnershipLink("C1", "company", "Company A", 60.0, OwnershipType.INDIRECT),
            OwnershipLink("C2", "company", "Company B", 80.0, OwnershipType.INDIRECT)
        ]
        
        effective = ubo._calculate_effective_ownership(chain)
        assert effective == pytest.approx(24.0, rel=0.01)
    
    def test_calculate_empty_chain(self):
        """Test effective ownership with empty chain"""
        ubo = UBODiscovery()
        
        effective = ubo._calculate_effective_ownership([])
        assert effective == 0.0
    
    def test_calculate_full_ownership_chain(self):
        """Test 100% ownership through chain"""
        ubo = UBODiscovery()
        
        chain = [
            OwnershipLink("P1", "person", "Owner", 100.0, OwnershipType.INDIRECT),
            OwnershipLink("C1", "company", "Holding Co", 100.0, OwnershipType.INDIRECT)
        ]
        
        effective = ubo._calculate_effective_ownership(chain)
        assert effective == 100.0


class TestRiskScoreCalculation:
    """Tests for risk score calculation"""
    
    def test_risk_score_no_ubos(self):
        """Test risk score when no UBOs identified"""
        ubo = UBODiscovery()
        
        score = ubo._calculate_risk_score(
            ubos=[],
            chains=[],
            indicators=[]
        )
        
        # No UBOs = +20 risk
        assert score >= 20.0
    
    def test_risk_score_pep(self):
        """Test risk score with PEP"""
        ubo = UBODiscovery()
        
        score = ubo._calculate_risk_score(
            ubos=[{"person_id": "P1", "is_pep": True}],
            chains=[[OwnershipLink("P1", "person", "PEP", 100.0, OwnershipType.DIRECT)]],
            indicators=[]
        )
        
        # PEP = +15 risk
        assert score >= 15.0
    
    def test_risk_score_sanctioned(self):
        """Test risk score with sanctioned individual"""
        ubo = UBODiscovery()
        
        score = ubo._calculate_risk_score(
            ubos=[{"person_id": "P1", "is_sanctioned": True}],
            chains=[[OwnershipLink("P1", "person", "Sanctioned", 100.0, OwnershipType.DIRECT)]],
            indicators=[]
        )
        
        # Sanctioned = +25 risk
        assert score >= 25.0
    
    def test_risk_score_complex_structure(self):
        """Test risk score with complex ownership structure"""
        ubo = UBODiscovery()
        
        # 3-layer structure = up to 30 points
        chain = [
            OwnershipLink("P1", "person", "Owner", 100.0, OwnershipType.INDIRECT),
            OwnershipLink("C1", "company", "Layer 1", 100.0, OwnershipType.INDIRECT),
            OwnershipLink("C2", "company", "Layer 2", 100.0, OwnershipType.INDIRECT)
        ]
        
        score = ubo._calculate_risk_score(
            ubos=[{"person_id": "P1"}],
            chains=[chain],
            indicators=[]
        )
        
        # 3 layers * 10 = 30 points
        assert score >= 30.0
    
    def test_risk_score_high_risk_jurisdiction(self):
        """Test risk score with high-risk jurisdiction indicators"""
        ubo = UBODiscovery()
        
        indicators = [
            "High-risk jurisdiction: Shell Co (VG)",
            "High-risk jurisdiction: Holding Co (PA)"
        ]
        
        score = ubo._calculate_risk_score(
            ubos=[{"person_id": "P1"}],
            chains=[[OwnershipLink("P1", "person", "Owner", 100.0, OwnershipType.DIRECT)]],
            indicators=indicators
        )
        
        # 2 indicators * 5 = 10 points (plus base)
        assert score >= 10.0
    
    def test_risk_score_capped_at_100(self):
        """Test risk score is capped at 100"""
        ubo = UBODiscovery()
        
        # Create scenario with maximum risk
        score = ubo._calculate_risk_score(
            ubos=[
                {"person_id": "P1", "is_pep": True, "is_sanctioned": True},
                {"person_id": "P2", "is_pep": True, "is_sanctioned": True}
            ],
            chains=[
                [OwnershipLink("P1", "person", "PEP1", 100.0, OwnershipType.INDIRECT) for _ in range(10)],
                [OwnershipLink("P2", "person", "PEP2", 100.0, OwnershipType.INDIRECT) for _ in range(10)]
            ],
            indicators=["Indicator"] * 20
        )
        
        assert score <= 100.0


class TestFlattenValueMap:
    """Tests for JanusGraph valueMap flattening"""
    
    def test_flatten_simple_values(self):
        """Test flattening simple single-value lists"""
        ubo = UBODiscovery()
        
        value_map = {
            'person_id': ['P001'],
            'name': ['John Doe'],
            'age': [35]
        }
        
        flat = ubo._flatten_value_map(value_map)
        
        assert flat['person_id'] == 'P001'
        assert flat['name'] == 'John Doe'
        assert flat['age'] == 35
    
    def test_flatten_multi_value_lists(self):
        """Test flattening multi-value lists (kept as-is)"""
        ubo = UBODiscovery()
        
        value_map = {
            'tags': ['tag1', 'tag2', 'tag3']
        }
        
        flat = ubo._flatten_value_map(value_map)
        
        assert flat['tags'] == ['tag1', 'tag2', 'tag3']


class TestOwnershipTypes:
    """Tests for OwnershipType enum"""
    
    def test_ownership_type_values(self):
        """Test all ownership type values"""
        assert OwnershipType.DIRECT.value == "direct"
        assert OwnershipType.INDIRECT.value == "indirect"
        assert OwnershipType.NOMINEE.value == "nominee"
        assert OwnershipType.TRUST.value == "trust"
        assert OwnershipType.BEARER.value == "bearer"
    
    def test_ownership_type_string_comparison(self):
        """Test ownership type string comparison"""
        assert OwnershipType.DIRECT == "direct"
        assert OwnershipType.INDIRECT == "indirect"


class TestUBODiscoveryConnection:
    """Tests for UBO Discovery connection management"""
    
    @patch('src.python.analytics.ubo_discovery.DriverRemoteConnection')
    @patch('src.python.analytics.ubo_discovery.traversal')
    def test_connect_success(self, mock_traversal, mock_connection):
        """Test successful connection"""
        mock_conn_instance = Mock()
        mock_connection.return_value = mock_conn_instance
        mock_traversal_instance = Mock()
        mock_traversal.return_value.withRemote.return_value = mock_traversal_instance
        
        ubo = UBODiscovery()
        result = ubo.connect()
        
        assert result is True
        assert ubo.connection is mock_conn_instance
        assert ubo.g is mock_traversal_instance
    
    @patch('src.python.analytics.ubo_discovery.DriverRemoteConnection')
    def test_connect_failure(self, mock_connection):
        """Test connection failure"""
        mock_connection.side_effect = Exception("Connection refused")
        
        ubo = UBODiscovery()
        result = ubo.connect()
        
        assert result is False
        assert ubo.connection is None
    
    def test_close_without_connection(self):
        """Test close when not connected"""
        ubo = UBODiscovery()
        # Should not raise
        ubo.close()
    
    @patch('src.python.analytics.ubo_discovery.DriverRemoteConnection')
    @patch('src.python.analytics.ubo_discovery.traversal')
    def test_close_with_connection(self, mock_traversal, mock_connection):
        """Test close when connected"""
        mock_conn_instance = Mock()
        mock_connection.return_value = mock_conn_instance
        mock_traversal.return_value.withRemote.return_value = Mock()
        
        ubo = UBODiscovery()
        ubo.connect()
        ubo.close()
        
        mock_conn_instance.close.assert_called_once()


class TestConvenienceFunction:
    """Tests for convenience function"""
    
    @patch.object(UBODiscovery, 'connect')
    @patch.object(UBODiscovery, 'find_ubos_for_company')
    @patch.object(UBODiscovery, 'close')
    def test_discover_ubos_convenience(self, mock_close, mock_find, mock_connect):
        """Test discover_ubos convenience function"""
        mock_connect.return_value = True
        mock_find.return_value = UBOResult(
            target_entity_id="COMP-001",
            target_entity_name="Test Corp",
            ubos=[],
            ownership_chains=[],
            total_layers=0,
            high_risk_indicators=[],
            risk_score=0.0
        )
        
        result = discover_ubos("COMP-001")
        
        mock_connect.assert_called_once()
        mock_find.assert_called_once_with("COMP-001")
        mock_close.assert_called_once()
        assert result.target_entity_id == "COMP-001"
    
    @patch.object(UBODiscovery, 'connect')
    def test_discover_ubos_connection_failure(self, mock_connect):
        """Test discover_ubos when connection fails"""
        mock_connect.return_value = False
        
        with pytest.raises(RuntimeError, match="Failed to connect"):
            discover_ubos("COMP-001")


# Additional edge case tests
class TestEdgeCases:
    """Edge case tests"""
    
    def test_ubo_not_connected_raises(self):
        """Test that operations without connection raise error"""
        ubo = UBODiscovery()
        
        with pytest.raises(RuntimeError, match="Not connected"):
            ubo.find_ubos_for_company("COMP-001")
    
    def test_ownership_threshold_validation(self):
        """Test ownership threshold is properly used"""
        ubo_strict = UBODiscovery(ownership_threshold=50.0)
        ubo_lenient = UBODiscovery(ownership_threshold=10.0)
        
        assert ubo_strict.ownership_threshold == 50.0
        assert ubo_lenient.ownership_threshold == 10.0
