"""Tests for banking.streaming.dlq_handler module."""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, mock_open, patch

import pytest

from banking.streaming.dlq_handler import (
    DLQMessage,
    DLQStats,
    MockDLQHandler,
    get_dlq_handler,
)
from banking.streaming.events import EntityEvent


class TestDLQMessage:
    def test_creation(self):
        msg = DLQMessage(
            original_topic="test-topic",
            original_event=None,
            failure_reason="parse error",
            failure_count=1,
            first_failure_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            last_failure_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            message_id="msg-123",
        )
        assert msg.original_topic == "test-topic"
        assert msg.failure_count == 1

    def test_to_dict(self):
        msg = DLQMessage(
            original_topic="topic",
            original_event=None,
            failure_reason="err",
            failure_count=2,
            first_failure_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            last_failure_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            message_id="m1",
        )
        d = msg.to_dict()
        assert d["original_topic"] == "topic"
        assert d["failure_count"] == 2

    def test_to_json(self):
        msg = DLQMessage(
            original_topic="topic",
            original_event=None,
            failure_reason="err",
            failure_count=1,
            first_failure_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            last_failure_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            message_id="m1",
        )
        j = msg.to_json()
        parsed = json.loads(j)
        assert parsed["original_topic"] == "topic"

    def test_to_dict_with_event(self):
        event = MagicMock(spec=EntityEvent)
        event.to_dict.return_value = {"entity_type": "person"}
        msg = DLQMessage(
            original_topic="topic",
            original_event=event,
            failure_reason="err",
            failure_count=1,
            first_failure_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            last_failure_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            message_id="m1",
        )
        d = msg.to_dict()
        assert d["original_event"]["entity_type"] == "person"


class TestDLQStats:
    def test_defaults(self):
        stats = DLQStats()
        assert stats.messages_processed == 0
        assert stats.errors == []

    def test_to_dict(self):
        stats = DLQStats(messages_processed=5, messages_retried=2)
        d = stats.to_dict()
        assert d["messages_processed"] == 5


class TestMockDLQHandler:
    def test_lifecycle(self):
        handler = MockDLQHandler()
        handler.connect()
        handler.start()
        assert handler._running
        handler.stop()
        assert not handler._running
        handler.close()

    def test_process_message(self):
        handler = MockDLQHandler()
        assert handler.process_message(MagicMock())
        assert handler.stats.messages_processed == 1

    def test_process_batch(self):
        handler = MockDLQHandler()
        assert handler.process_batch() == 0

    def test_get_stats(self):
        handler = MockDLQHandler()
        stats = handler.get_stats()
        assert stats["messages_processed"] == 0

    def test_context_manager(self):
        with MockDLQHandler() as h:
            assert h is not None


class TestGetDLQHandler:
    def test_mock_handler(self):
        handler = get_dlq_handler(mock=True)
        assert isinstance(handler, MockDLQHandler)

    def test_no_pulsar_returns_mock(self):
        with patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", False):
            handler = get_dlq_handler()
            assert isinstance(handler, MockDLQHandler)


