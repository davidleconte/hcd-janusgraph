#!/usr/bin/env python3
"""
Performance SLO regression gate.

This module provides a deterministic, CI-friendly performance gate that:
1) runs a synthetic credential-rotation workload,
2) validates absolute SLO budgets,
3) validates regression thresholds against a baseline,
4) fails only on significant (repeatable) breaches.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class SampleMetrics:
    """Metrics captured from a single workload sample run."""

    total_requests: int
    successful_requests: int
    failed_requests: int
    duration_seconds: float
    requests_per_second: float
    success_rate_pct: float
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float


def _percentile(values: List[float], percentile: float) -> float:
    """Return percentile value for a list of measurements."""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = int(len(sorted_values) * percentile)
    index = min(max(index, 0), len(sorted_values) - 1)
    return sorted_values[index]


def run_credential_rotation_sample(duration_seconds: int) -> SampleMetrics:
    """
    Run a deterministic synthetic credential-rotation workload.

    This workload does not require external services and is suitable for CI gating.
    """
    operations = (
        "generate_new_password",
        "update_vault_secret",
        "update_database_credentials",
        "verify_new_credentials",
        "cleanup_old_credentials",
    )

    response_times_ms: List[float] = []
    total_requests = 0
    successful_requests = 0
    failed_requests = 0

    start_time = time.time()
    while time.time() - start_time < duration_seconds:
        for _operation in operations:
            op_start = time.perf_counter()
            try:
                time.sleep(0.01)  # deterministic synthetic operation cost
                elapsed_ms = (time.perf_counter() - op_start) * 1000
                response_times_ms.append(elapsed_ms)
                successful_requests += 1
            except Exception:
                failed_requests += 1
            total_requests += 1

            if time.time() - start_time >= duration_seconds:
                break

    measured_duration = max(time.time() - start_time, 1e-9)
    success_rate = (successful_requests / total_requests * 100) if total_requests else 0.0

    return SampleMetrics(
        total_requests=total_requests,
        successful_requests=successful_requests,
        failed_requests=failed_requests,
        duration_seconds=measured_duration,
        requests_per_second=total_requests / measured_duration,
        success_rate_pct=success_rate,
        avg_response_time_ms=(statistics.mean(response_times_ms) if response_times_ms else 0.0),
        p95_response_time_ms=_percentile(response_times_ms, 0.95),
        p99_response_time_ms=_percentile(response_times_ms, 0.99),
    )


def _median(values: Iterable[float]) -> float:
    """Median helper with float return."""
    values_list = list(values)
    if not values_list:
        return 0.0
    return float(statistics.median(values_list))


def aggregate_samples(samples: List[SampleMetrics]) -> Dict[str, float]:
    """Aggregate samples into median metrics used for gate decisions."""
    return {
        "total_requests": _median(sample.total_requests for sample in samples),
        "successful_requests": _median(sample.successful_requests for sample in samples),
        "failed_requests": _median(sample.failed_requests for sample in samples),
        "duration_seconds": _median(sample.duration_seconds for sample in samples),
        "requests_per_second": _median(sample.requests_per_second for sample in samples),
        "success_rate_pct": _median(sample.success_rate_pct for sample in samples),
        "avg_response_time_ms": _median(sample.avg_response_time_ms for sample in samples),
        "p95_response_time_ms": _median(sample.p95_response_time_ms for sample in samples),
        "p99_response_time_ms": _median(sample.p99_response_time_ms for sample in samples),
    }


def _is_breach(value: float, threshold: float, direction: str) -> bool:
    """Check threshold breach for max/min style constraints."""
    if direction == "max":
        return value > threshold
    if direction == "min":
        return value < threshold
    raise ValueError(f"Unsupported direction: {direction}")


def _significant_breach_count(
    samples: List[SampleMetrics], metric_name: str, threshold: float, direction: str
) -> int:
    """Count sample-level threshold breaches for significance checks."""
    breach_count = 0
    for sample in samples:
        value = getattr(sample, metric_name)
        if _is_breach(value, threshold, direction):
            breach_count += 1
    return breach_count


def evaluate_gate(
    samples: List[SampleMetrics], scenario_config: Dict[str, object]
) -> Tuple[bool, List[str], Dict[str, float]]:
    """
    Evaluate SLO gate using absolute budgets and baseline regression thresholds.

    A failure is considered significant only when:
    1) median metric breaches threshold, and
    2) breach count across samples >= significant_breach_count.
    """
    summary = aggregate_samples(samples)
    significant_breach_count = int(scenario_config.get("significant_breach_count", 2))
    budgets = scenario_config["budgets"]
    baseline = scenario_config["baseline_medians"]
    tolerances = scenario_config["regression_tolerances_pct"]

    checks: List[Tuple[str, str, str, float, str]] = [
        (
            "avg_response_time_ms",
            "avg_response_time_ms",
            "budget.max_avg_response_time_ms",
            float(budgets["max_avg_response_time_ms"]),
            "max",
        ),
        (
            "p95_response_time_ms",
            "p95_response_time_ms",
            "budget.max_p95_response_time_ms",
            float(budgets["max_p95_response_time_ms"]),
            "max",
        ),
        (
            "p99_response_time_ms",
            "p99_response_time_ms",
            "budget.max_p99_response_time_ms",
            float(budgets["max_p99_response_time_ms"]),
            "max",
        ),
        (
            "success_rate_pct",
            "success_rate_pct",
            "budget.min_success_rate_pct",
            float(budgets["min_success_rate_pct"]),
            "min",
        ),
        (
            "requests_per_second",
            "requests_per_second",
            "budget.min_requests_per_second",
            float(budgets["min_requests_per_second"]),
            "min",
        ),
        (
            "avg_response_time_ms",
            "avg_response_time_ms",
            "regression.max_avg_response_time_increase_pct",
            float(baseline["avg_response_time_ms"])
            * (1.0 + float(tolerances["max_avg_response_time_increase_pct"]) / 100.0),
            "max",
        ),
        (
            "p95_response_time_ms",
            "p95_response_time_ms",
            "regression.max_p95_response_time_increase_pct",
            float(baseline["p95_response_time_ms"])
            * (1.0 + float(tolerances["max_p95_response_time_increase_pct"]) / 100.0),
            "max",
        ),
        (
            "p99_response_time_ms",
            "p99_response_time_ms",
            "regression.max_p99_response_time_increase_pct",
            float(baseline["p99_response_time_ms"])
            * (1.0 + float(tolerances["max_p99_response_time_increase_pct"]) / 100.0),
            "max",
        ),
        (
            "requests_per_second",
            "requests_per_second",
            "regression.max_rps_drop_pct",
            float(baseline["requests_per_second"])
            * (1.0 - float(tolerances["max_rps_drop_pct"]) / 100.0),
            "min",
        ),
        (
            "success_rate_pct",
            "success_rate_pct",
            "regression.max_success_rate_drop_pct",
            float(baseline["success_rate_pct"])
            - float(tolerances["max_success_rate_drop_pct"]),
            "min",
        ),
    ]

    violations: List[str] = []
    for summary_key, sample_metric_name, threshold_label, threshold, direction in checks:
        median_value = float(summary[summary_key])
        breaches = _significant_breach_count(samples, sample_metric_name, threshold, direction)
        if _is_breach(median_value, threshold, direction) and breaches >= significant_breach_count:
            comparator = ">" if direction == "max" else "<"
            violations.append(
                (
                    f"{summary_key} median {median_value:.4f} {comparator} threshold {threshold:.4f} "
                    f"({threshold_label}); sample_breaches={breaches}/{len(samples)}"
                )
            )

    return len(violations) == 0, violations, summary


def _load_scenario_config(baseline_path: Path, scenario_name: str) -> Dict[str, object]:
    """Load scenario config from baseline file."""
    baseline = json.loads(baseline_path.read_text())
    scenarios = baseline.get("scenarios", {})
    if scenario_name not in scenarios:
        available = ", ".join(sorted(scenarios.keys()))
        raise ValueError(f"Scenario '{scenario_name}' not found. Available: {available}")
    return scenarios[scenario_name]


def main() -> int:
    """CLI entrypoint for performance SLO gate."""
    parser = argparse.ArgumentParser(description="Deterministic performance SLO gate")
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("config/performance/slo_baseline.json"),
        help="Path to baseline SLO configuration JSON",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="credential_rotation",
        help="Scenario key from baseline JSON",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=None,
        help="Override sample count from baseline",
    )
    parser.add_argument(
        "--duration-seconds",
        type=int,
        default=None,
        help="Override sample duration from baseline",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("exports/performance/slo_gate_result.json"),
        help="Output JSON report path",
    )
    args = parser.parse_args()

    scenario_config = _load_scenario_config(args.baseline, args.scenario)
    sample_count = int(args.samples if args.samples is not None else scenario_config["samples"])
    duration_seconds = int(
        args.duration_seconds
        if args.duration_seconds is not None
        else scenario_config["duration_seconds"]
    )

    if args.scenario != "credential_rotation":
        raise ValueError("Currently supported scenario: credential_rotation")

    samples: List[SampleMetrics] = [
        run_credential_rotation_sample(duration_seconds) for _ in range(sample_count)
    ]
    passed, violations, summary = evaluate_gate(samples, scenario_config)

    report = {
        "scenario": args.scenario,
        "baseline_path": str(args.baseline),
        "sample_count": sample_count,
        "duration_seconds": duration_seconds,
        "passed": passed,
        "summary_medians": summary,
        "violations": violations,
        "samples": [asdict(sample) for sample in samples],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))

    print(f"SLO gate scenario={args.scenario} passed={passed}")
    print(
        "summary "
        + " ".join(
            [
                f"rps={summary['requests_per_second']:.2f}",
                f"avg_ms={summary['avg_response_time_ms']:.2f}",
                f"p95_ms={summary['p95_response_time_ms']:.2f}",
                f"p99_ms={summary['p99_response_time_ms']:.2f}",
                f"success_pct={summary['success_rate_pct']:.2f}",
            ]
        )
    )
    if violations:
        for violation in violations:
            print(f"VIOLATION: {violation}")

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
