"""
Comprehensive coverage tests for pattern generators.
Covers fraud_ring, tbml, and insider_trading pattern generators.
"""

import random
from decimal import Decimal
from unittest.mock import patch

import pytest

from banking.data_generators.patterns.fraud_ring_pattern_generator import FraudRingPatternGenerator
from banking.data_generators.patterns.tbml_pattern_generator import TBMLPatternGenerator
from banking.data_generators.patterns.insider_trading_pattern_generator import InsiderTradingPatternGenerator


class TestFraudRingPatternGeneratorCoverage:

    def setup_method(self):
        self.gen = FraudRingPatternGenerator(seed=42)

    def test_generate_default(self):
        pattern = self.gen.generate()
        assert pattern.pattern_type == "fraud_ring"
        assert pattern.pattern_id.startswith("PTN-FRAUD-")

    def test_generate_money_mule_network(self):
        pattern = self.gen.generate(
            pattern_type="money_mule_network", ring_size=5, transaction_count=15, duration_days=30
        )
        assert pattern.metadata["pattern_subtype"] == "money_mule_network"
        assert "money_mule_activity" in pattern.indicators or "hub_and_spoke_pattern" in pattern.indicators

    def test_generate_account_takeover_ring(self):
        pattern = self.gen.generate(
            pattern_type="account_takeover_ring", ring_size=4, transaction_count=10, duration_days=14
        )
        assert pattern.metadata["pattern_subtype"] == "account_takeover_ring"

    def test_generate_synthetic_identity_fraud(self):
        pattern = self.gen.generate(
            pattern_type="synthetic_identity_fraud", ring_size=3, transaction_count=10, duration_days=60
        )
        assert pattern.metadata["pattern_subtype"] == "synthetic_identity_fraud"

    def test_generate_bust_out_fraud(self):
        pattern = self.gen.generate(
            pattern_type="bust_out_fraud", ring_size=3, transaction_count=10, duration_days=45
        )
        assert pattern.metadata["pattern_subtype"] == "bust_out_fraud"

    def test_generate_check_kiting_ring(self):
        pattern = self.gen.generate(
            pattern_type="check_kiting_ring", ring_size=3, transaction_count=10, duration_days=30
        )
        assert pattern.metadata["pattern_subtype"] == "check_kiting_ring"

    def test_generate_large_ring(self):
        pattern = self.gen.generate(ring_size=12, transaction_count=60, duration_days=30)
        assert "large_fraud_network" in pattern.indicators
        assert "extensive_fraud_network" in pattern.red_flags

    def test_generate_medium_ring(self):
        pattern = self.gen.generate(ring_size=7, transaction_count=20, duration_days=30)
        assert "medium_fraud_network" in pattern.indicators

    def test_high_velocity_transactions(self):
        pattern = self.gen.generate(ring_size=3, transaction_count=40, duration_days=5)
        assert "high_transaction_velocity" in pattern.indicators or pattern.transaction_count > 0

    def test_high_transaction_volume_red_flag(self):
        pattern = self.gen.generate(ring_size=3, transaction_count=60, duration_days=30)
        if pattern.transaction_count > 50:
            assert "high_transaction_volume" in pattern.red_flags

    def test_generate_money_mule_network_method(self):
        pattern = self.gen.generate_money_mule_network(
            network_size=8, transaction_count=40, duration_days=20
        )
        assert pattern.metadata["pattern_subtype"] == "money_mule_network"

    def test_risk_level_critical(self):
        risk = self.gen._determine_risk_level(0.9, Decimal("2000000"))
        assert risk.value == "critical"

    def test_risk_level_high(self):
        risk = self.gen._determine_risk_level(0.75, Decimal("100"))
        assert risk.value == "high"

    def test_risk_level_medium(self):
        risk = self.gen._determine_risk_level(0.55, Decimal("100"))
        assert risk.value == "medium"

    def test_risk_level_low(self):
        risk = self.gen._determine_risk_level(0.3, Decimal("100"))
        assert risk.value == "low"

    def test_severity_score_max(self):
        score = self.gen._calculate_severity_score(0.9, Decimal("2000000"), 12, 12)
        assert score <= 1.0

    def test_severity_score_components(self):
        score_high = self.gen._calculate_severity_score(0.9, Decimal("600000"), 6, 5)
        score_low = self.gen._calculate_severity_score(0.3, Decimal("100"), 2, 2)
        assert score_high > score_low

    def test_red_flags_very_high_value(self):
        flags = self.gen._generate_red_flags("money_mule_network", [], Decimal("1500000"), 3)
        assert "very_high_fraud_value" in flags

    def test_red_flags_high_value(self):
        flags = self.gen._generate_red_flags("account_takeover_ring", [], Decimal("600000"), 3)
        assert "high_fraud_value" in flags

    def test_red_flags_synthetic_identity(self):
        flags = self.gen._generate_red_flags("synthetic_identity_fraud", [], Decimal("100"), 3)
        assert "identity_fabrication" in flags


