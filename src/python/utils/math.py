"""Math helpers for deterministic score normalization."""

from __future__ import annotations


def normalize_score_100(score: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Normalize a bounded score to a 0-100 scale."""
    bounded_score = min(max(score, min_val), max_val)
    return round(bounded_score * 100, 2)
