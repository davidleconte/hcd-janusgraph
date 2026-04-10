"""
Tests for MixerDetector

Tests mixer detection functionality including:
- Direct mixer interaction detection
- Indirect mixer interaction detection (multi-hop)
- Risk score calculation
- Recommendation generation
- Batch detection
- Statistics calculation
"""

import pytest
from datetime import datetime

from banking.crypto.mixer_detector import (
    MixerDetector,
    MixerPath,
    MixerDetectionResult,
    REFERENCE_TIMESTAMP,
)


class TestMixerPath:
    """Test MixerPath dataclass."""

    def test_create_mixer_path(self):
        """Test creating a MixerPath."""
        path = MixerPath(
            wallet_id="wallet-1",
            mixer_id="mixer-1",
            path_length=2,
            path_wallets=["wallet-1", "wallet-2", "mixer-1"],
            total_amount=100.0,
        )

        assert path.wallet_id == "wallet-1"
        assert path.mixer_id == "mixer-1"
        assert path.path_length == 2
        assert len(path.path_wallets) == 3
        assert path.total_amount == 100.0
        assert path.timestamp == REFERENCE_TIMESTAMP

    def test_mixer_path_to_dict(self):
        """Test converting MixerPath to dictionary."""
        path = MixerPath(
            wallet_id="wallet-1",
            mixer_id="mixer-1",
            path_length=1,
            path_wallets=["wallet-1", "mixer-1"],
            total_amount=50.0,
        )

        path_dict = path.to_dict()

        assert path_dict["wallet_id"] == "wallet-1"
        assert path_dict["mixer_id"] == "mixer-1"
        assert path_dict["path_length"] == 1
        assert path_dict["path_wallets"] == ["wallet-1", "mixer-1"]
        assert path_dict["total_amount"] == 50.0
        assert "timestamp" in path_dict


class TestMixerDetectionResult:
    """Test MixerDetectionResult dataclass."""

    def test_create_detection_result(self):
        """Test creating a MixerDetectionResult."""
        path = MixerPath(
            wallet_id="wallet-1",
            mixer_id="mixer-1",
            path_length=1,
            path_wallets=["wallet-1", "mixer-1"],
            total_amount=100.0,
        )

        result = MixerDetectionResult(
            wallet_id="wallet-1",
            is_mixer=False,
            has_mixer_interaction=True,
            risk_score=0.9,
            mixer_paths=[path],
            direct_mixer_count=1,
            indirect_mixer_count=0,
            recommendation="reject",
        )

        assert result.wallet_id == "wallet-1"
        assert result.is_mixer is False
        assert result.has_mixer_interaction is True
        assert result.risk_score == 0.9
        assert len(result.mixer_paths) == 1
        assert result.direct_mixer_count == 1
        assert result.indirect_mixer_count == 0
        assert result.recommendation == "reject"

    def test_detection_result_to_dict(self):
        """Test converting MixerDetectionResult to dictionary."""
        path = MixerPath(
            wallet_id="wallet-1",
            mixer_id="mixer-1",
            path_length=1,
            path_wallets=["wallet-1", "mixer-1"],
            total_amount=100.0,
        )

        result = MixerDetectionResult(
            wallet_id="wallet-1",
            is_mixer=False,
            has_mixer_interaction=True,
            risk_score=0.9,
            mixer_paths=[path],
            direct_mixer_count=1,
            indirect_mixer_count=0,
            recommendation="reject",
        )

        result_dict = result.to_dict()

        assert result_dict["wallet_id"] == "wallet-1"
        assert result_dict["is_mixer"] is False
        assert result_dict["has_mixer_interaction"] is True
        assert result_dict["risk_score"] == 0.9
        assert len(result_dict["mixer_paths"]) == 1
        assert result_dict["direct_mixer_count"] == 1
        assert result_dict["indirect_mixer_count"] == 0
        assert result_dict["recommendation"] == "reject"