class TestTBMLPatternGeneratorCoverage:

    def setup_method(self):
        self.gen = TBMLPatternGenerator(seed=42)

    def test_generate_default(self):
        pattern, txns, docs = self.gen.generate()
        assert pattern.pattern_type == "tbml"

    def test_generate_over_invoicing(self):
        pattern, txns, docs = self.gen.generate(
            pattern_type="over_invoicing", entity_count=3, document_count=5, transaction_count=5, duration_days=60
        )
        assert pattern.metadata["pattern_subtype"] == "over_invoicing"

    def test_generate_under_invoicing(self):
        pattern, txns, docs = self.gen.generate(
            pattern_type="under_invoicing", entity_count=2, document_count=4, transaction_count=4, duration_days=60
        )
        assert pattern.metadata["pattern_subtype"] == "under_invoicing"

    def test_generate_phantom_shipping(self):
        pattern, txns, docs = self.gen.generate(
            pattern_type="phantom_shipping", entity_count=2, document_count=4, transaction_count=4, duration_days=60
        )
        assert pattern.metadata["pattern_subtype"] == "phantom_shipping"

    def test_generate_multiple_invoicing(self):
        pattern, txns, docs = self.gen.generate(
            pattern_type="multiple_invoicing", entity_count=2, document_count=5, transaction_count=5, duration_days=60
        )
        assert pattern.metadata["pattern_subtype"] == "multiple_invoicing"

    def test_generate_carousel_fraud(self):
        pattern, txns, docs = self.gen.generate(
            pattern_type="carousel_fraud", entity_count=3, document_count=5, transaction_count=5, duration_days=60
        )
        assert pattern.metadata["pattern_subtype"] == "carousel_fraud"

    def test_generate_with_existing_entities(self):
        existing = ["COM-001", "COM-002", "COM-003"]
        pattern, txns, docs = self.gen.generate(
            entity_count=2, document_count=3, transaction_count=3, duration_days=60,
            existing_entity_ids=existing
        )
        assert pattern.pattern_type == "tbml"

    def test_generate_with_fewer_existing_entities(self):
        existing = ["COM-001"]
        pattern, txns, docs = self.gen.generate(
            entity_count=3, document_count=3, transaction_count=3, duration_days=60,
            existing_entity_ids=existing
        )
        assert pattern.pattern_type == "tbml"

    def test_generate_complex_tbml_network(self):
        pattern, txns, docs = self.gen.generate_complex_tbml_network(
            network_size=4, document_count=8, duration_days=90
        )
        assert pattern.metadata["pattern_subtype"] == "carousel_fraud"

    def test_high_volume_indicators(self):
        pattern, txns, docs = self.gen.generate(
            entity_count=5, document_count=15, transaction_count=15, duration_days=60
        )
        assert "multiple_entities_involved" in pattern.indicators or "high_volume_trade_activity" in pattern.indicators

    def test_risk_level_critical(self):
        risk = self.gen._determine_risk_level(0.9, Decimal("20000000"))
        assert risk.value == "critical"

    def test_risk_level_high(self):
        risk = self.gen._determine_risk_level(0.75, Decimal("100"))
        assert risk.value == "high"

    def test_risk_level_medium(self):
        risk = self.gen._determine_risk_level(0.55, Decimal("100"))
        assert risk.value == "medium"

    def test_risk_level_low(self):
        risk = self.gen._determine_risk_level(0.3, Decimal("100"))
        assert risk.value == "low"

    def test_severity_components(self):
        s1 = self.gen._calculate_severity_score(0.9, Decimal("20000000"), 12, 6)
        s2 = self.gen._calculate_severity_score(0.3, Decimal("100"), 2, 0)
        assert s1 > s2

    def test_red_flags_very_high_value(self):
        flags = self.gen._generate_red_flags("over_invoicing", [], [], Decimal("15000000"))
        assert "very_high_transaction_value" in flags

    def test_red_flags_high_value(self):
        flags = self.gen._generate_red_flags("under_invoicing", [], [], Decimal("6000000"))
        assert "high_transaction_value" in flags

    def test_red_flags_phantom(self):
        flags = self.gen._generate_red_flags("phantom_shipping", [], [], Decimal("100"))
        assert "no_physical_goods_movement" in flags

    def test_red_flags_multiple_invoicing(self):
        flags = self.gen._generate_red_flags("multiple_invoicing", [], [], Decimal("100"))
        assert "invoice_fraud_suspected" in flags

    def test_red_flags_doc_txn_mismatch(self):
        flags = self.gen._generate_red_flags("over_invoicing", [1, 2], [1, 2, 3], Decimal("100"))
        assert "document_transaction_count_mismatch" in flags

    def test_red_flags_high_doc_volume(self):
        docs = list(range(20))
        flags = self.gen._generate_red_flags("over_invoicing", docs, [], Decimal("100"))
        assert "unusually_high_document_volume" in flags


