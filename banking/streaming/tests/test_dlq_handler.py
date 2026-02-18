"""
Unit tests for DLQHandler.

Tests cover:
- Initialization and configuration
- Connection management
- Message parsing
- Retry logic
- Archiving
- Batch processing
- Statistics tracking
- Context manager usage

Created: 2026-02-11
Week 2 Day 11: DLQ Handler Tests
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from banking.streaming.dlq_handler import (
    DLQHandler,
    DLQMessage,
    DLQStats,
    MockDLQHandler,
    get_dlq_handler,
)
from banking.streaming.events import EntityEvent


class TestDLQMessage:
    """Test DLQMessage dataclass."""

    def test_create_dlq_message(self):
        """Test creating a DLQMessage."""
        event = EntityEvent(
            entity_id="p-123",
            event_type="create",
            entity_type="person",
            payload={"name": "John"},
        )

        dlq_msg = DLQMessage(
            original_topic="persons-events",
            original_event=event,
            failure_reason="processing_error",
            failure_count=1,
            first_failure_time=datetime.now(timezone.utc),
            last_failure_time=datetime.now(timezone.utc),
            message_id="msg-123",
        )

        assert dlq_msg.original_topic == "persons-events"
        assert dlq_msg.original_event == event
        assert dlq_msg.failure_reason == "processing_error"
        assert dlq_msg.failure_count == 1
        assert dlq_msg.message_id == "msg-123"

    def test_dlq_message_to_dict(self):
        """Test converting DLQMessage to dictionary."""
        event = EntityEvent(
            entity_id="p-123",
            event_type="create",
            entity_type="person",
            payload={"name": "John"},
        )

        now = datetime.now(timezone.utc)
        dlq_msg = DLQMessage(
            original_topic="persons-events",
            original_event=event,
            failure_reason="error",
            failure_count=2,
            first_failure_time=now,
            last_failure_time=now,
            message_id="msg-123",
            metadata={"key": "value"},
        )

        result = dlq_msg.to_dict()

        assert result["original_topic"] == "persons-events"
        assert result["failure_reason"] == "error"
        assert result["failure_count"] == 2
        assert result["message_id"] == "msg-123"
        assert result["metadata"] == {"key": "value"}
        assert "original_event" in result

    def test_dlq_message_to_json(self):
        """Test converting DLQMessage to JSON."""
        now = datetime.now(timezone.utc)
        dlq_msg = DLQMessage(
            original_topic="test",
            original_event=None,
            failure_reason="error",
            failure_count=1,
            first_failure_time=now,
            last_failure_time=now,
            message_id="msg-123",
        )

        json_str = dlq_msg.to_json()
        parsed = json.loads(json_str)

        assert parsed["original_topic"] == "test"
        assert parsed["failure_count"] == 1


class TestDLQStats:
    """Test DLQStats dataclass."""

    def test_create_dlq_stats(self):
        """Test creating DLQStats."""
        stats = DLQStats()

        assert stats.messages_processed == 0
        assert stats.messages_retried == 0
        assert stats.messages_archived == 0
        assert stats.messages_failed_permanently == 0
        assert stats.errors == []

    def test_dlq_stats_to_dict(self):
        """Test converting DLQStats to dictionary."""
        stats = DLQStats(
            messages_processed=10,
            messages_retried=5,
            messages_archived=3,
            messages_failed_permanently=2,
            errors=["error1", "error2"],
        )

        result = stats.to_dict()

        assert result["messages_processed"] == 10
        assert result["messages_retried"] == 5
        assert result["messages_archived"] == 3
        assert result["messages_failed_permanently"] == 2
        assert result["errors"] == ["error1", "error2"]


class TestDLQHandlerInitialization:
    """Test DLQHandler initialization."""

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", True)
    def test_init_with_defaults(self):
        """Test initialization with default configuration."""
        handler = DLQHandler()

        assert handler.pulsar_url == "pulsar://localhost:6650"
        assert handler.subscription_name == "dlq-processor"
        assert handler.dlq_topic == DLQHandler.DEFAULT_DLQ_TOPIC
        assert handler.max_retries == DLQHandler.DEFAULT_MAX_RETRIES
        assert handler.archive_dir == Path(DLQHandler.DEFAULT_ARCHIVE_DIR)
        assert handler.retry_handler is None
        assert handler.failure_handler is None

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", True)
    def test_init_with_custom_config(self):
        """Test initialization with custom configuration."""
        retry_fn = Mock()
        failure_fn = Mock()

        with tempfile.TemporaryDirectory() as tmpdir:
            handler = DLQHandler(
                pulsar_url="pulsar://custom:6650",
                subscription_name="custom-sub",
                dlq_topic="custom-dlq",
                max_retries=5,
                archive_dir=tmpdir,
                retry_handler=retry_fn,
                failure_handler=failure_fn,
            )

            assert handler.pulsar_url == "pulsar://custom:6650"
            assert handler.subscription_name == "custom-sub"
            assert handler.dlq_topic == "custom-dlq"
            assert handler.max_retries == 5
            assert handler.archive_dir == Path(tmpdir)
            assert handler.retry_handler == retry_fn
            assert handler.failure_handler == failure_fn

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", False)
    def test_init_without_pulsar(self):
        """Test initialization fails without pulsar-client."""
        with pytest.raises(ImportError, match="pulsar-client is not installed"):
            DLQHandler()

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", True)
    def test_initial_state(self):
        """Test initial state."""
        handler = DLQHandler()

        assert handler.client is None
        assert handler.consumer is None
        assert handler._running is False
        assert isinstance(handler.stats, DLQStats)

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", True)
    def test_archive_directory_created(self):
        """Test archive directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "test_archive"
            _ = DLQHandler(archive_dir=str(archive_path))  # Creates archive_dir

            assert archive_path.exists()
            assert archive_path.is_dir()


