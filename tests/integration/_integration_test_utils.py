"""Integration test utilities for non-blocking service checks.

Provides small timeout wrappers used by service availability checks to avoid
hanging during module import and pre-checks.
"""

from __future__ import annotations

import threading
from typing import Any, Callable, Dict, Optional, TypeVar

T = TypeVar("T")


def run_with_timeout(callable_fn: Callable[[], T], timeout_seconds: float, default: T) -> T:
    """Run `callable_fn` in a thread with a strict timeout.

    Args:
        callable_fn: Callable to execute.
        timeout_seconds: Timeout in seconds.
        default: Default value returned on timeout.

    Returns:
        The callable result or `default` if execution timed out.

    Raises:
        Any exception from `callable_fn` if it completes before timeout.
    """

    result: Dict[str, Any] = {"done": False, "result": default}

    def _worker() -> None:
        try:
            result["result"] = callable_fn()
        except Exception:
            result["result"] = default
        finally:
            result["done"] = True

    worker = threading.Thread(target=_worker, daemon=True)
    worker.start()
    worker.join(timeout=timeout_seconds)

    if not result["done"]:
        return default

    return result["result"]


def run_with_timeout_bool(
    callable_fn: Callable[[], bool], timeout_seconds: float = 5.0, default: bool = False
) -> bool:
    """Run a boolean service check with a timeout and return default on timeout."""

    return run_with_timeout(callable_fn, timeout_seconds=timeout_seconds, default=default)
