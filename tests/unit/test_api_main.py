#!/usr/bin/env python3
"""Tests for FastAPI Analytics API endpoints."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.python.api.main import (
    HealthResponse, UBORequest, UBOOwner, UBOResponse,
    StructuringAlertRequest, StructuringAlert, StructuringResponse
)


class TestPydanticModels:
    """Test Pydantic model validation."""

    def test_health_response(self):
        response = HealthResponse(
            status="healthy",
            timestamp="2026-02-06T12:00:00Z",
            services={"janusgraph": True, "opensearch": True}
        )
        assert response.status == "healthy"
        assert response.services["janusgraph"] is True

    def test_ubo_request_defaults(self):
        request = UBORequest(company_id="comp-123")
        assert request.company_id == "comp-123"
        assert request.include_indirect is True
        assert request.max_depth == 10
        assert request.ownership_threshold == 25.0

    def test_ubo_request_custom(self):
        request = UBORequest(
            company_id="comp-456",
            include_indirect=False,
            max_depth=5,
            ownership_threshold=50.0
        )
        assert request.max_depth == 5
        assert request.ownership_threshold == 50.0

    def test_ubo_owner(self):
        owner = UBOOwner(
            person_id="person-123",
            name="John Doe",
            ownership_percentage=30.0,
            ownership_type="direct",
            chain_length=1
        )
        assert owner.name == "John Doe"
        assert owner.ownership_percentage == 30.0

    def test_structuring_alert_request_defaults(self):
        request = StructuringAlertRequest()
        assert request.account_id is None
        assert request.time_window_days == 7
        assert request.threshold_amount == 10000.0

    def test_structuring_alert(self):
        alert = StructuringAlert(
            account_id="acc-123",
            account_holder="Jane Smith",
            total_amount=9500.0,
            transaction_count=5,
            time_window="7 days",
            risk_score=0.85,
            pattern_type="just_below_threshold"
        )
        assert alert.risk_score == 0.85
        assert alert.pattern_type == "just_below_threshold"

    def test_structuring_response(self):
        alert = StructuringAlert(
            account_id="acc-123",
            account_holder="Jane Smith",
            total_amount=9500.0,
            transaction_count=5,
            time_window="7 days",
            risk_score=0.85,
            pattern_type="smurfing"
        )
        response = StructuringResponse(
            alerts=[alert],
            total_alerts=1,
            analysis_period="7 days",
            query_time_ms=42.5
        )
        assert response.total_alerts == 1
        assert response.query_time_ms == 42.5
        assert len(response.alerts) == 1
        assert len(response.alerts) == 1


class TestAPIConfiguration:
    """Test API configuration."""

    def test_default_janusgraph_config(self):
        from src.python.config.settings import get_settings
        settings = get_settings()
        assert settings.janusgraph_host == "localhost"
        assert isinstance(settings.janusgraph_port, int)


class TestHealthEndpoints:
    """Test liveness and readiness probe endpoints."""

    @pytest.fixture(autouse=True)
    def client(self):
        from fastapi.testclient import TestClient
        from src.python.api.main import app
        self.client = TestClient(app)

    def test_liveness_returns_200(self):
        resp = self.client.get("/healthz")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_readiness_returns_200(self):
        resp = self.client.get("/readyz")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "services" in data

    def test_health_alias_returns_200(self):
        resp = self.client.get("/health")
        assert resp.status_code == 200

    def test_docs_accessible(self):
        resp = self.client.get("/docs")
        assert resp.status_code == 200

    def test_openapi_json(self):
        resp = self.client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert "paths" in schema
        assert "/healthz" in schema["paths"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
