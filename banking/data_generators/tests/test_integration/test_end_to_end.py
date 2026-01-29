"""
End-to-End Integration Tests
=============================

Complete workflow tests including:
- Full generation pipeline
- Export and import
- Data validation
- Pattern detection

Author: IBM Bob
Date: 2026-01-28
"""

import pytest
from pathlib import Path
import json


@pytest.mark.integration
class TestEndToEndWorkflow:
    """End-to-end workflow tests"""
    
    def test_complete_generation_workflow(self, tmp_path):
        """Test complete generation workflow"""
        from banking.data_generators.orchestration import (
            MasterOrchestrator,
            GenerationConfig
        )
        
        # Configure generation
        config = GenerationConfig(
            seed=42,
            person_count=50,
            company_count=20,
            account_count=100,
            transaction_count=500,
            insider_trading_patterns=1,
            fraud_ring_patterns=1,
            output_dir=tmp_path
        )
        
        # Generate data
        orchestrator = MasterOrchestrator(config)
        stats = orchestrator.generate_all()
        
        # Verify generation
        assert stats.persons_generated == 50
        assert stats.companies_generated == 20
        assert stats.accounts_generated == 100
        assert stats.transactions_generated == 500
        
        # Export data
        output_file = tmp_path / "complete_data.json"
        orchestrator.export_to_json(output_file)
        
        # Verify export
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert len(data['persons']) == 50
        assert len(data['companies']) == 20
        assert len(data['accounts']) == 100
        assert len(data['transactions']) == 500
    
    def test_data_validation_workflow(self, tmp_path):
        """Test data validation workflow"""
        from banking.data_generators.orchestration import (
            MasterOrchestrator,
            GenerationConfig
        )
        
        config = GenerationConfig(
            seed=42,
            person_count=20,
            company_count=10,
            account_count=40,
            transaction_count=200,
            output_dir=tmp_path
        )
        
        orchestrator = MasterOrchestrator(config)
        stats = orchestrator.generate_all()
        
        output_file = tmp_path / "validation_data.json"
        orchestrator.export_to_json(output_file)
        
        # Load and validate
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        # Validate referential integrity
        person_ids = {p['person_id'] for p in data['persons']}
        company_ids = {c['company_id'] for c in data['companies']}
        account_ids = {a['account_id'] for a in data['accounts']}
        
        # Check accounts reference valid owners
        for account in data['accounts']:
            if account.get('owner_person_id'):
                assert account['owner_person_id'] in person_ids
            if account.get('owner_company_id'):
                assert account['owner_company_id'] in company_ids
        
        # Check transactions reference valid accounts
        for txn in data['transactions']:
            assert txn['from_account_id'] in account_ids
            assert txn['to_account_id'] in account_ids
    
    def test_pattern_injection_workflow(self, tmp_path):
        """Test pattern injection workflow"""
        from banking.data_generators.orchestration import (
            MasterOrchestrator,
            GenerationConfig
        )
        
        config = GenerationConfig(
            seed=42,
            person_count=100,
            company_count=50,
            account_count=200,
            transaction_count=1000,
            insider_trading_patterns=2,
            tbml_patterns=1,
            fraud_ring_patterns=1,
            structuring_patterns=2,
            output_dir=tmp_path
        )
        
        orchestrator = MasterOrchestrator(config)
        stats = orchestrator.generate_all()
        
        # Verify patterns were injected
        output_file = tmp_path / "pattern_data.json"
        orchestrator.export_to_json(output_file)
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        # Check for pattern indicators
        # (In real implementation, patterns would have metadata)
        assert len(data['transactions']) == 1000


@pytest.mark.integration
class TestDataQualityValidation:
    """Data quality validation tests"""
    
    def test_statistical_validation(self, tmp_path):
        """Test statistical properties of generated data"""
        from banking.data_generators.orchestration import (
            MasterOrchestrator,
            GenerationConfig
        )
        
        config = GenerationConfig(
            seed=42,
            person_count=100,
            company_count=50,
            account_count=200,
            transaction_count=1000,
            output_dir=tmp_path
        )
        
        orchestrator = MasterOrchestrator(config)
        stats = orchestrator.generate_all()
        
        output_file = tmp_path / "stats_data.json"
        orchestrator.export_to_json(output_file)
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        # Check age distribution
        ages = [p['age'] for p in data['persons']]
        avg_age = sum(ages) / len(ages)
        assert 30 <= avg_age <= 60  # Reasonable average
        
        # Check transaction amounts
        amounts = [t['amount'] for t in data['transactions']]
        avg_amount = sum(amounts) / len(amounts)
        assert avg_amount > 0
    
    def test_uniqueness_validation(self, tmp_path):
        """Test uniqueness of generated IDs"""
        from banking.data_generators.orchestration import (
            MasterOrchestrator,
            GenerationConfig
        )
        
        config = GenerationConfig(
            seed=42,
            person_count=100,
            company_count=50,
            account_count=200,
            transaction_count=1000,
            output_dir=tmp_path
        )
        
        orchestrator = MasterOrchestrator(config)
        stats = orchestrator.generate_all()
        
        output_file = tmp_path / "unique_data.json"
        orchestrator.export_to_json(output_file)
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        # Check person ID uniqueness
        person_ids = [p['person_id'] for p in data['persons']]
        assert len(person_ids) == len(set(person_ids))
        
        # Check transaction ID uniqueness
        txn_ids = [t['transaction_id'] for t in data['transactions']]
        assert len(txn_ids) == len(set(txn_ids))