class TestDLQHandler:
    @pytest.fixture
    def mock_pulsar(self):
        with patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", True):
            with patch("banking.streaming.dlq_handler.pulsar") as mp:
                mp.Client.return_value = MagicMock()
                mp.InitialPosition = MagicMock()
                yield mp

    def test_init(self, mock_pulsar, tmp_path):
        from banking.streaming.dlq_handler import DLQHandler

        h = DLQHandler(archive_dir=str(tmp_path / "archive"))
        assert h.max_retries == 3

    def test_connect(self, mock_pulsar, tmp_path):
        from banking.streaming.dlq_handler import DLQHandler

        h = DLQHandler(archive_dir=str(tmp_path / "archive"))
        h.connect()
        mock_pulsar.Client.assert_called_once()

    def test_should_retry(self, mock_pulsar, tmp_path):
        from banking.streaming.dlq_handler import DLQHandler

        h = DLQHandler(max_retries=3, archive_dir=str(tmp_path / "archive"))
        msg = DLQMessage(
            "t", None, "err", 1, datetime.now(timezone.utc), datetime.now(timezone.utc), "m1"
        )
        assert h._should_retry(msg)
        msg2 = DLQMessage(
            "t", None, "err", 5, datetime.now(timezone.utc), datetime.now(timezone.utc), "m2"
        )
        assert not h._should_retry(msg2)

    def test_retry_message_no_handler(self, mock_pulsar, tmp_path):
        from banking.streaming.dlq_handler import DLQHandler

        h = DLQHandler(archive_dir=str(tmp_path / "archive"))
        msg = DLQMessage(
            "t", None, "err", 1, datetime.now(timezone.utc), datetime.now(timezone.utc), "m1"
        )
        assert not h._retry_message(msg)

    def test_retry_message_with_handler(self, mock_pulsar, tmp_path):
        from banking.streaming.dlq_handler import DLQHandler

        handler_fn = MagicMock(return_value=True)
        h = DLQHandler(retry_handler=handler_fn, archive_dir=str(tmp_path / "archive"))
        event = MagicMock(spec=EntityEvent)
        msg = DLQMessage(
            "t", event, "err", 1, datetime.now(timezone.utc), datetime.now(timezone.utc), "m1"
        )
        assert h._retry_message(msg)
        assert h.stats.messages_retried == 1

    def test_retry_message_handler_fails(self, mock_pulsar, tmp_path):
        from banking.streaming.dlq_handler import DLQHandler

        handler_fn = MagicMock(side_effect=Exception("fail"))
        h = DLQHandler(retry_handler=handler_fn, archive_dir=str(tmp_path / "archive"))
        event = MagicMock(spec=EntityEvent)
        msg = DLQMessage(
            "t", event, "err", 1, datetime.now(timezone.utc), datetime.now(timezone.utc), "m1"
        )
        assert not h._retry_message(msg)

    def test_archive_message(self, mock_pulsar, tmp_path):
        from banking.streaming.dlq_handler import DLQHandler

        h = DLQHandler(archive_dir=str(tmp_path / "archive"))
        msg = DLQMessage(
            "t",
            None,
            "err",
            3,
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
            "msg12345678",
        )
        h._archive_message(msg)
        assert h.stats.messages_archived == 1
        files = list((tmp_path / "archive").glob("*.json"))
        assert len(files) == 1

    def test_handle_permanent_failure(self, mock_pulsar, tmp_path):
        from banking.streaming.dlq_handler import DLQHandler

        failure_fn = MagicMock()
        h = DLQHandler(failure_handler=failure_fn, archive_dir=str(tmp_path / "archive"))
        msg = DLQMessage(
            "t", None, "err", 5, datetime.now(timezone.utc), datetime.now(timezone.utc), "m1234567"
        )
        h._handle_permanent_failure(msg)
        assert h.stats.messages_failed_permanently == 1
        failure_fn.assert_called_once()

    def test_handle_permanent_failure_handler_error(self, mock_pulsar, tmp_path):
        from banking.streaming.dlq_handler import DLQHandler

        failure_fn = MagicMock(side_effect=Exception("fail"))
        h = DLQHandler(failure_handler=failure_fn, archive_dir=str(tmp_path / "archive"))
        msg = DLQMessage(
            "t", None, "err", 5, datetime.now(timezone.utc), datetime.now(timezone.utc), "m1234567"
        )
        h._handle_permanent_failure(msg)

    def test_process_message(self, mock_pulsar, tmp_path):
        from banking.streaming.dlq_handler import DLQHandler

        h = DLQHandler(archive_dir=str(tmp_path / "archive"))
        mock_msg = MagicMock()
        mock_msg.data.return_value = b'{"entity_type": "person"}'
        mock_msg.properties.return_value = {
            "original_topic": "test",
            "failure_reason": "err",
            "failure_count": "5",
        }
        mock_msg.message_id.return_value = "mid-12345678"
        result = h.process_message(mock_msg)
        assert result is True

    def test_process_message_error(self, mock_pulsar, tmp_path):
        from banking.streaming.dlq_handler import DLQHandler

        h = DLQHandler(archive_dir=str(tmp_path / "archive"))
        mock_msg = MagicMock()
        mock_msg.data.side_effect = Exception("decode error")
        result = h.process_message(mock_msg)
        assert result is False

    def test_process_batch(self, mock_pulsar, tmp_path):
        from banking.streaming.dlq_handler import DLQHandler

        h = DLQHandler(archive_dir=str(tmp_path / "archive"))
        mock_consumer = MagicMock()
        mock_consumer.receive.side_effect = Exception("timeout")
        h.consumer = mock_consumer
        result = h.process_batch(max_messages=5)
        assert result == 0

    def test_stop(self, mock_pulsar, tmp_path):
        from banking.streaming.dlq_handler import DLQHandler

        h = DLQHandler(archive_dir=str(tmp_path / "archive"))
        h._running = True
        h.stop()
        assert not h._running

    def test_close(self, mock_pulsar, tmp_path):
        from banking.streaming.dlq_handler import DLQHandler

        h = DLQHandler(archive_dir=str(tmp_path / "archive"))
        mock_consumer = MagicMock()
        mock_client = MagicMock()
        h.consumer = mock_consumer
        h.client = mock_client
        h.close()
        mock_consumer.close.assert_called_once()
        mock_client.close.assert_called_once()

    def test_get_stats(self, mock_pulsar, tmp_path):
        from banking.streaming.dlq_handler import DLQHandler

        h = DLQHandler(archive_dir=str(tmp_path / "archive"))
        stats = h.get_stats()
        assert stats["messages_processed"] == 0

    def test_context_manager(self, mock_pulsar, tmp_path):
        from banking.streaming.dlq_handler import DLQHandler

        h = DLQHandler(archive_dir=str(tmp_path / "archive"))
        with h:
            pass

    def test_no_pulsar_raises(self):
        with patch("banking.streaming.dlq_handler.PULSAR_AVAILABLE", False):
            from banking.streaming.dlq_handler import DLQHandler

            with pytest.raises(ImportError):
                DLQHandler()