class TestDLQHandlerConnection:
    """Test connection management."""

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.dlq_handler.pulsar")
    def test_connect_success(self, mock_pulsar):
        """Test successful connection."""
        mock_client = Mock()
        mock_consumer = Mock()
        mock_pulsar.Client.return_value = mock_client
        mock_client.subscribe.return_value = mock_consumer

        handler = DLQHandler()
        handler.connect()

        mock_pulsar.Client.assert_called_once()
        mock_client.subscribe.assert_called_once()
        assert handler.client == mock_client
        assert handler.consumer == mock_consumer

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.dlq_handler.pulsar")
    def test_connect_failure(self, mock_pulsar):
        """Test connection failure."""
        mock_pulsar.Client.side_effect = Exception("Connection failed")

        handler = DLQHandler()

        with pytest.raises(Exception, match="Connection failed"):
            handler.connect()


class TestDLQHandlerMessageParsing:
    """Test message parsing."""

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", True)
    def test_parse_dlq_message_with_event(self):
        """Test parsing message with valid EntityEvent."""
        handler = DLQHandler()

        event = EntityEvent(
            entity_id="p-123",
            event_type="create",
            entity_type="person",
            payload={"name": "John"},
        )

        mock_msg = Mock()
        mock_msg.data.return_value = event.to_bytes()
        mock_msg.properties.return_value = {
            "original_topic": "persons-events",
            "failure_reason": "processing_error",
            "failure_count": "2",
            "first_failure_time": datetime.now(timezone.utc).isoformat(),
        }
        mock_msg.message_id.return_value = "msg-123"

        dlq_msg = handler._parse_dlq_message(mock_msg)

        assert dlq_msg.original_topic == "persons-events"
        assert dlq_msg.original_event is not None
        assert dlq_msg.failure_reason == "processing_error"
        assert dlq_msg.failure_count == 2
        assert dlq_msg.message_id == "msg-123"

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", True)
    def test_parse_dlq_message_without_event(self):
        """Test parsing message with invalid event data."""
        handler = DLQHandler()

        mock_msg = Mock()
        mock_msg.data.return_value = b"invalid data"
        mock_msg.properties.return_value = {
            "original_topic": "test",
            "failure_reason": "error",
        }
        mock_msg.message_id.return_value = "msg-123"

        dlq_msg = handler._parse_dlq_message(mock_msg)

        assert dlq_msg.original_event is None
        assert dlq_msg.raw_data == b"invalid data"

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", True)
    def test_parse_dlq_message_with_defaults(self):
        """Test parsing message with missing properties."""
        handler = DLQHandler()

        mock_msg = Mock()
        mock_msg.data.return_value = b"data"
        mock_msg.properties.return_value = {}
        mock_msg.message_id.return_value = "msg-123"

        dlq_msg = handler._parse_dlq_message(mock_msg)

        assert dlq_msg.original_topic == "unknown"
        assert dlq_msg.failure_reason == "unknown"
        assert dlq_msg.failure_count == 1


