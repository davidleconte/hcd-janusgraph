"""Tests for src.python.utils.math module."""

from src.python.utils.math import normalize_score_100


def test_normalize_score_100_nominal():
    assert normalize_score_100(0.93) == 93.0


def test_normalize_score_100_lower_bound():
    assert normalize_score_100(-0.2) == 0.0


def test_normalize_score_100_upper_bound():
    assert normalize_score_100(1.4) == 100.0


def test_normalize_score_100_rounding():
    assert normalize_score_100(0.12345) == 12.35
