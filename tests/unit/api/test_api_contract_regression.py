"""
API contract regression tests.

These tests protect backward-compatible API contracts by validating:
1) critical path/method availability
2) request/response model bindings in OpenAPI
3) key validation constraints for regulated inputs
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("AUDIT_LOG_DIR", "/tmp/janusgraph-test-logs")

src_path = str(Path(__file__).parent.parent.parent.parent / "src" / "python")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

with patch("banking.compliance.audit_logger.AuditLogger.__init__", lambda self, *a, **kw: None):
    with patch("banking.compliance.audit_logger.AuditLogger.log_event", MagicMock()):
        import banking.compliance.audit_logger as _al

        _al._audit_logger = MagicMock()

with patch.dict(
    "sys.modules",
    {
        "gremlin_python": MagicMock(),
        "gremlin_python.driver": MagicMock(),
        "gremlin_python.driver.driver_remote_connection": MagicMock(),
        "gremlin_python.driver.serializer": MagicMock(),
        "gremlin_python.process": MagicMock(),
        "gremlin_python.process.anonymous_traversal": MagicMock(),
        "gremlin_python.process.graph_traversal": MagicMock(),
        "gremlin_python.process.traversal": MagicMock(),
    },
):
    from src.python.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def _openapi(client: TestClient) -> dict:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    return response.json()


def _schema_ref_name(schema_obj: dict) -> str:
    ref = schema_obj["$ref"]
    return ref.rsplit("/", maxsplit=1)[-1]


def test_critical_paths_and_methods_are_stable(client: TestClient):
    schema = _openapi(client)
    paths = schema["paths"]

    expected = {
        "/healthz": {"get"},
        "/readyz": {"get"},
        "/health": {"get"},
        "/stats": {"get"},
        "/api/v1/ubo/discover": {"post"},
        "/api/v1/ubo/network/{company_id}": {"get"},
        "/api/v1/aml/structuring": {"post"},
        "/api/v1/fraud/rings": {"get"},
        "/api/v1/auth/login": {"post"},
        "/api/v1/auth/refresh": {"post"},
        "/api/v1/auth/logout": {"post"},
        "/api/v1/performance/cache/stats": {"get"},
        "/api/v1/performance/cache/invalidate": {"post"},
        "/api/v1/performance/profiler/config": {"get", "put"},
    }

    for path, required_methods in expected.items():
        assert path in paths, f"Missing API path: {path}"
        available = set(paths[path].keys())
        assert required_methods.issubset(available), (
            f"Path {path} missing methods {required_methods - available}"
        )


def test_core_response_models_are_stable(client: TestClient):
    schema = _openapi(client)
    paths = schema["paths"]

    expected = {
        ("/healthz", "get"): "LivenessResponse",
        ("/readyz", "get"): "HealthResponse",
        ("/health", "get"): "HealthResponse",
        ("/stats", "get"): "GraphStatsResponse",
        ("/api/v1/ubo/discover", "post"): "UBOResponse",
        ("/api/v1/ubo/network/{company_id}", "get"): "NetworkResponse",
        ("/api/v1/aml/structuring", "post"): "StructuringResponse",
        ("/api/v1/auth/login", "post"): "LoginResponse",
        ("/api/v1/auth/refresh", "post"): "RefreshTokenResponse",
        ("/api/v1/auth/logout", "post"): "LogoutResponse",
        ("/api/v1/performance/cache/stats", "get"): "CacheStatsResponse",
        ("/api/v1/performance/profiler/config", "get"): "ProfilerConfigResponse",
        ("/api/v1/performance/profiler/config", "put"): "ProfilerConfigResponse",
    }

    for (path, method), model_name in expected.items():
        operation = paths[path][method]
        schema_obj = operation["responses"]["200"]["content"]["application/json"]["schema"]
        assert _schema_ref_name(schema_obj) == model_name


def test_core_request_models_are_stable(client: TestClient):
    schema = _openapi(client)
    paths = schema["paths"]

    expected = {
        ("/api/v1/ubo/discover", "post"): "UBORequest",
        ("/api/v1/aml/structuring", "post"): "StructuringAlertRequest",
        ("/api/v1/auth/login", "post"): "LoginRequest",
        ("/api/v1/auth/refresh", "post"): "RefreshTokenRequest",
        ("/api/v1/auth/logout", "post"): "LogoutRequest",
        ("/api/v1/performance/cache/invalidate", "post"): "CacheInvalidateRequest",
        ("/api/v1/performance/profiler/config", "put"): "ProfilerConfigRequest",
    }

    for (path, method), model_name in expected.items():
        operation = paths[path][method]
        schema_obj = operation["requestBody"]["content"]["application/json"]["schema"]
        assert _schema_ref_name(schema_obj) == model_name


def test_ubo_network_parameter_contract(client: TestClient):
    schema = _openapi(client)
    params = schema["paths"]["/api/v1/ubo/network/{company_id}"]["get"]["parameters"]
    params_by_name = {p["name"]: p for p in params}

    assert "company_id" in params_by_name
    company_id = params_by_name["company_id"]
    assert company_id["in"] == "path"
    assert company_id["required"] is True
    assert company_id["schema"]["type"] == "string"

    assert "depth" in params_by_name
    depth = params_by_name["depth"]
    assert depth["in"] == "query"
    assert depth["required"] is False
    assert depth["schema"]["type"] == "integer"
    assert depth["schema"]["default"] == 3
    assert depth["schema"]["minimum"] == 1
    assert depth["schema"]["maximum"] == 5


def test_regulated_input_validation_constraints(client: TestClient):
    schema = _openapi(client)
    components = schema["components"]["schemas"]

    ubo_request = components["UBORequest"]
    company_id = ubo_request["properties"]["company_id"]
    assert company_id["type"] == "string"
    assert company_id["minLength"] == 5
    assert company_id["maxLength"] == 50
    assert company_id["pattern"] == "^[A-Z0-9\\-_]+$"

    structuring_request = components["StructuringAlertRequest"]
    time_window_days = structuring_request["properties"]["time_window_days"]
    assert time_window_days["type"] == "integer"
    assert time_window_days["minimum"] == 1
    assert time_window_days["maximum"] == 90
    assert time_window_days["default"] == 7

    refresh_request = components["RefreshTokenRequest"]
    refresh_token = refresh_request["properties"]["refresh_token"]
    assert refresh_token["type"] == "string"
    assert refresh_token["minLength"] == 32


def test_validation_error_contract_is_stable(client: TestClient):
    schema = _openapi(client)
    ubo_discover = schema["paths"]["/api/v1/ubo/discover"]["post"]
    validation_schema = ubo_discover["responses"]["422"]["content"]["application/json"]["schema"]
    assert _schema_ref_name(validation_schema) == "HTTPValidationError"
