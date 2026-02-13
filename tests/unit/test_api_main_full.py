"""Comprehensive tests for src.python.api.main and routers — targets main 44% → 80%+, ubo 41% → 80%+."""
import os
import sys
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("AUDIT_LOG_DIR", "/tmp/janusgraph-test-logs")

from unittest.mock import patch as _patch, MagicMock as _MagicMock
with _patch("banking.compliance.audit_logger.AuditLogger.__init__", lambda self, *a, **kw: None):
    with _patch("banking.compliance.audit_logger.AuditLogger.log_event", _MagicMock()):
        import banking.compliance.audit_logger as _al
        _al._audit_logger = _MagicMock()

from src.python.api.main import create_app, _error_response, _configure_logging
from src.python.api.dependencies import close_graph_connection, flatten_value_map, PUBLIC_PATHS


class TestErrorResponse:
    def test_returns_json_response(self):
        resp = _error_response(404, "not_found", "Not found")
        assert resp.status_code == 404
        import json
        body = json.loads(resp.body)
        assert body["error"] == "not_found"
        assert body["detail"] == "Not found"
        assert "timestamp" in body

    def test_500_error(self):
        resp = _error_response(500, "internal_error", "Boom")
        assert resp.status_code == 500


class TestConfigureLogging:
    def test_standard_format(self):
        from src.python.config.settings import Settings
        settings = Settings()
        settings.log_json = False
        _configure_logging(settings)

    def test_json_format(self):
        from src.python.config.settings import Settings
        settings = Settings()
        settings.log_json = True
        try:
            _configure_logging(settings)
        except ImportError:
            pytest.skip("pythonjsonlogger not installed")


class TestAppCreation:
    def test_create_app(self):
        app = create_app()
        assert app.title == "Graph Analytics API"

    def test_app_has_routers(self):
        app = create_app()
        paths = [r.path for r in app.routes]
        assert any("/healthz" in p for p in paths)


class TestAPIEndpoints:
    @pytest.fixture(autouse=True)
    def setup_client(self):
        from src.python.api.main import app
        self.client = TestClient(app)

    def test_healthz(self):
        resp = self.client.get("/healthz")
        assert resp.status_code == 200

    def test_ubo_discover_404(self):
        with patch("src.python.api.routers.ubo.get_graph_connection") as mock_conn:
            mock_g = MagicMock()
            mock_repo_cls = MagicMock()
            mock_repo_inst = MagicMock()
            mock_repo_inst.get_company.return_value = None
            mock_repo_cls.return_value = mock_repo_inst
            mock_conn.return_value = mock_g

            with patch("src.python.api.routers.ubo.GraphRepository", mock_repo_cls):
                resp = self.client.post("/api/v1/ubo/discover", json={"company_id": "COMP-MISSING"})
                assert resp.status_code == 404

    def test_ubo_discover_success(self):
        with patch("src.python.api.routers.ubo.get_graph_connection") as mock_conn:
            mock_repo_cls = MagicMock()
            mock_repo = MagicMock()
            mock_repo.get_company.return_value = {"legal_name": "Acme"}
            mock_repo.find_direct_owners.return_value = [
                {"person_id": "p-1", "name": "Alice", "ownership_percentage": 30.0}
            ]
            mock_repo_cls.return_value = mock_repo
            mock_conn.return_value = MagicMock()

            with patch("src.python.api.routers.ubo.GraphRepository", mock_repo_cls):
                resp = self.client.post("/api/v1/ubo/discover", json={"company_id": "COMP-00001"})
                assert resp.status_code == 200
                data = resp.json()
                assert len(data["ubos"]) == 1

    def test_ubo_network_404(self):
        with patch("src.python.api.routers.ubo.get_graph_connection") as mock_conn:
            mock_repo_cls = MagicMock()
            mock_repo_cls.return_value.get_company.return_value = None
            mock_conn.return_value = MagicMock()

            with patch("src.python.api.routers.ubo.GraphRepository", mock_repo_cls):
                resp = self.client.get("/api/v1/ubo/network/MISSING")
                assert resp.status_code == 404

    def test_ubo_network_success(self):
        with patch("src.python.api.routers.ubo.get_graph_connection") as mock_conn:
            mock_repo_cls = MagicMock()
            mock_repo = MagicMock()
            mock_repo.get_company.return_value = {"legal_name": "Acme"}
            mock_repo.get_owner_vertices.return_value = [
                {"person_id": "p-1", "full_name": "Alice"}
            ]
            mock_repo_cls.return_value = mock_repo
            mock_conn.return_value = MagicMock()

            with patch("src.python.api.routers.ubo.GraphRepository", mock_repo_cls):
                resp = self.client.get("/api/v1/ubo/network/C-1")
                assert resp.status_code == 200
                data = resp.json()
                assert len(data["nodes"]) >= 1

    def test_http_exception_handler(self):
        resp = self.client.get("/nonexistent-path")
        assert resp.status_code in (404, 405)

    def test_docs_accessible(self):
        resp = self.client.get("/docs")
        assert resp.status_code == 200


