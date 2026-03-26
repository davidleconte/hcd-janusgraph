"""
File: tracing.py
Created: 2026-01-28
Purpose: Distributed tracing instrumentation for JanusGraph applications

OpenTelemetry is OPTIONAL - graceful fallback when not installed.
"""

import logging
import os
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# OpenTelemetry is optional - graceful fallback when not installed
OTEL_AVAILABLE = False
trace = None
StatusCode = None
Status = None
TracerProvider = None
Resource = None
SERVICE_NAME = None
BatchSpanProcessor = None
OTLPSpanExporter = None
RequestsInstrumentor = None

try:
    from opentelemetry import trace as _trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as _OTLPSpanExporter
    from opentelemetry.sdk.resources import SERVICE_NAME as _SERVICE_NAME, Resource as _Resource
    from opentelemetry.sdk.trace import TracerProvider as _TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor as _BatchSpanProcessor
    from opentelemetry.trace import Status as _Status, StatusCode as _StatusCode

    # Try to instrument requests (optional)
    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor as _RequestsInstrumentor
        RequestsInstrumentor = _RequestsInstrumentor
    except ImportError:
        pass

    trace = _trace
    StatusCode = _StatusCode
    Status = _Status
    TracerProvider = _TracerProvider
    Resource = _Resource
    SERVICE_NAME = _SERVICE_NAME
    BatchSpanProcessor = _BatchSpanProcessor
    OTLPSpanExporter = _OTLPSpanExporter
    OTEL_AVAILABLE = True

except ImportError:
    logger.info("OpenTelemetry not installed - tracing disabled (install opentelemetry-api/opentelemetry-sdk to enable)")


# No-op implementations when OpenTelemetry is not available
class NoOpStatusCode:
    """No-op StatusCode enum replacement."""
    OK = "OK"
    ERROR = "ERROR"
    UNSET = "UNSET"


class NoOpStatus:
    """No-op Status class replacement."""
    
    def __init__(self, status_code: Any = None, description: str = ""):
        self.status_code = status_code
        self.description = description


class NoOpSpan:
    """No-op span that does nothing but supports context manager protocol."""
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        return False
    
    def set_attribute(self, key: str, value: Any) -> None:
        pass
    
    def set_status(self, status: Any) -> None:
        pass
    
    def record_exception(self, exc: Exception) -> None:
        pass


class NoOpTracer:
    """No-op tracer that returns no-op spans."""
    
    @contextmanager
    def start_as_current_span(self, name: str, **kwargs):
        yield NoOpSpan()
    
    def start_span(self, name: str, **kwargs):
        return NoOpSpan()


# Set Status and StatusCode to no-op versions if OTEL not available
if not OTEL_AVAILABLE:
    Status = NoOpStatus
    StatusCode = NoOpStatusCode


# Jaeger exporter is deprecated in newer OTEL SDK versions - make import optional
if OTEL_AVAILABLE:
    try:
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter as _JaegerExporter
        JAEGER_AVAILABLE = True
    except ImportError:
        _JaegerExporter = None  # type: ignore
        JAEGER_AVAILABLE = False
else:
    _JaegerExporter = None
    JAEGER_AVAILABLE = False


class TracingConfig:
    """Configuration for distributed tracing"""

    def __init__(
        self,
        service_name: str = "janusgraph-client",
        jaeger_host: str = "localhost",
        jaeger_port: int = 6831,
        otlp_endpoint: str = "http://localhost:4317",
        enabled: bool = True,
        sample_rate: float = 1.0,
    ):
        """Initialize tracing configuration.

        Args:
            service_name: Service identifier for traces.
            jaeger_host: Jaeger agent hostname (deprecated, use OTLP).
            jaeger_port: Jaeger agent UDP port.
            otlp_endpoint: OTLP collector endpoint URL.
            enabled: Whether to enable tracing.
            sample_rate: Sampling rate (0.0 to 1.0).
        """
        self.service_name = service_name
        self.jaeger_host = jaeger_host
        self.jaeger_port = jaeger_port
        self.otlp_endpoint = otlp_endpoint
        self.enabled = enabled and OTEL_AVAILABLE
        self.sample_rate = sample_rate

    @classmethod
    def from_env(cls) -> "TracingConfig":
        """Create configuration from environment variables"""
        return cls(
            service_name=os.getenv("OTEL_SERVICE_NAME", "janusgraph-client"),
            jaeger_host=os.getenv("JAEGER_HOST", "localhost"),
            jaeger_port=int(os.getenv("JAEGER_PORT", "6831")),
            otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
            enabled=os.getenv("TRACING_ENABLED", "true").lower() == "true",
            sample_rate=float(os.getenv("TRACING_SAMPLE_RATE", "1.0")),
        )


