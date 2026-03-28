"""
Corporate Procurement / Vendor Fraud Detection Module
=====================================================

Detects duplicate invoice and employee-vendor collusion indicators with
deterministic alert identifiers and notebook-ready evidence records.
"""

import hashlib
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from gremlin_python.driver import client, serializer

logger = logging.getLogger(__name__)


@dataclass
class ProcurementFraudAlert:
    """Alert for a detected procurement/vendor fraud signal."""

    alert_id: str
    employee_id: str
    vendor_id: str
    invoice_ids: List[str]
    shared_identifiers: List[str]
    total_amount: float
    risk_score: float
    reason_codes: List[str]
    rationale: str
    evidence_summary: str


class ProcurementFraudDetector:
    """Detect procurement fraud indicators using deterministic event payload evaluation."""

    DEFAULT_MIN_RISK_SCORE = 0.6

    def __init__(self, url: str = "ws://localhost:18182/gremlin"):
        """Initialize detector with JanusGraph Gremlin endpoint URL."""
        self.url = url
        self.client = None
        self.alerts: List[ProcurementFraudAlert] = []

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
        employee_id: str,
        vendor_id: str,
        invoice_ids: List[str],
        shared_identifiers: List[str],
    ) -> str:
        """Generate deterministic procurement-fraud alert id from stable event signature."""
        signature = "|".join(
            [
                employee_id,
                vendor_id,
                *sorted(str(invoice_id) for invoice_id in invoice_ids),
                *sorted(str(identifier) for identifier in shared_identifiers),
            ]
        )
        digest = hashlib.sha256(signature.encode("utf-8")).hexdigest()[:12]
        return f"PROC-FRD-{digest}"

    def _build_alert_from_signal(
        self,
        signal: Dict[str, Any],
        min_risk_score: float,
    ) -> Optional[ProcurementFraudAlert]:
        """Build a procurement-fraud alert from one signal payload when criteria are met."""
        employee_id = str(signal.get("employee_id", "")).strip()
        vendor_id = str(signal.get("vendor_id", "")).strip()
        invoice_ids = [str(invoice_id) for invoice_id in signal.get("invoice_ids", []) if str(invoice_id)]
        shared_identifiers = [
            str(identifier) for identifier in signal.get("shared_identifiers", []) if str(identifier)
        ]
        total_amount = float(signal.get("total_amount", 0.0))
        risk_score = float(signal.get("risk_score", 0.0))

        if not employee_id or not vendor_id:
            return None
        if len(invoice_ids) < 2:
            return None
        if not shared_identifiers:
            return None
        if risk_score < min_risk_score:
            return None

        alert_id = self._generate_alert_id(
            employee_id=employee_id,
            vendor_id=vendor_id,
            invoice_ids=invoice_ids,
            shared_identifiers=shared_identifiers,
        )
        reason_codes = [
            "PROC_DUPLICATE_INVOICE_SEQUENCE",
            "PROC_SHARED_IDENTIFIER_COLLUSION",
            "PROC_VENDOR_CONFLICT_OF_INTEREST",
        ]
        rationale = (
            "Invoice and identifier patterns indicate potential collusion between "
            "internal employee and vendor entities."
        )
        evidence_summary = (
            f"Employee={employee_id}; Vendor={vendor_id}; Invoices={len(invoice_ids)}; "
            f"SharedIdentifiers={len(shared_identifiers)}; Total=${total_amount:,.2f}; "
            f"Risk={risk_score:.3f}"
        )

        return ProcurementFraudAlert(
            alert_id=alert_id,
            employee_id=employee_id,
            vendor_id=vendor_id,
            invoice_ids=invoice_ids,
            shared_identifiers=shared_identifiers,
            total_amount=total_amount,
            risk_score=risk_score,
            reason_codes=reason_codes,
            rationale=rationale,
            evidence_summary=evidence_summary,
        )

    def detect_procurement_fraud(
        self,
        min_risk_score: float = DEFAULT_MIN_RISK_SCORE,
        signals: Optional[List[Dict[str, Any]]] = None,
    ) -> List[ProcurementFraudAlert]:
        """
        Detect procurement fraud signals from payloads.

        If `signals` is provided, signals are evaluated directly (deterministic test path).
        Graph-backed detection can be layered on later without changing output contract.
        """
        alerts: List[ProcurementFraudAlert] = []

        signal_payloads = signals or []
        for signal in signal_payloads:
            alert = self._build_alert_from_signal(signal, min_risk_score=min_risk_score)
            if alert:
                alerts.append(alert)

        self.alerts.extend(alerts)
        return alerts

    def detect_procurement_fraud_as_records(
        self,
        min_risk_score: float = DEFAULT_MIN_RISK_SCORE,
        signals: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Detect procurement fraud and return stable, notebook-ready evidence records."""
        alerts = self.detect_procurement_fraud(min_risk_score=min_risk_score, signals=signals)
        records: List[Dict[str, Any]] = []

        for alert in alerts:
            records.append(
                {
                    "alert_id": alert.alert_id,
                    "employee_id": alert.employee_id,
                    "vendor_id": alert.vendor_id,
                    "invoice_ids": alert.invoice_ids,
                    "shared_identifiers": alert.shared_identifiers,
                    "total_amount": alert.total_amount,
                    "risk_score": round(alert.risk_score, 4),
                    "reason_codes": alert.reason_codes,
                    "rationale": alert.rationale,
                    "evidence_summary": alert.evidence_summary,
                }
            )

        return sorted(records, key=lambda item: (item["alert_id"], -item["risk_score"]))
