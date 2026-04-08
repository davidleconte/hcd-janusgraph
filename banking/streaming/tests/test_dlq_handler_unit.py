"""
Unit tests for DLQHandler.

Tests the Dead Letter Queue handler with mocked dependencies.
All tests are deterministic with fixed timestamps and mocked Pulsar.

Created: 2026-04-07
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, call
import tempfile

import pytest

# Mock pulsar before importing DLQHandler
mock_pulsar = MagicMock()
mock_pulsar.Client = MagicMock
mock_pulsar.Consumer = MagicMock
mock_pulsar.ConsumerType = MagicMock()
mock_pulsar.ConsumerType.Shared = "Shared"
mock_pulsar.InitialPosition = MagicMock()
mock_pulsar.InitialPosition.Earliest = "Earliest"
sys.modules['pulsar'] = mock_pulsar

from banking.streaming.dlq_handler import (
    DLQHandler,
    DLQMessage,
    DLQStats,
    MockDLQHandler,
    get_dlq_handler
)
from banking.streaming.events import EntityEvent

# Fixed timestamp for deterministic tests
FIXED_TIMESTAMP = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def temp_archive_dir():
    """Create temporary archive directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_dlq_message():
    """Create a sample DLQ message."""
    event = EntityEvent(
        entity_id="p-123",
        entity_type="person",
        event_type="create",
        timestamp=FIXED_TIMESTAMP,
        version=1,
        source="test",
        text_for_embedding="John Doe",
        payload={"name": "John Doe"}
    )
    
    return DLQMessage(
        original_topic="persistent://public/banking/persons-events",
        original_event=event,
        failure_reason="Connection timeout",
        failure_count=1,
        first_failure_time=FIXED_TIMESTAMP,
        last_failure_time=FIXED_TIMESTAMP,
        message_id="msg-123",
        raw_data=event.to_bytes(),
        metadata={"retry_count": "1"}
    )


@pytest.fixture
def mock_pulsar_message(sample_dlq_message):
    """Create a mock Pulsar message."""
    msg = MagicMock()
    msg.data.return_value = sample_dlq_message.raw_data
    msg.message_id.return_value = "msg-123"
    msg.properties.return_value = {
        "original_topic": sample_dlq_message.original_topic,
        "failure_reason": sample_dlq_message.failure_reason,
        "failure_count": str(sample_dlq_message.failure_count),
        "first_failure_time": sample_dlq_message.first_failure_time.isoformat(),
    }
    return msg


class TestDLQMessage:
    """Test DLQMessage dataclass."""

    def test_to_dict(self, sample_dlq_message):
        """Test converting DLQMessage to dictionary."""
        result = sample_dlq_message.to_dict()
        
        assert result["original_topic"] == "persistent://public/banking/persons-events"
        assert result["failure_reason"] == "Connection timeout"
        assert result["failure_count"] == 1
        assert result["message_id"] == "msg-123"
        assert result["original_event"] is not None
        assert result["metadata"] == {"retry_count": "1"}

    def test_to_json(self, sample_dlq_message):
        """Test converting DLQMessage to JSON."""
        import json
        
        json_str = sample_dlq_message.to_json()
        result = json.loads(json_str)
        
        assert result["original_topic"] == "persistent://public/banking/persons-events"
        assert result["failure_count"] == 1

    def test_to_dict_without_event(self):
        """Test to_dict when original_event is None."""
        msg = DLQMessage(
            original_topic="test-topic",
            original_event=None,
            failure_reason="Parse error",
            failure_count=1,
            first_failure_time=FIXED_TIMESTAMP,
            last_failure_time=FIXED_TIMESTAMP,
            message_id="msg-456"
        )
        
        result = msg.to_dict()
        assert result["original_event"] is None


