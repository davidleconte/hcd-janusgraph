"""
Tests for SanctionsScreener

Tests sanctions screening functionality including:
- Direct sanctions list matching (OFAC, UN, EU)
- High-risk jurisdiction detection
- Suspicious pattern detection
- Risk score calculation
- Recommendation generation
- Batch screening
- Statistics calculation
"""

import pytest

from banking.crypto.sanctions_screener import (
    SanctionsScreener,
    SanctionsMatch,
    SanctionsScreeningResult,
    REFERENCE_TIMESTAMP,
)


class TestSanctionsMatch:
    """Test SanctionsMatch dataclass."""

    def test_create_sanctions_match(self):
        """Test creating a SanctionsMatch."""
        match = SanctionsMatch(
            wallet_id="wallet-1",
            sanctions_list="OFAC_SDN",
            match_type="direct",
            match_details="Wallet on OFAC SDN list",
        )

        assert match.wallet_id == "wallet-1"
        assert match.sanctions_list == "OFAC_SDN"
        assert match.match_type == "direct"
        assert match.match_details == "Wallet on OFAC SDN list"
        assert match.timestamp == REFERENCE_TIMESTAMP

    def test_sanctions_match_to_dict(self):
        """Test converting SanctionsMatch to dictionary."""
        match = SanctionsMatch(
            wallet_id="wallet-1",
            sanctions_list="UN_SANCTIONS",
            match_type="direct",
            match_details="Wallet on UN sanctions list",
        )

        match_dict = match.to_dict()

        assert match_dict["wallet_id"] == "wallet-1"
        assert match_dict["sanctions_list"] == "UN_SANCTIONS"
        assert match_dict["match_type"] == "direct"
        assert "timestamp" in match_dict


class TestSanctionsScreeningResult:
    """Test SanctionsScreeningResult dataclass."""

    def test_create_screening_result(self):
        """Test creating a SanctionsScreeningResult."""
        match = SanctionsMatch(
            wallet_id="wallet-1",
            sanctions_list="OFAC_SDN",
            match_type="direct",
            match_details="Wallet on OFAC SDN list",
        )

        result = SanctionsScreeningResult(
            wallet_id="wallet-1",
            is_sanctioned=True,
            sanctions_matches=[match],
            risk_score=1.0,
            recommendation="block",
            high_risk_jurisdiction=False,
            suspicious_patterns=[],
        )

        assert result.wallet_id == "wallet-1"
        assert result.is_sanctioned is True
        assert len(result.sanctions_matches) == 1
        assert result.risk_score == 1.0
        assert result.recommendation == "block"

    def test_screening_result_to_dict(self):
        """Test converting SanctionsScreeningResult to dictionary."""
        match = SanctionsMatch(
            wallet_id="wallet-1",
            sanctions_list="OFAC_SDN",
            match_type="direct",
            match_details="Wallet on OFAC SDN list",
        )

        result = SanctionsScreeningResult(
            wallet_id="wallet-1",
            is_sanctioned=True,
            sanctions_matches=[match],
            risk_score=1.0,
            recommendation="block",
            high_risk_jurisdiction=False,
            suspicious_patterns=[],
        )

        result_dict = result.to_dict()

        assert result_dict["wallet_id"] == "wallet-1"
        assert result_dict["is_sanctioned"] is True
        assert len(result_dict["sanctions_matches"]) == 1
        assert result_dict["risk_score"] == 1.0


class TestSanctionsScreenerInitialization:
    """Test SanctionsScreener initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default sanctions lists."""
        screener = SanctionsScreener()

        assert len(screener.ofac_list) > 0
        assert len(screener.un_list) > 0
        assert len(screener.eu_list) > 0
        assert len(screener.high_risk_jurisdictions) > 0

    def test_init_with_custom_lists(self):
        """Test initialization with custom sanctions lists."""
        custom_lists = {
            "OFAC_SDN": {"custom-wallet-1", "custom-wallet-2"},
            "UN_SANCTIONS": {"custom-wallet-3"},
            "EU_SANCTIONS": {"custom-wallet-4"},
        }

        screener = SanctionsScreener(custom_sanctions_lists=custom_lists)

        assert screener.ofac_list == {"custom-wallet-1", "custom-wallet-2"}
        assert screener.un_list == {"custom-wallet-3"}
        assert screener.eu_list == {"custom-wallet-4"}


