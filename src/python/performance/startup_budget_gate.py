#!/usr/bin/env python3
"""
Deterministic startup/import-time budget regression gate.

This module provides a CI-friendly gate that:
1) measures Python cold-start overhead,
2) measures import times for critical runtime modules,
3) measures API app-factory initialization cost,
4) enforces absolute budgets and baseline regression thresholds.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class StartupSampleMetrics:
    """Metrics captured from one deterministic startup/import sample."""

    noop_startup_ms: float
    total_import_ms: float
    max_single_import_ms: float
    app_factory_ms: float
    import_timings_ms: Dict[str, float]


def _median(values: Iterable[float]) -> float:
    """Median helper with float return."""
    values_list = list(values)
    if not values_list:
        return 0.0
    return float(statistics.median(values_list))


def _run_python_probe(code: str) -> str:
    """Execute an inline Python probe and return stdout."""
    process = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )
    if process.returncode != 0:
        raise RuntimeError(
            "Probe execution failed "
            f"(exit_code={process.returncode}): {process.stderr.strip() or process.stdout.strip()}"
        )
    return process.stdout.strip()


def measure_noop_startup_ms() -> float:
    """Measure subprocess cold-start overhead using a no-op Python command."""
    start = time.perf_counter()
    process = subprocess.run(
        [sys.executable, "-c", "pass"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    if process.returncode != 0:
        raise RuntimeError(
            "No-op startup probe failed "
            f"(exit_code={process.returncode}): {process.stderr.strip()}"
        )
    return elapsed_ms


def measure_module_import_ms(module_name: str) -> float:
    """Measure import latency (ms) for one module in a fresh Python process."""
    code = (
        "import importlib, json, time;"
        f"t=time.perf_counter();importlib.import_module({module_name!r});"
        "print(json.dumps({'elapsed_ms': (time.perf_counter()-t)*1000.0}))"
    )
    payload = json.loads(_run_python_probe(code))
    return float(payload["elapsed_ms"])


def measure_app_factory_ms(factory_target: str) -> float:
    """Measure app factory construction time (ms) in a fresh Python process."""
    if ":" not in factory_target:
        raise ValueError(
            f"Invalid factory target '{factory_target}'. Expected format: module.path:function_name"
        )
    module_name, factory_name = factory_target.split(":", 1)
    code = (
        "import importlib, json, time;"
        f"module=importlib.import_module({module_name!r});"
        f"factory=getattr(module, {factory_name!r});"
        "t=time.perf_counter();"
        "factory();"
        "print(json.dumps({'elapsed_ms': (time.perf_counter()-t)*1000.0}))"
    )
    payload = json.loads(_run_python_probe(code))
    return float(payload["elapsed_ms"])


def run_startup_sample(
    import_targets: List[str], app_factory_target: str
) -> StartupSampleMetrics:
    """Run one startup/import sample with deterministic probes."""
    import_timings = {module: measure_module_import_ms(module) for module in import_targets}
    noop_startup_ms = measure_noop_startup_ms()
    app_factory_ms = measure_app_factory_ms(app_factory_target)

    return StartupSampleMetrics(
        noop_startup_ms=noop_startup_ms,
        total_import_ms=sum(import_timings.values()),
        max_single_import_ms=max(import_timings.values()) if import_timings else 0.0,
        app_factory_ms=app_factory_ms,
        import_timings_ms=import_timings,
    )


def aggregate_samples(samples: List[StartupSampleMetrics]) -> Dict[str, object]:
    """Aggregate samples into median summary metrics."""
    all_targets = sorted(
        {target for sample in samples for target in sample.import_timings_ms.keys()}
    )
    import_medians = {
        target: _median(sample.import_timings_ms.get(target, 0.0) for sample in samples)
        for target in all_targets
    }
    return {
        "noop_startup_ms": _median(sample.noop_startup_ms for sample in samples),
        "total_import_ms": _median(sample.total_import_ms for sample in samples),
        "max_single_import_ms": _median(sample.max_single_import_ms for sample in samples),
        "app_factory_ms": _median(sample.app_factory_ms for sample in samples),
        "import_timings_ms": import_medians,
    }


def _is_breach(value: float, threshold: float, direction: str) -> bool:
    """Check threshold breach for max/min style constraints."""
    if direction == "max":
        return value > threshold
    if direction == "min":
        return value < threshold
    raise ValueError(f"Unsupported direction: {direction}")


def _sample_metric(sample: StartupSampleMetrics, metric_name: str) -> float:
    """Read numeric metric value from sample."""
    return float(getattr(sample, metric_name))


def _significant_breach_count(
    samples: List[StartupSampleMetrics], metric_name: str, threshold: float, direction: str
) -> int:
    """Count sample-level threshold breaches for significance checks."""
    breach_count = 0
    for sample in samples:
        value = _sample_metric(sample, metric_name)
        if _is_breach(value, threshold, direction):
            breach_count += 1
    return breach_count


def evaluate_gate(
    samples: List[StartupSampleMetrics], scenario_config: Dict[str, object]
) -> Tuple[bool, List[str], Dict[str, object]]:
    """
    Evaluate startup/import-time gate using absolute and regression thresholds.

    A failure is considered significant only when:
    1) median metric breaches threshold, and
    2) breach count across samples >= significant_breach_count.
    """
    summary = aggregate_samples(samples)
    significant_breach_count = int(scenario_config.get("significant_breach_count", 2))
    budgets = scenario_config["budgets"]
    baseline = scenario_config["baseline_medians"]
    tolerances = scenario_config["regression_tolerances_pct"]

    checks: List[Tuple[str, str, float, str]] = [
        ("noop_startup_ms", "budget.max_noop_startup_ms", float(budgets["max_noop_startup_ms"]), "max"),
        ("total_import_ms", "budget.max_total_import_ms", float(budgets["max_total_import_ms"]), "max"),
        (
            "max_single_import_ms",
            "budget.max_single_import_ms",
            float(budgets["max_single_import_ms"]),
            "max",
        ),
        ("app_factory_ms", "budget.max_app_factory_ms", float(budgets["max_app_factory_ms"]), "max"),
        (
            "noop_startup_ms",
            "regression.max_noop_startup_increase_pct",
            float(baseline["noop_startup_ms"])
            * (1.0 + float(tolerances["max_noop_startup_increase_pct"]) / 100.0),
            "max",
        ),
        (
            "total_import_ms",
            "regression.max_total_import_increase_pct",
            float(baseline["total_import_ms"])
            * (1.0 + float(tolerances["max_total_import_increase_pct"]) / 100.0),
            "max",
        ),
        (
            "max_single_import_ms",
            "regression.max_single_import_increase_pct",
            float(baseline["max_single_import_ms"])
            * (1.0 + float(tolerances["max_single_import_increase_pct"]) / 100.0),
            "max",
        ),
        (
            "app_factory_ms",
            "regression.max_app_factory_increase_pct",
            float(baseline["app_factory_ms"])
            * (1.0 + float(tolerances["max_app_factory_increase_pct"]) / 100.0),
            "max",
        ),
    ]

    violations: List[str] = []
    for metric_name, threshold_label, threshold, direction in checks:
        median_value = float(summary[metric_name])
        breaches = _significant_breach_count(samples, metric_name, threshold, direction)
        if _is_breach(median_value, threshold, direction) and breaches >= significant_breach_count:
            comparator = ">" if direction == "max" else "<"
            violations.append(
                (
                    f"{metric_name} median {median_value:.4f} {comparator} threshold {threshold:.4f} "
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
    """CLI entrypoint for startup/import-time budget gate."""
    parser = argparse.ArgumentParser(description="Deterministic startup/import-time budget gate")
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("config/performance/startup_budget_baseline.json"),
        help="Path to startup budget configuration JSON",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="startup_import",
        help="Scenario key from baseline JSON",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=None,
        help="Override sample count from baseline",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("exports/performance/startup_budget_gate_result.json"),
        help="Output JSON report path",
    )
    args = parser.parse_args()

    scenario_config = _load_scenario_config(args.baseline, args.scenario)
    sample_count = int(args.samples if args.samples is not None else scenario_config["samples"])
    import_targets = [str(target) for target in scenario_config["import_targets"]]
    app_factory_target = str(scenario_config["app_factory_target"])

    samples: List[StartupSampleMetrics] = [
        run_startup_sample(import_targets, app_factory_target) for _ in range(sample_count)
    ]
    passed, violations, summary = evaluate_gate(samples, scenario_config)

    report = {
        "scenario": args.scenario,
        "baseline_path": str(args.baseline),
        "sample_count": sample_count,
        "import_targets": import_targets,
        "app_factory_target": app_factory_target,
        "passed": passed,
        "summary_medians": summary,
        "violations": violations,
        "samples": [asdict(sample) for sample in samples],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))

    print(f"Startup budget gate scenario={args.scenario} passed={passed}")
    print(
        "summary "
        + " ".join(
            [
                f"noop_ms={float(summary['noop_startup_ms']):.2f}",
                f"total_import_ms={float(summary['total_import_ms']):.2f}",
                f"max_single_import_ms={float(summary['max_single_import_ms']):.2f}",
                f"app_factory_ms={float(summary['app_factory_ms']):.2f}",
            ]
        )
    )
    import_timings = summary.get("import_timings_ms", {})
    if isinstance(import_timings, dict) and import_timings:
        slowest_module, slowest_ms = max(import_timings.items(), key=lambda item: float(item[1]))
        print(f"slowest_import module={slowest_module} ms={float(slowest_ms):.2f}")
    if violations:
        for violation in violations:
            print(f"VIOLATION: {violation}")

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
