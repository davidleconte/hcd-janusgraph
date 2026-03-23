"""
Deterministic Utilities
=======================

Provides seeded UUID generation and fixed reference timestamps
to ensure fully reproducible data pipelines.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-15
"""

import hashlib
import threading
from datetime import datetime, timezone

REFERENCE_TIMESTAMP = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

_counter_lock = threading.Lock()
_counter = 0


def seeded_uuid_hex(prefix: str = "") -> str:
    """Generate a deterministic UUID-like hex string.
    
    Uses SHA-256 hashing with an internal counter to produce
    reproducible identifiers across runs with the same seed.
    
    Args:
        prefix: Optional prefix to prepend to the hex string.
        
    Returns:
        12-character uppercase hex string, optionally prefixed.
    """
    global _counter
    with _counter_lock:
        _counter += 1
        current = _counter
    digest = hashlib.sha256(f"deterministic-{current}".encode()).hexdigest()[:12].upper()
    return f"{prefix}{digest}" if prefix else digest


def reset_counter(value: int = 0) -> None:
    """Reset the internal counter for deterministic UUID generation.
    
    Call this before generating data to ensure reproducible results.
    
    Args:
        value: Counter value to set (default: 0).
    """
    global _counter
    with _counter_lock:
        _counter = value


def reference_now() -> datetime:
    """Return the fixed reference timestamp for deterministic data generation.
    
    Returns:
        datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    """
    return REFERENCE_TIMESTAMP
