"""
Additional tests to achieve 100% coverage for AuditLogger.

These tests cover the remaining uncovered lines:
- Lines 256-257: Unknown authentication action (else branch)
- Line 451: Global audit logger initialization

Created: 2026-04-08
Phase 1: Compliance Module 100% Coverage
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from banking.compliance.audit_logger import (
    AuditLogger,
    AuditEventType,
    AuditSeverity,
    get_audit_logger,
    _audit_logger
)

# Fixed timestamp for deterministic tests
FIXED_TIMESTAMP = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def temp_log_dir():
    """Create temporary log directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestAuthenticationUnknownAction:
    """Test authentication logging with unknown action (lines 256-257)."""
    
    @patch('banking.compliance.audit_logger.datetime')
    def test_log_authentication_unknown_action_success(self, mock_datetime, temp_log_dir):
        """Test authentication with unknown action and success result."""
        mock_datetime.now.return_value = FIXED_TIMESTAMP
        
        logger = AuditLogger(log_dir=temp_log_dir)
        
        # Call with unknown action (not "login" or "logout") and success result
        logger.log_authentication(
            user="test_user",
            action="unknown_action",  # This triggers the else branch
            result="success",
            ip_address="192.168.1.1"
        )
        
        # Verify event was logged
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path) as f:
            log_line = f.read().strip()
        
        parsed = json.loads(log_line)
        assert parsed["event_type"] == "auth_failed"  # Unknown action defaults to AUTH_FAILED
        assert parsed["severity"] == "warning"
        assert parsed["user"] == "test_user"
        assert parsed["action"] == "unknown_action"
        assert parsed["result"] == "success"
    
    @patch('banking.compliance.audit_logger.datetime')
    def test_log_authentication_invalid_action_success(self, mock_datetime, temp_log_dir):
        """Test authentication with invalid action and success result."""
        mock_datetime.now.return_value = FIXED_TIMESTAMP
        
        logger = AuditLogger(log_dir=temp_log_dir)
        
        # Call with invalid action
        logger.log_authentication(
            user="admin",
            action="invalid",  # This also triggers the else branch
            result="success",
            ip_address="10.0.0.1",
            metadata={"reason": "testing"}
        )
        
        # Verify event was logged with AUTH_FAILED type
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path) as f:
            log_line = f.read().strip()
        
        parsed = json.loads(log_line)
        assert parsed["event_type"] == "auth_failed"
        assert parsed["severity"] == "warning"
        assert parsed["action"] == "invalid"
    
    @patch('banking.compliance.audit_logger.datetime')
    def test_log_authentication_empty_action_success(self, mock_datetime, temp_log_dir):
        """Test authentication with empty action string."""
        mock_datetime.now.return_value = FIXED_TIMESTAMP
        
        logger = AuditLogger(log_dir=temp_log_dir)
        
        # Call with empty action
        logger.log_authentication(
            user="user123",
            action="",  # Empty string triggers else branch
            result="success"
        )
        
        # Verify event was logged
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path) as f:
            log_line = f.read().strip()
        
        parsed = json.loads(log_line)
        assert parsed["event_type"] == "auth_failed"
        assert parsed["severity"] == "warning"
        assert parsed["action"] == ""
    
    @patch('banking.compliance.audit_logger.datetime')
    def test_log_authentication_refresh_action(self, mock_datetime, temp_log_dir):
        """Test authentication with 'refresh' action (common but not login/logout)."""
        mock_datetime.now.return_value = FIXED_TIMESTAMP
        
        logger = AuditLogger(log_dir=temp_log_dir)
        
        # Call with refresh action
        logger.log_authentication(
            user="api_user",
            action="refresh",  # Common action that's not login/logout
            result="success",
            metadata={"token_type": "refresh"}
        )
        
        # Verify event was logged
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path) as f:
            log_line = f.read().strip()
        
        parsed = json.loads(log_line)
        assert parsed["event_type"] == "auth_failed"
        assert parsed["severity"] == "warning"
        assert parsed["action"] == "refresh"


