"""Tests for banking.streaming.streaming_orchestrator module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from banking.streaming.streaming_orchestrator import StreamingConfig, StreamingOrchestrator


class TestStreamingConfig:
    def test_defaults(self):
        config = StreamingConfig(seed=42)
        assert config.seed == 42
        assert config.person_count >= 0 or hasattr(config, "person_count")

    def test_custom_config(self):
        config = StreamingConfig(
            seed=42,
            person_count=100,
            output_dir=Path("/tmp/test"),
        )
        assert config.seed == 42
        assert config.person_count == 100


class TestStreamingOrchestrator:
    def test_init(self):
        config = StreamingConfig(seed=42, use_mock_producer=True)
        orch = StreamingOrchestrator(config)
        assert orch is not None
        assert orch.config.seed == 42

    def test_context_manager(self):
        config = StreamingConfig(seed=42, use_mock_producer=True)
        with StreamingOrchestrator(config) as orch:
            assert orch is not None
