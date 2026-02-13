"""Tests for WAF middleware — OWASP attack vector detection."""

import pytest
from starlette.testclient import TestClient
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.python.api.waf_middleware import (
    WAFConfig,
    WAFMiddleware,
    _check_patterns,
    ATTACK_CATEGORIES,
)


def _make_app(config: WAFConfig | None = None) -> FastAPI:
    app = FastAPI()
    app.add_middleware(WAFMiddleware, config=config)

    @app.get("/api/test")
    async def _get():
        return {"ok": True}

    @app.post("/api/test")
    async def _post(request: Request):
        body = await request.json()
        return {"received": body}

    @app.get("/health")
    async def _health():
        return {"status": "healthy"}

    return app


@pytest.fixture
def client():
    return TestClient(_make_app())


@pytest.fixture
def dry_run_client():
    return TestClient(_make_app(WAFConfig(dry_run=True)))


class TestSQLInjection:
    def test_blocks_select_in_query(self, client):
        r = client.get("/api/test?q=SELECT * FROM users")
        assert r.status_code == 403
        assert r.json()["category"] == "sql_injection"

    def test_blocks_union_injection(self, client):
        r = client.get("/api/test?id=1 UNION SELECT password")
        assert r.status_code == 403

    def test_blocks_or_1_equals_1(self, client):
        r = client.get("/api/test?user=' OR 1=1")
        assert r.status_code == 403

    def test_blocks_sleep_injection(self, client):
        r = client.get("/api/test?id=1;SLEEP(5)")
        assert r.status_code == 403

    def test_allows_normal_query(self, client):
        r = client.get("/api/test?search=hello+world")
        assert r.status_code == 200


class TestGremlinInjection:
    def test_blocks_gremlin_v(self, client):
        r = client.get("/api/test?q=g.V()")
        assert r.status_code == 403
        assert r.json()["category"] == "gremlin_injection"

    def test_blocks_drop(self, client):
        r = client.get("/api/test?q=foo.drop()")
        assert r.status_code == 403

    def test_blocks_runtime_getruntime(self, client):
        r = client.get("/api/test?q=Runtime.getRuntime()")
        assert r.status_code == 403


class TestXSS:
    def test_blocks_script_tag(self, client):
        r = client.get("/api/test?q=<script>alert(1)</script>")
        assert r.status_code == 403
        assert r.json()["category"] == "xss"

    def test_blocks_javascript_uri(self, client):
        r = client.get("/api/test?url=javascript:alert(1)")
        assert r.status_code == 403

    def test_blocks_onerror_handler(self, client):
        r = client.get("/api/test?q=<img src=x onerror=alert(1)>")
        assert r.status_code == 403

    def test_blocks_iframe(self, client):
        r = client.get("/api/test?q=<iframe src=evil.com>")
        assert r.status_code == 403


class TestPathTraversal:
    def test_blocks_dotdot_slash(self, client):
        r = client.get("/api/test?file=../../../etc/passwd")
        assert r.status_code == 403
        assert r.json()["category"] == "path_traversal"

    def test_blocks_encoded_traversal(self, client):
        r = client.get("/api/test?file=%2e%2e%2fetc/passwd")
        assert r.status_code == 403

    def test_blocks_proc_self(self, client):
        r = client.get("/api/test?f=/proc/self/environ")
        assert r.status_code == 403


class TestCommandInjection:
    def test_blocks_semicolon_cat(self, client):
        r = client.get("/api/test?q=foo;cat /etc/passwd")
        assert r.status_code == 403
        assert r.json()["category"] == "command_injection"

    def test_blocks_backtick_exec(self, client):
        r = client.get("/api/test?q=`whoami`")
        assert r.status_code == 403

    def test_blocks_dollar_paren(self, client):
        r = client.get("/api/test?q=$(id)")
        assert r.status_code == 403


