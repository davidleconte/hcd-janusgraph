"""
Fraud Ring Pattern Generator

Generates sophisticated fraud ring patterns with network-based detection,
coordinated account activity, mule account identification, and transaction flow analysis.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..core.account_generator import AccountGenerator
from ..core.base_generator import BaseGenerator
from ..events.transaction_generator import TransactionGenerator
from ..utils.data_models import Pattern, RiskLevel
from ..utils.helpers import (
    calculate_pattern_confidence,
    random_choice_weighted,
    random_datetime_between,
)


class FraudRingPatternGenerator(BaseGenerator[Pattern]):
    """
    Generates fraud ring patterns with network-based detection.

    Features:
    - Network-based fraud detection
    - Coordinated account activity
    - Mule account identification
    - Transaction flow analysis
    - Geographic clustering
    - Velocity pattern detection
    - Account takeover indicators
    - Money mule networks

    Pattern Types:
    1. Money mule network: Coordinated money movement through mule accounts
    2. Account takeover ring: Multiple accounts compromised by same group
    3. Synthetic identity fraud: Fake identities used to open accounts
    4. Bust-out fraud: Credit extended then accounts abandoned
    5. Check kiting ring: Coordinated check fraud across accounts

    Use Cases:
    - Fraud investigation
    - Money mule detection
    - Account takeover prevention
    - Synthetic identity detection
    """

    def __init__(
        self,
        seed: Optional[int] = None,
        locale: str = "en_US",
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize FraudRingPatternGenerator.

        Args:
            seed: Random seed for reproducibility
            locale: Faker locale
            config: Additional configuration options
        """
        super().__init__(seed, locale, config)

        # Initialize sub-generators
        self.txn_gen = TransactionGenerator(seed=seed, locale=locale, config=config)
        self.account_gen = AccountGenerator(seed=seed, locale=locale, config=config)

        # Pattern type distribution
        self.pattern_type_weights = {
            "money_mule_network": 0.35,
            "account_takeover_ring": 0.25,
            "synthetic_identity_fraud": 0.20,
            "bust_out_fraud": 0.15,
            "check_kiting_ring": 0.05,
        }

    def generate(
        self,
        pattern_type: Optional[str] = None,
        ring_size: Optional[int] = None,
        transaction_count: Optional[int] = None,
        duration_days: Optional[int] = None,
    ) -> Pattern:
        """
        Generate a single fraud ring pattern.

        Args:
            pattern_type: Type of fraud ring pattern
            ring_size: Number of accounts in ring (3-15)
            transaction_count: Number of transactions (10-100)
            duration_days: Duration of pattern (7-90 days)

        Returns:
            Pattern object with all attributes
        """
        # Select pattern type
        if pattern_type is None:
            pattern_type = random_choice_weighted(list(self.pattern_type_weights.items()))

        # Type assertion
        assert pattern_type is not None, "pattern_type must be set"

        # Set defaults
        if ring_size is None:
            ring_size = random.randint(3, 15)
        if transaction_count is None:
            transaction_count = random.randint(10, 100)
        if duration_days is None:
            duration_days = random.randint(7, 90)

        # Generate pattern dates
        from banking.data_generators.utils.deterministic import REFERENCE_TIMESTAMP
        end_date = REFERENCE_TIMESTAMP
        start_date = end_date - timedelta(days=duration_days)

        # Generate ring accounts
        account_ids = [f"ACC-{self.faker.uuid4()[:8]}" for _ in range(ring_size)]
        entity_ids = [f"PER-{self.faker.uuid4()[:8]}" for _ in range(ring_size)]

        # Generate transactions
        transactions = self._generate_ring_transactions(
            account_ids, transaction_count, start_date, end_date, pattern_type
        )

        # Calculate pattern characteristics
        total_value: Decimal
        if transactions:
            total_value = sum((Decimal(str(t.amount)) for t in transactions), Decimal("0.00"))
        else:
            total_value = Decimal("0.00")

        # Generate indicators
        indicators = self._generate_fraud_indicators(
            pattern_type, transactions, ring_size, duration_days
        )

        # Generate red flags
        red_flags = self._generate_red_flags(pattern_type, transactions, total_value, ring_size)

        # Calculate confidence score
        confidence_score = calculate_pattern_confidence(
            indicators, red_flags, total_value, duration_days
        )

        # Determine risk level
        risk_level = self._determine_risk_level(confidence_score, total_value)

        # Calculate severity score
        severity_score = self._calculate_severity_score(
            confidence_score, total_value, ring_size, len(indicators)
        )

        return Pattern(
            pattern_id=f"PTN-FRAUD-{self.faker.uuid4()[:12]}",
            pattern_type="fraud_ring",
            detection_date=REFERENCE_TIMESTAMP,
            detection_method=f"network_analysis_{pattern_type}",
            confidence_score=confidence_score,
            entity_ids=entity_ids,
            entity_types=["person"] * ring_size,
            transaction_ids=[t.id for t in transactions],
            communication_ids=[],
            start_date=start_date,
            end_date=end_date,
            duration_days=duration_days,
            total_value=total_value,
            transaction_count=len(transactions),
            risk_level=risk_level,
            severity_score=severity_score,
            indicators=indicators,
            red_flags=red_flags,
            is_investigated=False,
            investigation_status=None,
            investigator_id=None,
            investigation_notes=None,
            is_confirmed=None,
            outcome=None,
            action_taken=None,
            metadata={
                "pattern_subtype": pattern_type,
                "ring_size": ring_size,
                "account_ids": account_ids,
                "average_transaction_value": (
                    float(total_value / len(transactions)) if transactions else 0
                ),
                "transaction_velocity": (
                    len(transactions) / duration_days if duration_days > 0 else 0
                ),
                "geographic_clustering": random.random() < 0.7,  # 70% show geographic clustering
                "ip_address_overlap": random.random() < 0.6,  # 60% share IP addresses
            },
        )

    def _generate_ring_transactions(
        self,
        account_ids: List[str],
        transaction_count: int,
        start_date: datetime,
        end_date: datetime,
        pattern_type: str,
    ) -> List[Any]:
        """Generate transactions forming the fraud ring pattern."""
        transactions = []

        # Identify hub account (money mule coordinator)
        hub_account = account_ids[0]

        for i in range(transaction_count):
            # Transaction date
            txn_date = random_datetime_between(start_date, end_date)

            # Select accounts based on pattern type
            if pattern_type == "money_mule_network":
                # Hub and spoke pattern
                if random.random() < 0.7:
                    # Transaction involving hub
                    from_acc = (
                        hub_account if random.random() < 0.5 else random.choice(account_ids[1:])
                    )
                    to_acc = (
                        random.choice(account_ids[1:]) if from_acc == hub_account else hub_account
                    )
                else:
                    # Peer-to-peer
                    from_acc, to_acc = random.sample(account_ids, 2)
            else:
                # Random pairs
                from_acc, to_acc = random.sample(account_ids, 2)

            # Generate transaction
            txn = self.txn_gen.generate(from_account_id=from_acc, to_account_id=to_acc)

            # Override date
            txn.transaction_date = txn_date

            # Add pattern metadata
            txn.metadata["pattern_type"] = pattern_type
            txn.metadata["ring_sequence"] = i + 1
            txn.metadata["involves_hub"] = hub_account in [from_acc, to_acc]

            transactions.append(txn)

        return transactions

    def _generate_fraud_indicators(
        self, pattern_type: str, transactions: List[Any], ring_size: int, duration_days: int
    ) -> List[str]:
        """Generate fraud ring indicators."""
        indicators = ["fraud_ring_detected", "coordinated_activity", "network_pattern_identified"]

        if pattern_type == "money_mule_network":
            indicators.extend(
                [
                    "money_mule_activity",
                    "hub_and_spoke_pattern",
                    "rapid_fund_movement",
                    "layering_detected",
                ]
            )

        elif pattern_type == "account_takeover_ring":
            indicators.extend(
                [
                    "account_takeover_indicators",
                    "multiple_compromised_accounts",
                    "unauthorized_access_pattern",
                    "credential_stuffing_suspected",
                ]
            )

        elif pattern_type == "synthetic_identity_fraud":
            indicators.extend(
                [
                    "synthetic_identity_suspected",
                    "fabricated_identity_indicators",
                    "credit_building_pattern",
                    "bust_out_preparation",
                ]
            )

        elif pattern_type == "bust_out_fraud":
            indicators.extend(
                [
                    "bust_out_fraud_detected",
                    "credit_maximization",
                    "sudden_account_abandonment",
                    "coordinated_credit_abuse",
                ]
            )

        # Velocity indicators
        if len(transactions) / duration_days > 5:
            indicators.append("high_transaction_velocity")

        # Network size indicators
        if ring_size >= 10:
            indicators.append("large_fraud_network")
        elif ring_size >= 5:
            indicators.append("medium_fraud_network")

        return list(set(indicators))

    def _generate_red_flags(
        self, pattern_type: str, transactions: List[Any], total_value: Decimal, ring_size: int
    ) -> List[str]:
        """Generate red flags."""
        red_flags = []

        # High value
        if total_value > 1000000:
            red_flags.append("very_high_fraud_value")
        elif total_value > 500000:
            red_flags.append("high_fraud_value")

        # Large network
        if ring_size >= 10:
            red_flags.append("extensive_fraud_network")

        # High transaction count
        if len(transactions) > 50:
            red_flags.append("high_transaction_volume")

        # Pattern-specific red flags
        if pattern_type == "money_mule_network":
            red_flags.extend(["money_laundering_suspected", "organized_crime_indicators"])

        elif pattern_type == "account_takeover_ring":
            red_flags.extend(["cybercrime_indicators", "credential_theft_suspected"])

        elif pattern_type == "synthetic_identity_fraud":
            red_flags.extend(["identity_fabrication", "credit_fraud_indicators"])

        return red_flags

    def _determine_risk_level(self, confidence_score: float, total_value: Decimal) -> RiskLevel:
        """Determine risk level."""
        if confidence_score >= 0.8 and total_value > 1000000:
            return RiskLevel.CRITICAL
        elif confidence_score >= 0.7 or total_value > 500000:
            return RiskLevel.HIGH
        elif confidence_score >= 0.5 or total_value > 100000:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _calculate_severity_score(
        self, confidence_score: float, total_value: Decimal, ring_size: int, indicator_count: int
    ) -> float:
        """Calculate severity score (0-1)."""
        score = confidence_score * 0.4

        # Value component
        if total_value > 1000000:
            score += 0.3
        elif total_value > 500000:
            score += 0.2
        elif total_value > 100000:
            score += 0.1

        # Network size component
        if ring_size >= 10:
            score += 0.2
        elif ring_size >= 5:
            score += 0.1

        # Indicator count
        if indicator_count >= 10:
            score += 0.1

        return min(score, 1.0)

    def generate_money_mule_network(
        self, network_size: int = 10, transaction_count: int = 50, duration_days: int = 30
    ) -> Pattern:
        """
        Generate a money mule network pattern.

        Args:
            network_size: Number of mule accounts
            transaction_count: Total transactions
            duration_days: Duration of activity

        Returns:
            Pattern object representing money mule network
        """
        return self.generate(
            pattern_type="money_mule_network",
            ring_size=network_size,
            transaction_count=transaction_count,
            duration_days=duration_days,
        )
