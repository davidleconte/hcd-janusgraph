"""
File: tracing.py
Created: 2026-01-28
Purpose: Distributed tracing instrumentation for JanusGraph applications
"""

import logging
import os
import time
from functools import wraps
from typing import Any, Dict, Optional

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger(__name__)


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
        self.service_name = service_name
        self.jaeger_host = jaeger_host
        self.jaeger_port = jaeger_port
        self.otlp_endpoint = otlp_endpoint
        self.enabled = enabled
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
        self.config = config or TracingConfig.from_env()
        self.tracer_provider: Optional[TracerProvider] = None
        self.tracer: Optional[trace.Tracer] = None

        if self.config.enabled:
            self._initialize_tracing()

    def _initialize_tracing(self):
        """Initialize OpenTelemetry tracing"""
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

            # Add Jaeger exporter
            jaeger_exporter = JaegerExporter(
                agent_host_name=self.config.jaeger_host,
                agent_port=self.config.jaeger_port,
            )
            self.tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

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

            # Instrument HTTP requests
            RequestsInstrumentor().instrument()

            logger.info("Tracing initialized for service: %s", self.config.service_name)

        except Exception as e:
            logger.error("Failed to initialize tracing: %s", e)
            self.config.enabled = False

    def get_tracer(self) -> trace.Tracer:
        """Get the tracer instance"""
        if not self.config.enabled:
            return trace.get_tracer(__name__)
        return self.tracer or trace.get_tracer(__name__)

    def shutdown(self):
        """Shutdown tracing and flush spans"""
        if self.tracer_provider:
            self.tracer_provider.shutdown()
            logger.info("Tracing shutdown complete")


# Global tracing manager instance
_tracing_manager: Optional[TracingManager] = None


def initialize_tracing(config: Optional[TracingConfig] = None) -> TracingManager:
    """Initialize global tracing manager"""
    global _tracing_manager
    _tracing_manager = TracingManager(config)
    return _tracing_manager


def get_tracer() -> trace.Tracer:
    """Get the global tracer instance"""
    global _tracing_manager
    if _tracing_manager is None:
        _tracing_manager = TracingManager()
    return _tracing_manager.get_tracer()


def trace_function(name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """
    Decorator to trace a function

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
                    span.set_status(Status(StatusCode.OK))

                    return result

                except Exception as e:
                    # Record exception
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        return wrapper

    return decorator


def trace_gremlin_query(query: str, bindings: Optional[Dict] = None):
    """
    Decorator to trace Gremlin queries

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
                    span.set_status(Status(StatusCode.OK))

                    return result

                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise

        return wrapper

    return decorator


class TracedGremlinClient:
    """Wrapper for Gremlin client with tracing"""

    def __init__(self, client):
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
                span.set_status(Status(StatusCode.OK))

                return result

            except Exception as e:
                span.record_exception(e)
                span.set_attribute("db.error", str(e))
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    def close(self):
        """Close the client"""
        with self.tracer.start_as_current_span("gremlin.close"):
            self.client.close()


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