class TestSanctionsScreenerOFAC:
    """Test OFAC SDN list screening."""

    def test_screen_ofac_sanctioned_wallet(self):
        """Test screening wallet on OFAC SDN list."""
        screener = SanctionsScreener()

        result = screener.screen_wallet("sanctioned-wallet-1")

        assert result.wallet_id == "sanctioned-wallet-1"
        assert result.is_sanctioned is True
        assert len(result.sanctions_matches) == 1
        assert result.sanctions_matches[0].sanctions_list == "OFAC_SDN"
        assert result.risk_score == 1.0
        assert result.recommendation == "block"

    def test_screen_non_sanctioned_wallet(self):
        """Test screening wallet not on any sanctions list."""
        screener = SanctionsScreener()

        result = screener.screen_wallet("clean-wallet-1")

        assert result.wallet_id == "clean-wallet-1"
        assert result.is_sanctioned is False
        assert len(result.sanctions_matches) == 0
        assert result.risk_score == 0.0
        assert result.recommendation == "allow"


class TestSanctionsScreenerUN:
    """Test UN sanctions list screening."""

    def test_screen_un_sanctioned_wallet(self):
        """Test screening wallet on UN sanctions list."""
        screener = SanctionsScreener()

        result = screener.screen_wallet("un-sanctioned-1")

        assert result.is_sanctioned is True
        assert len(result.sanctions_matches) == 1
        assert result.sanctions_matches[0].sanctions_list == "UN_SANCTIONS"
        assert result.risk_score == 1.0
        assert result.recommendation == "block"


class TestSanctionsScreenerEU:
    """Test EU sanctions list screening."""

    def test_screen_eu_sanctioned_wallet(self):
        """Test screening wallet on EU sanctions list."""
        screener = SanctionsScreener()

        result = screener.screen_wallet("eu-sanctioned-1")

        assert result.is_sanctioned is True
        assert len(result.sanctions_matches) == 1
        assert result.sanctions_matches[0].sanctions_list == "EU_SANCTIONS"
        assert result.risk_score == 1.0
        assert result.recommendation == "block"


class TestSanctionsScreenerJurisdiction:
    """Test high-risk jurisdiction screening."""

    def test_screen_high_risk_jurisdiction(self):
        """Test screening wallet in high-risk jurisdiction."""
        screener = SanctionsScreener()

        wallet_data = {"jurisdiction": "IR"}  # Iran

        result = screener.screen_wallet("wallet-1", wallet_data)

        assert result.high_risk_jurisdiction is True
        assert len(result.sanctions_matches) == 1
        assert result.sanctions_matches[0].match_type == "jurisdiction"
        assert result.risk_score == 0.6
        assert result.recommendation == "review"

    def test_screen_safe_jurisdiction(self):
        """Test screening wallet in safe jurisdiction."""
        screener = SanctionsScreener()

        wallet_data = {"jurisdiction": "US"}  # United States

        result = screener.screen_wallet("wallet-1", wallet_data)

        assert result.high_risk_jurisdiction is False
        assert result.risk_score == 0.0
        assert result.recommendation == "allow"


class TestSanctionsScreenerSuspiciousPatterns:
    """Test suspicious pattern detection."""

    def test_screen_mixer_usage(self):
        """Test screening wallet with mixer usage."""
        screener = SanctionsScreener()

        wallet_data = {"is_mixer": True}

        result = screener.screen_wallet("wallet-1", wallet_data)

        assert "mixer_usage" in result.suspicious_patterns
        assert result.risk_score == 0.4
        assert result.recommendation == "review"

    def test_screen_high_value_transactions(self):
        """Test screening wallet with high-value transactions."""
        screener = SanctionsScreener()

        wallet_data = {"high_value_transactions": True}

        result = screener.screen_wallet("wallet-1", wallet_data)

        assert "high_value_transactions" in result.suspicious_patterns
        assert result.risk_score == 0.4
        assert result.recommendation == "review"

    def test_screen_rapid_movement(self):
        """Test screening wallet with rapid movement."""
        screener = SanctionsScreener()

        wallet_data = {"rapid_movement": True}

        result = screener.screen_wallet("wallet-1", wallet_data)

        assert "rapid_movement" in result.suspicious_patterns
        assert result.risk_score == 0.4
        assert result.recommendation == "review"


class TestSanctionsScreenerBatchScreening:
    """Test batch screening."""

    def test_batch_screen_multiple_wallets(self):
        """Test batch screening for multiple wallets."""
        screener = SanctionsScreener()

        wallet_ids = [
            "sanctioned-wallet-1",  # OFAC
            "clean-wallet-1",  # Clean
            "un-sanctioned-1",  # UN
        ]

        results = screener.batch_screen(wallet_ids)

        assert len(results) == 3
        assert results[0].is_sanctioned is True
        assert results[1].is_sanctioned is False
        assert results[2].is_sanctioned is True

    def test_batch_screen_with_wallet_data(self):
        """Test batch screening with wallet data."""
        screener = SanctionsScreener()

        wallet_ids = ["wallet-1", "wallet-2"]
        wallet_data_map = {
            "wallet-1": {"jurisdiction": "IR"},
            "wallet-2": {"is_mixer": True},
        }

        results = screener.batch_screen(wallet_ids, wallet_data_map)

        assert len(results) == 2
        assert results[0].high_risk_jurisdiction is True
        assert "mixer_usage" in results[1].suspicious_patterns


