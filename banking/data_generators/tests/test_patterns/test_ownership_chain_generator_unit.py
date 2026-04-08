"""
Unit Tests for Ownership Chain Generator
========================================

Tests for multi-layer ownership structure generation for UBO discovery.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-08
Phase: 5A (Pattern Generators - Ownership Chains)
"""

import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from banking.data_generators.patterns.ownership_chain_generator import (
    OwnershipChainGenerator,
    OwnershipLink,
    OwnershipChain,
    OwnershipStructure,
    DEMO_SCENARIOS,
    create_demo_ownership_data
)


# ============================================================================
# Test Data Models
# ============================================================================

class TestOwnershipLink:
    """Test OwnershipLink dataclass"""
    
    def test_ownership_link_creation(self):
        """Test creating an ownership link"""
        link = OwnershipLink(
            owner_id="p-123",
            owner_type="person",
            owner_name="John Doe",
            target_id="c-456",
            target_type="company",
            target_name="Acme Corp",
            ownership_percentage=60.0,
            ownership_type="direct",
            jurisdiction="US"
        )
        
        assert link.owner_id == "p-123"
        assert link.owner_type == "person"
        assert link.ownership_percentage == 60.0
        assert link.is_shell_company is False
        assert link.is_pep is False
        assert link.effective_ownership == 0.0
    
    def test_ownership_link_with_flags(self):
        """Test ownership link with risk flags"""
        link = OwnershipLink(
            owner_id="p-123",
            owner_type="person",
            owner_name="John Doe",
            target_id="c-456",
            target_type="company",
            target_name="Shell Corp",
            ownership_percentage=100.0,
            ownership_type="shell",
            jurisdiction="VG",
            is_shell_company=True,
            is_pep=True,
            is_sanctioned=True
        )
        
        assert link.is_shell_company is True
        assert link.is_pep is True
        assert link.is_sanctioned is True


class TestOwnershipChain:
    """Test OwnershipChain dataclass"""
    
    def test_ownership_chain_creation(self):
        """Test creating an ownership chain"""
        link = OwnershipLink(
            owner_id="p-123",
            owner_type="person",
            owner_name="John Doe",
            target_id="c-456",
            target_type="company",
            target_name="Acme Corp",
            ownership_percentage=60.0,
            ownership_type="direct",
            jurisdiction="US"
        )
        
        chain = OwnershipChain(
            target_company_id="c-456",
            target_company_name="Acme Corp",
            ultimate_beneficial_owner_id="p-123",
            ultimate_beneficial_owner_name="John Doe",
            chain_length=1,
            effective_ownership_percentage=60.0,
            chain_links=[link]
        )
        
        assert chain.target_company_id == "c-456"
        assert chain.chain_length == 1
        assert chain.effective_ownership_percentage == 60.0
        assert len(chain.chain_links) == 1
    
    def test_exceeds_threshold_true(self):
        """Test threshold check when ownership exceeds 25%"""
        chain = OwnershipChain(
            target_company_id="c-456",
            target_company_name="Acme Corp",
            ultimate_beneficial_owner_id="p-123",
            ultimate_beneficial_owner_name="John Doe",
            chain_length=1,
            effective_ownership_percentage=30.0,
            chain_links=[]
        )
        
        assert chain.exceeds_threshold(25.0) is True
    
    def test_exceeds_threshold_false(self):
        """Test threshold check when ownership below 25%"""
        chain = OwnershipChain(
            target_company_id="c-456",
            target_company_name="Acme Corp",
            ultimate_beneficial_owner_id="p-123",
            ultimate_beneficial_owner_name="John Doe",
            chain_length=1,
            effective_ownership_percentage=20.0,
            chain_links=[]
        )
        
        assert chain.exceeds_threshold(25.0) is False
    
    def test_exceeds_threshold_exact(self):
        """Test threshold check when ownership exactly 25%"""
        chain = OwnershipChain(
            target_company_id="c-456",
            target_company_name="Acme Corp",
            ultimate_beneficial_owner_id="p-123",
            ultimate_beneficial_owner_name="John Doe",
            chain_length=1,
            effective_ownership_percentage=25.0,
            chain_links=[]
        )
        
        assert chain.exceeds_threshold(25.0) is True


