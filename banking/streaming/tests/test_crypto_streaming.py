"""
Tests for Crypto Streaming Integration
=======================================

Tests for crypto event helpers and orchestrator.

Author: AI Assistant
Date: 2026-04-10
"""

import pytest

from banking.streaming.crypto_events import (
    create_crypto_transaction_event,
    create_mixer_detection_event,
    create_sanctions_screening_event,
    create_wallet_event,
)
from banking.streaming.crypto_orchestrator import CryptoStreamingOrchestrator


class TestCryptoEventHelpers:
    """Test crypto event helper functions."""
    
    def test_create_wallet_event(self):
        """Test wallet event creation."""
        wallet_data = {
            "wallet_id": "wallet-TEST123",
            "address": "0x1234567890abcdef",
            "currency": "BTC",
            "wallet_type": "hot",
            "balance": 1.5,
            "is_mixer": False,
            "is_sanctioned": False,
            "risk_score": 0.2,
        }
        
        event = create_wallet_event("wallet-TEST123", wallet_data)
        
        assert event.entity_id == "wallet-TEST123"
        assert event.entity_type == "crypto_wallet"
        assert event.event_type == "create"
        assert event.payload == wallet_data
        assert "BTC" in event.text_for_embedding
        assert "hot" in event.text_for_embedding
        assert event.metadata["currency"] == "BTC"
        assert event.metadata["is_mixer"] is False
    
    def test_create_wallet_event_mixer(self):
        """Test wallet event creation for mixer."""
        wallet_data = {
            "wallet_id": "wallet-MIXER",
            "address": "0xmixer",
            "currency": "ETH",
            "wallet_type": "mixer",
            "balance": 100.0,
            "is_mixer": True,
            "is_sanctioned": False,
            "risk_score": 1.0,
        }
        
        event = create_wallet_event("wallet-MIXER", wallet_data)
        
        assert "MIXER WALLET" in event.text_for_embedding
        assert event.metadata["is_mixer"] is True
        assert event.metadata["risk_score"] == 1.0
    
    def test_create_crypto_transaction_event(self):
        """Test transaction event creation."""
        tx_data = {
            "transaction_id": "ctx-TEST456",
            "from_wallet": "wallet-A",
            "to_wallet": "wallet-B",
            "amount": 0.5,
            "currency": "BTC",
            "transaction_type": "transfer",
            "is_suspicious": False,
            "involves_mixer": False,
        }
        
        event = create_crypto_transaction_event("ctx-TEST456", tx_data)
        
        assert event.entity_id == "ctx-TEST456"
        assert event.entity_type == "crypto_transaction"
        assert event.payload == tx_data
        assert "BTC" in event.text_for_embedding
        assert "transfer" in event.text_for_embedding
        assert event.metadata["amount"] == 0.5
    
    def test_create_mixer_detection_event(self):
        """Test mixer detection event creation."""
        detection_result = {
            "wallet_id": "wallet-TEST",
            "is_mixer": False,
            "has_mixer_interaction": True,
            "risk_score": 0.7,
            "recommendation": "review",
            "closest_mixer_distance": 2,
        }
        
        event = create_mixer_detection_event("wallet-TEST", detection_result)
        
        assert event.entity_id == "detection-wallet-TEST"
        assert event.entity_type == "mixer_detection"
        assert event.metadata["risk_score"] == 0.7
        assert event.metadata["recommendation"] == "review"
        assert "HAS MIXER INTERACTION" in event.text_for_embedding
    
    def test_create_sanctions_screening_event(self):
        """Test sanctions screening event creation."""
        screening_result = {
            "wallet_id": "wallet-TEST",
            "is_sanctioned": False,
            "high_risk_jurisdiction": True,
            "risk_score": 0.6,
            "recommendation": "review",
            "matches": [],
        }
        
        event = create_sanctions_screening_event("wallet-TEST", screening_result)
        
        assert event.entity_id == "screening-wallet-TEST"
        assert event.entity_type == "sanctions_screening"
        assert event.metadata["risk_score"] == 0.6
        assert "HIGH-RISK JURISDICTION" in event.text_for_embedding


class TestCryptoStreamingOrchestrator:
    """Test crypto streaming orchestrator."""
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        config = {
            "seed": 42,
            "wallet_count": 10,
            "transaction_count": 20,
            "mixer_pattern_count": 2,
            "pulsar_url": "pulsar://localhost:6650",
        }
        
        orchestrator = CryptoStreamingOrchestrator(config, use_mock_producer=True)
        
        assert orchestrator.seed == 42
        assert orchestrator.wallet_count == 10
        assert orchestrator.transaction_count == 20
        assert orchestrator.mixer_pattern_count == 2
    
    def test_orchestrator_run_small_scale(self):
        """Test orchestrator with small dataset."""
        config = {
            "seed": 42,
            "wallet_count": 20,  # Need more wallets to ensure mixers are generated
            "transaction_count": 30,
            "mixer_pattern_count": 2,
        }
        
        orchestrator = CryptoStreamingOrchestrator(config, use_mock_producer=True)
        stats = orchestrator.run()
        
        # Verify statistics
        assert stats["wallets_generated"] == 20
        assert stats["patterns_injected"] == 2
        assert stats["mixer_detections"] == 20
        assert stats["sanctions_screenings"] == 20
        
        # Verify events published
        # Note: Pattern injection adds transactions, so total is:
        # wallets + transactions (original + pattern-added) + detections + screenings
        expected_events = (
            stats["wallets_generated"] +
            stats["transactions_generated"] +
            stats["mixer_detections"] +
            stats["sanctions_screenings"]
        )
        assert stats["events_published"] == expected_events
        
        # Verify mock producer received events
        assert orchestrator.producer.send_count == expected_events
        assert len(orchestrator.producer.events) == expected_events
    
    def test_orchestrator_event_types(self):
        """Test that orchestrator publishes all event types."""
        config = {
            "seed": 42,
            "wallet_count": 15,  # Need more wallets for mixers
            "transaction_count": 20,
            "mixer_pattern_count": 2,
        }
        
        orchestrator = CryptoStreamingOrchestrator(config, use_mock_producer=True)
        stats = orchestrator.run()
        
        # Get all events
        events = orchestrator.producer.get_events()
        
        # Count event types
        event_types = {}
        for event in events:
            event_type = event.entity_type
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        # Verify all event types present
        assert "crypto_wallet" in event_types
        assert "crypto_transaction" in event_types
        assert "mixer_detection" in event_types
        assert "sanctions_screening" in event_types
        
        # Verify counts (use actual stats, not hardcoded values)
        assert event_types["crypto_wallet"] == stats["wallets_generated"]
        assert event_types["crypto_transaction"] == stats["transactions_generated"]
        assert event_types["mixer_detection"] == stats["mixer_detections"]
        assert event_types["sanctions_screening"] == stats["sanctions_screenings"]
    
    def test_orchestrator_deterministic(self):
        """Test that orchestrator produces deterministic results."""
        config = {
            "seed": 42,
            "wallet_count": 15,  # Need more wallets for mixers
            "transaction_count": 20,
            "mixer_pattern_count": 2,
        }
        
        # Run twice with same seed
        orchestrator1 = CryptoStreamingOrchestrator(config, use_mock_producer=True)
        stats1 = orchestrator1.run()
        
        orchestrator2 = CryptoStreamingOrchestrator(config, use_mock_producer=True)
        stats2 = orchestrator2.run()
        
        # Verify identical statistics
        assert stats1 == stats2
        
        # Verify identical event counts
        assert len(orchestrator1.producer.events) == len(orchestrator2.producer.events)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
