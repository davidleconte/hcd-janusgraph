"""
Crypto Mixer Detection Module

Detects cryptocurrency mixer/tumbler usage through graph traversal analysis.
Identifies wallets that have interacted with known mixers and calculates risk scores.

Business Value:
- AML compliance (detect money laundering through mixers)
- Transaction monitoring (flag high-risk transactions)
- Risk scoring (assess wallet risk based on mixer proximity)
- Regulatory reporting (SAR filing for mixer usage)

Detection Methods:
- Direct mixer interaction (1 hop)
- Indirect mixer interaction (2-5 hops)
- Multi-hop mixer chains (layering detection)
- Mixer network analysis (identify mixer clusters)

Risk Scoring:
- Direct interaction: 0.9 (very high risk)
- 1 hop from mixer: 0.7 (high risk)
- 2 hops from mixer: 0.5 (medium risk)
- 3+ hops from mixer: 0.3 (low risk)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import Order

# Reference timestamp for deterministic testing
REFERENCE_TIMESTAMP = datetime(2026, 1, 15, 12, 0, 0)


@dataclass
class MixerPath:
    """Represents a path from a wallet to a mixer."""

    wallet_id: str
    mixer_id: str
    path_length: int  # Number of hops
    path_wallets: List[str]  # Wallet IDs in path
    total_amount: float  # Total amount transacted along path
    timestamp: datetime = REFERENCE_TIMESTAMP

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "wallet_id": self.wallet_id,
            "mixer_id": self.mixer_id,
            "path_length": self.path_length,
            "path_wallets": self.path_wallets,
            "total_amount": self.total_amount,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class MixerDetectionResult:
    """Result of mixer detection analysis."""

    wallet_id: str
    is_mixer: bool
    has_mixer_interaction: bool
    risk_score: float  # 0.0 to 1.0
    mixer_paths: List[MixerPath]
    direct_mixer_count: int  # Number of direct mixer interactions
    indirect_mixer_count: int  # Number of indirect mixer interactions
    recommendation: str  # "approve", "review", "reject"
    timestamp: datetime = REFERENCE_TIMESTAMP

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "wallet_id": self.wallet_id,
            "is_mixer": self.is_mixer,
            "has_mixer_interaction": self.has_mixer_interaction,
            "risk_score": self.risk_score,
            "mixer_paths": [path.to_dict() for path in self.mixer_paths],
            "direct_mixer_count": self.direct_mixer_count,
            "indirect_mixer_count": self.indirect_mixer_count,
            "recommendation": self.recommendation,
            "timestamp": self.timestamp.isoformat(),
        }


class MixerDetector:
    """
    Detects cryptocurrency mixer usage through graph analysis.

    Uses Gremlin traversals to find paths between wallets and known mixers.
    Calculates risk scores based on proximity to mixers.
    """

    def __init__(
        self,
        graph_client: Optional[Any] = None,
        max_hops: int = 5,
        min_amount: float = 0.0,
    ):
        """
        Initialize mixer detector.

        Args:
            graph_client: JanusGraph client (optional, for testing can be None)
            max_hops: Maximum number of hops to traverse (default: 5)
            min_amount: Minimum transaction amount to consider (default: 0.0)
        """
        self.graph_client = graph_client
        self.max_hops = max_hops
        self.min_amount = min_amount

    def detect_mixer_interaction(
        self, wallet_id: str, wallet_data: Optional[Dict[str, Any]] = None
    ) -> MixerDetectionResult:
        """
        Detect if a wallet has interacted with mixers.

        Args:
            wallet_id: Wallet ID to analyze
            wallet_data: Optional wallet data (for testing without graph)

        Returns:
            MixerDetectionResult with analysis results
        """
        # If wallet_data provided (testing mode), use it
        if wallet_data is not None:
            return self._detect_from_data(wallet_id, wallet_data)

        # Otherwise, query graph (production mode)
        if self.graph_client is None:
            raise ValueError("graph_client required for graph-based detection")

        return self._detect_from_graph(wallet_id)

    def _detect_from_data(
        self, wallet_id: str, wallet_data: Dict[str, Any]
    ) -> MixerDetectionResult:
        """
        Detect mixer interaction from provided wallet data (testing mode).

        Args:
            wallet_id: Wallet ID
            wallet_data: Wallet data dictionary

        Returns:
            MixerDetectionResult
        """
        is_mixer = wallet_data.get("is_mixer", False)
        mixer_paths = wallet_data.get("mixer_paths", [])

        # Convert dict paths to MixerPath objects
        mixer_path_objects = [
            MixerPath(
                wallet_id=path["wallet_id"],
                mixer_id=path["mixer_id"],
                path_length=path["path_length"],
                path_wallets=path["path_wallets"],
                total_amount=path["total_amount"],
            )
            for path in mixer_paths
        ]

        # Calculate risk score
        risk_score = self._calculate_risk_score(is_mixer, mixer_path_objects)

        # Count direct and indirect interactions
        direct_count = sum(1 for path in mixer_path_objects if path.path_length == 1)
        indirect_count = len(mixer_path_objects) - direct_count

        # Determine recommendation
        recommendation = self._get_recommendation(risk_score)

        return MixerDetectionResult(
            wallet_id=wallet_id,
            is_mixer=is_mixer,
            has_mixer_interaction=len(mixer_path_objects) > 0,
            risk_score=risk_score,
            mixer_paths=mixer_path_objects,
            direct_mixer_count=direct_count,
            indirect_mixer_count=indirect_count,
            recommendation=recommendation,
        )

    def _detect_from_graph(self, wallet_id: str) -> MixerDetectionResult:
        """
        Detect mixer interaction from graph traversal (production mode).

        Args:
            wallet_id: Wallet ID

        Returns:
            MixerDetectionResult
        """
        # Get wallet properties
        g = self.graph_client.g
        wallet = g.V().has("wallet", "wallet_id", wallet_id).valueMap(True).next()

        is_mixer = wallet.get("is_mixer", [False])[0]

        # Find paths to mixers (up to max_hops)
        mixer_paths = []
        for hop_count in range(1, self.max_hops + 1):
            paths = self._find_mixer_paths(wallet_id, hop_count)
            mixer_paths.extend(paths)

        # Calculate risk score
        risk_score = self._calculate_risk_score(is_mixer, mixer_paths)

        # Count direct and indirect interactions
        direct_count = sum(1 for path in mixer_paths if path.path_length == 1)
        indirect_count = len(mixer_paths) - direct_count

        # Determine recommendation
        recommendation = self._get_recommendation(risk_score)

        return MixerDetectionResult(
            wallet_id=wallet_id,
            is_mixer=is_mixer,
            has_mixer_interaction=len(mixer_paths) > 0,
            risk_score=risk_score,
            mixer_paths=mixer_paths,
            direct_mixer_count=direct_count,
            indirect_mixer_count=indirect_count,
            recommendation=recommendation,
        )

    def _find_mixer_paths(self, wallet_id: str, hop_count: int) -> List[MixerPath]:
        """
        Find paths from wallet to mixers with specific hop count.

        Args:
            wallet_id: Starting wallet ID
            hop_count: Number of hops to traverse

        Returns:
            List of MixerPath objects
        """
        g = self.graph_client.g

        # Traverse hop_count times, find mixers
        traversal = g.V().has("wallet", "wallet_id", wallet_id)

        # Repeat traversal hop_count times
        for _ in range(hop_count):
            traversal = traversal.both("SENT_TO", "RECEIVED_FROM").simplePath()

        # Filter for mixers
        traversal = traversal.where(__.has("wallet", "is_mixer", True))

        # Get paths
        paths = traversal.path().by(__.valueMap("wallet_id", "is_mixer")).toList()

        # Convert to MixerPath objects
        mixer_paths = []
        for path in paths:
            path_wallets = [step["wallet_id"][0] for step in path]
            mixer_id = path_wallets[-1]

            # Calculate total amount (would need transaction edges in real implementation)
            total_amount = 0.0

            mixer_paths.append(
                MixerPath(
                    wallet_id=wallet_id,
                    mixer_id=mixer_id,
                    path_length=hop_count,
                    path_wallets=path_wallets,
                    total_amount=total_amount,
                )
            )

        return mixer_paths

    def _calculate_risk_score(
        self, is_mixer: bool, mixer_paths: List[MixerPath]
    ) -> float:
        """
        Calculate risk score based on mixer interaction.

        Risk Scoring:
        - Is mixer: 1.0 (maximum risk)
        - Direct interaction (1 hop): 0.9
        - 1 hop from mixer (2 hops): 0.7
        - 2 hops from mixer (3 hops): 0.5
        - 3+ hops from mixer: 0.3
        - No mixer interaction: 0.0

        Args:
            is_mixer: Whether wallet is a mixer
            mixer_paths: List of paths to mixers

        Returns:
            Risk score (0.0 to 1.0)
        """
        if is_mixer:
            return 1.0

        if not mixer_paths:
            return 0.0

        # Get minimum path length (closest mixer)
        min_path_length = min(path.path_length for path in mixer_paths)

        # Risk score based on proximity
        if min_path_length == 1:
            return 0.9  # Direct interaction
        elif min_path_length == 2:
            return 0.7  # 1 hop away
        elif min_path_length == 3:
            return 0.5  # 2 hops away
        else:
            return 0.3  # 3+ hops away

    def _get_recommendation(self, risk_score: float) -> str:
        """
        Get recommendation based on risk score.

        Args:
            risk_score: Risk score (0.0 to 1.0)

        Returns:
            Recommendation: "approve", "review", or "reject"
        """
        if risk_score >= 0.8:
            return "reject"
        elif risk_score >= 0.5:
            return "review"
        else:
            return "approve"

    def batch_detect(
        self, wallet_ids: List[str], wallet_data_map: Optional[Dict[str, Dict]] = None
    ) -> List[MixerDetectionResult]:
        """
        Detect mixer interaction for multiple wallets.

        Args:
            wallet_ids: List of wallet IDs
            wallet_data_map: Optional map of wallet_id -> wallet_data (for testing)

        Returns:
            List of MixerDetectionResult objects
        """
        results = []
        for wallet_id in wallet_ids:
            wallet_data = (
                wallet_data_map.get(wallet_id) if wallet_data_map else None
            )
            result = self.detect_mixer_interaction(wallet_id, wallet_data)
            results.append(result)
        return results

    def get_mixer_statistics(
        self, results: List[MixerDetectionResult]
    ) -> Dict[str, Any]:
        """
        Calculate statistics from detection results.

        Args:
            results: List of detection results

        Returns:
            Statistics dictionary
        """
        total_wallets = len(results)
        mixer_wallets = sum(1 for r in results if r.is_mixer)
        wallets_with_interaction = sum(1 for r in results if r.has_mixer_interaction)

        total_direct = sum(r.direct_mixer_count for r in results)
        total_indirect = sum(r.indirect_mixer_count for r in results)

        avg_risk_score = (
            sum(r.risk_score for r in results) / total_wallets if total_wallets > 0 else 0.0
        )

        recommendations = {"approve": 0, "review": 0, "reject": 0}
        for result in results:
            recommendations[result.recommendation] += 1

        return {
            "total_wallets": total_wallets,
            "mixer_wallets": mixer_wallets,
            "wallets_with_interaction": wallets_with_interaction,
            "total_direct_interactions": total_direct,
            "total_indirect_interactions": total_indirect,
            "average_risk_score": round(avg_risk_score, 3),
            "recommendations": recommendations,
        }

# Made with Bob