class TestGlobalAuditLoggerInitialization:
    """Test global audit logger initialization (line 451)."""
    
    @patch('banking.compliance.audit_logger.Path.mkdir')
    @patch('banking.compliance.audit_logger.logging.FileHandler')
    def test_get_audit_logger_creates_instance_when_none(self, mock_file_handler, mock_mkdir):
        """Test that get_audit_logger creates new instance when _audit_logger is None (line 451)."""
        import banking.compliance.audit_logger as audit_module
        
        # Mock the file handler to avoid file system operations
        mock_handler = MagicMock()
        mock_file_handler.return_value = mock_handler
        
        # Reset global instance to None to trigger initialization path
        audit_module._audit_logger = None
        
        # Call get_audit_logger - should create new instance (line 451)
        logger = get_audit_logger()
        
        # Verify instance was created
        assert logger is not None
        assert isinstance(logger, AuditLogger)
        assert audit_module._audit_logger is logger
        
        # Verify subsequent calls return same instance (singleton)
        logger2 = get_audit_logger()
        assert logger2 is logger
    
    @patch('banking.compliance.audit_logger.Path.mkdir')
    def test_get_audit_logger_returns_existing_instance(self, mock_mkdir, temp_log_dir):
        """Test that get_audit_logger returns existing instance when not None."""
        import banking.compliance.audit_logger as audit_module
        
        # Create a logger instance directly with temp directory
        audit_module._audit_logger = AuditLogger(log_dir=temp_log_dir)
        first_logger = audit_module._audit_logger
        
        # Call get_audit_logger - should return existing instance
        second_logger = get_audit_logger()
        
        # Verify same instance returned (singleton pattern)
        assert first_logger is second_logger
        assert audit_module._audit_logger is first_logger
    
    @patch('banking.compliance.audit_logger.Path.mkdir')
    def test_get_audit_logger_singleton_pattern(self, mock_mkdir, temp_log_dir):
        """Test that get_audit_logger implements singleton pattern correctly."""
        import banking.compliance.audit_logger as audit_module
        
        # Reset to None and create with temp directory
        audit_module._audit_logger = None
        
        # Create first instance with temp directory
        audit_module._audit_logger = AuditLogger(log_dir=temp_log_dir)
        logger1 = audit_module._audit_logger
        
        # Get logger multiple times - should return same instance
        logger2 = get_audit_logger()
        logger3 = get_audit_logger()
        
        # All should be the same instance
        assert logger1 is logger2
        assert logger2 is logger3
        assert audit_module._audit_logger is logger1


class TestAuthenticationEdgeCases:
    """Additional edge case tests for authentication logging."""
    
    @patch('banking.compliance.audit_logger.datetime')
    def test_log_authentication_special_characters_in_action(self, mock_datetime, temp_log_dir):
        """Test authentication with special characters in action."""
        mock_datetime.now.return_value = FIXED_TIMESTAMP
        
        logger = AuditLogger(log_dir=temp_log_dir)
        
        # Call with action containing special characters
        logger.log_authentication(
            user="test_user",
            action="login@#$%",  # Special characters
            result="success"
        )
        
        # Verify event was logged
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path) as f:
            log_line = f.read().strip()
        
        parsed = json.loads(log_line)
        assert parsed["event_type"] == "auth_failed"
        assert parsed["action"] == "login@#$%"
    
    @patch('banking.compliance.audit_logger.datetime')
    def test_log_authentication_numeric_action(self, mock_datetime, temp_log_dir):
        """Test authentication with numeric action."""
        mock_datetime.now.return_value = FIXED_TIMESTAMP
        
        logger = AuditLogger(log_dir=temp_log_dir)
        
        # Call with numeric action
        logger.log_authentication(
            user="test_user",
            action="12345",  # Numeric string
            result="success"
        )
        
        # Verify event was logged
        log_path = Path(temp_log_dir) / "audit.log"
        with open(log_path) as f:
            log_line = f.read().strip()
        
        parsed = json.loads(log_line)
        assert parsed["event_type"] == "auth_failed"
        assert parsed["action"] == "12345"


# Summary of coverage improvements:
# 1. Lines 256-257: Covered by test_log_authentication_unknown_action_success and related tests
# 2. Line 451: Covered by test_get_audit_logger_creates_instance_when_none
# 3. Additional edge cases for robustness
#
# Expected coverage after these tests: 100% for audit_logger.py

# Made with Bob
