#!/usr/bin/env python3
"""Tests for audit logger module."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from banking.compliance.audit_logger import AuditEventType


class TestAuditEventType:
    def test_auth_event_types_exist(self):
        assert hasattr(AuditEventType, 'AUTH_LOGIN')
        assert hasattr(AuditEventType, 'AUTH_LOGOUT')
        assert hasattr(AuditEventType, 'AUTH_FAILED')

    def test_data_event_types_exist(self):
        assert hasattr(AuditEventType, 'DATA_ACCESS')
        assert hasattr(AuditEventType, 'DATA_CREATE')
        assert hasattr(AuditEventType, 'DATA_UPDATE')
        assert hasattr(AuditEventType, 'DATA_DELETE')

    def test_compliance_event_types_exist(self):
        assert hasattr(AuditEventType, 'GDPR_DATA_REQUEST')
        assert hasattr(AuditEventType, 'AML_ALERT_GENERATED')
        assert hasattr(AuditEventType, 'FRAUD_ALERT_GENERATED')

    def test_event_type_values(self):
        assert AuditEventType.AUTH_LOGIN.value == "auth_login"
        assert AuditEventType.AUTH_LOGOUT.value == "auth_logout"
        assert AuditEventType.DATA_ACCESS.value == "data_access"


class TestAuditLogger:
    @pytest.fixture
    def temp_log_dir(self, tmp_path):
        return tmp_path / "audit_logs"

    def test_logger_can_be_imported(self):
        from banking.compliance.audit_logger import AuditLogger
        assert AuditLogger is not None

    @patch.dict(os.environ, {"AUDIT_LOG_DIR": ""})
    def test_logger_with_mocked_path(self, temp_log_dir):
        with patch("banking.compliance.audit_logger.Path") as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.mkdir = lambda **kwargs: None
            from banking.compliance.audit_logger import AuditLogger
            # Just test that import and class definition work


class TestAuditEventTypeEnumeration:
    def test_all_event_types_have_values(self):
        for event_type in AuditEventType:
            assert event_type.value is not None
            assert isinstance(event_type.value, str)

    def test_event_type_count(self):
        # Should have at least 20 event types for compliance coverage
        assert len(list(AuditEventType)) >= 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
