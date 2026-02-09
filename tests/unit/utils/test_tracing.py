"""Tests for distributed tracing module."""

import os
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from src.python.utils.tracing import (
    TracingConfig,
    TracingManager,
    initialize_tracing,
    get_tracer,
    trace_function,
    trace_gremlin_query,
    TracedGremlinClient,
)


class TestTracingConfig:
    def test_defaults(self):
        cfg = TracingConfig()
        assert cfg.service_name == "janusgraph-client"
        assert cfg.jaeger_host == "localhost"
        assert cfg.jaeger_port == 6831
        assert cfg.enabled is True
        assert cfg.sample_rate == 1.0

    def test_custom(self):
        cfg = TracingConfig(service_name="test", enabled=False, sample_rate=0.5)
        assert cfg.service_name == "test"
        assert cfg.enabled is False

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("OTEL_SERVICE_NAME", "my-svc")
        monkeypatch.setenv("JAEGER_HOST", "jaeger.local")
        monkeypatch.setenv("JAEGER_PORT", "9999")
        monkeypatch.setenv("TRACING_ENABLED", "false")
        monkeypatch.setenv("TRACING_SAMPLE_RATE", "0.25")
        cfg = TracingConfig.from_env()
        assert cfg.service_name == "my-svc"
        assert cfg.jaeger_host == "jaeger.local"
        assert cfg.jaeger_port == 9999
        assert cfg.enabled is False
        assert cfg.sample_rate == 0.25


class TestTracingManager:
    def test_disabled_skips_init(self):
        cfg = TracingConfig(enabled=False)
        mgr = TracingManager(config=cfg)
        assert mgr.tracer_provider is None

    @patch("src.python.utils.tracing.RequestsInstrumentor")
    @patch("src.python.utils.tracing.OTLPSpanExporter")
    @patch("src.python.utils.tracing.JaegerExporter")
    @patch("src.python.utils.tracing.BatchSpanProcessor")
    @patch("src.python.utils.tracing.TracerProvider")
    @patch("src.python.utils.tracing.trace")
    def test_enabled_initializes(self, mock_trace, mock_tp, mock_bsp, mock_jaeger, mock_otlp, mock_req):
        cfg = TracingConfig(enabled=True)
        mgr = TracingManager(config=cfg)
        mock_tp.assert_called_once()
        mock_trace.set_tracer_provider.assert_called_once()

    def test_get_tracer_disabled(self):
        cfg = TracingConfig(enabled=False)
        mgr = TracingManager(config=cfg)
        tracer = mgr.get_tracer()
        assert tracer is not None

    def test_shutdown_noop_when_disabled(self):
        cfg = TracingConfig(enabled=False)
        mgr = TracingManager(config=cfg)
        mgr.shutdown()


class TestGlobalFunctions:
    @patch("src.python.utils.tracing.TracingManager")
    def test_initialize_tracing(self, mock_mgr_cls):
        cfg = TracingConfig(enabled=False)
        mgr = initialize_tracing(cfg)
        mock_mgr_cls.assert_called_once_with(cfg)

    @patch("src.python.utils.tracing._tracing_manager", None)
    @patch("src.python.utils.tracing.TracingManager")
    def test_get_tracer_creates_manager(self, mock_mgr_cls):
        mock_instance = MagicMock()
        mock_mgr_cls.return_value = mock_instance
        get_tracer()
        mock_mgr_cls.assert_called_once()


class TestTraceFunction:
    @patch("src.python.utils.tracing.get_tracer")
    def test_decorator(self, mock_get_tracer):
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        @trace_function(name="test_fn", attributes={"key": "val"})
        def my_func():
            return 42

        assert my_func() == 42
        mock_tracer.start_as_current_span.assert_called_once_with("test_fn")

    @patch("src.python.utils.tracing.get_tracer")
    def test_decorator_exception(self, mock_get_tracer):
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        @trace_function()
        def failing():
            raise ValueError("boom")

        with pytest.raises(ValueError):
            failing()
        mock_span.record_exception.assert_called_once()


class TestTraceGremlinQuery:
    @patch("src.python.utils.tracing.get_tracer")
    def test_decorator(self, mock_get_tracer):
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        @trace_gremlin_query("g.V().count()", bindings={"x": 1})
        def count():
            return 100

        assert count() == 100
        mock_span.set_attribute.assert_any_call("db.system", "janusgraph")


class TestTracedGremlinClient:
    @patch("src.python.utils.tracing.get_tracer")
    def test_submit(self, mock_get_tracer):
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        inner = MagicMock()
        inner.submit.return_value = [42]
        traced = TracedGremlinClient(inner)
        result = traced.submit("g.V().count()")
        assert result == [42]

    @patch("src.python.utils.tracing.get_tracer")
    def test_submit_with_bindings(self, mock_get_tracer):
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        inner = MagicMock()
        traced = TracedGremlinClient(inner)
        traced.submit("g.V().has('name', x)", bindings={"x": "Alice"})
        mock_span.set_attribute.assert_any_call("db.bindings", "{'x': 'Alice'}")

    @patch("src.python.utils.tracing.get_tracer")
    def test_close(self, mock_get_tracer):
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock()
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        inner = MagicMock()
        traced = TracedGremlinClient(inner)
        traced.close()
        inner.close.assert_called_once()

    @patch("src.python.utils.tracing.get_tracer")
    def test_submit_exception(self, mock_get_tracer):
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_tracer.return_value = mock_tracer

        inner = MagicMock()
        inner.submit.side_effect = RuntimeError("conn lost")
        traced = TracedGremlinClient(inner)
        with pytest.raises(RuntimeError):
            traced.submit("g.V()")
        mock_span.record_exception.assert_called_once()
