"""
Mule Chain Pattern Generator
============================

Generates deterministic Authorized Push Payment (APP) fraud mule-chain patterns
with rapid multi-hop transaction movement and cash-out behavior.
"""

import random
from datetime import timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from ..core.base_generator import BaseGenerator
from ..events.transaction_generator import TransactionGenerator
from ..utils.data_models import Pattern, RiskLevel, Transaction, TransactionType
from ..utils.deterministic import REFERENCE_TIMESTAMP
from ..utils.helpers import calculate_pattern_confidence, random_datetime_between


class MuleChainGenerator(BaseGenerator[Pattern]):
    """
    Generate APP fraud mule-chain patterns.

    Pattern shape:
        Victim account -> Mule 1 -> ... -> Mule N -> Cash-out account

    Notes:
        - Deterministic by seed through BaseGenerator/Faker/random initialization.
        - Returns both Pattern and generated Transactions for orchestrator injection.
    """

    def __init__(
        self,
        seed: Optional[int] = None,
        locale: str = "en_US",
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(seed, locale, config)
        self.txn_gen = TransactionGenerator(seed=seed, locale=locale, config=config)

    def generate(
        self,
        chain_length: int = 4,
        start_amount: float = 10000.0,
        hop_delay_minutes: int = 15,
        duration_days: int = 3,
    ) -> Tuple[Pattern, List[Transaction]]:
        """
        Generate one deterministic mule-chain pattern and linked transactions.

        Args:
            chain_length: Number of accounts in chain including victim and cash-out (min 3).
            start_amount: Initial transfer amount from victim.
            hop_delay_minutes: Approximate hop delay between transfers.
            duration_days: Pattern duration window.

        Returns:
            Tuple[Pattern, List[Transaction]]
        """
        chain_length = max(chain_length, 3)
        hop_delay_minutes = max(hop_delay_minutes, 1)

        account_ids = [f"ACC-{self.faker.uuid4()[:8].upper()}" for _ in range(chain_length)]
        mule_ids = account_ids[1:-1]

        end_date = REFERENCE_TIMESTAMP
        start_date = end_date - timedelta(days=max(duration_days, 1))

        transactions = self._generate_chain_transactions(
            account_ids=account_ids,
            start_amount=Decimal(str(start_amount)),
            hop_delay_minutes=hop_delay_minutes,
            start_date=start_date,
            end_date=end_date,
        )

        total_value = sum((Decimal(str(tx.amount)) for tx in transactions), Decimal("0.00"))
        indicators = [
            "app_fraud_suspected",
            "rapid_multi_hop_transfers",
            "mule_account_chain",
            "cash_out_pattern",
        ]
        red_flags = [
            "velocity_across_intermediary_accounts",
            "funds_dispersal_and_extraction",
        ]

        confidence_score = calculate_pattern_confidence(
            indicators=indicators,
            red_flags=red_flags,
            total_value=total_value,
            duration_days=max(duration_days, 1),
        )

        severity_score = self._calculate_severity_score(
            confidence_score=confidence_score,
            hop_count=len(transactions),
            total_value=total_value,
        )

        risk_level = self._determine_risk_level(severity_score)

        pattern = Pattern(
            pattern_id=f"PTN-MULE-{self.faker.uuid4()[:12].upper()}",
            pattern_type="mule_chain",
            detection_date=REFERENCE_TIMESTAMP,
            detection_method="app_mule_chain_velocity_analysis",
            confidence_score=confidence_score,
            entity_ids=account_ids,
            entity_types=["account"] * len(account_ids),
            transaction_ids=[tx.transaction_id for tx in transactions],
            communication_ids=[],
            start_date=start_date,
            end_date=end_date,
            duration_days=max(duration_days, 1),
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
                "pattern_subtype": "app_mule_chain",
                "victim_account_id": account_ids[0],
                "mule_account_ids": mule_ids,
                "cash_out_account_id": account_ids[-1],
                "hop_delay_minutes": hop_delay_minutes,
                "fee_decay_applied": True,
            },
        )

        return pattern, transactions

    def _generate_chain_transactions(
        self,
        account_ids: List[str],
        start_amount: Decimal,
        hop_delay_minutes: int,
        start_date,
        end_date,
    ) -> List[Transaction]:
        """Generate sequential transfers along account chain with deterministic decay."""
        transactions: List[Transaction] = []

        # Choose deterministic anchor within window and then advance by hop delay.
        first_tx_time = random_datetime_between(start_date, end_date - timedelta(hours=1))
        current_amount = start_amount

        for hop_index in range(len(account_ids) - 1):
            from_acc = account_ids[hop_index]
            to_acc = account_ids[hop_index + 1]

            tx = self.txn_gen.generate(
                from_account_id=from_acc,
                to_account_id=to_acc,
                transaction_type=TransactionType.TRANSFER,
            )

            # Override critical fields for deterministic APP mule-chain semantics.
            tx.transaction_date = first_tx_time + timedelta(minutes=hop_index * hop_delay_minutes)
            tx.posting_date = tx.transaction_date
            tx.value_date = tx.transaction_date.date()
            tx.amount = current_amount
            tx.currency = "USD"
            tx.description = f"APP mule-chain hop {hop_index + 1}"
            tx.is_part_of_pattern = True
            tx.pattern_type = "mule_chain"

            # 2-6% decay to emulate mule extraction/fees while retaining deterministic randomness.
            decay = Decimal(str(random.uniform(0.94, 0.98)))
            current_amount = (current_amount * decay).quantize(Decimal("0.01"))

            transactions.append(tx)

        return transactions

    def _calculate_severity_score(
        self, confidence_score: float, hop_count: int, total_value: Decimal
    ) -> float:
        """Calculate bounded severity score (0-1)."""
        score = confidence_score * 0.5
        score += min(hop_count * 0.08, 0.25)

        if total_value >= Decimal("100000"):
            score += 0.2
        elif total_value >= Decimal("50000"):
            score += 0.1

        return min(score, 1.0)

    def _determine_risk_level(self, severity_score: float) -> RiskLevel:
        """Map severity score to RiskLevel enum."""
        if severity_score >= 0.85:
            return RiskLevel.CRITICAL
        if severity_score >= 0.65:
            return RiskLevel.HIGH
        if severity_score >= 0.40:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
