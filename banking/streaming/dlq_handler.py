"""
Dead Letter Queue Handler (Week 6)
==================================

Handles failed messages from Pulsar consumers by:
1. Consuming from the DLQ topic
2. Logging failure details
3. Optionally retrying failed messages
4. Archiving permanently failed messages

Created: 2026-02-06
Week 6: DLQ Handling + Monitoring
"""

import logging
import json
import os
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from pathlib import Path

try:
    import pulsar
    from pulsar import Client, Consumer, ConsumerType, MessageId
    PULSAR_AVAILABLE = True
except ImportError:
    PULSAR_AVAILABLE = False
    pulsar = None
    Client = None
    Consumer = None
    ConsumerType = None
    MessageId = None

from .events import EntityEvent

logger = logging.getLogger(__name__)


@dataclass
class DLQMessage:
    """Represents a message from the Dead Letter Queue."""
    
    original_topic: str
    original_event: Optional[EntityEvent]
    failure_reason: str
    failure_count: int
    first_failure_time: datetime
    last_failure_time: datetime
    message_id: str
    raw_data: Optional[bytes] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'original_topic': self.original_topic,
            'original_event': self.original_event.to_dict() if self.original_event else None,
            'failure_reason': self.failure_reason,
            'failure_count': self.failure_count,
            'first_failure_time': self.first_failure_time.isoformat(),
            'last_failure_time': self.last_failure_time.isoformat(),
            'message_id': self.message_id,
            'metadata': self.metadata
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)


