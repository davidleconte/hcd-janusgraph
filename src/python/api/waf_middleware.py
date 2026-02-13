"""
Web Application Firewall (WAF) Middleware
==========================================

OWASP-aligned request inspection middleware that blocks common attack vectors:
- SQL / Gremlin injection
- Cross-Site Scripting (XSS)
- Path traversal / Local File Inclusion (LFI)
- Command injection
- Request size & content-type enforcement
"""

import logging
import re
from dataclasses import dataclass
from typing import FrozenSet, List, Pattern
from urllib.parse import unquote

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

_SQL_PATTERNS: List[Pattern] = [
    re.compile(r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|UNION|CREATE)\b\s)", re.IGNORECASE),
    re.compile(r"(--|;)\s*(SELECT|DROP|INSERT|UPDATE|DELETE)", re.IGNORECASE),
    re.compile(r"'\s*(OR|AND)\s+'", re.IGNORECASE),
    re.compile(r"'\s*(OR|AND)\s+\d+\s*=\s*\d+", re.IGNORECASE),
    re.compile(r"SLEEP\s*\(", re.IGNORECASE),
    re.compile(r"BENCHMARK\s*\(", re.IGNORECASE),
    re.compile(r"WAITFOR\s+DELAY", re.IGNORECASE),
]

_GREMLIN_PATTERNS: List[Pattern] = [
    re.compile(r"g\s*\.\s*V\s*\("),
    re.compile(r"g\s*\.\s*E\s*\("),
    re.compile(r"\.drop\s*\(\s*\)"),
    re.compile(r"\.submit\s*\("),
    re.compile(r"System\s*\.\s*(exit|getenv|getProperty)", re.IGNORECASE),
    re.compile(r"Runtime\s*\.\s*getRuntime", re.IGNORECASE),
    re.compile(r"Thread\s*\.\s*sleep", re.IGNORECASE),
]

