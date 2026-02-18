"""Tests for src.python.utils.resilience module."""

import time

import pytest

from src.python.utils.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
    CircuitState,
    retry_with_backoff,
)


class TestCircuitBreakerConfig:
    def test_defaults(self):
        c = CircuitBreakerConfig()
        assert c.failure_threshold == 5
        assert c.recovery_timeout == 30.0
        assert c.half_open_max_calls == 1

    def test_custom(self):
        c = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=10.0, half_open_max_calls=2)
        assert c.failure_threshold == 3


class TestCircuitState:
    def test_values(self):
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"


class TestCircuitBreaker:
    def test_initial_state(self):
        cb = CircuitBreaker(name="test")
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request() is True

    def test_record_success_resets(self):
        cb = CircuitBreaker(name="test")
        cb.record_failure()
        cb.record_success()
        assert cb._failure_count == 0

    def test_opens_after_threshold(self):
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker(config=config, name="test")
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.allow_request() is False

    def test_half_open_after_timeout(self):
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.1)
        cb = CircuitBreaker(config=config, name="test")
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        time.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.allow_request() is True

    def test_half_open_limits_calls(self):
        config = CircuitBreakerConfig(
            failure_threshold=1, recovery_timeout=0.1, half_open_max_calls=1
        )
        cb = CircuitBreaker(config=config, name="test")
        cb.record_failure()
        time.sleep(0.15)
        assert cb.allow_request() is True
        assert cb.allow_request() is False

    def test_half_open_success_closes(self):
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.1)
        cb = CircuitBreaker(config=config, name="test")
        cb.record_failure()
        time.sleep(0.15)
        cb.state  # trigger transition
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_reset(self):
        config = CircuitBreakerConfig(failure_threshold=1)
        cb = CircuitBreaker(config=config, name="test")
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        cb.reset()
        assert cb.state == CircuitState.CLOSED


class TestRetryWithBackoff:
    def test_succeeds_first_try(self):
        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def ok():
            return 42

        assert ok() == 42

    def test_retries_on_failure(self):
        attempts = [0]

        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def flaky():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ValueError("fail")
            return "ok"

        assert flaky() == "ok"
        assert attempts[0] == 3

    def test_raises_after_exhaustion(self):
        @retry_with_backoff(max_retries=1, base_delay=0.01)
        def always_fail():
            raise RuntimeError("permanent")

        with pytest.raises(RuntimeError):
            always_fail()

    def test_circuit_breaker_integration(self):
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker(config=config, name="test")

        @retry_with_backoff(max_retries=0, base_delay=0.01, circuit_breaker=cb)
        def fail():
            raise ValueError("fail")

        for _ in range(3):
            with pytest.raises(ValueError):
                fail()
        assert cb.state == CircuitState.OPEN
        with pytest.raises(CircuitOpenError):
            fail()

    def test_only_retries_specified_exceptions(self):
        @retry_with_backoff(max_retries=2, base_delay=0.01, retryable_exceptions=(ValueError,))
        def wrong_type():
            raise TypeError("not retryable")

        with pytest.raises(TypeError):
            wrong_type()


class TestCircuitOpenError:
    def test_is_exception(self):
        assert issubclass(CircuitOpenError, Exception)
        e = CircuitOpenError("open")
        assert str(e) == "open"