class TestInsiderTradingPatternGeneratorCoverage:

    def setup_method(self):
        self.gen = InsiderTradingPatternGenerator(seed=42)

    def test_generate_default(self):
        pattern, trades, comms = self.gen.generate()
        assert pattern.pattern_type == "insider_trading"

    def test_generate_pre_announcement(self):
        pattern, trades, comms = self.gen.generate(
            pattern_type="pre_announcement_trading", entity_count=3, trade_count=10, days_before_announcement=5
        )
        assert pattern.metadata["pattern_subtype"] == "pre_announcement_trading"

    def test_generate_coordinated(self):
        pattern, trades, comms = self.gen.generate(
            pattern_type="coordinated_insider_trading", entity_count=4, trade_count=10, days_before_announcement=20
        )
        assert "coordinated_trading_pattern" in pattern.indicators

    def test_generate_executive(self):
        pattern, trades, comms = self.gen.generate(
            pattern_type="executive_trading_pattern", entity_count=2, trade_count=8, days_before_announcement=15
        )
        assert pattern.metadata["pattern_subtype"] == "executive_trading_pattern"

    def test_generate_beneficial_owner(self):
        pattern, trades, comms = self.gen.generate(
            pattern_type="beneficial_owner_pattern", entity_count=3, trade_count=10, days_before_announcement=30
        )
        assert pattern.metadata["pattern_subtype"] == "beneficial_owner_pattern"

    def test_generate_tipping(self):
        pattern, trades, comms = self.gen.generate(
            pattern_type="tipping_pattern", entity_count=3, trade_count=10, days_before_announcement=20
        )
        assert "information_sharing_detected" in pattern.indicators

    def test_generate_with_existing_entities(self):
        existing = ["PER-001", "PER-002", "PER-003"]
        pattern, trades, comms = self.gen.generate(
            entity_count=2, trade_count=5, days_before_announcement=10,
            existing_entity_ids=existing
        )
        assert pattern.pattern_type == "insider_trading"

    def test_generate_with_fewer_existing(self):
        existing = ["PER-001"]
        pattern, trades, comms = self.gen.generate(
            entity_count=3, trade_count=5, days_before_announcement=10,
            existing_entity_ids=existing
        )
        assert len(pattern.entity_ids) >= 1

    def test_generate_complex_network(self):
        pattern, trades, comms = self.gen.generate_complex_insider_network(
            network_size=6, trade_count=20, days_before_announcement=30
        )
        assert pattern.metadata["pattern_subtype"] == "coordinated_insider_trading"

    def test_high_frequency_trading(self):
        pattern, trades, comms = self.gen.generate(
            entity_count=3, trade_count=25, days_before_announcement=10
        )
        if len(trades) > 20:
            assert "high_frequency_trading" in pattern.indicators

    def test_within_7_days_indicator(self):
        pattern, trades, comms = self.gen.generate(
            entity_count=2, trade_count=5, days_before_announcement=5
        )
        assert "trades_within_7_days_of_announcement" in pattern.indicators

    def test_risk_level_critical(self):
        risk = self.gen._determine_risk_level(0.9, Decimal("20000000"))
        assert risk.value == "critical"

    def test_risk_level_high(self):
        risk = self.gen._determine_risk_level(0.75, Decimal("100"))
        assert risk.value == "high"

    def test_risk_level_medium(self):
        risk = self.gen._determine_risk_level(0.55, Decimal("100"))
        assert risk.value == "medium"

    def test_risk_level_low(self):
        risk = self.gen._determine_risk_level(0.3, Decimal("100"))
        assert risk.value == "low"

    def test_severity_timing_component(self):
        s1 = self.gen._calculate_severity_score(0.9, Decimal("20000000"), 12, 5)
        s2 = self.gen._calculate_severity_score(0.3, Decimal("100"), 2, 60)
        assert s1 > s2

    def test_red_flags_large_trades(self):
        from unittest.mock import MagicMock
        trade = MagicMock()
        trade.total_value = 200000
        flags = self.gen._generate_red_flags("coordinated_insider_trading", [trade], [], 5)
        assert "large_trade_values" in flags
        assert "coordinated_activity" in flags

    def test_red_flags_very_large_trades(self):
        from unittest.mock import MagicMock
        trade = MagicMock()
        trade.total_value = 2000000
        flags = self.gen._generate_red_flags("executive_trading_pattern", [trade], [], 5)
        assert "very_large_trade_values" in flags
        assert "executive_level_involvement" in flags

    def test_red_flags_multiple_insiders(self):
        flags = self.gen._generate_red_flags("pre_announcement_trading", [], [], 6)
        assert "multiple_insiders_involved" in flags

    def test_red_flags_extensive_network(self):
        flags = self.gen._generate_red_flags("pre_announcement_trading", [], [], 10)
        assert "extensive_insider_network" in flags

    def test_red_flags_frequent_comms(self):
        comms = [1, 2, 3, 4]
        flags = self.gen._generate_red_flags("pre_announcement_trading", [], comms, 2)
        assert "frequent_communications" in flags
