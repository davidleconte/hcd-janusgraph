"""
Banking Compliance Module

This module provides compliance-related functionality including:
- Audit logging for regulatory requirements
- GDPR data subject request handling
- Compliance reporting and analytics
- Regulatory alert generation
"""

from banking.compliance.audit_logger import AuditEvent, AuditEventType, AuditLogger

__all__ = ["AuditLogger", "AuditEvent", "AuditEventType"]