class TestDLQHandlerRetryLogic:
    """Test retry logic."""

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", True)
    def test_should_retry_below_max(self):
        """Test should retry when below max retries."""
        handler = DLQHandler(max_retries=3)

        dlq_msg = DLQMessage(
            original_topic="test",
            original_event=None,
            failure_reason="error",
            failure_count=2,
            first_failure_time=datetime.now(timezone.utc),
            last_failure_time=datetime.now(timezone.utc),
            message_id="msg-123",
        )

        assert handler._should_retry(dlq_msg) is True

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", True)
    def test_should_not_retry_at_max(self):
        """Test should not retry when at max retries."""
        handler = DLQHandler(max_retries=3)

        dlq_msg = DLQMessage(
            original_topic="test",
            original_event=None,
            failure_reason="error",
            failure_count=3,
            first_failure_time=datetime.now(timezone.utc),
            last_failure_time=datetime.now(timezone.utc),
            message_id="msg-123",
        )

        assert handler._should_retry(dlq_msg) is False

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", True)
    def test_retry_message_success(self):
        """Test successful message retry."""
        retry_fn = Mock(return_value=True)
        handler = DLQHandler(retry_handler=retry_fn)

        event = EntityEvent(
            entity_id="p-123",
            event_type="create",
            entity_type="person",
            payload={},
        )

        dlq_msg = DLQMessage(
            original_topic="test",
            original_event=event,
            failure_reason="error",
            failure_count=1,
            first_failure_time=datetime.now(timezone.utc),
            last_failure_time=datetime.now(timezone.utc),
            message_id="msg-123",
        )

        result = handler._retry_message(dlq_msg)

        assert result is True
        assert handler.stats.messages_retried == 1
        retry_fn.assert_called_once_with(event)

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", True)
    def test_retry_message_failure(self):
        """Test failed message retry."""
        retry_fn = Mock(return_value=False)
        handler = DLQHandler(retry_handler=retry_fn)

        event = EntityEvent(
            entity_id="p-123",
            event_type="create",
            entity_type="person",
            payload={},
        )

        dlq_msg = DLQMessage(
            original_topic="test",
            original_event=event,
            failure_reason="error",
            failure_count=1,
            first_failure_time=datetime.now(timezone.utc),
            last_failure_time=datetime.now(timezone.utc),
            message_id="msg-123",
        )

        result = handler._retry_message(dlq_msg)

        assert result is False
        assert handler.stats.messages_retried == 0

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", True)
    def test_retry_message_no_handler(self):
        """Test retry without handler."""
        handler = DLQHandler(retry_handler=None)

        dlq_msg = DLQMessage(
            original_topic="test",
            original_event=None,
            failure_reason="error",
            failure_count=1,
            first_failure_time=datetime.now(timezone.utc),
            last_failure_time=datetime.now(timezone.utc),
            message_id="msg-123",
        )

        result = handler._retry_message(dlq_msg)

        assert result is False


