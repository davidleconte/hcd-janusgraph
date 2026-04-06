"""
Test Seed Validation
====================

Tests for seed validation in MasterOrchestrator to ensure only approved
seeds are used for deterministic baseline generation.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-04-06
"""

import pytest

from banking.data_generators.orchestration.master_orchestrator import (
    VALID_SEEDS,
    GenerationConfig,
    MasterOrchestrator,
    validate_seed,
)


class TestSeedValidation:
    """Test suite for seed validation."""

    def test_valid_seeds_constant(self):
        """Test that VALID_SEEDS contains expected values."""
        assert VALID_SEEDS == {42, 123, 999}
        assert 42 in VALID_SEEDS  # Primary
        assert 123 in VALID_SEEDS  # Secondary
        assert 999 in VALID_SEEDS  # Stress test

    def test_validate_seed_with_valid_seeds(self):
        """Test that valid seeds pass validation."""
        # Should not raise
        validate_seed(42)
        validate_seed(123)
        validate_seed(999)
        validate_seed(None)  # None is allowed (non-deterministic mode)

    def test_validate_seed_with_invalid_seed(self):
        """Test that invalid seeds raise ValueError."""
        with pytest.raises(ValueError, match="Invalid seed 100"):
            validate_seed(100)

        with pytest.raises(ValueError, match="Invalid seed 1"):
            validate_seed(1)

        with pytest.raises(ValueError, match="Invalid seed -1"):
            validate_seed(-1)

    def test_validate_seed_error_message_contains_valid_seeds(self):
        """Test that error message lists valid seeds."""
        with pytest.raises(ValueError) as exc_info:
            validate_seed(100)

        error_msg = str(exc_info.value)
        assert "42" in error_msg
        assert "123" in error_msg
        assert "999" in error_msg
        assert "Primary baseline" in error_msg
        assert "Secondary baseline" in error_msg
        assert "Stress test baseline" in error_msg

    def test_validate_seed_error_message_contains_docs_link(self):
        """Test that error message references documentation."""
        with pytest.raises(ValueError) as exc_info:
            validate_seed(100)

        error_msg = str(exc_info.value)
        assert "docs/operations/deterministic-baseline-management.md" in error_msg

    def test_master_orchestrator_with_valid_seed(self):
        """Test that MasterOrchestrator accepts valid seeds."""
        # Should not raise
        config = GenerationConfig(seed=42)
        orchestrator = MasterOrchestrator(config)
        assert orchestrator.config.seed == 42

        config = GenerationConfig(seed=123)
        orchestrator = MasterOrchestrator(config)
        assert orchestrator.config.seed == 123

        config = GenerationConfig(seed=999)
        orchestrator = MasterOrchestrator(config)
        assert orchestrator.config.seed == 999

    def test_master_orchestrator_with_none_seed(self):
        """Test that MasterOrchestrator accepts None seed (non-deterministic)."""
        config = GenerationConfig(seed=None)
        orchestrator = MasterOrchestrator(config)
        assert orchestrator.config.seed is None

    def test_master_orchestrator_with_invalid_seed(self):
        """Test that MasterOrchestrator rejects invalid seeds."""
        config = GenerationConfig(seed=100)
        with pytest.raises(ValueError, match="Invalid seed 100"):
            MasterOrchestrator(config)

    def test_master_orchestrator_default_config_no_seed(self):
        """Test that MasterOrchestrator with default config (no seed) works."""
        # Default GenerationConfig has seed=None
        orchestrator = MasterOrchestrator()
        assert orchestrator.config.seed is None

    def test_seed_validation_boundary_values(self):
        """Test seed validation with boundary values."""
        # Valid seeds
        validate_seed(42)
        validate_seed(123)
        validate_seed(999)

        # Invalid: just outside valid set
        with pytest.raises(ValueError):
            validate_seed(41)

        with pytest.raises(ValueError):
            validate_seed(43)

        with pytest.raises(ValueError):
            validate_seed(122)

        with pytest.raises(ValueError):
            validate_seed(124)

        with pytest.raises(ValueError):
            validate_seed(998)

        with pytest.raises(ValueError):
            validate_seed(1000)

    def test_seed_validation_with_zero(self):
        """Test that seed=0 is rejected."""
        with pytest.raises(ValueError, match="Invalid seed 0"):
            validate_seed(0)

    def test_seed_validation_with_negative(self):
        """Test that negative seeds are rejected."""
        with pytest.raises(ValueError, match="Invalid seed -42"):
            validate_seed(-42)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
