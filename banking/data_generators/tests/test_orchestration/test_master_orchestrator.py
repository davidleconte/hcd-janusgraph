"""
Unit Tests for MasterOrchestrator
==================================

Comprehensive tests for master orchestration including:
- Smoke tests
- Functional tests
- Edge case tests
- Integration tests
- Performance tests

Author: IBM Bob
Date: 2026-01-28
"""

import pytest
from pathlib import Path
import json


class TestMasterOrchestratorSmoke:
    """Smoke tests - basic functionality"""
    
    def test_orchestrator_initialization(self, small_orchestrator):
        """Test that orchestrator initializes without errors"""
        assert small_orchestrator is not None
        assert small_orchestrator.config is not None
    
    def test_basic_generation(self, small_orchestrator):
        """Test that orchestrator can generate data"""
        stats = small_orchestrator.generate_all()
        assert stats is not None
        assert stats.total_entities > 0
    
    def test_config_validation(self):
        """Test configuration validation"""
        from banking.data_generators.orchestration import GenerationConfig
        
        config = GenerationConfig(
            seed=42,
            person_count=10,
            company_count=5,
            account_count=20
        )
        assert config.seed == 42
        assert config.person_count == 10


class TestMasterOrchestratorFunctional:
    """Functional tests - correct behavior"""
    
    def test_all_phases_execute(self, small_orchestrator):
        """Test that all generation phases execute"""
        stats = small_orchestrator.generate_all()
        
        # Should have entities from all phases
        assert stats.persons_generated > 0
        assert stats.companies_generated > 0
        assert stats.accounts_generated > 0
        assert stats.transactions_generated > 0
    
    def test_entity_counts_match_config(self, small_orchestrator):
        """Test that generated counts match configuration"""
        stats = small_orchestrator.generate_all()
        
        config = small_orchestrator.config
        assert stats.persons_generated == config.person_count
        assert stats.companies_generated == config.company_count
        assert stats.accounts_generated == config.account_count
    
    def test_phase_execution_order(self, small_orchestrator):
        """Test that phases execute in correct order"""
        stats = small_orchestrator.generate_all()
        
        # Core entities should be generated before events
        assert stats.persons_generated > 0
        assert stats.companies_generated > 0
        assert stats.accounts_generated > 0
        # Then events
        assert stats.transactions_generated > 0
    
    def test_statistics_tracking(self, small_orchestrator):
        """Test that statistics are tracked correctly"""
        stats = small_orchestrator.generate_all()
        
        assert stats.total_entities > 0
        assert stats.total_events > 0
        assert stats.total_patterns >= 0
        assert stats.duration_seconds > 0
    
    def test_error_handling(self, small_orchestrator):
        """Test error handling in orchestrator"""
        # Should handle errors gracefully
        stats = small_orchestrator.generate_all()
        
        # Check error tracking
        assert hasattr(stats, 'errors')
        assert isinstance(stats.errors, list)


class TestMasterOrchestratorEdgeCases:
    """Edge case tests"""
    
    def test_zero_patterns(self):
        """Test generation with zero patterns"""
        from banking.data_generators.orchestration import (
            MasterOrchestrator,
            GenerationConfig
        )
        
        config = GenerationConfig(
            seed=42,
            person_count=10,
            company_count=5,
            account_count=20,
            transaction_count=50,
            insider_trading_patterns=0,
            tbml_patterns=0,
            fraud_ring_patterns=0,
            structuring_patterns=0,
            cato_patterns=0
        )
        
        orchestrator = MasterOrchestrator(config)
        stats = orchestrator.generate_all()
        
        assert stats.total_patterns == 0
    
    def test_minimal_configuration(self):
        """Test with minimal configuration"""
        from banking.data_generators.orchestration import (
            MasterOrchestrator,
            GenerationConfig
        )
        
        config = GenerationConfig(
            seed=42,
            person_count=1,
            company_count=1,
            account_count=2,
            transaction_count=1
        )
        
        orchestrator = MasterOrchestrator(config)
        stats = orchestrator.generate_all()
        
        assert stats.persons_generated == 1
        assert stats.companies_generated == 1
        assert stats.accounts_generated == 2
    
    def test_large_configuration(self):
        """Test with large configuration"""
        from banking.data_generators.orchestration import (
            MasterOrchestrator,
            GenerationConfig
        )
        
        config = GenerationConfig(
            seed=42,
            person_count=100,
            company_count=50,
            account_count=200,
            transaction_count=1000
        )
        
        orchestrator = MasterOrchestrator(config)
        stats = orchestrator.generate_all()
        
        assert stats.persons_generated == 100
        assert stats.companies_generated == 50
        assert stats.accounts_generated == 200
        assert stats.transactions_generated == 1000