class TestDLQHandlerArchiving:
    """Test message archiving."""

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", True)
    def test_archive_message(self):
        """Test archiving a message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            handler = DLQHandler(archive_dir=tmpdir)

            dlq_msg = DLQMessage(
                original_topic="test",
                original_event=None,
                failure_reason="error",
                failure_count=3,
                first_failure_time=datetime.now(timezone.utc),
                last_failure_time=datetime.now(timezone.utc),
                message_id="msg-123",
            )

            handler._archive_message(dlq_msg)

            assert handler.stats.messages_archived == 1
            # Check file was created
            files = list(Path(tmpdir).glob("dlq_*.json"))
            assert len(files) == 1

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", True)
    def test_handle_permanent_failure(self):
        """Test handling permanent failure."""
        failure_fn = Mock()

        with tempfile.TemporaryDirectory() as tmpdir:
            handler = DLQHandler(archive_dir=tmpdir, failure_handler=failure_fn)

            dlq_msg = DLQMessage(
                original_topic="test",
                original_event=None,
                failure_reason="error",
                failure_count=3,
                first_failure_time=datetime.now(timezone.utc),
                last_failure_time=datetime.now(timezone.utc),
                message_id="msg-123",
            )

            handler._handle_permanent_failure(dlq_msg)

            assert handler.stats.messages_failed_permanently == 1
            assert handler.stats.messages_archived == 1
            failure_fn.assert_called_once_with(dlq_msg)


class TestDLQHandlerProcessing:
    """Test message processing."""

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", True)
    def test_process_message_with_retry_success(self):
        """Test processing message with successful retry."""
        retry_fn = Mock(return_value=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            handler = DLQHandler(
                max_retries=3,
                archive_dir=tmpdir,
                retry_handler=retry_fn,
            )

            event = EntityEvent(
                entity_id="p-123",
                event_type="create",
                entity_type="person",
                payload={},
            )

            mock_msg = Mock()
            mock_msg.data.return_value = event.to_bytes()
            mock_msg.properties.return_value = {
                "original_topic": "test",
                "failure_reason": "error",
                "failure_count": "1",
                "first_failure_time": datetime.now(timezone.utc).isoformat(),
            }
            mock_msg.message_id.return_value = "msg-123"

            result = handler.process_message(mock_msg)

            assert result is True
            assert handler.stats.messages_processed == 1
            assert handler.stats.messages_retried == 1
            assert handler.stats.messages_failed_permanently == 0

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", True)
    def test_process_message_max_retries_reached(self):
        """Test processing message when max retries reached."""
        retry_fn = Mock(return_value=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            handler = DLQHandler(
                max_retries=3,
                archive_dir=tmpdir,
                retry_handler=retry_fn,
            )

            mock_msg = Mock()
            mock_msg.data.return_value = b"data"
            mock_msg.properties.return_value = {
                "original_topic": "test",
                "failure_reason": "error",
                "failure_count": "3",  # At max
                "first_failure_time": datetime.now(timezone.utc).isoformat(),
            }
            mock_msg.message_id.return_value = "msg-123"

            result = handler.process_message(mock_msg)

            assert result is True
            assert handler.stats.messages_processed == 1
            assert handler.stats.messages_failed_permanently == 1
            assert handler.stats.messages_archived == 1


class TestDLQHandlerBatchProcessing:
    """Test batch processing."""

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.dlq_handler.pulsar")
    def test_process_batch(self, mock_pulsar):
        """Test batch processing."""
        mock_client = Mock()
        mock_consumer = Mock()
        mock_pulsar.Client.return_value = mock_client
        mock_client.subscribe.return_value = mock_consumer

        # Mock messages
        mock_messages = []
        for i in range(3):
            msg = Mock()
            msg.data.return_value = b"data"
            msg.properties.return_value = {
                "original_topic": "test",
                "failure_reason": "error",
                "failure_count": "5",  # Over max
            }
            msg.message_id.return_value = f"msg-{i}"
            mock_messages.append(msg)

        mock_consumer.receive.side_effect = mock_messages + [Exception("Timeout")]

        with tempfile.TemporaryDirectory() as tmpdir:
            handler = DLQHandler(archive_dir=tmpdir)
            processed = handler.process_batch(max_messages=10, timeout_ms=100)

            assert processed == 3
            assert handler.stats.messages_processed == 3


class TestDLQHandlerStatistics:
    """Test statistics tracking."""

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", True)
    def test_get_stats(self):
        """Test getting statistics."""
        handler = DLQHandler()

        handler.stats.messages_processed = 10
        handler.stats.messages_retried = 5

        stats = handler.get_stats()

        assert stats["messages_processed"] == 10
        assert stats["messages_retried"] == 5
        assert isinstance(stats, dict)


class TestDLQHandlerContextManager:
    """Test context manager usage."""

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", True)
    @patch("banking.streaming.dlq_handler.pulsar")
    def test_context_manager(self, mock_pulsar):
        """Test using DLQHandler as context manager."""
        mock_client = Mock()
        mock_consumer = Mock()
        mock_pulsar.Client.return_value = mock_client
        mock_client.subscribe.return_value = mock_consumer

        handler = DLQHandler()

        with handler as h:
            assert h == handler
            assert h.client is not None

        mock_consumer.close.assert_called_once()
        mock_client.close.assert_called_once()


class TestMockDLQHandler:
    """Test MockDLQHandler."""

    def test_mock_handler_creation(self):
        """Test creating mock handler."""
        handler = MockDLQHandler()

        assert handler.messages == []
        assert isinstance(handler.stats, DLQStats)
        assert handler._running is False

    def test_mock_handler_process_message(self):
        """Test mock handler process message."""
        handler = MockDLQHandler()

        result = handler.process_message(Mock())

        assert result is True
        assert handler.stats.messages_processed == 1


class TestGetDLQHandler:
    """Test factory function."""

    def test_get_dlq_handler_mock(self):
        """Test getting mock handler."""
        handler = get_dlq_handler(mock=True)

        assert isinstance(handler, MockDLQHandler)

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", False)
    def test_get_dlq_handler_no_pulsar(self):
        """Test getting handler without Pulsar."""
        handler = get_dlq_handler(mock=False)

        assert isinstance(handler, MockDLQHandler)

    @patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", True)
    def test_get_dlq_handler_real(self):
        """Test getting real handler."""
        handler = get_dlq_handler(mock=False)

        assert isinstance(handler, DLQHandler)


# Made with Bob
