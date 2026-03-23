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
_current_seed = 0  # Track the current seed for hash generation


def seeded_uuid_hex(prefix: str = "", seed: int = None) -> str:
    """Generate a deterministic UUID-like hex string.
    
    Uses SHA-256 hashing with seed and counter to produce
    reproducible identifiers across runs with the same seed.
    
    Args:
        prefix: Optional prefix to prepend to the hex string.
        seed: Optional seed to use for this UUID. If None, uses internal counter only.
              When provided, combines seed with counter for guaranteed determinism.
        
    Returns:
        12-character uppercase hex string, optionally prefixed.
    """
    global _counter, _current_seed
    with _counter_lock:
        _counter += 1
        current = _counter
        current_seed = seed if seed is not None else _current_seed
    # Include seed in hash for guaranteed determinism
    digest = hashlib.sha256(f"deterministic-{current_seed}-{current}".encode()).hexdigest()[:12].upper()
    return f"{prefix}{digest}" if prefix else digest


def reset_counter(value: int = 0, seed: int = None) -> None:
    """Reset the internal counter for deterministic UUID generation.
    
    Call this before generating data to ensure reproducible results.
    
    Args:
        value: Counter value to set (default: 0).
        seed: Optional seed to store for UUID generation. If None, keeps current seed.
    """
    global _counter, _current_seed
    with _counter_lock:
        _counter = value
        if seed is not None:
            _current_seed = seed


def reference_now() -> datetime:
    """Return the fixed reference timestamp for deterministic data generation.
    
    Returns:
        datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    """
    return REFERENCE_TIMESTAMP