class TestDLQStats:
    """Test DLQStats dataclass."""

    def test_initialization(self):
        """Test DLQStats initialization."""
        stats = DLQStats()
        
        assert stats.messages_processed == 0
        assert stats.messages_retried == 0
        assert stats.messages_archived == 0
        assert stats.messages_failed_permanently == 0
        assert stats.errors == []

    def test_to_dict(self):
        """Test converting DLQStats to dictionary."""
        stats = DLQStats(
            messages_processed=10,
            messages_retried=5,
            messages_archived=3,
            messages_failed_permanently=2,
            errors=["error1", "error2"]
        )
        
        result = stats.to_dict()
        
        assert result["messages_processed"] == 10
        assert result["messages_retried"] == 5
        assert result["messages_archived"] == 3
        assert result["messages_failed_permanently"] == 2
        assert result["errors"] == ["error1", "error2"]


class TestDLQHandlerInitialization:
    """Test DLQHandler initialization."""

    def test_init_with_defaults(self, temp_archive_dir):
        """Test initialization with default values."""
        handler = DLQHandler(archive_dir=temp_archive_dir)
        
        assert handler.pulsar_url == "pulsar://localhost:6650"
        assert handler.subscription_name == "dlq-processor"
        assert handler.dlq_topic == "persistent://public/banking/dlq-events"
        assert handler.max_retries == 3
        assert handler.archive_dir == Path(temp_archive_dir)
        assert handler.retry_handler is None
        assert handler.failure_handler is None

    def test_init_with_custom_values(self, temp_archive_dir):
        """Test initialization with custom values."""
        retry_handler = lambda event: True
        failure_handler = lambda msg: None
        
        handler = DLQHandler(
            pulsar_url="pulsar://custom:6650",
            subscription_name="custom-sub",
            dlq_topic="custom-dlq",
            max_retries=5,
            archive_dir=temp_archive_dir,
            retry_handler=retry_handler,
            failure_handler=failure_handler
        )
        
        assert handler.pulsar_url == "pulsar://custom:6650"
        assert handler.subscription_name == "custom-sub"
        assert handler.dlq_topic == "custom-dlq"
        assert handler.max_retries == 5
        assert handler.retry_handler == retry_handler
        assert handler.failure_handler == failure_handler

    def test_init_creates_archive_directory(self, temp_archive_dir):
        """Test that initialization creates archive directory."""
        archive_path = Path(temp_archive_dir) / "subdir"
        handler = DLQHandler(archive_dir=str(archive_path))
        
        assert archive_path.exists()

    def test_init_state_initialized(self, temp_archive_dir):
        """Test that state is initialized correctly."""
        handler = DLQHandler(archive_dir=temp_archive_dir)
        
        assert handler.client is None
        assert handler.consumer is None
        assert handler.stats.messages_processed == 0
        assert handler._running is False


class TestDLQHandlerConnection:
    """Test DLQHandler connection management."""

    @patch('banking.streaming.dlq_handler.pulsar')
    def test_connect_establishes_connection(self, mock_pulsar_module, temp_archive_dir):
        """Test that connect establishes Pulsar connection."""
        mock_client = MagicMock()
        mock_consumer = MagicMock()
        mock_pulsar_module.Client.return_value = mock_client
        mock_client.subscribe.return_value = mock_consumer
        
        handler = DLQHandler(archive_dir=temp_archive_dir)
        handler.connect()
        
        mock_pulsar_module.Client.assert_called_once()
        assert handler.client == mock_client
        assert handler.consumer == mock_consumer

    def test_close_closes_connections(self, temp_archive_dir):
        """Test that close closes all connections."""
        handler = DLQHandler(archive_dir=temp_archive_dir)
        handler.client = MagicMock()
        handler.consumer = MagicMock()
        handler._running = True
        
        handler.close()
        
        handler.consumer.close.assert_called_once()
        handler.client.close.assert_called_once()
        assert handler._running is False