class TestSanctionsScreenerStatistics:
    """Test statistics calculation."""

    def test_get_screening_statistics(self):
        """Test calculating statistics from screening results."""
        screener = SanctionsScreener()

        results = [
            SanctionsScreeningResult(
                wallet_id="wallet-1",
                is_sanctioned=True,
                sanctions_matches=[
                    SanctionsMatch(
                        wallet_id="wallet-1",
                        sanctions_list="OFAC_SDN",
                        match_type="direct",
                        match_details="OFAC match",
                    )
                ],
                risk_score=1.0,
                recommendation="block",
                high_risk_jurisdiction=False,
                suspicious_patterns=[],
            ),
            SanctionsScreeningResult(
                wallet_id="wallet-2",
                is_sanctioned=False,
                sanctions_matches=[],
                risk_score=0.0,
                recommendation="allow",
                high_risk_jurisdiction=False,
                suspicious_patterns=[],
            ),
            SanctionsScreeningResult(
                wallet_id="wallet-3",
                is_sanctioned=False,
                sanctions_matches=[],
                risk_score=0.6,
                recommendation="review",
                high_risk_jurisdiction=True,
                suspicious_patterns=[],
            ),
        ]

        stats = screener.get_screening_statistics(results)

        assert stats["total_wallets"] == 3
        assert stats["sanctioned_wallets"] == 1
        assert stats["high_risk_jurisdiction_wallets"] == 1
        assert stats["total_matches"] == 1
        assert stats["ofac_matches"] == 1
        assert stats["average_risk_score"] == 0.533  # (1.0 + 0.0 + 0.6) / 3
        assert stats["recommendations"]["block"] == 1
        assert stats["recommendations"]["allow"] == 1
        assert stats["recommendations"]["review"] == 1

    def test_statistics_with_empty_results(self):
        """Test statistics with empty results list."""
        screener = SanctionsScreener()

        stats = screener.get_screening_statistics([])

        assert stats["total_wallets"] == 0
        assert stats["sanctioned_wallets"] == 0
        assert stats["average_risk_score"] == 0.0


class TestSanctionsScreenerRecommendations:
    """Test recommendation generation."""

    def test_recommendation_block_high_risk(self):
        """Test block recommendation for high risk (>= 0.8)."""
        screener = SanctionsScreener()

        # Risk score 1.0 -> block
        recommendation = screener._get_recommendation(1.0)
        assert recommendation == "block"

        # Risk score 0.8 -> block
        recommendation = screener._get_recommendation(0.8)
        assert recommendation == "block"

    def test_recommendation_review_medium_risk(self):
        """Test review recommendation for medium risk (0.4 - 0.8)."""
        screener = SanctionsScreener()

        # Risk score 0.6 -> review
        recommendation = screener._get_recommendation(0.6)
        assert recommendation == "review"

        # Risk score 0.4 -> review
        recommendation = screener._get_recommendation(0.4)
        assert recommendation == "review"

    def test_recommendation_allow_low_risk(self):
        """Test allow recommendation for low risk (< 0.4)."""
        screener = SanctionsScreener()

        # Risk score 0.3 -> allow
        recommendation = screener._get_recommendation(0.3)
        assert recommendation == "allow"

        # Risk score 0.0 -> allow
        recommendation = screener._get_recommendation(0.0)
        assert recommendation == "allow"


class TestSanctionsScreenerEdgeCases:
    """Test edge cases and error handling."""

    def test_batch_screen_empty_list(self):
        """Test batch screening with empty wallet list."""
        screener = SanctionsScreener()

        results = screener.batch_screen([])

        assert len(results) == 0

    def test_screen_wallet_without_data(self):
        """Test screening wallet without wallet_data."""
        screener = SanctionsScreener()

        result = screener.screen_wallet("wallet-1")

        assert result.wallet_id == "wallet-1"
        assert result.high_risk_jurisdiction is False
        assert len(result.suspicious_patterns) == 0

    def test_custom_high_risk_jurisdictions(self):
        """Test custom high-risk jurisdictions."""
        custom_jurisdictions = {"XX", "YY"}
        screener = SanctionsScreener(high_risk_jurisdictions=custom_jurisdictions)

        wallet_data = {"jurisdiction": "XX"}
        result = screener.screen_wallet("wallet-1", wallet_data)

        assert result.high_risk_jurisdiction is True

# Made with Bob
