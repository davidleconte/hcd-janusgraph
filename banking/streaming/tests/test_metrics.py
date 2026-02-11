"""
Unit tests for StreamingMetrics.

Tests cover:
- Metric initialization
- Producer metrics (publish, failures, latency)
- Consumer metrics (consume, failures, latency, lag)
- DLQ metrics (messages, retries, archived)
- System health metrics (connection status)
- Batch metrics
- Decorators (timed_publish, timed_consume)
- Metrics output

Created: 2026-02-11
Week 2 Day 11: Metrics Tests
"""

from unittest.mock import Mock, patch
import time

import pytest

from banking.streaming.metrics import (
    StreamingMetrics,
    streaming_metrics,
    timed_publish,
    timed_consume,
    get_metrics_output,
    get_content_type,
    get_metric,
)


class TestStreamingMetricsInitialization:
    """Test StreamingMetrics initialization."""

    def test_create_metrics(self):
        """Test creating StreamingMetrics instance."""
        metrics = StreamingMetrics()
        assert metrics is not None

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("banking.streaming.metrics._init_metrics")
    def test_init_calls_init_metrics(self, mock_init):
        """Test initialization calls _init_metrics."""
        StreamingMetrics()
        mock_init.assert_called_once()

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", False)
    def test_init_without_prometheus(self):
        """Test initialization without Prometheus."""
        metrics = StreamingMetrics()
        assert metrics is not None


class TestProducerMetrics:
    """Test producer metrics recording."""

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("banking.streaming.metrics._metrics")
    def test_record_publish(self, mock_metrics_dict):
        """Test recording successful publish."""
        mock_counter = Mock()
        mock_histogram = Mock()
        mock_metrics_dict.__getitem__.side_effect = lambda x: {
            "events_published_total": mock_counter,
            "publish_latency_seconds": mock_histogram,
        }[x]

        metrics = StreamingMetrics()
        metrics.record_publish("person", "generator", 0.05)

        mock_counter.labels.assert_called_with(entity_type="person", source="generator")
        mock_counter.labels.return_value.inc.assert_called_once()
        mock_histogram.labels.assert_called_with(entity_type="person")
        mock_histogram.labels.return_value.observe.assert_called_with(0.05)

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("banking.streaming.metrics._metrics")
    def test_record_publish_without_latency(self, mock_metrics_dict):
        """Test recording publish without latency."""
        mock_counter = Mock()
        mock_metrics_dict.__getitem__.return_value = mock_counter

        metrics = StreamingMetrics()
        metrics.record_publish("person", "generator")

        mock_counter.labels.assert_called_with(entity_type="person", source="generator")

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("banking.streaming.metrics._metrics")
    def test_record_publish_failure(self, mock_metrics_dict):
        """Test recording publish failure."""
        mock_counter = Mock()
        mock_metrics_dict.__getitem__.return_value = mock_counter

        metrics = StreamingMetrics()
        metrics.record_publish_failure("person", "generator", "ConnectionError")

        mock_counter.labels.assert_called_with(
            entity_type="person", source="generator", error_type="ConnectionError"
        )
        mock_counter.labels.return_value.inc.assert_called_once()

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", False)
    def test_record_publish_without_prometheus(self):
        """Test recording publish without Prometheus (no-op)."""
        metrics = StreamingMetrics()
        # Should not raise exception
        metrics.record_publish("person", "generator", 0.05)
        metrics.record_publish_failure("person", "generator", "error")


class TestConsumerMetrics:
    """Test consumer metrics recording."""

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("banking.streaming.metrics._metrics")
    def test_record_consume(self, mock_metrics_dict):
        """Test recording successful consume."""
        mock_counter = Mock()
        mock_histogram = Mock()
        mock_metrics_dict.__getitem__.side_effect = lambda x: {
            "events_consumed_total": mock_counter,
            "consume_latency_seconds": mock_histogram,
        }[x]

        metrics = StreamingMetrics()
        metrics.record_consume("person", "graph", 0.1)

        mock_counter.labels.assert_called_with(entity_type="person", consumer_type="graph")
        mock_counter.labels.return_value.inc.assert_called_once()
        mock_histogram.labels.assert_called_with(entity_type="person", consumer_type="graph")
        mock_histogram.labels.return_value.observe.assert_called_with(0.1)

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("banking.streaming.metrics._metrics")
    def test_record_consume_failure(self, mock_metrics_dict):
        """Test recording consume failure."""
        mock_counter = Mock()
        mock_metrics_dict.__getitem__.return_value = mock_counter

        metrics = StreamingMetrics()
        metrics.record_consume_failure("person", "graph", "ProcessingError")

        mock_counter.labels.assert_called_with(
            entity_type="person", consumer_type="graph", error_type="ProcessingError"
        )
        mock_counter.labels.return_value.inc.assert_called_once()

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("banking.streaming.metrics._metrics")
    def test_set_consumer_lag(self, mock_metrics_dict):
        """Test setting consumer lag."""
        mock_gauge = Mock()
        mock_metrics_dict.__getitem__.return_value = mock_gauge

        metrics = StreamingMetrics()
        metrics.set_consumer_lag("graph", "persons-events", 100)

        mock_gauge.labels.assert_called_with(consumer_type="graph", topic="persons-events")
        mock_gauge.labels.return_value.set.assert_called_with(100)