class TestOwnershipStructure:
    """Test OwnershipStructure dataclass"""
    
    def test_ownership_structure_creation(self):
        """Test creating an ownership structure"""
        structure = OwnershipStructure(
            target_company_id="c-456",
            target_company_name="Acme Corp",
            ownership_chains=[],
            all_ubos=[],
            high_risk_indicators=[],
            overall_risk_score=20.0,
            total_layers=1
        )
        
        assert structure.target_company_id == "c-456"
        assert structure.overall_risk_score == 20.0
        assert structure.total_layers == 1


# ============================================================================
# Test Generator Initialization
# ============================================================================

class TestOwnershipChainGeneratorInitialization:
    """Test generator initialization"""
    
    def test_init_default_parameters(self):
        """Test initialization with default parameters"""
        generator = OwnershipChainGenerator()
        
        assert generator.ownership_threshold == 25.0
        assert generator.seed is None
    
    def test_init_with_seed(self):
        """Test initialization with custom seed"""
        generator = OwnershipChainGenerator(seed=42)
        
        assert generator.seed == 42
        assert generator.ownership_threshold == 25.0
    
    def test_init_with_custom_threshold(self):
        """Test initialization with custom ownership threshold"""
        generator = OwnershipChainGenerator(ownership_threshold=30.0)
        
        assert generator.ownership_threshold == 30.0
    
    def test_init_with_config(self):
        """Test initialization with custom config"""
        config = {"custom_param": "value"}
        generator = OwnershipChainGenerator(config=config)
        
        assert generator.config == config
    
    def test_init_deterministic_with_seed(self):
        """Test that same seed produces same results"""
        gen1 = OwnershipChainGenerator(seed=42)
        gen2 = OwnershipChainGenerator(seed=42)
        
        struct1 = gen1.generate()
        struct2 = gen2.generate()
        
        # Same seed should produce same number of chains
        assert len(struct1.ownership_chains) == len(struct2.ownership_chains)
        # Same seed should produce same risk score
        assert struct1.overall_risk_score == struct2.overall_risk_score


# ============================================================================
# Test Simple Chain Generation
# ============================================================================

