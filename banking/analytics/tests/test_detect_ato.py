"""
Unit Tests for Account Takeover (ATO) Detector
==============================================

Tests for additive FR-031 ATO analytics:
- Detector initialization and connection guard behavior
- Deterministic alert ID generation
- Risk-threshold and required-field filtering
- Notebook-ready record schema and deterministic ordering
"""

from unittest.mock import Mock

import pytest

from banking.analytics.detect_ato import ATODetector


class TestATODetectorInitialization:
    """Test ATODetector initialization and connection guard behavior."""

    def test_init_default_url(self):
        """Test default JanusGraph URL and empty alert list."""
        detector = ATODetector()
        assert detector.url == "ws://localhost:18182/gremlin"
        assert detector.client is None
        assert detector.alerts == []

    def test_query_without_connection_raises(self):
        """Test _query guard when connect() has not been called."""
        detector = ATODetector()

        with pytest.raises(RuntimeError, match="Not connected"):
            detector._query("g.V().count()")


class TestATOAlertConstruction:
    """Test event-to-alert conversion and deterministic id behavior."""

    def test_generate_alert_id_is_deterministic(self):
        """Test deterministic alert ID for identical event signature."""
        detector = ATODetector()

        alert_id_one = detector._generate_alert_id(
            account_id="ACC-001",
            novel_device_id="DEV-NEW-9",
            novel_ip="203.0.113.42",
            event_timestamp="2026-01-15T12:00:00Z",
        )
        alert_id_two = detector._generate_alert_id(
            account_id="ACC-001",
            novel_device_id="DEV-NEW-9",
            novel_ip="203.0.113.42",
            event_timestamp="2026-01-15T12:00:00Z",
        )

        assert alert_id_one == alert_id_two
        assert alert_id_one.startswith("APP-ATO-")
        assert len(alert_id_one) == 20

    def test_build_alert_rejects_low_risk_event(self):
        """Test events below threshold are filtered out."""
        detector = ATODetector()
        event = {
            "account_id": "ACC-LOW",
            "novel_device_id": "DEV-LOW",
            "novel_ip": "198.51.100.7",
            "event_timestamp": "2026-01-15T12:00:00Z",
            "risk_score": 0.4,
        }

        alert = detector._build_alert_from_event(event, min_risk_score=0.6)
        assert alert is None

    def test_build_alert_rejects_missing_required_fields(self):
        """Test events missing required identity fields are filtered out."""
        detector = ATODetector()
        event = {
            "account_id": "ACC-MISSING",
            "novel_device_id": "",
            "novel_ip": "198.51.100.8",
            "event_timestamp": "2026-01-15T12:10:00Z",
            "risk_score": 0.9,
        }

        alert = detector._build_alert_from_event(event, min_risk_score=0.6)
        assert alert is None


class TestATORecordsAPI:
    """Test notebook-ready records API behavior and deterministic ordering."""

    def test_detect_ato_as_records_schema(self):
        """Test records API emits required evidence fields and rounded risk score."""
        detector = ATODetector()
        events = [
            {
                "account_id": "ACC-HIGH",
                "novel_device_id": "DEV-NEW-1",
                "novel_ip": "203.0.113.50",
                "event_timestamp": "2026-01-15T12:30:00Z",
                "risk_score": 0.87654,
            }
        ]

        records = detector.detect_ato_as_records(events=events)

        assert len(records) == 1
        record = records[0]
        assert set(record.keys()) == {
            "alert_id",
            "account_id",
            "novel_device_id",
            "novel_ip",
            "event_timestamp",
            "risk_score",
            "reason_codes",
            "rationale",
            "evidence_summary",
        }
        assert record["alert_id"].startswith("APP-ATO-")
        assert record["account_id"] == "ACC-HIGH"
        assert record["novel_device_id"] == "DEV-NEW-1"
        assert record["novel_ip"] == "203.0.113.50"
        assert record["event_timestamp"] == "2026-01-15T12:30:00Z"
        assert record["risk_score"] == pytest.approx(0.8765)
        assert record["reason_codes"] == [
            "ATO_DEVICE_NOVELTY",
            "ATO_IP_NOVELTY",
            "ATO_SESSION_RISK",
        ]
        assert "potential account takeover behavior" in record["rationale"]
        assert "Account=ACC-HIGH" in record["evidence_summary"]

    def test_detect_ato_as_records_deterministic_sort(self):
        """Test records are sorted by alert_id then descending risk_score."""
        detector = ATODetector()

        events = [
            {
                "account_id": "ACC-B",
                "novel_device_id": "DEV-B",
                "novel_ip": "203.0.113.2",
                "event_timestamp": "2026-01-15T12:01:00Z",
                "risk_score": 0.7,
            },
            {
                "account_id": "ACC-A-LOW",
                "novel_device_id": "DEV-A",
                "novel_ip": "203.0.113.1",
                "event_timestamp": "2026-01-15T12:00:00Z",
                "risk_score": 0.62,
            },
            {
                "account_id": "ACC-A-HIGH",
                "novel_device_id": "DEV-A",
                "novel_ip": "203.0.113.1",
                "event_timestamp": "2026-01-15T12:00:00Z",
                "risk_score": 0.95,
            },
        ]

        # Patch deterministic IDs to force tie on alert_id and validate secondary sort key.
        detector._generate_alert_id = Mock(
            side_effect=[
                "APP-ATO-bbbbbbbbbbbb",
                "APP-ATO-aaaaaaaaaaaa",
                "APP-ATO-aaaaaaaaaaaa",
            ]
        )

        records = detector.detect_ato_as_records(events=events)

        assert [record["alert_id"] for record in records] == [
            "APP-ATO-aaaaaaaaaaaa",
            "APP-ATO-aaaaaaaaaaaa",
            "APP-ATO-bbbbbbbbbbbb",
        ]
        assert [record["risk_score"] for record in records] == [0.95, 0.62, 0.7]
