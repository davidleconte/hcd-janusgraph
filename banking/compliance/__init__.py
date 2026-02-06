"""
Banking Compliance Module

This module provides compliance-related functionality including:
- Audit logging for regulatory requirements
- GDPR data subject request handling
- Compliance reporting and analytics
- Regulatory alert generation
"""

from banking.compliance.audit_logger import AuditLogger, AuditEvent, AuditEventType

__all__ = ["AuditLogger", "AuditEvent", "AuditEventType"]

# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS | +33614126117