class TestSimpleChainGeneration:
    """Test basic ownership chain generation"""
    
    def test_generate_default_structure(self):
        """Test generating default ownership structure"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate()
        
        assert isinstance(structure, OwnershipStructure)
        assert structure.target_company_id is not None
        assert structure.target_company_name is not None
        assert len(structure.ownership_chains) > 0
    
    def test_generate_simple_direct_scenario(self):
        """Test generating simple direct ownership scenario"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="simple_direct")
        
        assert len(structure.ownership_chains) == 1
        chain = structure.ownership_chains[0]
        assert chain.chain_length == 1
        assert chain.effective_ownership_percentage == 60.0
    
    def test_generate_two_layer_holding(self):
        """Test generating two-layer holding structure"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="two_layer_holding")
        
        assert len(structure.ownership_chains) == 1
        chain = structure.ownership_chains[0]
        assert chain.chain_length == 2
        # 80% * 70% = 56%
        assert 55.0 < chain.effective_ownership_percentage < 57.0
    
    def test_generate_with_custom_target_name(self):
        """Test generating structure with custom target name"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(
            target_name="Custom Corp Ltd",
            scenario="simple_direct"
        )
        
        assert structure.target_company_name == "Custom Corp Ltd"
    
    def test_generate_with_custom_target_id(self):
        """Test generating structure with custom target ID"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(
            target_id="custom-123",
            scenario="simple_direct"
        )
        
        assert structure.target_company_id == "custom-123"


# ============================================================================
# Test Complex Chain Generation
# ============================================================================

class TestComplexChainGeneration:
    """Test complex ownership structure generation"""
    
    def test_generate_shell_company_chain(self):
        """Test generating shell company chain"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="shell_company_chain")
        
        assert len(structure.ownership_chains) == 1
        chain = structure.ownership_chains[0]
        assert chain.chain_length == 3
        assert "Shell company structure detected" in chain.risk_indicators
    
    def test_generate_complex_multi_ubo(self):
        """Test generating structure with multiple UBOs"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="complex_multi_ubo")
        
        assert len(structure.ownership_chains) == 3
        assert len(structure.all_ubos) >= 2  # At least 2 UBOs exceed threshold
    
    def test_generate_pep_sanctioned_scenario(self):
        """Test generating PEP/sanctioned scenario"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="pep_sanctioned")
        
        assert len(structure.ownership_chains) == 1
        chain = structure.ownership_chains[0]
        assert any("PEP" in ind for ind in chain.risk_indicators)
    
    def test_generate_nominee_arrangement(self):
        """Test generating nominee arrangement"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="nominee_arrangement")
        
        assert len(structure.ownership_chains) == 1
        chain = structure.ownership_chains[0]
        assert chain.chain_length == 2
    
    def test_generate_with_custom_chains(self):
        """Test generating structure with custom chain definitions"""
        generator = OwnershipChainGenerator(seed=42)
        custom_chains = [
            {"layers": 1, "ownership_path": [75.0], "type": "direct"}
        ]
        structure = generator.generate_complex_structure(custom_chains=custom_chains)
        
        assert len(structure.ownership_chains) == 1
        assert structure.ownership_chains[0].effective_ownership_percentage == 75.0


# ============================================================================
# Test UBO Discovery
# ============================================================================

class TestUBODiscovery:
    """Test Ultimate Beneficial Owner discovery"""
    
    def test_ubo_exceeds_threshold(self):
        """Test UBO identification when ownership exceeds threshold"""
        generator = OwnershipChainGenerator(seed=42, ownership_threshold=25.0)
        structure = generator.generate_complex_structure(scenario="simple_direct")
        
        assert len(structure.all_ubos) == 1
        ubo = structure.all_ubos[0]
        assert ubo["ownership_percentage"] >= 25.0
    
    def test_ubo_below_threshold_not_included(self):
        """Test that UBOs below threshold are not included"""
        generator = OwnershipChainGenerator(seed=42, ownership_threshold=70.0)
        structure = generator.generate_complex_structure(scenario="simple_direct")
        
        # 60% ownership is below 70% threshold
        assert len(structure.all_ubos) == 0
    
    def test_multiple_ubos_identified(self):
        """Test identifying multiple UBOs"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="complex_multi_ubo")
        
        assert len(structure.all_ubos) >= 2
        for ubo in structure.all_ubos:
            assert ubo["ownership_percentage"] >= 25.0
    
    def test_ubo_details_complete(self):
        """Test that UBO details are complete"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="simple_direct")
        
        ubo = structure.all_ubos[0]
        assert "person_id" in ubo
        assert "name" in ubo
        assert "ownership_percentage" in ubo
        assert "ownership_type" in ubo
        assert "chain_length" in ubo
        assert "jurisdictions" in ubo


# ============================================================================
# Test Risk Scoring
# ============================================================================

class TestRiskScoring:
    """Test risk scoring calculations"""
    
    def test_base_risk_score(self):
        """Test base risk score for simple structure"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="simple_direct")
        
        # Base score is 20, simple structure adds minimal risk
        assert 20.0 <= structure.overall_risk_score <= 50.0
    
    def test_high_risk_pep_scenario(self):
        """Test high risk score for PEP scenario"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="pep_sanctioned")
        
        # PEP adds 20 points, complex structure adds more
        assert structure.overall_risk_score >= 50.0
    
    def test_shell_company_increases_risk(self):
        """Test that shell companies increase risk score"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="shell_company_chain")
        
        # Shell companies add risk
        assert structure.overall_risk_score >= 40.0
    
    def test_risk_score_capped_at_100(self):
        """Test that risk score is capped at 100"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="pep_sanctioned")
        
        assert structure.overall_risk_score <= 100.0
    
    def test_risk_indicators_collected(self):
        """Test that risk indicators are collected"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="shell_company_chain")
        
        assert len(structure.high_risk_indicators) > 0
        assert any("Shell company" in ind for ind in structure.high_risk_indicators)


# ============================================================================
# Test Effective Ownership Calculation
# ============================================================================