@dataclass
class DLQStats:
    """Statistics for DLQ processing."""
    
    messages_processed: int = 0
    messages_retried: int = 0
    messages_archived: int = 0
    messages_failed_permanently: int = 0
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DLQHandler:
    """
    Handler for Dead Letter Queue messages.
    
    Processes messages that failed to be consumed by the main consumers.
    Supports retry logic, archiving, and custom failure handlers.
    
    Example:
        >>> handler = DLQHandler(
        ...     pulsar_url="pulsar://localhost:6650",
        ...     subscription_name="dlq-processor"
        ... )
        >>> handler.start()
        >>> # Process messages until stopped
        >>> handler.stop()
    """
    
    DEFAULT_DLQ_TOPIC = "persistent://public/banking/dlq-events"
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_ARCHIVE_DIR = "/tmp/dlq_archive"
    
    def __init__(
        self,
        pulsar_url: str = None,
        subscription_name: str = "dlq-processor",
        dlq_topic: str = None,
        max_retries: int = None,
        archive_dir: str = None,
        retry_handler: Optional[Callable[[EntityEvent], bool]] = None,
        failure_handler: Optional[Callable[[DLQMessage], None]] = None
    ):
        """
        Initialize DLQ Handler.
        
        Args:
            pulsar_url: Pulsar broker URL
            subscription_name: Consumer subscription name
            dlq_topic: DLQ topic to consume from
            max_retries: Maximum retry attempts before permanent failure
            archive_dir: Directory to archive failed messages
            retry_handler: Custom function to retry messages
            failure_handler: Custom function to handle permanent failures
        """
        if not PULSAR_AVAILABLE:
            raise ImportError("pulsar-client is not installed")
        
        self.pulsar_url = pulsar_url or os.getenv('PULSAR_URL', 'pulsar://localhost:6650')
        self.subscription_name = subscription_name
        self.dlq_topic = dlq_topic or self.DEFAULT_DLQ_TOPIC
        self.max_retries = max_retries or self.DEFAULT_MAX_RETRIES
        self.archive_dir = Path(archive_dir or self.DEFAULT_ARCHIVE_DIR)
        self.retry_handler = retry_handler
        self.failure_handler = failure_handler
        
        # State
        self.client: Optional[Client] = None
        self.consumer: Optional[Consumer] = None
        self.stats = DLQStats()
        self._running = False
        
        # Create archive directory
        self.archive_dir.mkdir(parents=True, exist_ok=True)
    
    def connect(self):
        """Connect to Pulsar and create consumer."""
        logger.info("Connecting DLQ handler to %s", self.pulsar_url)
        
        self.client = pulsar.Client(
            self.pulsar_url,
            operation_timeout_seconds=30
        )
        
        self.consumer = self.client.subscribe(
            self.dlq_topic,
            subscription_name=self.subscription_name,
            consumer_type=ConsumerType.Shared,
            initial_position=pulsar.InitialPosition.Earliest
        )
        
        logger.info("Connected to DLQ topic: %s", self.dlq_topic)
    
    def _parse_dlq_message(self, msg) -> DLQMessage:
        """Parse a Pulsar message into DLQMessage."""
        try:
            data = msg.data()
            properties = msg.properties()
            
            # Try to parse as EntityEvent
            original_event = None
            try:
                original_event = EntityEvent.from_bytes(data)
            except Exception:
                pass
            
            return DLQMessage(
                original_topic=properties.get('original_topic', 'unknown'),
                original_event=original_event,
                failure_reason=properties.get('failure_reason', 'unknown'),
                failure_count=int(properties.get('failure_count', 1)),
                first_failure_time=datetime.fromisoformat(
                    properties.get('first_failure_time', datetime.now(timezone.utc).isoformat())
                ),
                last_failure_time=datetime.now(timezone.utc),
                message_id=str(msg.message_id()),
                raw_data=data,
                metadata=dict(properties)
            )
        except Exception as e:
            logger.error("Failed to parse DLQ message: %s", e)
            raise
    
    def _should_retry(self, dlq_msg: DLQMessage) -> bool:
        """Determine if message should be retried."""
        return dlq_msg.failure_count < self.max_retries
    
    def _retry_message(self, dlq_msg: DLQMessage) -> bool:
        """Attempt to retry a failed message."""
        if self.retry_handler and dlq_msg.original_event:
            try:
                success = self.retry_handler(dlq_msg.original_event)
                if success:
                    self.stats.messages_retried += 1
                    logger.info("Successfully retried message: %s", dlq_msg.message_id)
                return success
            except Exception as e:
                logger.error("Retry failed: %s", e)
                return False
        return False
    
    def _archive_message(self, dlq_msg: DLQMessage):
        """Archive a permanently failed message."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"dlq_{timestamp}_{dlq_msg.message_id[-8:]}.json"
        filepath = self.archive_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                f.write(dlq_msg.to_json())
            
            self.stats.messages_archived += 1
            logger.info("Archived failed message to: %s", filepath)
        except Exception as e:
            logger.error("Failed to archive message: %s", e)
            self.stats.errors.append(str(e))
    
    def _handle_permanent_failure(self, dlq_msg: DLQMessage):
        """Handle a message that has permanently failed."""
        self.stats.messages_failed_permanently += 1
        
        # Archive the message
        self._archive_message(dlq_msg)
        
        # Call custom handler if provided
        if self.failure_handler:
            try:
                self.failure_handler(dlq_msg)
            except Exception as e:
                logger.error("Custom failure handler error: %s", e)
    
    def process_message(self, msg) -> bool:
        """
        Process a single DLQ message.
        
        Returns:
            True if message was successfully handled, False otherwise
        """
        try:
            dlq_msg = self._parse_dlq_message(msg)
            self.stats.messages_processed += 1
            
            logger.info(
                "Processing DLQ message: %s (attempt %d, reason: %s)",
                dlq_msg.message_id, dlq_msg.failure_count, dlq_msg.failure_reason
            )
            
            if self._should_retry(dlq_msg):
                if self._retry_message(dlq_msg):
                    return True
                else:
                    # Retry failed, update failure count and try again later
                    logger.warning("Retry attempt failed for message: %s", dlq_msg.message_id)
            
            # Max retries reached or no retry handler
            self._handle_permanent_failure(dlq_msg)
            return True
            
        except Exception as e:
            logger.error("Error processing DLQ message: %s", e)
            self.stats.errors.append(str(e))
            return False
    
    def process_batch(self, max_messages: int = 100, timeout_ms: int = 5000) -> int:
        """
        Process a batch of DLQ messages.
        
        Args:
            max_messages: Maximum number of messages to process
            timeout_ms: Timeout for receiving messages
        
        Returns:
            Number of messages processed
        """
        if not self.consumer:
            self.connect()
        
        processed = 0
        
        for _ in range(max_messages):
            try:
                msg = self.consumer.receive(timeout_millis=timeout_ms)
                
                if self.process_message(msg):
                    self.consumer.acknowledge(msg)
                else:
                    self.consumer.negative_acknowledge(msg)
                
                processed += 1
                
            except Exception as e:
                if "timeout" not in str(e).lower():
                    logger.error("Error receiving message: %s", e)
                break
        
        return processed
    
    def start(self, poll_interval_ms: int = 1000):
        """Start continuous processing of DLQ messages."""
        if not self.consumer:
            self.connect()
        
        self._running = True
        logger.info("Starting DLQ handler...")
        
        while self._running:
            try:
                msg = self.consumer.receive(timeout_millis=poll_interval_ms)
                
                if self.process_message(msg):
                    self.consumer.acknowledge(msg)
                else:
                    self.consumer.negative_acknowledge(msg)
                    
            except Exception as e:
                if "timeout" not in str(e).lower():
                    logger.error("Error in DLQ processing loop: %s", e)
    
    def stop(self):
        """Stop DLQ processing."""
        self._running = False
        logger.info("Stopping DLQ handler...")
    
    def close(self):
        """Close connections and clean up."""
        self.stop()
        
        if self.consumer:
            self.consumer.close()
        if self.client:
            self.client.close()
        
        logger.info("DLQ handler closed")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get DLQ processing statistics."""
        return self.stats.to_dict()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


class MockDLQHandler:
    """Mock DLQ handler for testing."""
    
    def __init__(self, **kwargs):
        self.messages: List[DLQMessage] = []
        self.stats = DLQStats()
        self._running = False
    
    def connect(self):
        pass
    
    def process_message(self, msg) -> bool:
        self.stats.messages_processed += 1
        return True
    
    def process_batch(self, max_messages: int = 100, timeout_ms: int = 5000) -> int:
        return 0
    
    def start(self, poll_interval_ms: int = 1000):
        self._running = True
    
    def stop(self):
        self._running = False
    
    def close(self):
        self.stop()
    
    def get_stats(self) -> Dict[str, Any]:
        return self.stats.to_dict()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


def get_dlq_handler(mock: bool = False, **kwargs):
    """Factory function to get appropriate DLQ handler."""
    if mock or not PULSAR_AVAILABLE:
        return MockDLQHandler(**kwargs)
    return DLQHandler(**kwargs)


__all__ = [
    'DLQMessage',
    'DLQStats',
    'DLQHandler',
    'MockDLQHandler',
    'get_dlq_handler',
]