class TestAMLRouter:
    @pytest.fixture(autouse=True)
    def setup_client(self):
        from src.python.api.main import app
        self.client = TestClient(app)

    def test_structuring_success(self):
        with patch("src.python.api.routers.aml.get_graph_connection") as mock_conn:
            mock_repo_cls = MagicMock()
            mock_repo = MagicMock()
            mock_repo.get_account_transaction_summaries.return_value = [
                {"account_id": "ACC-001", "holder": "Alice", "txn_count": 15, "total": 140000.0},
            ]
            mock_repo_cls.return_value = mock_repo
            mock_conn.return_value = MagicMock()

            with patch("src.python.api.routers.aml.GraphRepository", mock_repo_cls):
                resp = self.client.post("/api/v1/aml/structuring", json={})
                assert resp.status_code == 200
                data = resp.json()
                assert "alerts" in data
                assert "total_alerts" in data

    def test_structuring_with_alert(self):
        with patch("src.python.api.routers.aml.get_graph_connection") as mock_conn:
            mock_repo_cls = MagicMock()
            mock_repo = MagicMock()
            mock_repo.get_account_transaction_summaries.return_value = [
                {"account_id": "ACC-001", "holder": "Bob", "txn_count": 10, "total": 90000.0},
            ]
            mock_repo_cls.return_value = mock_repo
            mock_conn.return_value = MagicMock()

            with patch("src.python.api.routers.aml.GraphRepository", mock_repo_cls):
                resp = self.client.post("/api/v1/aml/structuring", json={
                    "threshold_amount": 10000.0,
                    "min_transaction_count": 3,
                })
                assert resp.status_code == 200
                data = resp.json()
                assert data["total_alerts"] >= 1

    def test_structuring_no_alerts(self):
        with patch("src.python.api.routers.aml.get_graph_connection") as mock_conn:
            mock_repo_cls = MagicMock()
            mock_repo = MagicMock()
            mock_repo.get_account_transaction_summaries.return_value = []
            mock_repo_cls.return_value = mock_repo
            mock_conn.return_value = MagicMock()

            with patch("src.python.api.routers.aml.GraphRepository", mock_repo_cls):
                resp = self.client.post("/api/v1/aml/structuring", json={})
                assert resp.status_code == 200
                assert resp.json()["total_alerts"] == 0