class TracingManager:
    """Manager for distributed tracing"""

    def __init__(self, config: Optional[TracingConfig] = None):
        """Initialize the tracing manager.

        Args:
            config: Tracing configuration. If None, loaded from environment.
        """
        self.config = config or TracingConfig.from_env()
        self.tracer_provider: Optional[Any] = None
        self.tracer: Optional[Any] = None
        self._no_op_tracer = NoOpTracer()

        if self.config.enabled and OTEL_AVAILABLE:
            self._initialize_tracing()
        else:
            logger.info("Tracing disabled (OTEL_AVAILABLE=%s, enabled=%s)", 
                       OTEL_AVAILABLE, self.config.enabled)

    def _initialize_tracing(self):
        """Initialize OpenTelemetry tracing with Jaeger and OTLP exporters.

        Sets up the tracer provider, configures span processors for both
        Jaeger (deprecated) and OTLP exporters, and instruments HTTP requests.
        Falls back to disabled tracing if initialization fails.
        """
        if not OTEL_AVAILABLE:
            return

        try:
            # Create resource with service information
            resource = Resource(
                attributes={
                    SERVICE_NAME: self.config.service_name,
                    "service.version": "1.0.0",
                    "deployment.environment": os.getenv("ENVIRONMENT", "production"),
                }
            )

            # Create tracer provider
            self.tracer_provider = TracerProvider(resource=resource)

            # Add Jaeger exporter (optional - deprecated in newer OTEL SDK)
            if JAEGER_AVAILABLE and _JaegerExporter is not None:
                jaeger_exporter = _JaegerExporter(
                    agent_host_name=self.config.jaeger_host,
                    agent_port=self.config.jaeger_port,
                )
                self.tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
                logger.info("Jaeger exporter initialized (deprecated)")
            else:
                logger.info("Jaeger exporter not available - using OTLP only")

            # Add OTLP exporter
            try:
                otlp_exporter = OTLPSpanExporter(endpoint=self.config.otlp_endpoint, insecure=True)
                self.tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            except Exception as e:
                logger.warning("Failed to initialize OTLP exporter: %s", e)

            # Set global tracer provider
            trace.set_tracer_provider(self.tracer_provider)

            # Get tracer
            self.tracer = trace.get_tracer(__name__)

            # Instrument HTTP requests (optional)
            if RequestsInstrumentor is not None:
                try:
                    RequestsInstrumentor().instrument()
                except Exception as e:
                    logger.warning("Failed to instrument requests: %s", e)

            logger.info("Tracing initialized for service: %s", self.config.service_name)

        except Exception as e:
            logger.error("Failed to initialize tracing: %s", e)
            self.config.enabled = False

    def get_tracer(self) -> Any:
        """Get the tracer instance (real or no-op)"""
        if not self.config.enabled or not OTEL_AVAILABLE:
            return self._no_op_tracer
        if self.tracer:
            return self.tracer
        if trace:
            return trace.get_tracer(__name__)
        return self._no_op_tracer

    def shutdown(self):
        """Shutdown tracing and flush spans"""
        if self.tracer_provider:
            try:
                self.tracer_provider.shutdown()
                logger.info("Tracing shutdown complete")
            except Exception as e:
                logger.warning("Error during tracing shutdown: %s", e)


# Global tracing manager instance
_tracing_manager: Optional[TracingManager] = None


def initialize_tracing(config: Optional[TracingConfig] = None) -> TracingManager:
    """Initialize global tracing manager"""
    global _tracing_manager
    _tracing_manager = TracingManager(config)
    return _tracing_manager