class TestDLQHandlerMessageParsing:
    """Test DLQ message parsing."""

    def test_parse_dlq_message_success(self, temp_archive_dir, mock_pulsar_message):
        """Test successful message parsing."""
        handler = DLQHandler(archive_dir=temp_archive_dir)
        
        dlq_msg = handler._parse_dlq_message(mock_pulsar_message)
        
        assert dlq_msg.original_topic == "persistent://public/banking/persons-events"
        assert dlq_msg.failure_reason == "Connection timeout"
        assert dlq_msg.failure_count == 1
        assert dlq_msg.message_id == "msg-123"
        assert dlq_msg.original_event is not None

    def test_parse_dlq_message_without_event(self, temp_archive_dir):
        """Test parsing message that can't be decoded as EntityEvent."""
        handler = DLQHandler(archive_dir=temp_archive_dir)
        
        msg = MagicMock()
        msg.data.return_value = b"invalid data"
        msg.message_id.return_value = "msg-456"
        msg.properties.return_value = {
            "original_topic": "test-topic",
            "failure_reason": "Parse error",
            "failure_count": "1",
        }
        
        dlq_msg = handler._parse_dlq_message(msg)
        
        assert dlq_msg.original_event is None
        assert dlq_msg.failure_reason == "Parse error"


class TestDLQHandlerRetryLogic:
    """Test retry logic."""

    def test_should_retry_below_max(self, temp_archive_dir, sample_dlq_message):
        """Test should_retry returns True when below max retries."""
        handler = DLQHandler(archive_dir=temp_archive_dir, max_retries=3)
        sample_dlq_message.failure_count = 2
        
        assert handler._should_retry(sample_dlq_message) is True

    def test_should_retry_at_max(self, temp_archive_dir, sample_dlq_message):
        """Test should_retry returns False when at max retries."""
        handler = DLQHandler(archive_dir=temp_archive_dir, max_retries=3)
        sample_dlq_message.failure_count = 3
        
        assert handler._should_retry(sample_dlq_message) is False

    def test_should_retry_above_max(self, temp_archive_dir, sample_dlq_message):
        """Test should_retry returns False when above max retries."""
        handler = DLQHandler(archive_dir=temp_archive_dir, max_retries=3)
        sample_dlq_message.failure_count = 5
        
        assert handler._should_retry(sample_dlq_message) is False

    def test_retry_message_success(self, temp_archive_dir, sample_dlq_message):
        """Test successful message retry."""
        retry_handler = Mock(return_value=True)
        handler = DLQHandler(archive_dir=temp_archive_dir, retry_handler=retry_handler)
        
        result = handler._retry_message(sample_dlq_message)
        
        assert result is True
        assert handler.stats.messages_retried == 1
        retry_handler.assert_called_once_with(sample_dlq_message.original_event)

    def test_retry_message_failure(self, temp_archive_dir, sample_dlq_message):
        """Test failed message retry."""
        retry_handler = Mock(return_value=False)
        handler = DLQHandler(archive_dir=temp_archive_dir, retry_handler=retry_handler)
        
        result = handler._retry_message(sample_dlq_message)
        
        assert result is False
        assert handler.stats.messages_retried == 0

    def test_retry_message_exception(self, temp_archive_dir, sample_dlq_message):
        """Test retry with exception."""
        retry_handler = Mock(side_effect=Exception("Retry failed"))
        handler = DLQHandler(archive_dir=temp_archive_dir, retry_handler=retry_handler)
        
        result = handler._retry_message(sample_dlq_message)
        
        assert result is False

    def test_retry_message_without_handler(self, temp_archive_dir, sample_dlq_message):
        """Test retry without retry handler."""
        handler = DLQHandler(archive_dir=temp_archive_dir)
        
        result = handler._retry_message(sample_dlq_message)
        
        assert result is False


class TestDLQHandlerArchiving:
    """Test message archiving."""

    def test_archive_message_success(self, temp_archive_dir, sample_dlq_message):
        """Test successful message archiving."""
        handler = DLQHandler(archive_dir=temp_archive_dir)
        
        handler._archive_message(sample_dlq_message)
        
        assert handler.stats.messages_archived == 1
        # Check that file was created
        archive_files = list(Path(temp_archive_dir).glob("dlq_*.json"))
        assert len(archive_files) == 1

    def test_archive_message_creates_json_file(self, temp_archive_dir, sample_dlq_message):
        """Test that archived message is valid JSON."""
        import json
        
        handler = DLQHandler(archive_dir=temp_archive_dir)
        handler._archive_message(sample_dlq_message)
        
        archive_files = list(Path(temp_archive_dir).glob("dlq_*.json"))
        with open(archive_files[0]) as f:
            data = json.load(f)
        
        assert data["original_topic"] == sample_dlq_message.original_topic
        assert data["failure_count"] == sample_dlq_message.failure_count