class TestHealthRouter:
    @pytest.fixture(autouse=True)
    def setup_client(self):
        from src.python.api.main import app
        self.client = TestClient(app)

    def test_readyz_healthy(self):
        with patch("src.python.api.routers.health.get_graph_connection") as mock_conn:
            mock_repo_cls = MagicMock()
            mock_repo_cls.return_value.health_check.return_value = True
            mock_conn.return_value = MagicMock()
            with patch("src.python.api.routers.health.GraphRepository", mock_repo_cls):
                resp = self.client.get("/readyz")
                assert resp.status_code == 200
                assert resp.json()["status"] == "healthy"

    def test_readyz_degraded(self):
        with patch("src.python.api.routers.health.get_graph_connection") as mock_conn:
            mock_repo_cls = MagicMock()
            mock_repo_cls.return_value.health_check.return_value = False
            mock_conn.return_value = MagicMock()
            with patch("src.python.api.routers.health.GraphRepository", mock_repo_cls):
                resp = self.client.get("/readyz")
                assert resp.status_code == 200
                assert resp.json()["status"] == "degraded"

    def test_readyz_exception(self):
        with patch("src.python.api.routers.health.get_graph_connection", side_effect=Exception("down")):
            resp = self.client.get("/readyz")
            assert resp.status_code == 200
            data = resp.json()
            assert data["services"]["janusgraph"] is False

    def test_stats(self):
        with patch("src.python.api.routers.health.get_graph_connection") as mock_conn:
            mock_repo_cls = MagicMock()
            mock_repo_cls.return_value.graph_stats.return_value = {
                "vertex_count": 100, "edge_count": 200,
                "person_count": 50, "company_count": 20,
                "account_count": 30, "transaction_count": 80,
            }
            mock_conn.return_value = MagicMock()
            with patch("src.python.api.routers.health.GraphRepository", mock_repo_cls):
                resp = self.client.get("/stats")
                assert resp.status_code == 200


class TestGetGraphConnection:
    def test_creates_connection(self):
        import src.python.api.dependencies as deps
        old_conn = deps._connection
        old_trav = deps._traversal
        deps._connection = None
        deps._traversal = None

        with patch("src.python.api.dependencies.DriverRemoteConnection") as mock_drc:
            with patch("src.python.api.dependencies.traversal") as mock_trav:
                mock_trav.return_value.with_remote.return_value = MagicMock()
                result = deps.get_graph_connection()
                assert result is not None
                mock_drc.assert_called_once()

        deps._connection = old_conn
        deps._traversal = old_trav

    def test_reuses_connection(self):
        import src.python.api.dependencies as deps
        old_conn = deps._connection
        old_trav = deps._traversal
        mock_t = MagicMock()
        deps._connection = MagicMock()
        deps._traversal = mock_t

        result = deps.get_graph_connection()
        assert result is mock_t

        deps._connection = old_conn
        deps._traversal = old_trav

    def test_connection_failure(self):
        import src.python.api.dependencies as deps
        from fastapi import HTTPException
        old_conn = deps._connection
        old_trav = deps._traversal
        deps._connection = None
        deps._traversal = None

        with patch("src.python.api.dependencies.DriverRemoteConnection", side_effect=Exception("fail")):
            with pytest.raises(HTTPException) as exc_info:
                deps.get_graph_connection()
            assert exc_info.value.status_code == 503

        deps._connection = old_conn
        deps._traversal = old_trav


class TestVerifyAuth:
    def test_auth_enabled_no_token(self):
        from src.python.api.main import app
        with patch("src.python.api.dependencies.get_settings") as mock_settings:
            s = MagicMock()
            s.auth_enabled = True
            s.api_key = "secret-key"
            s.rate_limit_per_minute = 60
            s.cors_origins_list = ["*"]
            s.api_cors_origins = "*"
            mock_settings.return_value = s
            client = TestClient(app)
            resp = client.get("/api/v1/ubo/network/COMP-00001")
            assert resp.status_code == 401


class TestDependencies:
    def test_public_paths(self):
        assert "/health" in PUBLIC_PATHS
        assert "/docs" in PUBLIC_PATHS

    def test_flatten_value_map(self):
        result = flatten_value_map({"name": ["Alice"], "age": [30]})
        assert result["name"] == "Alice"

    def test_close_graph_connection(self):
        import src.python.api.dependencies as deps
        old = deps._connection
        deps._connection = MagicMock()
        close_graph_connection()
        assert deps._connection is None
        deps._connection = old

    def test_verify_auth_disabled(self):
        from src.python.api.main import app
        client = TestClient(app)
        resp = client.get("/healthz")
        assert resp.status_code == 200
