"""
Streaming Metrics (Week 6)
==========================

Prometheus metrics for monitoring streaming components:
- Producer metrics (events published, failures, latency)
- Consumer metrics (events consumed, processing time, lag)
- DLQ metrics (messages processed, retried, archived)

Created: 2026-02-06
Week 6: DLQ Handling + Monitoring
"""

import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

try:
    from prometheus_client import Counter, Gauge, Histogram, Info, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


# Metric definitions (created lazily)
_metrics_initialized = False
_metrics = {}


def _init_metrics():
    """Initialize Prometheus metrics."""
    global _metrics_initialized, _metrics
    
    if _metrics_initialized or not PROMETHEUS_AVAILABLE:
        return
    
    from prometheus_client import REGISTRY
    
    def _get_existing(name):
        """Get existing metric from registry by name."""
        # Counters create multiple entries: name, name_total, name_created
        # Check if any of these exist
        check_names = [name, f"{name}_total", f"{name}_created"]
        for check_name in check_names:
            if check_name in REGISTRY._names_to_collectors:
                collector = REGISTRY._names_to_collectors[check_name]
                return collector
        return None
    
    def _safe_counter(name, desc, labels):
        """Create counter or return existing one from registry."""
        existing = _get_existing(name)
        if existing:
            return existing
        try:
            return Counter(name, desc, labels)
        except ValueError:
            # Race condition - try to get it again
            return _get_existing(name)
    
    def _safe_histogram(name, desc, labels, buckets):
        """Create histogram or return existing one from registry."""
        existing = _get_existing(name)
        if existing:
            return existing
        try:
            return Histogram(name, desc, labels, buckets=buckets)
        except ValueError:
            return _get_existing(name)
    
    def _safe_gauge(name, desc, labels):
        """Create gauge or return existing one from registry."""
        existing = _get_existing(name)
        if existing:
            return existing
        try:
            return Gauge(name, desc, labels)
        except ValueError:
            return _get_existing(name)
    
    def _safe_info(name, desc):
        """Create info or return existing one from registry."""
        existing = _get_existing(name)
        if existing:
            return existing
        try:
            return Info(name, desc)
        except ValueError:
            return _get_existing(name)
    
    # Producer metrics
    _metrics['events_published_total'] = _safe_counter(
        'streaming_events_published_total',
        'Total number of events published to Pulsar',
        ['entity_type', 'source']
    )
    
    _metrics['events_publish_failed_total'] = _safe_counter(
        'streaming_events_publish_failed_total',
        'Total number of failed event publishes',
        ['entity_type', 'source', 'error_type']
    )
    
    _metrics['publish_latency_seconds'] = _safe_histogram(
        'streaming_publish_latency_seconds',
        'Event publish latency in seconds',
        ['entity_type'],
        (0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
    )
    
    # Consumer metrics
    _metrics['events_consumed_total'] = _safe_counter(
        'streaming_events_consumed_total',
        'Total number of events consumed from Pulsar',
        ['entity_type', 'consumer_type']  # consumer_type: graph, vector
    )
    
    _metrics['events_consume_failed_total'] = _safe_counter(
        'streaming_events_consume_failed_total',
        'Total number of failed event consumptions',
        ['entity_type', 'consumer_type', 'error_type']
    )
    
    _metrics['consume_latency_seconds'] = _safe_histogram(
        'streaming_consume_latency_seconds',
        'Event consume/process latency in seconds',
        ['entity_type', 'consumer_type'],
        (0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0)
    )
    
    _metrics['consumer_lag'] = _safe_gauge(
        'streaming_consumer_lag',
        'Consumer lag (messages behind)',
        ['consumer_type', 'topic']
    )
    
    # DLQ metrics
    _metrics['dlq_messages_total'] = _safe_counter(
        'streaming_dlq_messages_total',
        'Total messages sent to DLQ',
        ['entity_type', 'failure_reason']
    )
    
    _metrics['dlq_retries_total'] = _safe_counter(
        'streaming_dlq_retries_total',
        'Total DLQ message retry attempts',
        ['entity_type', 'success']
    )
    
    _metrics['dlq_archived_total'] = _safe_counter(
        'streaming_dlq_archived_total',
        'Total DLQ messages archived (permanently failed)',
        ['entity_type']
    )
    
    _metrics['dlq_queue_size'] = _safe_gauge(
        'streaming_dlq_queue_size',
        'Current DLQ queue size',
        []
    )
    
    # System health metrics
    _metrics['producer_connected'] = _safe_gauge(
        'streaming_producer_connected',
        'Producer connection status (1=connected, 0=disconnected)',
        ['producer_id']
    )
    
    _metrics['consumer_connected'] = _safe_gauge(
        'streaming_consumer_connected',
        'Consumer connection status (1=connected, 0=disconnected)',
        ['consumer_type', 'subscription']
    )
    
    # Batch metrics
    _metrics['batch_size'] = _safe_histogram(
        'streaming_batch_size',
        'Batch size for batch operations',
        ['operation'],
        (1, 5, 10, 25, 50, 100, 250, 500, 1000)
    )
    
    # Info metric
    _metrics['streaming_info'] = _safe_info(
        'streaming',
        'Streaming module information'
    )
    if _metrics['streaming_info']:
        try:
            _metrics['streaming_info'].info({
                'version': '1.0.0',
                'pulsar_namespace': 'public/banking'
            })
        except Exception:
            pass  # Info already set
    
    _metrics_initialized = True
    logger.info("Prometheus metrics initialized")


def get_metric(name: str):
    """Get a metric by name, initializing if needed."""
    if not PROMETHEUS_AVAILABLE:
        return None
    
    _init_metrics()
    return _metrics.get(name)


class StreamingMetrics:
    """
    Metrics collector for streaming components.
    
    Provides methods to record metrics for producers, consumers, and DLQ handlers.
    Falls back to no-op if prometheus_client is not installed.
    
    Example:
        >>> metrics = StreamingMetrics()
        >>> metrics.record_publish("person", "generator", 0.05)
        >>> metrics.record_consume("person", "graph", 0.1)
    """
    
    def __init__(self):
        """Initialize StreamingMetrics."""
        if PROMETHEUS_AVAILABLE:
            _init_metrics()
    
    def record_publish(
        self,
        entity_type: str,
        source: str,
        latency_seconds: float = None
    ):
        """Record a successful publish event."""
        if not PROMETHEUS_AVAILABLE:
            return
        
        _metrics['events_published_total'].labels(
            entity_type=entity_type,
            source=source
        ).inc()
        
        if latency_seconds is not None:
            _metrics['publish_latency_seconds'].labels(
                entity_type=entity_type
            ).observe(latency_seconds)
    
    def record_publish_failure(
        self,
        entity_type: str,
        source: str,
        error_type: str = "unknown"
    ):
        """Record a failed publish event."""
        if not PROMETHEUS_AVAILABLE:
            return
        
        _metrics['events_publish_failed_total'].labels(
            entity_type=entity_type,
            source=source,
            error_type=error_type
        ).inc()
    
    def record_consume(
        self,
        entity_type: str,
        consumer_type: str,  # "graph" or "vector"
        latency_seconds: float = None
    ):
        """Record a successful consume event."""
        if not PROMETHEUS_AVAILABLE:
            return
        
        _metrics['events_consumed_total'].labels(
            entity_type=entity_type,
            consumer_type=consumer_type
        ).inc()
        
        if latency_seconds is not None:
            _metrics['consume_latency_seconds'].labels(
                entity_type=entity_type,
                consumer_type=consumer_type
            ).observe(latency_seconds)
    
    def record_consume_failure(
        self,
        entity_type: str,
        consumer_type: str,
        error_type: str = "unknown"
    ):
        """Record a failed consume event."""
        if not PROMETHEUS_AVAILABLE:
            return
        
        _metrics['events_consume_failed_total'].labels(
            entity_type=entity_type,
            consumer_type=consumer_type,
            error_type=error_type
        ).inc()
    
    def record_dlq_message(
        self,
        entity_type: str,
        failure_reason: str
    ):
        """Record a message sent to DLQ."""
        if not PROMETHEUS_AVAILABLE:
            return
        
        _metrics['dlq_messages_total'].labels(
            entity_type=entity_type,
            failure_reason=failure_reason
        ).inc()
    
    def record_dlq_retry(
        self,
        entity_type: str,
        success: bool
    ):
        """Record a DLQ retry attempt."""
        if not PROMETHEUS_AVAILABLE:
            return
        
        _metrics['dlq_retries_total'].labels(
            entity_type=entity_type,
            success=str(success).lower()
        ).inc()
    
    def record_dlq_archived(self, entity_type: str):
        """Record a DLQ message archived (permanently failed)."""
        if not PROMETHEUS_AVAILABLE:
            return
        
        _metrics['dlq_archived_total'].labels(
            entity_type=entity_type
        ).inc()
    
    def set_consumer_lag(
        self,
        consumer_type: str,
        topic: str,
        lag: int
    ):
        """Set consumer lag gauge."""
        if not PROMETHEUS_AVAILABLE:
            return
        
        _metrics['consumer_lag'].labels(
            consumer_type=consumer_type,
            topic=topic
        ).set(lag)
    
    def set_dlq_queue_size(self, size: int):
        """Set DLQ queue size gauge."""
        if not PROMETHEUS_AVAILABLE:
            return
        
        _metrics['dlq_queue_size'].set(size)
    
    def set_producer_connected(self, producer_id: str, connected: bool):
        """Set producer connection status."""
        if not PROMETHEUS_AVAILABLE:
            return
        
        _metrics['producer_connected'].labels(
            producer_id=producer_id
        ).set(1 if connected else 0)
    
    def set_consumer_connected(
        self,
        consumer_type: str,
        subscription: str,
        connected: bool
    ):
        """Set consumer connection status."""
        if not PROMETHEUS_AVAILABLE:
            return
        
        _metrics['consumer_connected'].labels(
            consumer_type=consumer_type,
            subscription=subscription
        ).set(1 if connected else 0)
    
    def record_batch_size(self, operation: str, size: int):
        """Record batch operation size."""
        if not PROMETHEUS_AVAILABLE:
            return
        
        _metrics['batch_size'].labels(
            operation=operation
        ).observe(size)


def timed_publish(entity_type: str, source: str = "unknown"):
    """
    Decorator to time and record publish operations.
    
    Example:
        >>> @timed_publish("person", "generator")
        ... def publish_person(event):
        ...     producer.send(event)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            metrics = StreamingMetrics()
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                latency = time.time() - start_time
                metrics.record_publish(entity_type, source, latency)
                return result
            except Exception as e:
                metrics.record_publish_failure(entity_type, source, type(e).__name__)
                raise
        return wrapper
    return decorator


def timed_consume(entity_type: str, consumer_type: str):
    """
    Decorator to time and record consume operations.
    
    Example:
        >>> @timed_consume("person", "graph")
        ... def process_person_event(event):
        ...     graph.add_vertex(event)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            metrics = StreamingMetrics()
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                latency = time.time() - start_time
                metrics.record_consume(entity_type, consumer_type, latency)
                return result
            except Exception as e:
                metrics.record_consume_failure(entity_type, consumer_type, type(e).__name__)
                raise
        return wrapper
    return decorator


def get_metrics_output() -> bytes:
    """
    Get Prometheus metrics in exposition format.
    
    Returns:
        Bytes containing metrics in Prometheus format
    """
    if not PROMETHEUS_AVAILABLE:
        return b"# Prometheus client not available\n"
    
    _init_metrics()
    return generate_latest()


def get_content_type() -> str:
    """Get content type for metrics output."""
    if PROMETHEUS_AVAILABLE:
        return CONTENT_TYPE_LATEST
    return "text/plain"


# Global metrics instance
streaming_metrics = StreamingMetrics()


__all__ = [
    'StreamingMetrics',
    'streaming_metrics',
    'timed_publish',
    'timed_consume',
    'get_metrics_output',
    'get_content_type',
    'get_metric',
    'PROMETHEUS_AVAILABLE',
]
