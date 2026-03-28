"""
Unit Tests for Procurement / Vendor Fraud Detector
==================================================

Tests for additive FR-032 procurement fraud analytics:
- Detector initialization and connection guard behavior
- Deterministic alert ID generation
- Signal validation and threshold filtering
- Notebook-ready record schema and deterministic ordering
"""

from unittest.mock import Mock

import pytest

from banking.analytics.detect_procurement import ProcurementFraudDetector


class TestProcurementFraudDetectorInitialization:
    """Test ProcurementFraudDetector initialization and connection guard behavior."""

    def test_init_default_url(self):
        """Test default JanusGraph URL and empty alert list."""
        detector = ProcurementFraudDetector()
        assert detector.url == "ws://localhost:18182/gremlin"
        assert detector.client is None
        assert detector.alerts == []

    def test_query_without_connection_raises(self):
        """Test _query guard when connect() has not been called."""
        detector = ProcurementFraudDetector()

        with pytest.raises(RuntimeError, match="Not connected"):
            detector._query("g.V().count()")


class TestProcurementAlertConstruction:
    """Test signal-to-alert conversion and deterministic id behavior."""

    def test_generate_alert_id_is_deterministic(self):
        """Test deterministic alert ID for identical signal signature."""
        detector = ProcurementFraudDetector()

        alert_id_one = detector._generate_alert_id(
            employee_id="EMP-001",
            vendor_id="VEND-001",
            invoice_ids=["INV-1", "INV-2"],
            shared_identifiers=["ADDR-123", "PHONE-999"],
        )
        alert_id_two = detector._generate_alert_id(
            employee_id="EMP-001",
            vendor_id="VEND-001",
            invoice_ids=["INV-2", "INV-1"],
            shared_identifiers=["PHONE-999", "ADDR-123"],
        )

        assert alert_id_one == alert_id_two
        assert alert_id_one.startswith("PROC-FRD-")
        assert len(alert_id_one) == 21

    def test_build_alert_rejects_low_risk_signal(self):
        """Test signals below threshold are filtered out."""
        detector = ProcurementFraudDetector()
        signal = {
            "employee_id": "EMP-LOW",
            "vendor_id": "VEND-LOW",
            "invoice_ids": ["INV-A", "INV-B"],
            "shared_identifiers": ["ADDR-SHARED"],
            "total_amount": 25000.0,
            "risk_score": 0.5,
        }

        alert = detector._build_alert_from_signal(signal, min_risk_score=0.6)
        assert alert is None

    def test_build_alert_rejects_incomplete_signal(self):
        """Test signals missing duplicate/collusion attributes are filtered out."""
        detector = ProcurementFraudDetector()
        signal = {
            "employee_id": "EMP-X",
            "vendor_id": "VEND-X",
            "invoice_ids": ["INV-ONLY-1"],
            "shared_identifiers": [],
            "total_amount": 10000.0,
            "risk_score": 0.9,
        }

        alert = detector._build_alert_from_signal(signal, min_risk_score=0.6)
        assert alert is None


class TestProcurementRecordsAPI:
    """Test notebook-ready records API behavior and deterministic ordering."""

    def test_detect_procurement_fraud_as_records_schema(self):
        """Test records API emits required evidence fields and rounded risk score."""
        detector = ProcurementFraudDetector()
        signals = [
            {
                "employee_id": "EMP-HIGH",
                "vendor_id": "VEND-HIGH",
                "invoice_ids": ["INV-1001", "INV-1002"],
                "shared_identifiers": ["ADDR-777", "PHONE-222"],
                "total_amount": 88234.56,
                "risk_score": 0.91234,
            }
        ]

        records = detector.detect_procurement_fraud_as_records(signals=signals)

        assert len(records) == 1
        record = records[0]
        assert set(record.keys()) == {
            "alert_id",
            "employee_id",
            "vendor_id",
            "invoice_ids",
            "shared_identifiers",
            "total_amount",
            "risk_score",
            "reason_codes",
            "rationale",
            "evidence_summary",
        }
        assert record["alert_id"].startswith("PROC-FRD-")
        assert record["employee_id"] == "EMP-HIGH"
        assert record["vendor_id"] == "VEND-HIGH"
        assert record["invoice_ids"] == ["INV-1001", "INV-1002"]
        assert record["shared_identifiers"] == ["ADDR-777", "PHONE-222"]
        assert record["total_amount"] == pytest.approx(88234.56)
        assert record["risk_score"] == pytest.approx(0.9123)
        assert record["reason_codes"] == [
            "PROC_DUPLICATE_INVOICE_SEQUENCE",
            "PROC_SHARED_IDENTIFIER_COLLUSION",
            "PROC_VENDOR_CONFLICT_OF_INTEREST",
        ]
        assert "potential collusion" in record["rationale"]
        assert "Employee=EMP-HIGH" in record["evidence_summary"]

    def test_detect_procurement_fraud_as_records_deterministic_sort(self):
        """Test records are sorted by alert_id then descending risk_score."""
        detector = ProcurementFraudDetector()
        signals = [
            {
                "employee_id": "EMP-B",
                "vendor_id": "VEND-B",
                "invoice_ids": ["INV-B1", "INV-B2"],
                "shared_identifiers": ["ADDR-B"],
                "total_amount": 20000.0,
                "risk_score": 0.7,
            },
            {
                "employee_id": "EMP-A-LOW",
                "vendor_id": "VEND-A",
                "invoice_ids": ["INV-A1", "INV-A2"],
                "shared_identifiers": ["ADDR-A"],
                "total_amount": 15000.0,
                "risk_score": 0.64,
            },
            {
                "employee_id": "EMP-A-HIGH",
                "vendor_id": "VEND-A",
                "invoice_ids": ["INV-A3", "INV-A4"],
                "shared_identifiers": ["ADDR-A"],
                "total_amount": 30000.0,
                "risk_score": 0.95,
            },
        ]

        detector._generate_alert_id = Mock(
            side_effect=[
                "PROC-FRD-bbbbbbbbbbbb",
                "PROC-FRD-aaaaaaaaaaaa",
                "PROC-FRD-aaaaaaaaaaaa",
            ]
        )

        records = detector.detect_procurement_fraud_as_records(signals=signals)

        assert [record["alert_id"] for record in records] == [
            "PROC-FRD-aaaaaaaaaaaa",
            "PROC-FRD-aaaaaaaaaaaa",
            "PROC-FRD-bbbbbbbbbbbb",
        ]
        assert [record["risk_score"] for record in records] == [0.95, 0.64, 0.7]
