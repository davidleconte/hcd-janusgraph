#!/usr/bin/env python3
"""Tests for FastAPI Analytics API endpoints."""

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.python.api.models import (
    HealthResponse,
    StructuringAlert,
    StructuringAlertRequest,
    StructuringResponse,
    UBOOwner,
    UBORequest,
    UBOResponse,
)


class TestPydanticModels:
    """Test Pydantic model validation."""

    def test_health_response(self):
        response = HealthResponse(
            status="healthy",
            timestamp="2026-02-06T12:00:00Z",
            services={"janusgraph": True, "opensearch": True},
        )
        assert response.status == "healthy"
        assert response.services["janusgraph"] is True

    def test_ubo_request_defaults(self):
        request = UBORequest(company_id="COMP-123")
        assert request.company_id == "COMP-123"
        assert request.include_indirect is True
        assert request.max_depth == 10
        assert request.ownership_threshold == 25.0

    def test_ubo_request_custom(self):
        request = UBORequest(
            company_id="COMP-456", include_indirect=False, max_depth=5, ownership_threshold=50.0
        )
        assert request.max_depth == 5
        assert request.ownership_threshold == 50.0

    def test_ubo_owner(self):
        owner = UBOOwner(
            person_id="person-123",
            name="John Doe",
            ownership_percentage=30.0,
            ownership_type="direct",
            chain_length=1,
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
            pattern_type="just_below_threshold",
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
            pattern_type="smurfing",
        )
        response = StructuringResponse(
            alerts=[alert], total_alerts=1, analysis_period="7 days", query_time_ms=42.5
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
        with patch("src.python.api.routers.health.get_graph_connection") as mock_conn:
            mock_g = MagicMock()
            mock_g.V.return_value.limit.return_value.count.return_value.next.return_value = 1
            mock_conn.return_value = mock_g
            resp = self.client.get("/readyz")
            assert resp.status_code == 200
            data = resp.json()
            assert "status" in data
            assert "services" in data

    def test_health_alias_returns_200(self):
        with patch("src.python.api.routers.health.get_graph_connection") as mock_conn:
            mock_g = MagicMock()
            mock_g.V.return_value.limit.return_value.count.return_value.next.return_value = 1
            mock_conn.return_value = mock_g
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


class TestConfigureLogging:
    @patch("banking.compliance.audit_logger.Path.mkdir")
    def test_configure_logging_text_format(self, _mock_mkdir):
        from src.python.api.main import _configure_logging

        settings = MagicMock()
        settings.log_level = "INFO"
        settings.log_json = False
        _configure_logging(settings)

    @patch("banking.compliance.audit_logger.Path.mkdir")
    def test_configure_logging_json_format(self, _mock_mkdir):
        from src.python.api.main import _configure_logging

        settings = MagicMock()
        settings.log_level = "DEBUG"
        settings.log_json = True
        settings.log_sanitization = True
        settings.log_redact_ip = False
        _configure_logging(settings)

    @patch("banking.compliance.audit_logger.Path.mkdir")
    def test_configure_logging_adds_pii_filter_when_enabled(self, _mock_mkdir):
        from src.python.api.main import _configure_logging
        from src.python.utils.log_sanitizer import PIISanitizer

        settings = MagicMock()
        settings.log_level = "INFO"
        settings.log_json = False
        settings.log_sanitization = True
        settings.log_redact_ip = True
        _configure_logging(settings)

        root = logging.getLogger()
        assert len(root.handlers) >= 1
        assert any(isinstance(f, PIISanitizer) for f in root.handlers[0].filters)

    @patch("banking.compliance.audit_logger.Path.mkdir")
    def test_configure_logging_skips_pii_filter_when_disabled(self, _mock_mkdir):
        from src.python.api.main import _configure_logging
        from src.python.utils.log_sanitizer import PIISanitizer

        settings = MagicMock()
        settings.log_level = "INFO"
        settings.log_json = False
        settings.log_sanitization = False
        settings.log_redact_ip = False
        _configure_logging(settings)

        root = logging.getLogger()
        assert len(root.handlers) >= 1
        assert not any(isinstance(f, PIISanitizer) for f in root.handlers[0].filters)


@patch("banking.compliance.audit_logger.Path.mkdir")
class TestErrorResponse:
    def test_error_response_structure(self, _mock_mkdir):
        from src.python.api.main import _error_response

        resp = _error_response(404, "not_found", "Resource not found")
        assert resp.status_code == 404

    def test_error_response_500(self, _mock_mkdir):
        from src.python.api.main import _error_response

        resp = _error_response(500, "internal_error", "Something went wrong")
        assert resp.status_code == 500


@patch("banking.compliance.audit_logger.Path.mkdir")
class TestLifespan:
    @patch("src.python.api.main.get_settings")
    @patch("src.python.utils.startup_validation.validate_startup")
    @patch("src.python.utils.tracing.initialize_tracing")
    @patch("src.python.api.main.close_graph_connection")
    def test_lifespan_happy_path(
        self, mock_close, mock_tracing, mock_validate, mock_settings, _mock_mkdir
    ):
        from fastapi.testclient import TestClient

        from src.python.api.main import create_app

        mock_settings.return_value = MagicMock(
            log_level="INFO",
            log_json=False,
            tracing_enabled=False,
            api_cors_origins="*",
            cors_origins_list=["*"],
            rate_limit_per_minute=60,
        )
        mock_result = MagicMock()
        mock_result.has_errors = False
        mock_result.issues = []
        mock_validate.return_value = mock_result
        mock_tracing.return_value = MagicMock()

        app = create_app()
        with TestClient(app):
            pass

        mock_close.assert_called_once()

    @patch("src.python.api.main.get_settings")
    @patch("src.python.utils.startup_validation.validate_startup")
    def test_lifespan_validation_errors(self, mock_validate, mock_settings, _mock_mkdir):
        from fastapi.testclient import TestClient

        from src.python.api.main import create_app

        mock_settings.return_value = MagicMock(
            log_level="INFO",
            log_json=False,
            tracing_enabled=False,
            api_cors_origins="*",
            cors_origins_list=["*"],
            rate_limit_per_minute=60,
        )
        mock_result = MagicMock()
        mock_result.has_errors = True
        mock_issue = MagicMock()
        mock_issue.message = "Invalid config"
        mock_result.issues = [mock_issue]
        mock_validate.return_value = mock_result

        app = create_app()
        with pytest.raises(RuntimeError, match="Startup validation failed"):
            with TestClient(app):
                pass

    @patch("src.python.api.main.get_settings")
    @patch("src.python.utils.startup_validation.validate_startup")
    @patch("src.python.utils.tracing.initialize_tracing")
    @patch("src.python.api.main.close_graph_connection")
    def test_lifespan_with_warnings(
        self, mock_close, mock_tracing, mock_validate, mock_settings, _mock_mkdir
    ):
        from fastapi.testclient import TestClient

        from src.python.api.main import create_app

        mock_settings.return_value = MagicMock(
            log_level="INFO",
            log_json=False,
            tracing_enabled=False,
            api_cors_origins="*",
            cors_origins_list=["*"],
            rate_limit_per_minute=60,
        )
        mock_result = MagicMock()
        mock_result.has_errors = False
        mock_issue = MagicMock()
        mock_issue.message = "Non-critical warning"
        mock_result.issues = [mock_issue]
        mock_validate.return_value = mock_result
        mock_tracing.return_value = MagicMock()

        app = create_app()
        with TestClient(app):
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