class TestDLQHandlerPermanentFailure:
    """Test permanent failure handling."""

    def test_handle_permanent_failure_archives(self, temp_archive_dir, sample_dlq_message):
        """Test that permanent failure archives message."""
        handler = DLQHandler(archive_dir=temp_archive_dir)
        
        handler._handle_permanent_failure(sample_dlq_message)
        
        assert handler.stats.messages_failed_permanently == 1
        assert handler.stats.messages_archived == 1

    def test_handle_permanent_failure_calls_handler(self, temp_archive_dir, sample_dlq_message):
        """Test that permanent failure calls custom handler."""
        failure_handler = Mock()
        handler = DLQHandler(archive_dir=temp_archive_dir, failure_handler=failure_handler)
        
        handler._handle_permanent_failure(sample_dlq_message)
        
        failure_handler.assert_called_once_with(sample_dlq_message)

    def test_handle_permanent_failure_handler_exception(self, temp_archive_dir, sample_dlq_message):
        """Test permanent failure with handler exception."""
        failure_handler = Mock(side_effect=Exception("Handler failed"))
        handler = DLQHandler(archive_dir=temp_archive_dir, failure_handler=failure_handler)
        
        # Should not raise exception
        handler._handle_permanent_failure(sample_dlq_message)
        
        assert handler.stats.messages_failed_permanently == 1


class TestDLQHandlerProcessing:
    """Test message processing."""

    def test_process_message_success(self, temp_archive_dir, mock_pulsar_message):
        """Test successful message processing."""
        handler = DLQHandler(archive_dir=temp_archive_dir, max_retries=0)
        
        result = handler.process_message(mock_pulsar_message)
        
        assert result is True
        assert handler.stats.messages_processed == 1
        assert handler.stats.messages_failed_permanently == 1

    def test_process_message_with_retry(self, temp_archive_dir, mock_pulsar_message):
        """Test message processing with successful retry."""
        retry_handler = Mock(return_value=True)
        handler = DLQHandler(
            archive_dir=temp_archive_dir,
            max_retries=3,
            retry_handler=retry_handler
        )
        
        result = handler.process_message(mock_pulsar_message)
        
        assert result is True
        assert handler.stats.messages_processed == 1
        assert handler.stats.messages_retried == 1
        assert handler.stats.messages_failed_permanently == 0

    def test_process_batch_empty(self, temp_archive_dir):
        """Test processing empty batch."""
        handler = DLQHandler(archive_dir=temp_archive_dir)
        handler.consumer = MagicMock()
        handler.consumer.receive.side_effect = Exception("Timeout")
        
        result = handler.process_batch(max_messages=10, timeout_ms=100)
        
        assert result == 0

    def test_process_batch_single_message(self, temp_archive_dir, mock_pulsar_message):
        """Test processing single message batch."""
        handler = DLQHandler(archive_dir=temp_archive_dir, max_retries=0)
        handler.consumer = MagicMock()
        handler.consumer.receive.side_effect = [mock_pulsar_message, Exception("Timeout")]
        
        result = handler.process_batch(max_messages=10, timeout_ms=100)
        
        assert result == 1
        assert handler.stats.messages_processed == 1


