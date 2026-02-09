"""Tests for resilience utilities: CircuitBreaker and retry_with_backoff."""

import time
import pytest
from unittest.mock import patch

from src.python.utils.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
    CircuitState,
    retry_with_backoff,
)


class TestCircuitBreakerConfig:
    def test_defaults(self):
        cfg = CircuitBreakerConfig()
        assert cfg.failure_threshold == 5
        assert cfg.recovery_timeout == 30.0
        assert cfg.half_open_max_calls == 1

    def test_custom(self):
        cfg = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=10.0, half_open_max_calls=2)
        assert cfg.failure_threshold == 3


class TestCircuitBreaker:
    def test_initial_state_closed(self):
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request() is True

    def test_opens_after_threshold(self):
        cfg = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker(config=cfg, name="test")
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.allow_request() is False

    def test_half_open_after_recovery_timeout(self):
        cfg = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.05)
        cb = CircuitBreaker(config=cfg, name="test")
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        time.sleep(0.06)
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.allow_request() is True
        assert cb.allow_request() is False

    def test_half_open_success_closes(self):
        cfg = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.01)
        cb = CircuitBreaker(config=cfg)
        cb.record_failure()
        time.sleep(0.02)
        assert cb.state == CircuitState.HALF_OPEN
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_reset(self):
        cfg = CircuitBreakerConfig(failure_threshold=1)
        cb = CircuitBreaker(config=cfg)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request() is True

    def test_record_success_resets_count(self):
        cfg = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker(config=cfg)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED


class TestRetryWithBackoff:
    @patch("src.python.utils.resilience.time.sleep")
    def test_retries_on_failure(self, mock_sleep):
        call_count = 0

        @retry_with_backoff(max_retries=2, base_delay=0.1)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "ok"

        assert flaky() == "ok"
        assert call_count == 3
        assert mock_sleep.call_count == 2

    @patch("src.python.utils.resilience.time.sleep")
    def test_raises_after_exhausted(self, mock_sleep):
        @retry_with_backoff(max_retries=1, base_delay=0.01)
        def always_fail():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            always_fail()

    @patch("src.python.utils.resilience.time.sleep")
    def test_respects_retryable_exceptions(self, mock_sleep):
        @retry_with_backoff(max_retries=2, retryable_exceptions=(ValueError,))
        def wrong_type():
            raise TypeError("not retryable")

        with pytest.raises(TypeError):
            wrong_type()

    @patch("src.python.utils.resilience.time.sleep")
    def test_with_circuit_breaker(self, mock_sleep):
        cfg = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreaker(config=cfg, name="retry-test")

        @retry_with_backoff(max_retries=3, base_delay=0.01, circuit_breaker=cb)
        def fail_twice():
            raise ValueError("err")

        with pytest.raises(ValueError):
            fail_twice()
        assert cb.state == CircuitState.OPEN

    def test_circuit_open_rejects(self):
        cfg = CircuitBreakerConfig(failure_threshold=1)
        cb = CircuitBreaker(config=cfg, name="open-test")
        cb.record_failure()

        @retry_with_backoff(circuit_breaker=cb)
        def should_not_run():
            return "ran"

        with pytest.raises(CircuitOpenError):
            should_not_run()

    @patch("src.python.utils.resilience.time.sleep")
    def test_success_records_to_breaker(self, mock_sleep):
        cb = CircuitBreaker(name="success-test")

        @retry_with_backoff(circuit_breaker=cb)
        def ok():
            return 42

        assert ok() == 42

    @patch("src.python.utils.resilience.time.sleep")
    def test_max_delay_cap(self, mock_sleep):
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=100.0, max_delay=5.0)
        def fail_then_ok():
            nonlocal call_count
            call_count += 1
            if call_count < 4:
                raise ValueError("fail")
            return "ok"

        assert fail_then_ok() == "ok"
        for call in mock_sleep.call_args_list:
            assert call[0][0] <= 5.0
