"""Unit tests for deterministic performance SLO gate."""

from src.python.performance.slo_gate import SampleMetrics, aggregate_samples, evaluate_gate


def _scenario_config() -> dict:
    return {
        "significant_breach_count": 2,
        "budgets": {
            "max_avg_response_time_ms": 30.0,
            "max_p95_response_time_ms": 35.0,
            "max_p99_response_time_ms": 40.0,
            "min_success_rate_pct": 99.0,
            "min_requests_per_second": 70.0,
        },
        "baseline_medians": {
            "avg_response_time_ms": 12.0,
            "p95_response_time_ms": 12.5,
            "p99_response_time_ms": 12.6,
            "requests_per_second": 83.5,
            "success_rate_pct": 100.0,
        },
        "regression_tolerances_pct": {
            "max_avg_response_time_increase_pct": 35.0,
            "max_p95_response_time_increase_pct": 35.0,
            "max_p99_response_time_increase_pct": 35.0,
            "max_rps_drop_pct": 25.0,
            "max_success_rate_drop_pct": 1.0,
        },
        "samples": 3,
        "duration_seconds": 3,
    }


def _sample(
    *,
    rps: float = 84.0,
    avg_ms: float = 12.0,
    p95_ms: float = 12.5,
    p99_ms: float = 12.6,
    success_rate_pct: float = 100.0,
    total_requests: int = 252,
) -> SampleMetrics:
    successful = int(round(total_requests * (success_rate_pct / 100.0)))
    failed = total_requests - successful
    return SampleMetrics(
        total_requests=total_requests,
        successful_requests=successful,
        failed_requests=failed,
        duration_seconds=total_requests / rps,
        requests_per_second=rps,
        success_rate_pct=success_rate_pct,
        avg_response_time_ms=avg_ms,
        p95_response_time_ms=p95_ms,
        p99_response_time_ms=p99_ms,
    )


def test_aggregate_samples_uses_median():
    samples = [_sample(rps=70.0), _sample(rps=84.0), _sample(rps=100.0)]
    summary = aggregate_samples(samples)
    assert summary["requests_per_second"] == 84.0


def test_evaluate_gate_passes_within_thresholds():
    samples = [_sample(), _sample(rps=83.0, avg_ms=12.2), _sample(rps=85.0, avg_ms=11.8)]
    passed, violations, summary = evaluate_gate(samples, _scenario_config())
    assert passed is True
    assert violations == []
    assert summary["avg_response_time_ms"] <= 12.2


def test_evaluate_gate_fails_on_significant_latency_regression():
    samples = [
        _sample(avg_ms=24.0, p95_ms=26.0, p99_ms=27.0),
        _sample(avg_ms=25.0, p95_ms=27.0, p99_ms=28.0),
        _sample(avg_ms=12.0, p95_ms=12.5, p99_ms=12.6),
    ]
    passed, violations, _ = evaluate_gate(samples, _scenario_config())
    assert passed is False
    assert any("avg_response_time_ms" in violation for violation in violations)


def test_evaluate_gate_does_not_fail_on_single_outlier():
    samples = [
        _sample(),
        _sample(avg_ms=26.0, p95_ms=30.0, p99_ms=34.0, rps=60.0),
        _sample(),
    ]
    passed, violations, _ = evaluate_gate(samples, _scenario_config())
    assert passed is True
    assert violations == []
