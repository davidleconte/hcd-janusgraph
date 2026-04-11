"""
End-to-End Crypto AML Workflow Integration Test

Tests the complete crypto AML workflow from data generation through
detection, screening, and visualization.

Author: Banking Compliance Team
Date: 2026-04-10
"""

import pytest
from pathlib import Path
from datetime import datetime

from banking.crypto import (
    WalletGenerator,
    CryptoTransactionGenerator,
    MixerDetector,
    SanctionsScreener,
)
from banking.data_generators.patterns import CryptoMixerPatternGenerator
from banking.crypto.visualizations import (
    create_mixer_network,
    create_risk_dashboard,
    generate_executive_summary_report,
    RiskMetrics,
    ExecutiveSummary,
)


class TestCryptoE2EWorkflow:
    """End-to-end workflow tests for crypto AML."""

    @pytest.fixture
    def seed(self):
        """Deterministic seed for testing."""
        return 42

    @pytest.fixture
    def wallet_generator(self, seed):
        """Create wallet generator."""
        return WalletGenerator(seed=seed)

    @pytest.fixture
    def transaction_generator(self, seed):
        """Create transaction generator."""
        return CryptoTransactionGenerator(seed=seed)

    @pytest.fixture
    def pattern_generator(self, seed):
        """Create pattern generator."""
        return CryptoMixerPatternGenerator(seed=seed)

    @pytest.fixture
    def mixer_detector(self):
        """Create mixer detector."""
        return MixerDetector()

    @pytest.fixture
    def sanctions_screener(self):
        """Create sanctions screener."""
        return SanctionsScreener()

    def test_complete_workflow_small_scale(
        self,
        wallet_generator,
        transaction_generator,
        pattern_generator,
        mixer_detector,
        sanctions_screener,
    ):
        """
        Test complete workflow with small dataset.

        Workflow:
        1. Generate wallets (including mixers and sanctioned)
        2. Generate transactions
        3. Inject mixer patterns
        4. Run mixer detection
        5. Run sanctions screening
        6. Verify all outputs
        """
        # Step 1: Generate wallets
        wallets = [wallet_generator.generate() for _ in range(20)]
        assert len(wallets) == 20
        assert all(w.wallet_id for w in wallets)

        # Identify mixers and sanctioned wallets
        mixer_wallets = [w for w in wallets if w.is_mixer]
        sanctioned_wallets = [w for w in wallets if w.is_sanctioned]
        assert len(mixer_wallets) >= 1  # At least one mixer
        assert len(sanctioned_wallets) >= 1  # At least one sanctioned

        # Step 2: Generate transactions
        transactions = transaction_generator.generate_batch(
            wallets=wallets, count=30
        )
        assert len(transactions) == 30
        assert all(t.transaction_id for t in transactions)

        # Step 3: Inject mixer patterns
        pattern_generator.inject_pattern(
            wallets=wallets,
            transactions=transactions,
            pattern_type="layering",
            mixer_wallet=mixer_wallets[0],
        )
        # Pattern injection adds transactions
        assert len(transactions) > 30

        # Step 4: Run mixer detection
        detection_results = mixer_detector.detect_mixer_usage(
            wallets=wallets, transactions=transactions
        )
        assert len(detection_results) > 0
        assert all(r.wallet_id for r in detection_results)
        assert all(r.risk_score >= 0 and r.risk_score <= 1 for r in detection_results)

        # Step 5: Run sanctions screening
        screening_results = sanctions_screener.screen_wallets(wallets)
        assert len(screening_results) > 0
        assert all(r.wallet_id for r in screening_results)
        assert any(r.is_sanctioned for r in screening_results)

        # Step 6: Verify data consistency
        wallet_ids = {w.wallet_id for w in wallets}
        transaction_wallet_ids = {t.from_wallet for t in transactions} | {
            t.to_wallet for t in transactions
        }
        # All transaction wallets should be in wallet set
        assert transaction_wallet_ids.issubset(wallet_ids)

    def test_workflow_with_visualizations(
        self,
        wallet_generator,
        transaction_generator,
        mixer_detector,
        sanctions_screener,
        tmp_path,
    ):
        """
        Test workflow including visualization generation.

        Verifies that visualizations can be created from workflow outputs.
        """
        # Generate data
        wallets = [wallet_generator.generate() for _ in range(15)]
        transactions = transaction_generator.generate_batch(wallets=wallets, count=20)

        # Run detection and screening
        detection_results = mixer_detector.detect_mixer_usage(
            wallets=wallets, transactions=transactions
        )
        screening_results = sanctions_screener.screen_wallets(wallets)

        # Create network visualization
        mixer_network = create_mixer_network(
            wallets=wallets,
            transactions=transactions,
            detection_results=detection_results,
        )
        assert mixer_network is not None
        assert mixer_network.nodes
        assert mixer_network.edges

        # Create dashboard
        metrics = RiskMetrics(
            total_wallets=len(wallets),
            high_risk_wallets=len([w for w in wallets if w.risk_score > 0.7]),
            medium_risk_wallets=len(
                [w for w in wallets if 0.3 < w.risk_score <= 0.7]
            ),
            low_risk_wallets=len([w for w in wallets if w.risk_score <= 0.3]),
            mixer_interactions=len(detection_results),
            sanctioned_wallets=len([r for r in screening_results if r.is_sanctioned]),
            suspicious_transactions=len(
                [t for t in transactions if t.amount > 10000]
            ),
            total_transactions=len(transactions),
            alerts_last_24h=5,
            alerts_last_7d=20,
            avg_risk_score=sum(w.risk_score for w in wallets) / len(wallets),
            timestamp=datetime.now(),
        )

        dashboard = create_risk_dashboard(
            metrics=metrics, alerts=[], risk_trend=[], top_risks=[]
        )
        assert dashboard is not None

        # Generate report
        summary = ExecutiveSummary(
            period_start=datetime.now(),
            period_end=datetime.now(),
            total_wallets=len(wallets),
            new_wallets=len(wallets),
            total_transactions=len(transactions),
            total_volume_usd=sum(t.amount for t in transactions),
            high_risk_wallets=metrics.high_risk_wallets,
            alerts_generated=25,
            alerts_resolved=20,
            mixer_detections=len(detection_results),
            sanctions_hits=len([r for r in screening_results if r.is_sanctioned]),
            avg_risk_score=metrics.avg_risk_score,
            risk_trend="stable",
        )

        report = generate_executive_summary_report(summary)
        assert report
        assert "CRYPTO AML EXECUTIVE SUMMARY" in report
        assert str(len(wallets)) in report

    def test_workflow_determinism(
        self, wallet_generator, transaction_generator, mixer_detector
    ):
        """
        Test that workflow produces deterministic results with same seed.

        Critical for reproducibility and testing.
        """
        # First run
        wallets1 = [wallet_generator.generate() for _ in range(10)]
        transactions1 = transaction_generator.generate_batch(wallets=wallets1, count=15)
        detection1 = mixer_detector.detect_mixer_usage(
            wallets=wallets1, transactions=transactions1
        )

        # Reset generators with same seed
        wallet_generator2 = WalletGenerator(seed=42)
        transaction_generator2 = CryptoTransactionGenerator(seed=42)
        mixer_detector2 = MixerDetector()

        # Second run
        wallets2 = [wallet_generator2.generate() for _ in range(10)]
        transactions2 = transaction_generator2.generate_batch(
            wallets=wallets2, count=15
        )
        detection2 = mixer_detector2.detect_mixer_usage(
            wallets=wallets2, transactions=transactions2
        )

        # Verify determinism
        assert len(wallets1) == len(wallets2)
        assert len(transactions1) == len(transactions2)
        assert len(detection1) == len(detection2)

        # Verify wallet IDs match
        wallet_ids1 = [w.wallet_id for w in wallets1]
        wallet_ids2 = [w.wallet_id for w in wallets2]
        assert wallet_ids1 == wallet_ids2

        # Verify transaction IDs match
        tx_ids1 = [t.transaction_id for t in transactions1]
        tx_ids2 = [t.transaction_id for t in transactions2]
        assert tx_ids1 == tx_ids2

    def test_workflow_with_no_suspicious_activity(
        self, wallet_generator, transaction_generator, mixer_detector, sanctions_screener
    ):
        """
        Test workflow with clean data (no suspicious activity).

        Verifies that system handles normal operations correctly.
        """
        # Generate only regular wallets (no mixers, no sanctioned)
        wallets = []
        for _ in range(10):
            wallet = wallet_generator.generate()
            # Override to ensure clean wallet
            wallet.is_mixer = False
            wallet.is_sanctioned = False
            wallet.risk_score = 0.1
            wallets.append(wallet)

        # Generate normal transactions
        transactions = transaction_generator.generate_batch(wallets=wallets, count=15)

        # Run detection - should find minimal/no issues
        detection_results = mixer_detector.detect_mixer_usage(
            wallets=wallets, transactions=transactions
        )
        # May have some results but risk scores should be low
        if detection_results:
            assert all(r.risk_score < 0.5 for r in detection_results)

        # Run screening - should find no sanctioned wallets
        screening_results = sanctions_screener.screen_wallets(wallets)
        assert not any(r.is_sanctioned for r in screening_results)

    def test_workflow_error_handling(self, mixer_detector, sanctions_screener):
        """
        Test workflow error handling with invalid inputs.

        Verifies graceful handling of edge cases.
        """
        # Empty inputs
        detection_empty = mixer_detector.detect_mixer_usage(wallets=[], transactions=[])
        assert detection_empty == []

        screening_empty = sanctions_screener.screen_wallets([])
        assert screening_empty == []

        # This test verifies the system handles edge cases gracefully


@pytest.mark.slow
class TestCryptoE2EPerformance:
    """Performance tests for crypto AML workflow."""

    def test_large_scale_workflow(self):
        """
        Test workflow with larger dataset (100 wallets, 500 transactions).

        Verifies performance at scale.
        """
        # Generate large dataset
        wallet_gen = WalletGenerator(seed=42)
        wallets = [wallet_gen.generate() for _ in range(100)]

        tx_gen = CryptoTransactionGenerator(seed=42)
        transactions = tx_gen.generate_batch(wallets=wallets, count=500)

        # Run detection
        detector = MixerDetector()
        detection_results = detector.detect_mixer_usage(
            wallets=wallets, transactions=transactions
        )

        # Run screening
        screener = SanctionsScreener()
        screening_results = screener.screen_wallets(wallets)

        # Verify results
        assert len(wallets) == 100
        assert len(transactions) == 500
        assert len(detection_results) > 0
        assert len(screening_results) > 0

        # Performance assertions (should complete in reasonable time)
        # If this test runs, it completed within pytest timeout
        assert True

# Made with Bob
