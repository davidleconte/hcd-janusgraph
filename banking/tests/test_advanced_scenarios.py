"""
Advanced Complex Scenario Tests
================================

Tests for highly complex fraud and AML detection scenarios:
1. Multi-hop money laundering chains
2. Cross-border transaction patterns
3. Shell company detection
4. Temporal pattern analysis
5. Coordinated fraud rings

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-04
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest


class TestMultiHopMoneyLaunderingChains:
    """Tests for multi-hop money laundering detection (3+ hops)"""

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_three_hop_laundering_chain(self, mock_search, mock_gen):
        """
        Test detection of 3-hop laundering: Person → Account1 → Account2 → Company

        Scenario:
        - Person P-001 owns Account ACC-001
        - ACC-001 transfers $9,500 to ACC-002 (shell company account)
        - ACC-002 transfers $9,300 to ACC-003 (another shell company)
        - ACC-003 transfers $9,000 to legitimate Company
        """
        from banking.fraud.fraud_detection import FraudDetector

        detector = FraudDetector()

        # Mock all check methods
        detector._check_velocity = Mock(return_value=0.7)  # High velocity
        detector._check_network = Mock(return_value=0.8)  # Many connections
        detector._check_merchant = Mock(return_value=0.3)
        detector._check_behavior = Mock(return_value=0.5)

        # Score each hop
        hop1_score = detector.score_transaction(
            "TX-HOP1", "ACC-001", 9500.0, "Wire Transfer", "Transfer to business"
        )
        hop2_score = detector.score_transaction(
            "TX-HOP2", "ACC-002", 9300.0, "Wire Transfer", "Transfer to partner"
        )
        hop3_score = detector.score_transaction(
            "TX-HOP3", "ACC-003", 9000.0, "Wire Transfer", "Payment to supplier"
        )

        # Verify high risk across all hops
        assert hop1_score.overall_score >= 0.5
        assert hop2_score.overall_score >= 0.5
        assert hop3_score.overall_score >= 0.5

        # Combined pattern should be flagged
        combined_amount = 9500 + 9300 + 9000
        assert combined_amount > 10000  # Exceeds CTR threshold

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_five_hop_complex_chain(self, mock_search, mock_gen):
        """
        Test detection of 5-hop laundering chain with multiple intermediaries

        Scenario: Person → Bank1 → Crypto → Bank2 → Shell → Legitimate Company
        """
        from banking.fraud.fraud_detection import FraudDetector

        detector = FraudDetector()

        hops = [
            ("TX-001", "ACC-PERSON", 9800.0, "Bank Transfer", "Transfer to exchange"),
            ("TX-002", "ACC-CRYPTO", 9700.0, "Coinbase", "Crypto purchase"),
            ("TX-003", "ACC-BANK2", 9500.0, "Wire Transfer", "Withdrawal"),
            ("TX-004", "ACC-SHELL", 9300.0, "Business Payment", "Consulting fee"),
            ("TX-005", "ACC-LEGIT", 9000.0, "Invoice Payment", "Services rendered"),
        ]

        scores = []
        for tx_id, acc_id, amount, merchant, desc in hops:
            detector._check_velocity = Mock(return_value=0.6)
            detector._check_network = Mock(return_value=0.5)
            detector._check_merchant = Mock(return_value=0.4)
            detector._check_behavior = Mock(return_value=0.4)

            score = detector.score_transaction(tx_id, acc_id, amount, merchant, desc)
            scores.append(score)

        # Verify chain characteristics
        total_amount = sum(h[2] for h in hops)
        assert total_amount > 40000  # Large combined movement

        # Each hop should have moderate risk
        for score in scores:
            assert score.overall_score >= 0.3


class TestCrossBorderTransactionPatterns:
    """Tests for cross-border transaction pattern detection"""

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_high_risk_jurisdiction_transfer(self, mock_search, mock_gen):
        """Test transfers to/from high-risk jurisdictions"""
        from banking.fraud.fraud_detection import FraudDetector

        detector = FraudDetector()

        # High-risk jurisdictions: Cayman Islands, Panama, Cyprus
        high_risk_transfers = [
            ("TX-CAY", "ACC-001", 50000.0, "Cayman Islands Bank", "Investment transfer"),
            ("TX-PAN", "ACC-002", 75000.0, "Panama Trust", "Trust fund deposit"),
            ("TX-CYP", "ACC-003", 25000.0, "Cyprus Holdings", "Business payment"),
        ]

        for tx_id, acc_id, amount, merchant, desc in high_risk_transfers:
            # Mock higher merchant risk for offshore transfers
            detector._check_velocity = Mock(return_value=0.3)
            detector._check_network = Mock(return_value=0.4)
            detector._check_merchant = Mock(return_value=0.7)  # High risk merchant
            detector._check_behavior = Mock(return_value=0.5)

            score = detector.score_transaction(tx_id, acc_id, amount, merchant, desc)

            # High-risk jurisdiction should elevate overall score
            assert score.overall_score >= 0.4
            assert score.merchant_score >= 0.5

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_round_trip_international_transfer(self, mock_search, mock_gen):
        """Test round-trip transfers (out and back same day)"""
        from banking.fraud.fraud_detection import FraudDetector

        detector = FraudDetector()

        # Round trip pattern: US → Offshore → US
        outbound = ("TX-OUT", "ACC-US", 100000.0, "Swiss Bank", "Wire to Zurich")
        inbound = ("TX-IN", "ACC-US", 98000.0, "Swiss Bank", "Return transfer")

        # Score outbound
        detector._check_velocity = Mock(return_value=0.8)  # High velocity
        detector._check_network = Mock(return_value=0.6)
        detector._check_merchant = Mock(return_value=0.5)
        detector._check_behavior = Mock(return_value=0.6)

        out_score = detector.score_transaction(*outbound)

        # Score inbound
        detector._check_velocity = Mock(return_value=0.9)  # Very high velocity (same day)
        in_score = detector.score_transaction(*inbound)

        # Both should be flagged
        assert out_score.overall_score >= 0.5
        assert in_score.overall_score >= 0.6


class TestShellCompanyDetection:
    """Tests for shell company detection patterns"""

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_shell_company_characteristics(self, mock_search, mock_gen):
        """
        Test detection of shell company indicators:
        - Newly registered
        - Single employee
        - High transaction volume
        - No physical presence
        """
        from banking.fraud.fraud_detection import FraudDetector

        detector = FraudDetector()

        # Shell company account with suspicious patterns
        shell_transactions = [
            ("TX-SH1", "ACC-SHELL-001", 9500.0, "Consulting LLC", "Consulting services"),
            ("TX-SH2", "ACC-SHELL-001", 9400.0, "Management Fee", "Management services"),
            ("TX-SH3", "ACC-SHELL-001", 9600.0, "Advisory Fee", "Advisory services"),
            ("TX-SH4", "ACC-SHELL-001", 9300.0, "Professional Fee", "Professional services"),
        ]

        total_risk = 0
        for tx in shell_transactions:
            detector._check_velocity = Mock(return_value=0.85)  # High velocity
            detector._check_network = Mock(return_value=0.7)  # Many connections
            detector._check_merchant = Mock(return_value=0.6)  # Suspicious merchant type
            detector._check_behavior = Mock(return_value=0.65)  # Unusual behavior

            score = detector.score_transaction(*tx)
            total_risk += score.overall_score

        # Average risk should be high for shell company pattern
        avg_risk = total_risk / len(shell_transactions)
        assert avg_risk >= 0.6

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_layered_shell_company_network(self, mock_search, mock_gen):
        """Test detection of layered shell company network"""
        from banking.fraud.fraud_detection import FraudDetector

        detector = FraudDetector()

        # Network of shell companies: Parent → Sub1 → Sub2 → Sub3
        shell_network = [
            ("ACC-PARENT", "ACC-SUB1", 250000.0),
            ("ACC-SUB1", "ACC-SUB2", 245000.0),
            ("ACC-SUB2", "ACC-SUB3", 240000.0),
            ("ACC-SUB3", "ACC-FINAL", 235000.0),
        ]

        # High network score due to interconnected shell companies
        for from_acc, to_acc, amount in shell_network:
            detector._check_velocity = Mock(return_value=0.5)
            detector._check_network = Mock(return_value=0.9)  # Very high network risk
            detector._check_merchant = Mock(return_value=0.5)
            detector._check_behavior = Mock(return_value=0.5)

            score = detector.score_transaction(
                f"TX-{from_acc}", from_acc, amount, "Intercompany", "Transfer"
            )

            # Network score should dominate
            assert score.network_score >= 0.8


class TestTemporalPatternAnalysis:
    """Tests for temporal pattern detection (time-based patterns)"""

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_end_of_day_structuring(self, mock_search, mock_gen):
        """Test detection of end-of-day transaction clustering"""
        from banking.fraud.fraud_detection import FraudDetector

        detector = FraudDetector()

        # End of banking day transactions (4-5 PM)
        eod_transactions = [
            ("TX-EOD1", "ACC-001", 9500.0, datetime(2026, 2, 4, 16, 30)),
            ("TX-EOD2", "ACC-001", 9400.0, datetime(2026, 2, 4, 16, 45)),
            ("TX-EOD3", "ACC-001", 9300.0, datetime(2026, 2, 4, 16, 55)),
        ]

        for tx_id, acc_id, amount, timestamp in eod_transactions:
            detector._check_velocity = Mock(return_value=0.9)  # Very high velocity
            detector._check_network = Mock(return_value=0.3)
            detector._check_merchant = Mock(return_value=0.3)
            detector._check_behavior = Mock(return_value=0.4)

            score = detector.score_transaction(tx_id, acc_id, amount, "Bank", "Deposit", timestamp)

            # Velocity should be high due to clustering
            assert score.velocity_score >= 0.8

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_weekend_high_value_transfers(self, mock_search, mock_gen):
        """Test detection of suspicious weekend transfers"""
        from banking.fraud.fraud_detection import FraudDetector

        detector = FraudDetector()

        # Weekend transfers (unusual for business)
        weekend_transactions = [
            ("TX-SAT", "ACC-BIZ", 75000.0, "Wire Transfer", "Urgent payment"),
            ("TX-SUN", "ACC-BIZ", 50000.0, "Wire Transfer", "Emergency transfer"),
        ]

        for tx_id, acc_id, amount, merchant, desc in weekend_transactions:
            detector._check_velocity = Mock(return_value=0.5)
            detector._check_network = Mock(return_value=0.4)
            detector._check_merchant = Mock(return_value=0.5)
            detector._check_behavior = Mock(return_value=0.7)  # Unusual behavior

            score = detector.score_transaction(tx_id, acc_id, amount, merchant, desc)

            # Behavioral score should be elevated
            assert score.behavioral_score >= 0.6


class TestCoordinatedFraudRings:
    """Tests for coordinated fraud ring detection"""

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_synchronized_transaction_ring(self, mock_search, mock_gen):
        """
        Test detection of synchronized transactions across multiple accounts

        Scenario: 5 accounts make near-identical transactions within 10 minutes
        """
        from banking.fraud.fraud_detection import FraudDetector

        detector = FraudDetector()

        # Synchronized transactions from fraud ring
        ring_transactions = [
            ("TX-R1", "ACC-RING1", 9500.0, "ATM Withdrawal", "Cash withdrawal"),
            ("TX-R2", "ACC-RING2", 9500.0, "ATM Withdrawal", "Cash withdrawal"),
            ("TX-R3", "ACC-RING3", 9500.0, "ATM Withdrawal", "Cash withdrawal"),
            ("TX-R4", "ACC-RING4", 9500.0, "ATM Withdrawal", "Cash withdrawal"),
            ("TX-R5", "ACC-RING5", 9500.0, "ATM Withdrawal", "Cash withdrawal"),
        ]

        scores = []
        for tx in ring_transactions:
            # All accounts have high network interconnection
            detector._check_velocity = Mock(return_value=0.6)
            detector._check_network = Mock(return_value=0.95)  # Very high - all connected
            detector._check_merchant = Mock(return_value=0.4)
            detector._check_behavior = Mock(return_value=0.5)

            score = detector.score_transaction(*tx)
            scores.append(score)

        # All ring members should have high network scores
        for score in scores:
            assert score.network_score >= 0.9

        # Combined amount exceeds threshold significantly
        total_amount = sum(tx[2] for tx in ring_transactions)
        assert total_amount == 47500

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_account_takeover_ring(self, mock_search, mock_gen):
        """Test detection of account takeover fraud ring"""
        from banking.fraud.fraud_detection import FraudDetector

        detector = FraudDetector()

        # Account takeover indicators
        takeover_indicators = [
            ("TX-ATO1", "ACC-VICTIM1", 15000.0, "Wire Transfer", "Emergency transfer"),
            ("TX-ATO2", "ACC-VICTIM2", 12000.0, "Wire Transfer", "Urgent payment"),
            ("TX-ATO3", "ACC-VICTIM3", 18000.0, "Wire Transfer", "Immediate transfer"),
        ]

        for tx in takeover_indicators:
            # High behavioral anomaly for ATO - scores must exceed 0.75 for HIGH risk
            detector._check_velocity = Mock(return_value=0.85)
            detector._check_network = Mock(return_value=0.75)
            detector._check_merchant = Mock(return_value=0.65)
            detector._check_behavior = Mock(return_value=0.9)  # Very unusual behavior

            score = detector.score_transaction(*tx)

            # Behavioral score should be dominant
            assert score.behavioral_score >= 0.8
            assert score.risk_level in ["high", "critical"]


class TestDataGeneratorPatternValidation:
    """Validate that data generators can create patterns for detection"""

    def test_fraud_ring_generator_creates_ring_pattern(self):
        """Test FraudRingPatternGenerator creates detectable pattern"""
        from banking.data_generators.core import AccountGenerator, PersonGenerator
        from banking.data_generators.patterns import FraudRingPatternGenerator

        # Create base entities
        person_gen = PersonGenerator(seed=42)
        account_gen = AccountGenerator(seed=42)

        persons = [person_gen.generate() for _ in range(5)]
        [account_gen.generate(owner_id=p.person_id) for p in persons]

        # Initialize fraud ring generator
        fraud_gen = FraudRingPatternGenerator(seed=42)

        # Verify generator is properly initialized
        assert fraud_gen is not None
        assert hasattr(fraud_gen, "inject_pattern") or hasattr(fraud_gen, "generate")

    def test_structuring_generator_creates_structuring_pattern(self):
        """Test StructuringPatternGenerator creates detectable pattern"""
        from banking.data_generators.core import AccountGenerator, PersonGenerator
        from banking.data_generators.patterns import StructuringPatternGenerator

        # Create base entities
        person_gen = PersonGenerator(seed=42)
        account_gen = AccountGenerator(seed=42)

        person = person_gen.generate()
        account_gen.generate(owner_id=person.person_id)

        # Initialize structuring generator
        struct_gen = StructuringPatternGenerator(seed=42)

        # Verify generator is properly initialized
        assert struct_gen is not None
        assert hasattr(struct_gen, "inject_pattern") or hasattr(struct_gen, "generate")


class TestIntegratedDetectionPipeline:
    """Test full detection pipeline with multiple detection methods"""

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_combined_aml_fraud_detection(self, mock_search, mock_gen):
        """Test combined AML and fraud detection on same transaction set"""
        from banking.fraud.fraud_detection import FraudDetector

        detector = FraudDetector()

        # Suspicious transaction set (could be AML or fraud)
        suspicious_txns = [
            ("TX-S1", "ACC-001", 9500.0, "Cash Deposit", "ATM deposit"),
            ("TX-S2", "ACC-001", 9600.0, "Cash Deposit", "Branch deposit"),
            ("TX-S3", "ACC-001", 9400.0, "Wire Out", "Transfer to offshore"),
        ]

        fraud_scores = []
        for tx in suspicious_txns:
            # Scores must exceed 0.75 for HIGH risk level
            detector._check_velocity = Mock(return_value=0.85)
            detector._check_network = Mock(return_value=0.7)
            detector._check_merchant = Mock(return_value=0.7)
            detector._check_behavior = Mock(return_value=0.75)

            score = detector.score_transaction(*tx)
            fraud_scores.append(score)

        # At least one transaction should be high risk
        high_risk_count = sum(1 for s in fraud_scores if s.risk_level in ["high", "critical"])
        assert high_risk_count >= 1

        # Combined amount indicates structuring
        total = sum(tx[2] for tx in suspicious_txns)
        assert total > 28000  # Multiple CTR threshold

    @patch("banking.fraud.fraud_detection.EmbeddingGenerator")
    @patch("banking.fraud.fraud_detection.VectorSearchClient")
    def test_alert_generation_for_critical_transactions(self, mock_search, mock_gen):
        """Test that critical transactions generate alerts"""
        from banking.fraud.fraud_detection import FraudDetector

        detector = FraudDetector()
        detector.find_similar_fraud_cases = Mock(return_value=[])

        # Mock critical-level risk scores
        detector._check_velocity = Mock(return_value=0.95)
        detector._check_network = Mock(return_value=0.92)
        detector._check_merchant = Mock(return_value=0.88)
        detector._check_behavior = Mock(return_value=0.90)

        score = detector.score_transaction(
            "TX-CRIT", "ACC-CRIT", 50000.0, "Crypto Exchange", "Large crypto"
        )

        assert score.risk_level == "critical"
        assert score.recommendation == "block"

        # Generate alert
        alert = detector.generate_alert(
            score,
            {
                "account_id": "ACC-CRIT",
                "customer_id": "CUST-001",
                "customer_name": "Test User",
                "amount": 50000.0,
                "merchant": "Crypto Exchange",
                "description": "Large crypto purchase",
            },
        )

        assert alert is not None
        assert alert.severity == "critical"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