def get_tracer() -> Any:
    """Get the global tracer instance (real or no-op)"""
    global _tracing_manager
    if _tracing_manager is None:
        _tracing_manager = TracingManager()
    return _tracing_manager.get_tracer()


def trace_function(name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """
    Decorator to trace a function. Works with or without OpenTelemetry.

    Usage:
        @trace_function(name="my_function", attributes={"key": "value"})
        def my_function():
            pass
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            span_name = name or f"{func.__module__}.{func.__name__}"

            with tracer.start_as_current_span(span_name) as span:
                # Add attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, str(value))

                # Add function metadata
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                try:
                    # Execute function
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time

                    # Add performance metrics
                    span.set_attribute("function.duration_ms", duration * 1000)
                    if StatusCode and Status:
                        span.set_status(Status(StatusCode.OK))

                    return result

                except Exception as e:
                    # Record exception
                    span.record_exception(e)
                    if StatusCode and Status:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        return wrapper

    return decorator


def trace_gremlin_query(query: str, bindings: Optional[Dict] = None):
    """
    Decorator to trace Gremlin queries. Works with or without OpenTelemetry.

    Usage:
        @trace_gremlin_query("g.V().count()")
        def count_vertices():
            pass
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()

            with tracer.start_as_current_span("gremlin.query") as span:
                # Add query attributes
                span.set_attribute("db.system", "janusgraph")
                span.set_attribute("db.operation", "query")
                span.set_attribute("db.statement", query)

                if bindings:
                    span.set_attribute("db.bindings", str(bindings))

                try:
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time

                    span.set_attribute("db.duration_ms", duration * 1000)
                    if StatusCode and Status:
                        span.set_status(Status(StatusCode.OK))

                    return result

                except Exception as e:
                    span.record_exception(e)
                    if StatusCode and Status:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        return wrapper

    return decorator


class TracedGremlinClient:
    """Wrapper for Gremlin client with tracing. Works with or without OpenTelemetry."""

    def __init__(self, client):
        """Wrap a Gremlin client with tracing instrumentation.

        Args:
            client: The underlying Gremlin client to wrap.
        """
        self.client = client
        self.tracer = get_tracer()

    def submit(self, query: str, bindings: Optional[Dict] = None):
        """Submit a traced Gremlin query"""
        with self.tracer.start_as_current_span("gremlin.submit") as span:
            span.set_attribute("db.system", "janusgraph")
            span.set_attribute("db.operation", "submit")
            span.set_attribute("db.statement", query)

            if bindings:
                span.set_attribute("db.bindings", str(bindings))

            try:
                start_time = time.time()
                result = self.client.submit(query, bindings)
                duration = time.time() - start_time

                span.set_attribute("db.duration_ms", duration * 1000)
                if StatusCode and Status:
                    span.set_status(Status(StatusCode.OK))

                return result

            except Exception as e:
                span.record_exception(e)
                span.set_attribute("db.error", str(e))
                if StatusCode and Status:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    def close(self):
        """Close the client"""
        with self.tracer.start_as_current_span("gremlin.close"):
            self.client.close()


# Convenience function to check if tracing is available
def is_tracing_available() -> bool:
    """Check if OpenTelemetry tracing is available and enabled."""
    global _tracing_manager
    if _tracing_manager is None:
        return False
    return _tracing_manager.config.enabled and OTEL_AVAILABLE


# Example usage
if __name__ == "__main__":
    # Initialize tracing
    config = TracingConfig(
        service_name="janusgraph-example", jaeger_host="localhost", jaeger_port=6831
    )
    tracing_manager = initialize_tracing(config)

    # Example traced function
    @trace_function(name="example_function", attributes={"example": "true"})
    def example_function():
        print("This function is traced!")
        time.sleep(0.1)
        return "success"

    # Example traced query
    @trace_gremlin_query("g.V().count()")
    def count_vertices():
        print("Counting vertices...")
        time.sleep(0.05)
        return 42

    # Execute examples
    example_function()
    count_vertices()

    # Shutdown tracing
    tracing_manager.shutdown()