_XSS_PATTERNS: List[Pattern] = [
    re.compile(r"<\s*script", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on(load|error|click|mouseover|focus|blur)\s*=", re.IGNORECASE),
    re.compile(r"<\s*img[^>]+onerror\s*=", re.IGNORECASE),
    re.compile(r"<\s*iframe", re.IGNORECASE),
    re.compile(r"<\s*object", re.IGNORECASE),
    re.compile(r"<\s*embed", re.IGNORECASE),
    re.compile(r"<\s*svg[^>]+onload\s*=", re.IGNORECASE),
    re.compile(r"expression\s*\(", re.IGNORECASE),
    re.compile(r"url\s*\(\s*['\"]?\s*javascript:", re.IGNORECASE),
]

_PATH_TRAVERSAL_PATTERNS: List[Pattern] = [
    re.compile(r"\.\./"),
    re.compile(r"\.\.\\"),
    re.compile(r"%2e%2e[%2f/\\]", re.IGNORECASE),
    re.compile(r"\.\./etc/(passwd|shadow|hosts)", re.IGNORECASE),
    re.compile(r"/proc/self/", re.IGNORECASE),
    re.compile(r"\\\\[a-zA-Z0-9]"),
]

_COMMAND_INJECTION_PATTERNS: List[Pattern] = [
    re.compile(r"[;&|`]\s*(cat|ls|id|whoami|uname|pwd|wget|curl|nc|bash|sh|cmd)\b", re.IGNORECASE),
    re.compile(r"\$\(.*\)"),
    re.compile(r"`[^`]+`"),
    re.compile(r"\|\|\s*(cat|id|whoami|ls|rm|wget)", re.IGNORECASE),
    re.compile(r"&&\s*(cat|id|whoami|ls|rm|wget)", re.IGNORECASE),
]

_PROTOCOL_PATTERNS: List[Pattern] = [
    re.compile(r"(file|gopher|dict|ldap|ftp)://", re.IGNORECASE),
]

ATTACK_CATEGORIES = {
    "sql_injection": _SQL_PATTERNS,
    "gremlin_injection": _GREMLIN_PATTERNS,
    "xss": _XSS_PATTERNS,
    "path_traversal": _PATH_TRAVERSAL_PATTERNS,
    "command_injection": _COMMAND_INJECTION_PATTERNS,
    "protocol_abuse": _PROTOCOL_PATTERNS,
}


@dataclass(frozen=True)
class WAFConfig:
    max_body_bytes: int = 1_048_576  # 1 MiB
    max_url_length: int = 2048
    max_header_value_length: int = 8192
    max_query_params: int = 50
    allowed_content_types: FrozenSet[str] = frozenset(
        {"application/json", "application/x-www-form-urlencoded", "multipart/form-data"}
    )
    enabled_categories: FrozenSet[str] = frozenset(ATTACK_CATEGORIES.keys())
    exempt_paths: FrozenSet[str] = frozenset(
        {"/health", "/healthz", "/readyz", "/docs", "/redoc", "/openapi.json"}
    )
    log_blocked: bool = True
    dry_run: bool = False


def _check_patterns(value: str, categories: dict, enabled: FrozenSet[str]) -> str | None:
    for category, patterns in categories.items():
        if category not in enabled:
            continue
        for pattern in patterns:
            if pattern.search(value):
                return category
    return None


def _blocked_response(category: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={
            "error": "waf_blocked",
            "category": category,
            "detail": detail,
        },
    )


class WAFMiddleware(BaseHTTPMiddleware):
    """OWASP-aligned Web Application Firewall middleware."""

    def __init__(self, app, config: WAFConfig | None = None):
        super().__init__(app)
        self.config = config or WAFConfig()
        self._stats: dict = {"blocked": 0, "allowed": 0}

    @property
    def stats(self) -> dict:
        return dict(self._stats)

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.config.exempt_paths:
            self._stats["allowed"] += 1
            return await call_next(request)

        violation = self._inspect_request(request)
        if violation is not None:
            category, detail = violation
            self._stats["blocked"] += 1
            if self.config.log_blocked:
                logger.warning(
                    "WAF blocked request: category=%s path=%s ip=%s detail=%s",
                    category,
                    request.url.path,
                    request.client.host if request.client else "unknown",
                    detail,
                )
            if self.config.dry_run:
                response = await call_next(request)
                response.headers["X-WAF-Dry-Run"] = f"would-block:{category}"
                return response
            return _blocked_response(category, detail)

        body_violation = await self._inspect_body(request)
        if body_violation is not None:
            category, detail = body_violation
            self._stats["blocked"] += 1
            if self.config.log_blocked:
                logger.warning(
                    "WAF blocked request body: category=%s path=%s ip=%s",
                    category,
                    request.url.path,
                    request.client.host if request.client else "unknown",
                )
            if self.config.dry_run:
                response = await call_next(request)
                response.headers["X-WAF-Dry-Run"] = f"would-block:{category}"
                return response
            return _blocked_response(category, detail)

        self._stats["allowed"] += 1
        return await call_next(request)

    def _inspect_request(self, request: Request) -> tuple[str, str] | None:
        url_str = str(request.url)
        if len(url_str) > self.config.max_url_length:
            return ("request_limit", "URL exceeds maximum length")

        query_string = str(request.url.query or "")
        params = query_string.split("&") if query_string else []
        if len(params) > self.config.max_query_params:
            return ("request_limit", "Too many query parameters")

        for surface in (url_str, query_string, unquote(url_str), unquote(query_string)):
            hit = _check_patterns(surface, ATTACK_CATEGORIES, self.config.enabled_categories)
            if hit:
                return (hit, f"Suspicious pattern in URL/query: {hit}")

        for name, value in request.headers.items():
            if len(value) > self.config.max_header_value_length:
                return ("request_limit", f"Header '{name}' exceeds max length")
            if name.lower() in ("cookie", "referer", "user-agent", "x-forwarded-for"):
                hit = _check_patterns(
                    value, ATTACK_CATEGORIES, self.config.enabled_categories
                )
                if hit:
                    return (hit, f"Suspicious pattern in header '{name}': {hit}")

        if request.method in ("POST", "PUT", "PATCH"):
            ct = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
            if ct and ct not in self.config.allowed_content_types:
                return ("content_type", f"Disallowed content-type: {ct}")

        return None

    async def _inspect_body(self, request: Request) -> tuple[str, str] | None:
        if request.method not in ("POST", "PUT", "PATCH"):
            return None

        try:
            body = await request.body()
        except Exception:
            return None

        if len(body) > self.config.max_body_bytes:
            return ("request_limit", "Request body exceeds maximum size")

        try:
            text = body.decode("utf-8", errors="ignore")
        except Exception:
            return None

        if not text:
            return None

        hit = _check_patterns(text, ATTACK_CATEGORIES, self.config.enabled_categories)
        if hit:
            return (hit, f"Suspicious pattern in request body: {hit}")

        return None
