"""Unit tests for deterministic startup/import-time budget gate."""

from src.python.performance.startup_budget_gate import (
    StartupSampleMetrics,
    aggregate_samples,
    evaluate_gate,
)


def _scenario_config() -> dict:
    return {
        "samples": 3,
        "significant_breach_count": 2,
        "import_targets": [
            "src.python.config.settings",
            "src.python.utils.startup_validation",
            "src.python.client.connection_pool",
        ],
        "app_factory_target": "src.python.config.settings:get_settings",
        "budgets": {
            "max_noop_startup_ms": 300.0,
            "max_total_import_ms": 4000.0,
            "max_single_import_ms": 1600.0,
            "max_app_factory_ms": 1200.0,
        },
        "baseline_medians": {
            "noop_startup_ms": 120.0,
            "total_import_ms": 1800.0,
            "max_single_import_ms": 700.0,
            "app_factory_ms": 250.0,
        },
        "regression_tolerances_pct": {
            "max_noop_startup_increase_pct": 70.0,
            "max_total_import_increase_pct": 60.0,
            "max_single_import_increase_pct": 60.0,
            "max_app_factory_increase_pct": 70.0,
        },
    }


def _sample(
    *,
    noop_ms: float = 100.0,
    total_import_ms: float = 1500.0,
    max_single_import_ms: float = 600.0,
    app_factory_ms: float = 200.0,
) -> StartupSampleMetrics:
    return StartupSampleMetrics(
        noop_startup_ms=noop_ms,
        total_import_ms=total_import_ms,
        max_single_import_ms=max_single_import_ms,
        app_factory_ms=app_factory_ms,
        import_timings_ms={
            "src.python.config.settings": max_single_import_ms,
            "src.python.utils.startup_validation": total_import_ms * 0.3,
            "src.python.client.connection_pool": total_import_ms * 0.2,
        },
    )


def test_aggregate_samples_uses_median():
    samples = [
        _sample(total_import_ms=1200.0, max_single_import_ms=500.0),
        _sample(total_import_ms=1500.0, max_single_import_ms=600.0),
        _sample(total_import_ms=2000.0, max_single_import_ms=900.0),
    ]
    summary = aggregate_samples(samples)
    assert summary["total_import_ms"] == 1500.0
    assert summary["max_single_import_ms"] == 600.0


def test_evaluate_gate_passes_within_thresholds():
    samples = [
        _sample(),
        _sample(noop_ms=110.0, total_import_ms=1600.0, app_factory_ms=230.0),
        _sample(noop_ms=95.0, total_import_ms=1450.0, app_factory_ms=190.0),
    ]
    passed, violations, summary = evaluate_gate(samples, _scenario_config())
    assert passed is True
    assert violations == []
    assert summary["app_factory_ms"] <= 230.0


def test_evaluate_gate_fails_on_significant_import_regression():
    samples = [
        _sample(total_import_ms=3300.0, max_single_import_ms=1400.0),
        _sample(total_import_ms=3200.0, max_single_import_ms=1300.0),
        _sample(total_import_ms=1500.0, max_single_import_ms=600.0),
    ]
    passed, violations, _ = evaluate_gate(samples, _scenario_config())
    assert passed is False
    assert any("total_import_ms" in violation for violation in violations)


def test_evaluate_gate_does_not_fail_on_single_outlier():
    samples = [
        _sample(),
        _sample(total_import_ms=3400.0, max_single_import_ms=1500.0, app_factory_ms=800.0),
        _sample(),
    ]
    passed, violations, _ = evaluate_gate(samples, _scenario_config())
    assert passed is True
    assert violations == []
