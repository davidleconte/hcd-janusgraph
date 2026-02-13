"""Tests for src.python.security modules."""
import os
import pytest

os.environ.setdefault("AUDIT_LOG_DIR", "/tmp/janusgraph-test-logs")

from unittest.mock import patch
with patch("banking.compliance.audit_logger.AuditLogger.__init__", lambda self, *a, **kw: None):
    from src.python.security.query_sanitizer import (
        QueryComplexity, ValidationError, QueryPattern, QueryAllowlist,
    )
from src.python.security.rbac import (
    Permission, ResourceType, Role, RBACManager,
)
try:
    from src.python.security.mfa import MFAMethod, MFAConfig, MFAManager
    HAS_MFA = True
except ImportError:
    HAS_MFA = False


class TestQueryComplexity:
    def test_values(self):
        assert QueryComplexity.SIMPLE.value == 1
        assert QueryComplexity.MODERATE.value == 2
        assert QueryComplexity.COMPLEX.value == 3
        assert QueryComplexity.EXPENSIVE.value == 4


class TestQueryPattern:
    def test_creation(self):
        p = QueryPattern(
            name="test", pattern=r"^g\.V\(\)$", description="test pattern",
            complexity=QueryComplexity.SIMPLE,
        )
        assert p.name == "test"
        assert p.max_results == 1000
        assert p.timeout_seconds == 30

    def test_matches(self):
        p = QueryPattern(
            name="test", pattern=r"^g\.V\(\)$", description="test",
            complexity=QueryComplexity.SIMPLE,
        )
        assert p.matches("g.V()")
        assert not p.matches("g.E()")


class TestQueryAllowlist:
    def test_init_has_default_patterns(self):
        al = QueryAllowlist()
        assert len(al.patterns) > 0

    def test_add_pattern(self):
        al = QueryAllowlist()
        p = QueryPattern(
            name="custom", pattern=r"^custom$", description="custom",
            complexity=QueryComplexity.SIMPLE,
        )
        al.add_pattern(p)
        assert "custom" in al.patterns


class TestSanitizeGremlinQuery:
    def test_import(self):
        from src.python.security.query_sanitizer import sanitize_gremlin_query
        assert callable(sanitize_gremlin_query)


class TestPermission:
    def test_read_permissions(self):
        assert Permission.READ.value == "read"
        assert Permission.READ_OWN.value == "read_own"
        assert Permission.READ_ALL.value == "read_all"

    def test_write_permissions(self):
        assert Permission.WRITE.value == "write"

    def test_admin_permissions(self):
        assert Permission.MANAGE_USERS.value == "manage_users"
        assert Permission.MANAGE_ROLES.value == "manage_roles"


class TestResourceType:
    def test_values(self):
        assert ResourceType.VERTEX.value == "vertex"
        assert ResourceType.EDGE.value == "edge"
        assert ResourceType.GRAPH.value == "graph"


class TestRole:
    def test_creation(self):
        role = Role(name="admin", description="Administrator")
        assert role.name == "admin"


class TestRBACManager:
    def test_init(self):
        mgr = RBACManager()
        assert mgr is not None

    def test_check_permission(self):
        mgr = RBACManager()
        result = mgr.check_permission("admin", Permission.READ, ResourceType.VERTEX)
        assert isinstance(result, bool)


@pytest.mark.skipif(not HAS_MFA, reason="pyotp not installed")
class TestMFAConfig:
    def test_defaults(self):
        config = MFAConfig()
        assert config.issuer == "JanusGraph"
        assert config.digits == 6
        assert config.interval == 30
        assert config.backup_codes_count == 10
        assert "admin" in config.require_mfa_for_roles

    def test_custom_config(self):
        config = MFAConfig(issuer="TestApp", digits=8)
        assert config.issuer == "TestApp"
        assert config.digits == 8


@pytest.mark.skipif(not HAS_MFA, reason="pyotp not installed")
class TestMFAMethod:
    def test_values(self):
        assert MFAMethod.TOTP.value == "totp"
        assert MFAMethod.SMS.value == "sms"
        assert MFAMethod.EMAIL.value == "email"
        assert MFAMethod.BACKUP_CODE.value == "backup_code"


@pytest.mark.skipif(not HAS_MFA, reason="pyotp not installed")
class TestMFAManager:
    def test_init(self):
        mgr = MFAManager()
        assert mgr is not None
        assert mgr.config.issuer == "JanusGraph"

    def test_init_custom_config(self):
        config = MFAConfig(issuer="Test")
        mgr = MFAManager(config=config)
        assert mgr.config.issuer == "Test"

    def test_generate_secret(self):
        mgr = MFAManager()
        secret = mgr.generate_secret()
        assert isinstance(secret, str)
        assert len(secret) > 0

    def test_setup_totp(self):
        mgr = MFAManager()
        secret, qr_image = mgr.setup_totp("user1", "user1@test.com")
        assert isinstance(secret, str)
        assert isinstance(qr_image, bytes)
        assert len(qr_image) > 0

    def test_verify_totp(self):
        import pyotp
        mgr = MFAManager()
        secret = mgr.generate_secret()
        totp = pyotp.TOTP(secret)
        code = totp.now()
        result = mgr.verify_totp(secret, code)
        assert result is True

    def test_verify_totp_invalid(self):
        mgr = MFAManager()
        secret = mgr.generate_secret()
        result = mgr.verify_totp(secret, "000000")
        assert result is False

    def test_generate_backup_codes(self):
        mgr = MFAManager()
        codes = mgr.generate_backup_codes()
        assert len(codes) == mgr.config.backup_codes_count
        assert all(isinstance(c, str) for c in codes)