class TestDLQHandlerStats:
    """Test statistics collection."""

    def test_get_stats_returns_dict(self, temp_archive_dir):
        """Test that get_stats returns dictionary."""
        handler = DLQHandler(archive_dir=temp_archive_dir)
        handler.stats.messages_processed = 10
        
        stats = handler.get_stats()
        
        assert isinstance(stats, dict)
        assert stats["messages_processed"] == 10

    def test_stats_updated_on_processing(self, temp_archive_dir, mock_pulsar_message):
        """Test that stats are updated during processing."""
        handler = DLQHandler(archive_dir=temp_archive_dir, max_retries=0)
        
        handler.process_message(mock_pulsar_message)
        
        stats = handler.get_stats()
        assert stats["messages_processed"] == 1
        assert stats["messages_failed_permanently"] == 1
        assert stats["messages_archived"] == 1


class TestDLQHandlerContextManager:
    """Test context manager protocol."""

    @patch('banking.streaming.dlq_handler.pulsar')
    def test_context_manager_enter(self, mock_pulsar_module, temp_archive_dir):
        """Test context manager __enter__."""
        mock_client = MagicMock()
        mock_consumer = MagicMock()
        mock_pulsar_module.Client.return_value = mock_client
        mock_client.subscribe.return_value = mock_consumer
        
        handler = DLQHandler(archive_dir=temp_archive_dir)
        
        with handler as h:
            assert h == handler
            assert handler.client is not None
            assert handler.consumer is not None

    def test_context_manager_exit(self, temp_archive_dir):
        """Test context manager __exit__."""
        handler = DLQHandler(archive_dir=temp_archive_dir)
        handler.client = MagicMock()
        handler.consumer = MagicMock()
        
        handler.__exit__(None, None, None)
        
        handler.consumer.close.assert_called_once()
        handler.client.close.assert_called_once()

    def test_context_manager_exit_with_exception(self, temp_archive_dir):
        """Test context manager __exit__ with exception."""
        handler = DLQHandler(archive_dir=temp_archive_dir)
        handler.client = MagicMock()
        handler.consumer = MagicMock()
        
        result = handler.__exit__(ValueError, ValueError("test"), None)
        
        assert result is False  # Don't suppress exceptions


class TestMockDLQHandler:
    """Test MockDLQHandler."""

    def test_mock_handler_initialization(self):
        """Test MockDLQHandler initialization."""
        handler = MockDLQHandler()
        
        assert handler.messages == []
        assert handler.stats.messages_processed == 0
        assert handler._running is False

    def test_mock_handler_connect(self):
        """Test MockDLQHandler connect (no-op)."""
        handler = MockDLQHandler()
        handler.connect()  # Should not raise

    def test_mock_handler_process_message(self):
        """Test MockDLQHandler process_message."""
        handler = MockDLQHandler()
        
        result = handler.process_message(None)
        
        assert result is True
        assert handler.stats.messages_processed == 1

    def test_mock_handler_process_batch(self):
        """Test MockDLQHandler process_batch."""
        handler = MockDLQHandler()
        
        result = handler.process_batch()
        
        assert result == 0

    def test_mock_handler_start_stop(self):
        """Test MockDLQHandler start/stop."""
        handler = MockDLQHandler()
        
        handler.start()
        assert handler._running is True
        
        handler.stop()
        assert handler._running is False

    def test_mock_handler_context_manager(self):
        """Test MockDLQHandler context manager."""
        with MockDLQHandler() as handler:
            assert handler is not None


class TestGetDLQHandler:
    """Test get_dlq_handler factory function."""

    def test_get_dlq_handler_mock(self):
        """Test getting mock handler."""
        handler = get_dlq_handler(mock=True)
        
        assert isinstance(handler, MockDLQHandler)

    @patch('banking.streaming.dlq_handler.PULSAR_AVAILABLE', False)
    def test_get_dlq_handler_no_pulsar(self):
        """Test getting handler when Pulsar unavailable."""
        handler = get_dlq_handler(mock=False)
        
        assert isinstance(handler, MockDLQHandler)

    @patch('banking.streaming.dlq_handler.PULSAR_AVAILABLE', True)
    def test_get_dlq_handler_real(self, temp_archive_dir):
        """Test getting real handler when Pulsar available."""
        handler = get_dlq_handler(mock=False, archive_dir=temp_archive_dir)
        
        assert isinstance(handler, DLQHandler)

# Made with Bob