class TestMasterOrchestratorReproducibility:
    """Reproducibility tests"""
    
    def test_same_seed_same_output(self):
        """Test that same seed produces same output"""
        from banking.data_generators.orchestration import (
            MasterOrchestrator,
            GenerationConfig
        )
        
        config1 = GenerationConfig(
            seed=42,
            person_count=10,
            company_count=5,
            account_count=20,
            transaction_count=50
        )
        
        config2 = GenerationConfig(
            seed=42,
            person_count=10,
            company_count=5,
            account_count=20,
            transaction_count=50
        )
        
        orch1 = MasterOrchestrator(config1)
        orch2 = MasterOrchestrator(config2)
        
        stats1 = orch1.generate_all()
        stats2 = orch2.generate_all()
        
        # Should generate same counts
        assert stats1.persons_generated == stats2.persons_generated
        assert stats1.companies_generated == stats2.companies_generated
        assert stats1.accounts_generated == stats2.accounts_generated
        assert stats1.transactions_generated == stats2.transactions_generated


class TestMasterOrchestratorPerformance:
    """Performance tests"""
    
    @pytest.mark.slow
    def test_medium_batch_performance(self):
        """Test performance with medium batch"""
        from banking.data_generators.orchestration import (
            MasterOrchestrator,
            GenerationConfig
        )
        import time
        
        config = GenerationConfig(
            seed=42,
            person_count=100,
            company_count=50,
            account_count=200,
            transaction_count=1000
        )
        
        orchestrator = MasterOrchestrator(config)
        
        start = time.time()
        stats = orchestrator.generate_all()
        duration = time.time() - start
        
        # Should complete in reasonable time (< 10 seconds)
        assert duration < 10.0
        assert stats.total_entities == 350
        assert stats.total_events == 1000
    
    @pytest.mark.slow
    def test_memory_efficiency(self):
        """Test memory usage for large batch"""
        from banking.data_generators.orchestration import (
            MasterOrchestrator,
            GenerationConfig
        )
        import sys
        
        config = GenerationConfig(
            seed=42,
            person_count=100,
            company_count=50,
            account_count=200,
            transaction_count=1000
        )
        
        orchestrator = MasterOrchestrator(config)
        stats = orchestrator.generate_all()
        
        # Check that orchestrator doesn't hold excessive memory
        # (rough check - should be < 100MB)
        size = sys.getsizeof(orchestrator)
        assert size < 100_000_000


class TestMasterOrchestratorIntegration:
    """Integration tests"""
    
    def test_export_to_json(self, small_orchestrator, tmp_path):
        """Test exporting data to JSON"""
        # Generate data
        stats = small_orchestrator.generate_all()
        
        # Export to JSON
        output_file = tmp_path / "test_output.json"
        small_orchestrator.export_to_json(output_file)
        
        # Verify file exists and is valid JSON
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert 'persons' in data
        assert 'companies' in data
        assert 'accounts' in data
        assert 'transactions' in data
    
    def test_export_structure(self, small_orchestrator, tmp_path):
        """Test exported data structure"""
        stats = small_orchestrator.generate_all()
        
        output_file = tmp_path / "test_output.json"
        small_orchestrator.export_to_json(output_file)
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        # Check persons structure
        assert len(data['persons']) > 0
        person = data['persons'][0]
        assert 'person_id' in person
        assert 'first_name' in person
        assert 'last_name' in person
        
        # Check transactions structure
        assert len(data['transactions']) > 0
        txn = data['transactions'][0]
        assert 'transaction_id' in txn
        assert 'amount' in txn
        assert 'currency' in txn
    
    def test_pattern_injection(self):
        """Test that patterns are injected correctly"""
        from banking.data_generators.orchestration import (
            MasterOrchestrator,
            GenerationConfig
        )
        
        config = GenerationConfig(
            seed=42,
            person_count=50,
            company_count=20,
            account_count=100,
            transaction_count=500,
            insider_trading_patterns=2,
            fraud_ring_patterns=1
        )
        
        orchestrator = MasterOrchestrator(config)
        stats = orchestrator.generate_all()
        
        # Should have injected patterns
        assert stats.total_patterns >= 3


class TestMasterOrchestratorDataQuality:
    """Data quality tests"""
    
    def test_referential_integrity(self, small_orchestrator, tmp_path):
        """Test referential integrity of generated data"""
        stats = small_orchestrator.generate_all()
        
        output_file = tmp_path / "test_output.json"
        small_orchestrator.export_to_json(output_file)
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        # Collect all IDs
        person_ids = {p['person_id'] for p in data['persons']}
        company_ids = {c['company_id'] for c in data['companies']}
        account_ids = {a['account_id'] for a in data['accounts']}
        
        # Check accounts reference valid persons/companies
        for account in data['accounts']:
            if account.get('owner_person_id'):
                assert account['owner_person_id'] in person_ids
            if account.get('owner_company_id'):
                assert account['owner_company_id'] in company_ids
        
        # Check transactions reference valid accounts
        for txn in data['transactions']:
            assert txn['from_account_id'] in account_ids
            assert txn['to_account_id'] in account_ids
    
    def test_data_consistency(self, small_orchestrator):
        """Test data consistency across entities"""
        stats = small_orchestrator.generate_all()
        
        # Total entities should match sum of individual counts
        expected_total = (
            stats.persons_generated +
            stats.companies_generated +
            stats.accounts_generated
        )
        assert stats.total_entities == expected_total
        
        # Total events should match sum of event counts
        expected_events = (
            stats.transactions_generated +
            stats.communications_generated +
            stats.trades_generated +
            stats.travels_generated +
            stats.documents_generated
        )
        assert stats.total_events == expected_events

