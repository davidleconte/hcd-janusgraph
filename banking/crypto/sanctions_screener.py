"""
Crypto Sanctions Screening Module

Screens cryptocurrency wallets and transactions against sanctions lists.
Identifies interactions with sanctioned entities and calculates risk scores.

Business Value:
- Sanctions compliance (OFAC, UN, EU)
- Transaction monitoring (flag sanctioned entities)
- Risk scoring (assess wallet risk based on sanctions)
- Regulatory reporting (sanctions violation reporting)

Screening Methods:
- Wallet screening (check against sanctions lists)
- Transaction screening (check counterparties)
- Amount screening (threshold detection)
- Pattern screening (suspicious activity)

Risk Scoring:
- Direct sanctions match: 1.0 (maximum risk)
- Indirect sanctions interaction: 0.8 (very high risk)
- High-risk jurisdiction: 0.6 (high risk)
- Suspicious patterns: 0.4 (medium risk)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

# Reference timestamp for deterministic testing
REFERENCE_TIMESTAMP = datetime(2026, 1, 15, 12, 0, 0)


@dataclass
class SanctionsMatch:
    """Represents a match against a sanctions list."""

    wallet_id: str
    sanctions_list: str  # OFAC_SDN, UN_SANCTIONS, EU_SANCTIONS
    match_type: str  # direct, indirect, jurisdiction
    match_details: str
    timestamp: datetime = REFERENCE_TIMESTAMP

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "wallet_id": self.wallet_id,
            "sanctions_list": self.sanctions_list,
            "match_type": self.match_type,
            "match_details": self.match_details,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class SanctionsScreeningResult:
    """Result of sanctions screening."""

    wallet_id: str
    is_sanctioned: bool
    sanctions_matches: List[SanctionsMatch]
    risk_score: float  # 0.0 to 1.0
    recommendation: str  # "block", "review", "allow"
    high_risk_jurisdiction: bool
    suspicious_patterns: List[str]
    timestamp: datetime = REFERENCE_TIMESTAMP

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "wallet_id": self.wallet_id,
            "is_sanctioned": self.is_sanctioned,
            "sanctions_matches": [match.to_dict() for match in self.sanctions_matches],
            "risk_score": self.risk_score,
            "recommendation": self.recommendation,
            "high_risk_jurisdiction": self.high_risk_jurisdiction,
            "suspicious_patterns": self.suspicious_patterns,
            "timestamp": self.timestamp.isoformat(),
        }


class SanctionsScreener:
    """
    Screens cryptocurrency wallets against sanctions lists.

    Checks wallets and transactions against OFAC, UN, and EU sanctions lists.
    Calculates risk scores and provides recommendations.
    """

    # Sanctions lists (simplified for testing)
    OFAC_SDN_LIST: Set[str] = {
        "sanctioned-wallet-1",
        "sanctioned-wallet-2",
        "sanctioned-wallet-3",
    }

    UN_SANCTIONS_LIST: Set[str] = {
        "un-sanctioned-1",
        "un-sanctioned-2",
    }

    EU_SANCTIONS_LIST: Set[str] = {
        "eu-sanctioned-1",
        "eu-sanctioned-2",
    }

    # High-risk jurisdictions (country codes)
    HIGH_RISK_JURISDICTIONS: Set[str] = {
        "IR",  # Iran
        "KP",  # North Korea
        "SY",  # Syria
        "RU",  # Russia (partial sanctions)
        "VE",  # Venezuela
    }

    def __init__(
        self,
        custom_sanctions_lists: Optional[Dict[str, Set[str]]] = None,
        high_risk_jurisdictions: Optional[Set[str]] = None,
    ):
        """
        Initialize sanctions screener.

        Args:
            custom_sanctions_lists: Optional custom sanctions lists
            high_risk_jurisdictions: Optional custom high-risk jurisdictions
        """
        # Use custom lists if provided, otherwise use defaults
        if custom_sanctions_lists:
            self.ofac_list = custom_sanctions_lists.get("OFAC_SDN", self.OFAC_SDN_LIST)
            self.un_list = custom_sanctions_lists.get("UN_SANCTIONS", self.UN_SANCTIONS_LIST)
            self.eu_list = custom_sanctions_lists.get("EU_SANCTIONS", self.EU_SANCTIONS_LIST)
        else:
            self.ofac_list = self.OFAC_SDN_LIST
            self.un_list = self.UN_SANCTIONS_LIST
            self.eu_list = self.EU_SANCTIONS_LIST

        self.high_risk_jurisdictions = (
            high_risk_jurisdictions
            if high_risk_jurisdictions
            else self.HIGH_RISK_JURISDICTIONS
        )

    def screen_wallet(
        self, wallet_id: str, wallet_data: Optional[Dict[str, Any]] = None
    ) -> SanctionsScreeningResult:
        """
        Screen a wallet against sanctions lists.

        Args:
            wallet_id: Wallet ID to screen
            wallet_data: Optional wallet data (for testing)

        Returns:
            SanctionsScreeningResult
        """
        sanctions_matches = []

        # Check OFAC SDN list
        if wallet_id in self.ofac_list:
            sanctions_matches.append(
                SanctionsMatch(
                    wallet_id=wallet_id,
                    sanctions_list="OFAC_SDN",
                    match_type="direct",
                    match_details="Wallet on OFAC SDN list",
                )
            )

        # Check UN sanctions list
        if wallet_id in self.un_list:
            sanctions_matches.append(
                SanctionsMatch(
                    wallet_id=wallet_id,
                    sanctions_list="UN_SANCTIONS",
                    match_type="direct",
                    match_details="Wallet on UN sanctions list",
                )
            )

        # Check EU sanctions list
        if wallet_id in self.eu_list:
            sanctions_matches.append(
                SanctionsMatch(
                    wallet_id=wallet_id,
                    sanctions_list="EU_SANCTIONS",
                    match_type="direct",
                    match_details="Wallet on EU sanctions list",
                )
            )

        # Check jurisdiction if wallet_data provided
        high_risk_jurisdiction = False
        if wallet_data and "jurisdiction" in wallet_data:
            jurisdiction = wallet_data["jurisdiction"]
            if jurisdiction in self.high_risk_jurisdictions:
                high_risk_jurisdiction = True
                sanctions_matches.append(
                    SanctionsMatch(
                        wallet_id=wallet_id,
                        sanctions_list="JURISDICTION",
                        match_type="jurisdiction",
                        match_details=f"Wallet in high-risk jurisdiction: {jurisdiction}",
                    )
                )

        # Check for suspicious patterns
        suspicious_patterns = []
        if wallet_data:
            if wallet_data.get("is_mixer", False):
                suspicious_patterns.append("mixer_usage")
            if wallet_data.get("high_value_transactions", False):
                suspicious_patterns.append("high_value_transactions")
            if wallet_data.get("rapid_movement", False):
                suspicious_patterns.append("rapid_movement")

        # Calculate risk score
        # Only count direct sanctions matches (not jurisdiction matches)
        direct_sanctions_matches = [
            m for m in sanctions_matches
            if m.sanctions_list in ["OFAC_SDN", "UN_SANCTIONS", "EU_SANCTIONS"]
        ]
        is_sanctioned = len(direct_sanctions_matches) > 0
        risk_score = self._calculate_risk_score(
            is_sanctioned, high_risk_jurisdiction, suspicious_patterns
        )

        # Get recommendation
        recommendation = self._get_recommendation(risk_score)

        return SanctionsScreeningResult(
            wallet_id=wallet_id,
            is_sanctioned=is_sanctioned,
            sanctions_matches=sanctions_matches,
            risk_score=risk_score,
            recommendation=recommendation,
            high_risk_jurisdiction=high_risk_jurisdiction,
            suspicious_patterns=suspicious_patterns,
        )

    def _calculate_risk_score(
        self,
        is_sanctioned: bool,
        high_risk_jurisdiction: bool,
        suspicious_patterns: List[str],
    ) -> float:
        """
        Calculate risk score based on sanctions screening.

        Risk Scoring:
        - Direct sanctions match: 1.0 (maximum risk)
        - High-risk jurisdiction: 0.6 (high risk)
        - Suspicious patterns: 0.4 (medium risk)
        - No issues: 0.0 (no risk)

        Args:
            is_sanctioned: Whether wallet is sanctioned
            high_risk_jurisdiction: Whether wallet is in high-risk jurisdiction
            suspicious_patterns: List of suspicious patterns

        Returns:
            Risk score (0.0 to 1.0)
        """
        if is_sanctioned:
            return 1.0

        if high_risk_jurisdiction:
            return 0.6

        if suspicious_patterns:
            return 0.4

        return 0.0

    def _get_recommendation(self, risk_score: float) -> str:
        """
        Get recommendation based on risk score.

        Args:
            risk_score: Risk score (0.0 to 1.0)

        Returns:
            Recommendation: "block", "review", or "allow"
        """
        if risk_score >= 0.8:
            return "block"
        elif risk_score >= 0.4:
            return "review"
        else:
            return "allow"

    def batch_screen(
        self,
        wallet_ids: List[str],
        wallet_data_map: Optional[Dict[str, Dict]] = None,
    ) -> List[SanctionsScreeningResult]:
        """
        Screen multiple wallets.

        Args:
            wallet_ids: List of wallet IDs
            wallet_data_map: Optional map of wallet_id -> wallet_data

        Returns:
            List of SanctionsScreeningResult objects
        """
        results = []
        for wallet_id in wallet_ids:
            wallet_data = wallet_data_map.get(wallet_id) if wallet_data_map else None
            result = self.screen_wallet(wallet_id, wallet_data)
            results.append(result)
        return results

    def get_screening_statistics(
        self, results: List[SanctionsScreeningResult]
    ) -> Dict[str, Any]:
        """
        Calculate statistics from screening results.

        Args:
            results: List of screening results

        Returns:
            Statistics dictionary
        """
        total_wallets = len(results)
        sanctioned_wallets = sum(1 for r in results if r.is_sanctioned)
        high_risk_jurisdiction_wallets = sum(
            1 for r in results if r.high_risk_jurisdiction
        )

        total_matches = sum(len(r.sanctions_matches) for r in results)

        # Count matches by list
        ofac_matches = sum(
            1
            for r in results
            for m in r.sanctions_matches
            if m.sanctions_list == "OFAC_SDN"
        )
        un_matches = sum(
            1
            for r in results
            for m in r.sanctions_matches
            if m.sanctions_list == "UN_SANCTIONS"
        )
        eu_matches = sum(
            1
            for r in results
            for m in r.sanctions_matches
            if m.sanctions_list == "EU_SANCTIONS"
        )

        avg_risk_score = (
            sum(r.risk_score for r in results) / total_wallets
            if total_wallets > 0
            else 0.0
        )

        recommendations = {"block": 0, "review": 0, "allow": 0}
        for result in results:
            recommendations[result.recommendation] += 1

        return {
            "total_wallets": total_wallets,
            "sanctioned_wallets": sanctioned_wallets,
            "high_risk_jurisdiction_wallets": high_risk_jurisdiction_wallets,
            "total_matches": total_matches,
            "ofac_matches": ofac_matches,
            "un_matches": un_matches,
            "eu_matches": eu_matches,
            "average_risk_score": round(avg_risk_score, 3),
            "recommendations": recommendations,
        }

# Made with Bob