class TestMixerDetectorInitialization:
    """Test MixerDetector initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        detector = MixerDetector()

        assert detector.graph_client is None
        assert detector.max_hops == 5
        assert detector.min_amount == 0.0

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        detector = MixerDetector(max_hops=3, min_amount=10.0)

        assert detector.max_hops == 3
        assert detector.min_amount == 10.0


class TestMixerDetectorDirectInteraction:
    """Test detection of direct mixer interactions."""

    def test_detect_direct_mixer_interaction(self):
        """Test detecting direct interaction with mixer (1 hop)."""
        detector = MixerDetector()

        wallet_data = {
            "is_mixer": False,
            "mixer_paths": [
                {
                    "wallet_id": "wallet-1",
                    "mixer_id": "mixer-1",
                    "path_length": 1,
                    "path_wallets": ["wallet-1", "mixer-1"],
                    "total_amount": 100.0,
                }
            ],
        }

        result = detector.detect_mixer_interaction("wallet-1", wallet_data)

        assert result.wallet_id == "wallet-1"
        assert result.is_mixer is False
        assert result.has_mixer_interaction is True
        assert result.risk_score == 0.9  # Direct interaction
        assert result.direct_mixer_count == 1
        assert result.indirect_mixer_count == 0
        assert result.recommendation == "reject"

    def test_detect_wallet_is_mixer(self):
        """Test detecting that wallet itself is a mixer."""
        detector = MixerDetector()

        wallet_data = {"is_mixer": True, "mixer_paths": []}

        result = detector.detect_mixer_interaction("mixer-1", wallet_data)

        assert result.wallet_id == "mixer-1"
        assert result.is_mixer is True
        assert result.risk_score == 1.0  # Maximum risk
        assert result.recommendation == "reject"


class TestMixerDetectorIndirectInteraction:
    """Test detection of indirect mixer interactions."""

    def test_detect_two_hop_interaction(self):
        """Test detecting 2-hop interaction with mixer."""
        detector = MixerDetector()

        wallet_data = {
            "is_mixer": False,
            "mixer_paths": [
                {
                    "wallet_id": "wallet-1",
                    "mixer_id": "mixer-1",
                    "path_length": 2,
                    "path_wallets": ["wallet-1", "wallet-2", "mixer-1"],
                    "total_amount": 100.0,
                }
            ],
        }

        result = detector.detect_mixer_interaction("wallet-1", wallet_data)

        assert result.has_mixer_interaction is True
        assert result.risk_score == 0.7  # 2-hop interaction
        assert result.direct_mixer_count == 0
        assert result.indirect_mixer_count == 1
        assert result.recommendation == "review"

    def test_detect_three_hop_interaction(self):
        """Test detecting 3-hop interaction with mixer."""
        detector = MixerDetector()

        wallet_data = {
            "is_mixer": False,
            "mixer_paths": [
                {
                    "wallet_id": "wallet-1",
                    "mixer_id": "mixer-1",
                    "path_length": 3,
                    "path_wallets": ["wallet-1", "wallet-2", "wallet-3", "mixer-1"],
                    "total_amount": 100.0,
                }
            ],
        }

        result = detector.detect_mixer_interaction("wallet-1", wallet_data)

        assert result.has_mixer_interaction is True
        assert result.risk_score == 0.5  # 3-hop interaction
        assert result.recommendation == "review"

    def test_detect_four_hop_interaction(self):
        """Test detecting 4+ hop interaction with mixer."""
        detector = MixerDetector()

        wallet_data = {
            "is_mixer": False,
            "mixer_paths": [
                {
                    "wallet_id": "wallet-1",
                    "mixer_id": "mixer-1",
                    "path_length": 4,
                    "path_wallets": [
                        "wallet-1",
                        "wallet-2",
                        "wallet-3",
                        "wallet-4",
                        "mixer-1",
                    ],
                    "total_amount": 100.0,
                }
            ],
        }

        result = detector.detect_mixer_interaction("wallet-1", wallet_data)

        assert result.has_mixer_interaction is True
        assert result.risk_score == 0.3  # 4+ hop interaction
        assert result.recommendation == "approve"


class TestMixerDetectorNoInteraction:
    """Test detection when no mixer interaction exists."""

    def test_detect_no_mixer_interaction(self):
        """Test detecting wallet with no mixer interaction."""
        detector = MixerDetector()

        wallet_data = {"is_mixer": False, "mixer_paths": []}

        result = detector.detect_mixer_interaction("wallet-1", wallet_data)

        assert result.wallet_id == "wallet-1"
        assert result.is_mixer is False
        assert result.has_mixer_interaction is False
        assert result.risk_score == 0.0
        assert result.direct_mixer_count == 0
        assert result.indirect_mixer_count == 0
        assert result.recommendation == "approve"


class TestMixerDetectorMultiplePaths:
    """Test detection with multiple paths to mixers."""

    def test_detect_multiple_mixer_paths(self):
        """Test detecting multiple paths to different mixers."""
        detector = MixerDetector()

        wallet_data = {
            "is_mixer": False,
            "mixer_paths": [
                {
                    "wallet_id": "wallet-1",
                    "mixer_id": "mixer-1",
                    "path_length": 1,
                    "path_wallets": ["wallet-1", "mixer-1"],
                    "total_amount": 100.0,
                },
                {
                    "wallet_id": "wallet-1",
                    "mixer_id": "mixer-2",
                    "path_length": 2,
                    "path_wallets": ["wallet-1", "wallet-2", "mixer-2"],
                    "total_amount": 50.0,
                },
            ],
        }

        result = detector.detect_mixer_interaction("wallet-1", wallet_data)

        assert result.has_mixer_interaction is True
        assert len(result.mixer_paths) == 2
        assert result.direct_mixer_count == 1
        assert result.indirect_mixer_count == 1
        # Risk score based on closest mixer (1 hop)
        assert result.risk_score == 0.9
        assert result.recommendation == "reject"

    def test_risk_score_uses_closest_mixer(self):
        """Test that risk score is based on closest mixer."""
        detector = MixerDetector()

        wallet_data = {
            "is_mixer": False,
            "mixer_paths": [
                {
                    "wallet_id": "wallet-1",
                    "mixer_id": "mixer-1",
                    "path_length": 3,
                    "path_wallets": ["wallet-1", "wallet-2", "wallet-3", "mixer-1"],
                    "total_amount": 100.0,
                },
                {
                    "wallet_id": "wallet-1",
                    "mixer_id": "mixer-2",
                    "path_length": 2,
                    "path_wallets": ["wallet-1", "wallet-2", "mixer-2"],
                    "total_amount": 50.0,
                },
            ],
        }

        result = detector.detect_mixer_interaction("wallet-1", wallet_data)

        # Risk score based on closest mixer (2 hops)
        assert result.risk_score == 0.7


class TestMixerDetectorBatchDetection:
    """Test batch detection of multiple wallets."""

    def test_batch_detect_multiple_wallets(self):
        """Test batch detection for multiple wallets."""
        detector = MixerDetector()

        wallet_data_map = {
            "wallet-1": {
                "is_mixer": False,
                "mixer_paths": [
                    {
                        "wallet_id": "wallet-1",
                        "mixer_id": "mixer-1",
                        "path_length": 1,
                        "path_wallets": ["wallet-1", "mixer-1"],
                        "total_amount": 100.0,
                    }
                ],
            },
            "wallet-2": {"is_mixer": False, "mixer_paths": []},
            "mixer-1": {"is_mixer": True, "mixer_paths": []},
        }

        results = detector.batch_detect(
            ["wallet-1", "wallet-2", "mixer-1"], wallet_data_map
        )

        assert len(results) == 3
        assert results[0].wallet_id == "wallet-1"
        assert results[0].risk_score == 0.9
        assert results[1].wallet_id == "wallet-2"
        assert results[1].risk_score == 0.0
        assert results[2].wallet_id == "mixer-1"
        assert results[2].risk_score == 1.0


class TestMixerDetectorStatistics:
    """Test statistics calculation."""

    def test_get_mixer_statistics(self):
        """Test calculating statistics from detection results."""
        detector = MixerDetector()

        results = [
            MixerDetectionResult(
                wallet_id="wallet-1",
                is_mixer=False,
                has_mixer_interaction=True,
                risk_score=0.9,
                mixer_paths=[],
                direct_mixer_count=1,
                indirect_mixer_count=0,
                recommendation="reject",
            ),
            MixerDetectionResult(
                wallet_id="wallet-2",
                is_mixer=False,
                has_mixer_interaction=False,
                risk_score=0.0,
                mixer_paths=[],
                direct_mixer_count=0,
                indirect_mixer_count=0,
                recommendation="approve",
            ),
            MixerDetectionResult(
                wallet_id="mixer-1",
                is_mixer=True,
                has_mixer_interaction=False,
                risk_score=1.0,
                mixer_paths=[],
                direct_mixer_count=0,
                indirect_mixer_count=0,
                recommendation="reject",
            ),
        ]

        stats = detector.get_mixer_statistics(results)

        assert stats["total_wallets"] == 3
        assert stats["mixer_wallets"] == 1
        assert stats["wallets_with_interaction"] == 1
        assert stats["total_direct_interactions"] == 1
        assert stats["total_indirect_interactions"] == 0
        assert stats["average_risk_score"] == 0.633  # (0.9 + 0.0 + 1.0) / 3
        assert stats["recommendations"]["approve"] == 1
        assert stats["recommendations"]["review"] == 0
        assert stats["recommendations"]["reject"] == 2

    def test_statistics_with_empty_results(self):
        """Test statistics with empty results list."""
        detector = MixerDetector()

        stats = detector.get_mixer_statistics([])

        assert stats["total_wallets"] == 0
        assert stats["mixer_wallets"] == 0
        assert stats["average_risk_score"] == 0.0


class TestMixerDetectorRecommendations:
    """Test recommendation generation."""

    def test_recommendation_reject_high_risk(self):
        """Test reject recommendation for high risk (>= 0.8)."""
        detector = MixerDetector()

        # Risk score 0.9 -> reject
        recommendation = detector._get_recommendation(0.9)
        assert recommendation == "reject"

        # Risk score 0.8 -> reject
        recommendation = detector._get_recommendation(0.8)
        assert recommendation == "reject"

    def test_recommendation_review_medium_risk(self):
        """Test review recommendation for medium risk (0.5 - 0.8)."""
        detector = MixerDetector()

        # Risk score 0.7 -> review
        recommendation = detector._get_recommendation(0.7)
        assert recommendation == "review"

        # Risk score 0.5 -> review
        recommendation = detector._get_recommendation(0.5)
        assert recommendation == "review"

    def test_recommendation_approve_low_risk(self):
        """Test approve recommendation for low risk (< 0.5)."""
        detector = MixerDetector()

        # Risk score 0.3 -> approve
        recommendation = detector._get_recommendation(0.3)
        assert recommendation == "approve"

        # Risk score 0.0 -> approve
        recommendation = detector._get_recommendation(0.0)
        assert recommendation == "approve"


class TestMixerDetectorEdgeCases:
    """Test edge cases and error handling."""

    def test_detect_without_graph_client_raises_error(self):
        """Test that detection without graph client raises error."""
        detector = MixerDetector()

        with pytest.raises(ValueError, match="graph_client required"):
            detector.detect_mixer_interaction("wallet-1")

    def test_detect_with_wallet_data_works_without_client(self):
        """Test that detection with wallet_data works without graph client."""
        detector = MixerDetector()

        wallet_data = {"is_mixer": False, "mixer_paths": []}

        # Should not raise error
        result = detector.detect_mixer_interaction("wallet-1", wallet_data)
        assert result.wallet_id == "wallet-1"

    def test_batch_detect_empty_list(self):
        """Test batch detection with empty wallet list."""
        detector = MixerDetector()

        results = detector.batch_detect([])

        assert len(results) == 0

    def test_statistics_handles_division_by_zero(self):
        """Test that statistics handles empty results gracefully."""
        detector = MixerDetector()

        stats = detector.get_mixer_statistics([])

        assert stats["average_risk_score"] == 0.0
        assert stats["total_wallets"] == 0

# Made with Bob