class TestDLQMetrics:
    """Test DLQ metrics recording."""

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("banking.streaming.metrics._metrics")
    def test_record_dlq_message(self, mock_metrics_dict):
        """Test recording DLQ message."""
        mock_counter = Mock()
        mock_metrics_dict.__getitem__.return_value = mock_counter

        metrics = StreamingMetrics()
        metrics.record_dlq_message("person", "processing_error")

        mock_counter.labels.assert_called_with(
            entity_type="person", failure_reason="processing_error"
        )
        mock_counter.labels.return_value.inc.assert_called_once()

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("banking.streaming.metrics._metrics")
    def test_record_dlq_retry(self, mock_metrics_dict):
        """Test recording DLQ retry."""
        mock_counter = Mock()
        mock_metrics_dict.__getitem__.return_value = mock_counter

        metrics = StreamingMetrics()
        metrics.record_dlq_retry("person", True)

        mock_counter.labels.assert_called_with(entity_type="person", success="true")
        mock_counter.labels.return_value.inc.assert_called_once()

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("banking.streaming.metrics._metrics")
    def test_record_dlq_archived(self, mock_metrics_dict):
        """Test recording DLQ archived."""
        mock_counter = Mock()
        mock_metrics_dict.__getitem__.return_value = mock_counter

        metrics = StreamingMetrics()
        metrics.record_dlq_archived("person")

        mock_counter.labels.assert_called_with(entity_type="person")
        mock_counter.labels.return_value.inc.assert_called_once()

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("banking.streaming.metrics._metrics")
    def test_set_dlq_queue_size(self, mock_metrics_dict):
        """Test setting DLQ queue size."""
        mock_gauge = Mock()
        mock_metrics_dict.__getitem__.return_value = mock_gauge

        metrics = StreamingMetrics()
        metrics.set_dlq_queue_size(50)

        mock_gauge.set.assert_called_with(50)


class TestSystemHealthMetrics:
    """Test system health metrics."""

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("banking.streaming.metrics._metrics")
    def test_set_producer_connected(self, mock_metrics_dict):
        """Test setting producer connection status."""
        mock_gauge = Mock()
        mock_metrics_dict.__getitem__.return_value = mock_gauge

        metrics = StreamingMetrics()
        metrics.set_producer_connected("producer-1", True)

        mock_gauge.labels.assert_called_with(producer_id="producer-1")
        mock_gauge.labels.return_value.set.assert_called_with(1)

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("banking.streaming.metrics._metrics")
    def test_set_producer_disconnected(self, mock_metrics_dict):
        """Test setting producer disconnected."""
        mock_gauge = Mock()
        mock_metrics_dict.__getitem__.return_value = mock_gauge

        metrics = StreamingMetrics()
        metrics.set_producer_connected("producer-1", False)

        mock_gauge.labels.return_value.set.assert_called_with(0)

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("banking.streaming.metrics._metrics")
    def test_set_consumer_connected(self, mock_metrics_dict):
        """Test setting consumer connection status."""
        mock_gauge = Mock()
        mock_metrics_dict.__getitem__.return_value = mock_gauge

        metrics = StreamingMetrics()
        metrics.set_consumer_connected("graph", "graph-loaders", True)

        mock_gauge.labels.assert_called_with(consumer_type="graph", subscription="graph-loaders")
        mock_gauge.labels.return_value.set.assert_called_with(1)


class TestBatchMetrics:
    """Test batch metrics."""

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("banking.streaming.metrics._metrics")
    def test_record_batch_size(self, mock_metrics_dict):
        """Test recording batch size."""
        mock_histogram = Mock()
        mock_metrics_dict.__getitem__.return_value = mock_histogram

        metrics = StreamingMetrics()
        metrics.record_batch_size("publish", 100)

        mock_histogram.labels.assert_called_with(operation="publish")
        mock_histogram.labels.return_value.observe.assert_called_with(100)


