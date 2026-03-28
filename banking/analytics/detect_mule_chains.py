"""
APP Fraud Mule-Chain Detection Module
=====================================

Detects rapid multi-hop fund movement patterns typical of Authorized Push
Payment (APP) fraud mule chains.

Pattern example:
Victim Account -> Mule 1 -> Mule 2 -> Cash-out Account (within short time windows)
"""

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from gremlin_python.driver import client, serializer

logger = logging.getLogger(__name__)


@dataclass
class MuleChainAlert:
    """Alert for a detected rapid-transfer mule chain."""

    alert_id: str
    victim_account_id: str
    mule_account_ids: List[str]
    cash_out_account_id: str
    transaction_ids: List[str]
    hop_count: int
    total_value: float
    average_hop_minutes: float
    risk_score: float
    indicators: List[str]
    details: Dict[str, Any]


class MuleChainDetector:
    """
    Detect rapid multi-hop transfer chains characteristic of APP fraud cash-out behavior.
    """

    DEFAULT_MIN_HOPS = 3
    DEFAULT_MAX_HOP_MINUTES = 60

    def __init__(self, url: str = "ws://localhost:18182/gremlin"):
        """Initialize detector with JanusGraph Gremlin endpoint URL."""
        self.url = url
        self.client = None
        self.alerts: List[MuleChainAlert] = []

    def connect(self):
        """Establish connection to JanusGraph."""
        logger.info("Connecting to JanusGraph at %s...", self.url)
        self.client = client.Client(
            self.url, "g", message_serializer=serializer.GraphSONSerializersV3d0()
        )

    def close(self):
        """Close JanusGraph connection."""
        if self.client:
            self.client.close()

    def _query(self, gremlin: str) -> List[Any]:
        """Execute Gremlin query and return result list."""
        if not self.client:
            raise RuntimeError("Not connected. Call connect() first.")
        return self.client.submit(gremlin).all().result()

    def detect_mule_chains(
        self, min_hops: int = DEFAULT_MIN_HOPS, max_hop_minutes: int = DEFAULT_MAX_HOP_MINUTES
    ) -> List[MuleChainAlert]:
        """
        Detect rapid transfer chains with at least `min_hops` transactions where each hop
        occurs within `max_hop_minutes` from the previous hop.
        """
        query = """
        g.V().hasLabel('account').as('start')
         .repeat(out('sent_transaction').as('tx').out('received_by'))
         .times(3)
         .path()
         .limit(500)
        """

        alerts: List[MuleChainAlert] = []
        try:
            paths = self._query(query)
            for path in paths:
                alert = self._build_alert_from_path(path, min_hops=min_hops, max_hop_minutes=max_hop_minutes)
                if alert:
                    alerts.append(alert)
        except Exception:
            logger.warning("Mule-chain detection failed", exc_info=True)

        self.alerts.extend(alerts)
        return alerts

    def _build_alert_from_path(
        self, path: Dict[str, Any], min_hops: int, max_hop_minutes: int
    ) -> Optional[MuleChainAlert]:
        """Convert a traversal path payload into a MuleChainAlert when criteria are met."""
        transactions = path.get("transactions", [])
        accounts = path.get("accounts", [])

        if len(transactions) < min_hops:
            return None
        if len(accounts) < len(transactions) + 1:
            return None

        hop_minutes = self._calculate_hop_minutes(transactions)
        if not hop_minutes:
            return None
        if any(minutes > max_hop_minutes for minutes in hop_minutes):
            return None

        transaction_ids = [str(tx.get("transaction_id", "")) for tx in transactions]
        victim_account_id = str(accounts[0])
        cash_out_account_id = str(accounts[-1])
        mule_account_ids = [str(account_id) for account_id in accounts[1:-1]]

        total_value = float(sum(float(tx.get("amount", 0.0)) for tx in transactions))
        average_hop_minutes = sum(hop_minutes) / len(hop_minutes)
        risk_score = self._calculate_risk_score(
            hop_count=len(transactions),
            average_hop_minutes=average_hop_minutes,
            total_value=total_value,
        )

        indicators = [
            f"Rapid multi-hop chain ({len(transactions)} hops)",
            f"Average hop latency: {average_hop_minutes:.1f} minutes",
            "Potential APP fraud mule-chain cash-out behavior",
        ]

        signature = "|".join([victim_account_id, *mule_account_ids, cash_out_account_id, *transaction_ids])
        alert_id = f"APP-MULE-{hashlib.sha256(signature.encode('utf-8')).hexdigest()[:12]}"

        return MuleChainAlert(
            alert_id=alert_id,
            victim_account_id=victim_account_id,
            mule_account_ids=mule_account_ids,
            cash_out_account_id=cash_out_account_id,
            transaction_ids=transaction_ids,
            hop_count=len(transactions),
            total_value=total_value,
            average_hop_minutes=average_hop_minutes,
            risk_score=risk_score,
            indicators=indicators,
            details={
                "hop_minutes": hop_minutes,
                "min_hops_required": min_hops,
                "max_hop_minutes_allowed": max_hop_minutes,
            },
        )

    def _calculate_hop_minutes(self, transactions: List[Dict[str, Any]]) -> List[float]:
        """Calculate elapsed minutes between sequential transactions in a chain."""
        timestamps: List[datetime] = []
        for tx in transactions:
            parsed = self._parse_timestamp(tx.get("transaction_date"))
            if parsed is None:
                return []
            timestamps.append(parsed)

        hop_minutes: List[float] = []
        for i in range(1, len(timestamps)):
            delta_minutes = (timestamps[i] - timestamps[i - 1]).total_seconds() / 60.0
            if delta_minutes < 0:
                return []
            hop_minutes.append(delta_minutes)

        return hop_minutes

    def _parse_timestamp(self, value: Any) -> Optional[datetime]:
        """Parse transaction timestamp values to datetime."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str) and value.strip():
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    def _calculate_risk_score(self, hop_count: int, average_hop_minutes: float, total_value: float) -> float:
        """Compute a bounded (0-1) risk score for mule-chain alerts."""
        score = 0.4
        score += min(hop_count * 0.1, 0.3)

        if average_hop_minutes <= 10:
            score += 0.2
        elif average_hop_minutes <= 30:
            score += 0.1

        if total_value >= 100000:
            score += 0.1

        return min(score, 1.0)