class TestProtocolAbuse:
    def test_blocks_file_protocol(self, client):
        r = client.get("/api/test?url=file:///etc/passwd")
        assert r.status_code == 403
        assert r.json()["category"] == "protocol_abuse"

    def test_blocks_gopher(self, client):
        r = client.get("/api/test?url=gopher://evil.com")
        assert r.status_code == 403


class TestRequestLimits:
    def test_blocks_long_url(self):
        config = WAFConfig(max_url_length=50)
        c = TestClient(_make_app(config))
        r = c.get("/api/test?q=" + "a" * 100)
        assert r.status_code == 403
        assert r.json()["category"] == "request_limit"

    def test_blocks_too_many_params(self):
        config = WAFConfig(max_query_params=3)
        c = TestClient(_make_app(config))
        params = "&".join(f"p{i}=v" for i in range(5))
        r = c.get(f"/api/test?{params}")
        assert r.status_code == 403

    def test_blocks_large_body(self):
        config = WAFConfig(max_body_bytes=10)
        c = TestClient(_make_app(config))
        r = c.post("/api/test", json={"data": "x" * 100})
        assert r.status_code == 403

    def test_blocks_disallowed_content_type(self):
        c = TestClient(_make_app())
        r = c.post("/api/test", content=b"<xml/>", headers={"content-type": "text/xml"})
        assert r.status_code == 403
        assert r.json()["category"] == "content_type"


class TestBodyInspection:
    def test_blocks_sql_in_body(self, client):
        r = client.post(
            "/api/test",
            json={"query": "SELECT * FROM users"},
        )
        assert r.status_code == 403
        assert r.json()["category"] == "sql_injection"

    def test_blocks_xss_in_body(self, client):
        r = client.post(
            "/api/test",
            json={"name": "<script>alert(1)</script>"},
        )
        assert r.status_code == 403

    def test_allows_clean_body(self, client):
        r = client.post("/api/test", json={"name": "John Doe"})
        assert r.status_code == 200


class TestExemptPaths:
    def test_health_exempt(self, client):
        r = client.get("/health?q=<script>alert(1)</script>")
        assert r.status_code == 200


class TestDryRunMode:
    def test_dry_run_allows_but_tags(self, dry_run_client):
        r = dry_run_client.get("/api/test?q=SELECT * FROM users")
        assert r.status_code == 200
        assert "X-WAF-Dry-Run" in r.headers
        assert "sql_injection" in r.headers["X-WAF-Dry-Run"]


class TestHeaderInspection:
    def test_blocks_xss_in_user_agent(self, client):
        r = client.get("/api/test", headers={"user-agent": "<script>alert(1)</script>"})
        assert r.status_code == 403

    def test_blocks_sql_in_referer(self, client):
        r = client.get("/api/test", headers={"referer": "http://evil.com?q=SELECT * FROM users"})
        assert r.status_code == 403


class TestCheckPatterns:
    def test_returns_none_for_clean(self):
        result = _check_patterns("hello world", ATTACK_CATEGORIES, frozenset(ATTACK_CATEGORIES.keys()))
        assert result is None

    def test_returns_category_for_match(self):
        result = _check_patterns("SELECT * FROM users", ATTACK_CATEGORIES, frozenset(ATTACK_CATEGORIES.keys()))
        assert result == "sql_injection"

    def test_respects_enabled_categories(self):
        result = _check_patterns("SELECT * FROM users", ATTACK_CATEGORIES, frozenset(["xss"]))
        assert result is None


class TestDisabledCategories:
    def test_disabled_sql_allows_through(self):
        config = WAFConfig(enabled_categories=frozenset(["xss"]))
        c = TestClient(_make_app(config))
        r = c.get("/api/test?q=SELECT * FROM users")
        assert r.status_code == 200


class TestStats:
    def test_stats_tracking(self):
        app = _make_app()
        c = TestClient(app)
        c.get("/api/test?search=safe")
        c.get("/api/test?q=SELECT * FROM users")