class TestTimedDecorators:
    """Test timed decorators."""

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("banking.streaming.metrics._metrics")
    def test_timed_publish_success(self, mock_metrics_dict):
        """Test timed_publish decorator on success."""
        mock_counter = Mock()
        mock_histogram = Mock()
        mock_metrics_dict.__getitem__.side_effect = lambda x: {
            "events_published_total": mock_counter,
            "publish_latency_seconds": mock_histogram,
        }[x]

        @timed_publish("person", "test")
        def publish_event():
            time.sleep(0.01)
            return "success"

        result = publish_event()

        assert result == "success"
        mock_counter.labels.return_value.inc.assert_called_once()
        mock_histogram.labels.return_value.observe.assert_called_once()

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("banking.streaming.metrics._metrics")
    def test_timed_publish_failure(self, mock_metrics_dict):
        """Test timed_publish decorator on failure."""
        mock_counter = Mock()
        mock_metrics_dict.__getitem__.return_value = mock_counter

        @timed_publish("person", "test")
        def publish_event():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            publish_event()

        # Should record failure
        mock_counter.labels.assert_called()

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("banking.streaming.metrics._metrics")
    def test_timed_consume_success(self, mock_metrics_dict):
        """Test timed_consume decorator on success."""
        mock_counter = Mock()
        mock_histogram = Mock()
        mock_metrics_dict.__getitem__.side_effect = lambda x: {
            "events_consumed_total": mock_counter,
            "consume_latency_seconds": mock_histogram,
        }[x]

        @timed_consume("person", "graph")
        def consume_event():
            time.sleep(0.01)
            return "processed"

        result = consume_event()

        assert result == "processed"
        mock_counter.labels.return_value.inc.assert_called_once()
        mock_histogram.labels.return_value.observe.assert_called_once()

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("banking.streaming.metrics._metrics")
    def test_timed_consume_failure(self, mock_metrics_dict):
        """Test timed_consume decorator on failure."""
        mock_counter = Mock()
        mock_metrics_dict.__getitem__.return_value = mock_counter

        @timed_consume("person", "graph")
        def consume_event():
            raise RuntimeError("Processing error")

        with pytest.raises(RuntimeError):
            consume_event()

        # Should record failure
        mock_counter.labels.assert_called()


class TestMetricsOutput:
    """Test metrics output functions."""

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("banking.streaming.metrics.generate_latest")
    def test_get_metrics_output(self, mock_generate):
        """Test getting metrics output."""
        mock_generate.return_value = b"# HELP test\n"

        output = get_metrics_output()

        assert output == b"# HELP test\n"
        mock_generate.assert_called_once()

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", False)
    def test_get_metrics_output_without_prometheus(self):
        """Test getting metrics output without Prometheus."""
        output = get_metrics_output()

        assert b"not available" in output

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("banking.streaming.metrics.CONTENT_TYPE_LATEST", "text/plain; version=0.0.4")
    def test_get_content_type(self):
        """Test getting content type."""
        content_type = get_content_type()

        assert content_type == "text/plain; version=0.0.4"

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", False)
    def test_get_content_type_without_prometheus(self):
        """Test getting content type without Prometheus."""
        content_type = get_content_type()

        assert content_type == "text/plain"


class TestGetMetric:
    """Test get_metric function."""

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("banking.streaming.metrics._metrics")
    def test_get_metric_exists(self, mock_metrics_dict):
        """Test getting existing metric."""
        mock_counter = Mock()
        mock_metrics_dict.get.return_value = mock_counter

        metric = get_metric("events_published_total")

        assert metric == mock_counter

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", True)
    @patch("banking.streaming.metrics._metrics")
    def test_get_metric_not_exists(self, mock_metrics_dict):
        """Test getting non-existent metric."""
        mock_metrics_dict.get.return_value = None

        metric = get_metric("nonexistent")

        assert metric is None

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", False)
    def test_get_metric_without_prometheus(self):
        """Test getting metric without Prometheus."""
        metric = get_metric("events_published_total")

        assert metric is None


class TestGlobalMetricsInstance:
    """Test global metrics instance."""

    def test_streaming_metrics_instance(self):
        """Test global streaming_metrics instance exists."""
        assert streaming_metrics is not None
        assert isinstance(streaming_metrics, StreamingMetrics)


class TestMetricsWithoutPrometheus:
    """Test all metrics methods work without Prometheus."""

    @patch("banking.streaming.metrics.PROMETHEUS_AVAILABLE", False)
    def test_all_methods_no_op(self):
        """Test all methods work as no-op without Prometheus."""
        metrics = StreamingMetrics()

        # Should not raise exceptions
        metrics.record_publish("person", "test", 0.1)
        metrics.record_publish_failure("person", "test", "error")
        metrics.record_consume("person", "graph", 0.1)
        metrics.record_consume_failure("person", "graph", "error")
        metrics.record_dlq_message("person", "error")
        metrics.record_dlq_retry("person", True)
        metrics.record_dlq_archived("person")
        metrics.set_consumer_lag("graph", "topic", 100)
        metrics.set_dlq_queue_size(50)
        metrics.set_producer_connected("p1", True)
        metrics.set_consumer_connected("graph", "sub", True)
        metrics.record_batch_size("publish", 100)

# Made with Bob
