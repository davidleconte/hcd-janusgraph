"""
Account Takeover (ATO) Detection Module
=======================================

Detects account takeover indicators such as novel device and IP usage,
with deterministic alert identifiers and notebook-ready evidence records.
"""

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from gremlin_python.driver import client, serializer

logger = logging.getLogger(__name__)


@dataclass
class ATOAlert:
    """Alert for a detected account takeover signal."""

    alert_id: str
    account_id: str
    novel_device_id: str
    novel_ip: str
    event_timestamp: str
    risk_score: float
    reason_codes: List[str]
    rationale: str
    evidence_summary: str


class ATODetector:
    """Detect account takeover behavior using novelty indicators."""

    DEFAULT_MIN_RISK_SCORE = 0.6

    def __init__(self, url: str = "ws://localhost:18182/gremlin"):
        """Initialize detector with JanusGraph Gremlin endpoint URL."""
        self.url = url
        self.client = None
        self.alerts: List[ATOAlert] = []

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

    def _generate_alert_id(
        self,
        account_id: str,
        novel_device_id: str,
        novel_ip: str,
        event_timestamp: str,
    ) -> str:
        """Generate deterministic ATO alert id from stable event signature."""
        signature = "|".join([account_id, novel_device_id, novel_ip, event_timestamp])
        digest = hashlib.sha256(signature.encode("utf-8")).hexdigest()[:12]
        return f"APP-ATO-{digest}"

    def _build_alert_from_event(
        self, event: Dict[str, Any], min_risk_score: float
    ) -> Optional[ATOAlert]:
        """Build an ATO alert from one event payload when criteria are met."""
        account_id = str(event.get("account_id", "")).strip()
        novel_device_id = str(event.get("novel_device_id", "")).strip()
        novel_ip = str(event.get("novel_ip", "")).strip()
        event_timestamp = str(event.get("event_timestamp", "")).strip()
        risk_score = float(event.get("risk_score", 0.0))

        if not account_id or not novel_device_id or not novel_ip or not event_timestamp:
            return None
        if risk_score < min_risk_score:
            return None

        alert_id = self._generate_alert_id(
            account_id=account_id,
            novel_device_id=novel_device_id,
            novel_ip=novel_ip,
            event_timestamp=event_timestamp,
        )
        reason_codes = [
            "ATO_DEVICE_NOVELTY",
            "ATO_IP_NOVELTY",
            "ATO_SESSION_RISK",
        ]
        rationale = (
            "Login activity showed novel device and IP characteristics consistent "
            "with potential account takeover behavior."
        )
        evidence_summary = (
            f"Account={account_id}; Device={novel_device_id}; IP={novel_ip}; "
            f"Risk={risk_score:.3f}; EventTime={event_timestamp}"
        )

        return ATOAlert(
            alert_id=alert_id,
            account_id=account_id,
            novel_device_id=novel_device_id,
            novel_ip=novel_ip,
            event_timestamp=event_timestamp,
            risk_score=risk_score,
            reason_codes=reason_codes,
            rationale=rationale,
            evidence_summary=evidence_summary,
        )

    def detect_account_takeovers(
        self,
        min_risk_score: float = DEFAULT_MIN_RISK_SCORE,
        events: Optional[List[Dict[str, Any]]] = None,
    ) -> List[ATOAlert]:
        """
        Detect account takeover signals from event payloads.

        If `events` is provided, events are evaluated directly (deterministic test path).
        Graph-backed detection can be added later without changing the output contract.
        """
        alerts: List[ATOAlert] = []

        event_payloads = events or []
        for event in event_payloads:
            alert = self._build_alert_from_event(event, min_risk_score=min_risk_score)
            if alert:
                alerts.append(alert)

        self.alerts.extend(alerts)
        return alerts

    def detect_ato_as_records(
        self,
        min_risk_score: float = DEFAULT_MIN_RISK_SCORE,
        events: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Detect ATO signals and return stable, notebook-ready evidence records."""
        alerts = self.detect_account_takeovers(min_risk_score=min_risk_score, events=events)
        records: List[Dict[str, Any]] = []

        for alert in alerts:
            records.append(
                {
                    "alert_id": alert.alert_id,
                    "account_id": alert.account_id,
                    "novel_device_id": alert.novel_device_id,
                    "novel_ip": alert.novel_ip,
                    "event_timestamp": alert.event_timestamp,
                    "risk_score": round(alert.risk_score, 4),
                    "reason_codes": alert.reason_codes,
                    "rationale": alert.rationale,
                    "evidence_summary": alert.evidence_summary,
                }
            )

        return sorted(records, key=lambda item: (item["alert_id"], -item["risk_score"]))


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.utcnow().isoformat() + "Z"