class TestEffectiveOwnershipCalculation:
    """Test effective ownership percentage calculations"""
    
    def test_direct_ownership_calculation(self):
        """Test direct ownership (single layer)"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="simple_direct")
        
        chain = structure.ownership_chains[0]
        assert chain.effective_ownership_percentage == 60.0
    
    def test_two_layer_ownership_calculation(self):
        """Test two-layer ownership calculation"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="two_layer_holding")
        
        chain = structure.ownership_chains[0]
        # 80% * 70% = 56%
        expected = 80.0 * 70.0 / 100.0
        assert abs(chain.effective_ownership_percentage - expected) < 0.1
    
    def test_three_layer_ownership_calculation(self):
        """Test three-layer ownership calculation"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="shell_company_chain")
        
        chain = structure.ownership_chains[0]
        # 100% * 100% * 60% = 60%
        expected = 100.0 * 100.0 * 60.0 / 10000.0
        assert abs(chain.effective_ownership_percentage - expected) < 0.1
    
    def test_regulatory_threshold_above(self):
        """Test ownership just above 25% threshold"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="regulatory_threshold")
        
        # First chain: 51% * 50% = 25.5% (EXCEEDS)
        chain1 = structure.ownership_chains[0]
        assert chain1.exceeds_threshold(25.0) is True
    
    def test_regulatory_threshold_below(self):
        """Test ownership just below 25% threshold"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="regulatory_threshold")
        
        # Second chain: 49% * 50% = 24.5% (BELOW)
        chain2 = structure.ownership_chains[1]
        assert chain2.exceeds_threshold(25.0) is False


# ============================================================================
# Test Gremlin Script Generation
# ============================================================================

class TestGremlinScriptGeneration:
    """Test Gremlin script generation"""
    
    def test_generate_gremlin_script(self):
        """Test generating Gremlin load script"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="simple_direct")
        
        script = generator.generate_gremlin_load_script(structure)
        
        assert isinstance(script, str)
        assert len(script) > 0
        assert "// Ownership Chain Data Load" in script
    
    def test_gremlin_script_contains_target_company(self):
        """Test that script contains target company"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(
            target_name="Test Corp",
            scenario="simple_direct"
        )
        
        script = generator.generate_gremlin_load_script(structure)
        
        assert "Test Corp" in script
        assert structure.target_company_id in script
    
    def test_gremlin_script_contains_ubo(self):
        """Test that script contains UBO information"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="simple_direct")
        
        script = generator.generate_gremlin_load_script(structure)
        
        ubo_name = structure.ownership_chains[0].ultimate_beneficial_owner_name
        assert ubo_name in script
    
    def test_gremlin_script_has_commit(self):
        """Test that script includes transaction commit"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="simple_direct")
        
        script = generator.generate_gremlin_load_script(structure)
        
        assert "graph.tx().commit()" in script


# ============================================================================
# Test Demo Scenarios
# ============================================================================

class TestDemoScenarios:
    """Test predefined demo scenarios"""
    
    def test_all_demo_scenarios_exist(self):
        """Test that all demo scenarios are defined"""
        expected_scenarios = [
            "simple_direct",
            "two_layer_holding",
            "shell_company_chain",
            "complex_multi_ubo",
            "pep_sanctioned",
            "nominee_arrangement",
            "regulatory_threshold",
            "circular_ownership"
        ]
        
        for scenario in expected_scenarios:
            assert scenario in DEMO_SCENARIOS
    
    def test_generate_all_demo_scenarios(self):
        """Test generating all demo scenarios"""
        generator = OwnershipChainGenerator(seed=42)
        all_scenarios = generator.generate_all_demo_scenarios()
        
        assert len(all_scenarios) == len(DEMO_SCENARIOS)
        for scenario_name in DEMO_SCENARIOS:
            assert scenario_name in all_scenarios
            assert isinstance(all_scenarios[scenario_name], OwnershipStructure)
    
    def test_each_scenario_generates_valid_structure(self):
        """Test that each scenario generates valid structure"""
        generator = OwnershipChainGenerator(seed=42)
        
        for scenario_name in DEMO_SCENARIOS:
            structure = generator.generate_complex_structure(scenario=scenario_name)
            assert isinstance(structure, OwnershipStructure)
            assert len(structure.ownership_chains) > 0
            assert structure.overall_risk_score >= 0


# ============================================================================
# Test Helper Functions
# ============================================================================

class TestHelperFunctions:
    """Test helper functions"""
    
    @patch("builtins.open", new_callable=MagicMock)
    @patch("pathlib.Path")
    def test_create_demo_ownership_data(self, mock_path, mock_open):
        """Test creating demo ownership data"""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.mkdir = MagicMock()
        mock_path_instance.__truediv__ = MagicMock(return_value=mock_path_instance)
        
        result = create_demo_ownership_data(seed=42, output_dir="test_output")
        
        assert "metadata" in result
        assert "scenarios" in result
        assert result["metadata"]["seed"] == 42
        assert result["metadata"]["total_scenarios"] == len(DEMO_SCENARIOS)
    
    @patch("builtins.open", new_callable=MagicMock)
    @patch("pathlib.Path")
    def test_create_demo_ownership_data_metadata(self, mock_path, mock_open):
        """Test metadata in demo ownership data"""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.mkdir = MagicMock()
        mock_path_instance.__truediv__ = MagicMock(return_value=mock_path_instance)
        
        result = create_demo_ownership_data(seed=42)
        
        metadata = result["metadata"]
        assert metadata["generator"] == "OwnershipChainGenerator"
        assert metadata["ownership_threshold"] == 25.0
        assert "regulatory_basis" in metadata


# ============================================================================
# Test Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_zero_ownership_percentage(self):
        """Test handling of zero ownership percentage"""
        generator = OwnershipChainGenerator(seed=42)
        custom_chains = [
            {"layers": 1, "ownership_path": [0.0], "type": "direct"}
        ]
        structure = generator.generate_complex_structure(custom_chains=custom_chains)
        
        assert structure.ownership_chains[0].effective_ownership_percentage == 0.0
    
    def test_full_ownership_percentage(self):
        """Test handling of 100% ownership"""
        generator = OwnershipChainGenerator(seed=42)
        custom_chains = [
            {"layers": 1, "ownership_path": [100.0], "type": "direct"}
        ]
        structure = generator.generate_complex_structure(custom_chains=custom_chains)
        
        assert structure.ownership_chains[0].effective_ownership_percentage == 100.0
    
    def test_single_layer_chain(self):
        """Test single-layer ownership chain"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="simple_direct")
        
        assert structure.ownership_chains[0].chain_length == 1
    
    def test_maximum_depth_chain(self):
        """Test maximum depth ownership chain"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="pep_sanctioned")
        
        # PEP scenario has 4 layers
        assert structure.ownership_chains[0].chain_length == 4
    
    def test_invalid_scenario_uses_default(self):
        """Test that invalid scenario name uses default"""
        generator = OwnershipChainGenerator(seed=42)
        structure = generator.generate_complex_structure(scenario="invalid_scenario")
        
        # Should fall back to complex_multi_ubo
        assert len(structure.ownership_chains) == 3


# ============================================================================
# Test Determinism
# ============================================================================

class TestDeterminism:
    """Test deterministic behavior with seeds"""
    
    def test_same_seed_produces_same_structure(self):
        """Test that same seed produces identical structures"""
        gen1 = OwnershipChainGenerator(seed=42)
        gen2 = OwnershipChainGenerator(seed=42)
        
        struct1 = gen1.generate_complex_structure(scenario="simple_direct")
        struct2 = gen2.generate_complex_structure(scenario="simple_direct")
        
        # Same seed should produce same number of chains and risk score
        assert len(struct1.ownership_chains) == len(struct2.ownership_chains)
        assert struct1.overall_risk_score == struct2.overall_risk_score
        assert struct1.ownership_chains[0].effective_ownership_percentage == \
               struct2.ownership_chains[0].effective_ownership_percentage
    
    def test_different_seeds_produce_different_structures(self):
        """Test that different seeds produce different structures"""
        gen1 = OwnershipChainGenerator(seed=42)
        gen2 = OwnershipChainGenerator(seed=123)
        
        struct1 = gen1.generate_complex_structure(scenario="simple_direct")
        struct2 = gen2.generate_complex_structure(scenario="simple_direct")
        
        # IDs should be different (different seeds)
        assert struct1.target_company_id != struct2.target_company_id
    
    def test_reproducible_across_runs(self):
        """Test that results are reproducible across multiple runs"""
        results = []
        for _ in range(3):
            gen = OwnershipChainGenerator(seed=42)
            struct = gen.generate_complex_structure(scenario="simple_direct")
            results.append(struct.target_company_id)
        
        # All runs should produce same ID
        assert len(set(results)) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
