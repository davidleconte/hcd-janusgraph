"""
EntityEvent - Unified Event Schema for Banking Streaming

This module defines the event schema used for publishing entity events
to Apache Pulsar. The same event is consumed by both:
- Leg 1: Graph Consumer (JanusGraph/HCD)
- Leg 2: Vector Consumer (OpenSearch)

Created: 2026-02-04
Week 2: Event Schema & Producers
"""

import hashlib
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from itertools import count
from typing import Any, Dict, Iterator, List, Optional

DETERMINISTIC_IDS_ENV = "DEMO_STREAMING_DETERMINISTIC_IDS"
_TRUTHY_VALUES = {"1", "true", "yes", "on"}
_EVENT_ID_COUNTER = count(1)
_BATCH_ID_COUNTER = count(1)


def _deterministic_ids_enabled() -> bool:
    """Return True when deterministic streaming IDs are explicitly enabled."""
    return os.getenv(DETERMINISTIC_IDS_ENV, "0").strip().lower() in _TRUTHY_VALUES


def _canonical_json(value: Any) -> str:
    """Serialize arbitrary values with deterministic key ordering."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _generate_event_id(
    entity_id: str,
    event_type: str,
    entity_type: str,
    payload: Dict[str, Any],
    version: int,
    source: Optional[str],
    metadata: Optional[Dict[str, Any]],
) -> str:
    """Generate an event ID, deterministic only when explicitly requested."""
    if not _deterministic_ids_enabled():
        return str(uuid.uuid4())

    ordinal = next(_EVENT_ID_COUNTER)
    seed = "|".join(
        [
            entity_id,
            event_type,
            entity_type,
            str(version),
            str(source or ""),
            str(ordinal),
            _canonical_json(payload),
            _canonical_json(metadata or {}),
        ]
    )
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return f"evt-{digest[:32]}"


def _generate_batch_id(events: List["EntityEvent"]) -> str:
    """Generate a batch ID, deterministic only when explicitly requested."""
    if not _deterministic_ids_enabled():
        return str(uuid.uuid4())

    ordinal = next(_BATCH_ID_COUNTER)
    event_ids = ",".join(event.event_id for event in events)
    digest = hashlib.sha256(f"{ordinal}|{event_ids}".encode("utf-8")).hexdigest()
    return f"batch-{digest[:24]}"


@dataclass
class EntityEvent:
    """
    Unified event schema for all entity operations.
    Same event goes to both JanusGraph and OpenSearch consumers.

    Attributes:
        entity_id: UUID that links the entity across all systems (Pulsar, JanusGraph, OpenSearch)
        event_id: Unique event identifier for deduplication (used as Pulsar sequence_id)
        event_type: Operation type - 'create', 'update', 'delete'
        entity_type: Entity classification - 'person', 'account', 'transaction', 'company', 'communication'
        payload: Full entity data as dictionary
        text_for_embedding: Text to generate embedding for (used by Vector Consumer)
        timestamp: Event creation timestamp
        version: Version number for optimistic concurrency control
        source: Origin of the event - 'generator', 'notebook', 'api', 'migration'
        metadata: Additional metadata (optional)

    Example:
        >>> event = EntityEvent(
        ...     entity_id="550e8400-e29b-41d4-a716-446655440000",
        ...     event_type="create",
        ...     entity_type="person",
        ...     payload={"name": "John Smith", "email": "john@example.com"},
        ...     text_for_embedding="John Smith",
        ...     source="PersonGenerator"
        ... )
        >>> msg = event.to_pulsar_message()
    """

    # Core identifiers - SAME everywhere
    entity_id: str
    event_type: str  # 'create', 'update', 'delete'
    entity_type: str  # 'person', 'account', 'transaction', 'company', 'communication'

    # Entity data
    payload: Dict[str, Any]

    # Embedding data (for Leg 2 - OpenSearch)
    text_for_embedding: Optional[str] = None

    # Metadata
    event_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    # Validation
    VALID_EVENT_TYPES = {"create", "update", "delete"}
    VALID_ENTITY_TYPES = {
        "person",
        "account",
        "transaction",
        "company",
        "communication",
        "trade",
        "travel",
        "document",
    }

    def __post_init__(self) -> None:
        """Validate event after initialization."""
        if self.event_type not in self.VALID_EVENT_TYPES:
            raise ValueError(
                f"Invalid event_type: {self.event_type}. Must be one of {self.VALID_EVENT_TYPES}"
            )

        if self.entity_type not in self.VALID_ENTITY_TYPES:
            raise ValueError(
                f"Invalid entity_type: {self.entity_type}. Must be one of {self.VALID_ENTITY_TYPES}"
            )

        if not self.entity_id:
            raise ValueError("entity_id is required")

        if not isinstance(self.payload, dict):
            raise ValueError("payload must be a dictionary")

        if not self.event_id:
            self.event_id = _generate_event_id(
                entity_id=self.entity_id,
                event_type=self.event_type,
                entity_type=self.entity_type,
                payload=self.payload,
                version=self.version,
                source=self.source,
                metadata=self.metadata,
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "entity_id": self.entity_id,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "entity_type": self.entity_type,
            "payload": self.payload,
            "text_for_embedding": self.text_for_embedding,
            "timestamp": (
                self.timestamp.isoformat()
                if isinstance(self.timestamp, datetime)
                else self.timestamp
            ),
            "version": self.version,
            "source": self.source,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Serialize event to JSON string."""
        from datetime import date
        from decimal import Decimal

        def json_serializer(obj: Any) -> Any:
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, date):
                return obj.isoformat()
            if isinstance(obj, Decimal):
                return float(obj)
            # Pydantic V2+ - use model_dump() directly
            if hasattr(obj, "model_dump"):
                return obj.model_dump()
            if hasattr(obj, "__dict__"):
                return obj.__dict__
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

        return json.dumps(self.to_dict(), default=json_serializer)

    @staticmethod
    def _deterministic_sequence_id(event_id: str) -> int:
        """Create a deterministic positive sequence id from an event id."""
        digest = hashlib.sha256(event_id.encode("utf-8")).digest()[:8]
        return int.from_bytes(digest, byteorder="big", signed=False)

    def to_bytes(self) -> bytes:
        """Serialize event to bytes for Pulsar message content."""
        return self.to_json().encode("utf-8")

    def to_pulsar_message(self) -> Dict[str, Any]:
        """
        Convert to Pulsar message format with partition key and sequence ID.

        Returns:
            Dictionary with:
                - partition_key: entity_id (ensures ordering per entity)
                - sequence_id: deterministic sha256 hash of event_id
                - content: serialized event payload
        """
        return {
            "partition_key": self.entity_id,
            "sequence_id": self._deterministic_sequence_id(self.event_id) % (2**63),
            "content": self.to_bytes(),
        }

    def get_topic(self) -> str:
        """
        Get the Pulsar topic for this event based on entity_type.

        Returns:
            Topic name in format: persistent://public/banking/{entity_type}s-events
        """
        if self.entity_type == "company":
            topic_suffix = "companies-events"
        else:
            topic_suffix = f"{self.entity_type}s-events"
        return f"persistent://public/banking/{topic_suffix}"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntityEvent":
        """Create EntityEvent from dictionary."""
        # Handle timestamp conversion
        timestamp: Any = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        elif timestamp is None:
            timestamp = datetime.now(timezone.utc)

        return cls(
            entity_id=data["entity_id"],
            event_id=data.get("event_id", ""),
            event_type=data["event_type"],
            entity_type=data["entity_type"],
            payload=data["payload"],
            text_for_embedding=data.get("text_for_embedding"),
            timestamp=timestamp,
            version=data.get("version", 1),
            source=data.get("source"),
            metadata=data.get("metadata"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "EntityEvent":
        """Create EntityEvent from JSON string."""
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def from_bytes(cls, data: bytes) -> "EntityEvent":
        """Create EntityEvent from bytes."""
        return cls.from_json(data.decode("utf-8"))


@dataclass
class EntityEventBatch:
    """
    Batch of EntityEvents for bulk processing.

    Attributes:
        events: List of EntityEvent objects
        batch_id: Unique identifier for this batch
        created_at: Batch creation timestamp
    """

    events: List[EntityEvent]
    batch_id: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Populate batch defaults after dataclass initialization."""
        if not self.batch_id:
            self.batch_id = _generate_batch_id(self.events)

    def __len__(self) -> int:
        return len(self.events)

    def __iter__(self) -> Iterator[EntityEvent]:
        return iter(self.events)

    def by_entity_type(self) -> Dict[str, List[EntityEvent]]:
        """Group events by entity type."""
        grouped: Dict[str, List[EntityEvent]] = {}
        for event in self.events:
            if event.entity_type not in grouped:
                grouped[event.entity_type] = []
            grouped[event.entity_type].append(event)
        return grouped

    def by_topic(self) -> Dict[str, List[EntityEvent]]:
        """Group events by Pulsar topic."""
        grouped: Dict[str, List[EntityEvent]] = {}
        for event in self.events:
            topic = event.get_topic()
            if topic not in grouped:
                grouped[topic] = []
            grouped[topic].append(event)
        return grouped


# Convenience factory functions
def create_person_event(
    person_id: str,
    name: str,
    payload: Dict[str, Any],
    event_type: str = "create",
    source: Optional[str] = None,
) -> EntityEvent:
    """Create a person entity event."""
    return EntityEvent(
        entity_id=person_id,
        event_type=event_type,
        entity_type="person",
        payload=payload,
        text_for_embedding=name,  # Name is used for vector search
        source=source,
    )


def create_account_event(
    account_id: str,
    payload: Dict[str, Any],
    event_type: str = "create",
    source: Optional[str] = None,
) -> EntityEvent:
    """Create an account entity event."""
    return EntityEvent(
        entity_id=account_id,
        event_type=event_type,
        entity_type="account",
        payload=payload,
        text_for_embedding=None,  # Accounts typically don't need embeddings
        source=source,
    )


def create_transaction_event(
    transaction_id: str,
    payload: Dict[str, Any],
    event_type: str = "create",
    source: Optional[str] = None,
) -> EntityEvent:
    """Create a transaction entity event."""
    return EntityEvent(
        entity_id=transaction_id,
        event_type=event_type,
        entity_type="transaction",
        payload=payload,
        text_for_embedding=None,  # Transactions typically don't need embeddings
        source=source,
    )


def create_company_event(
    company_id: str,
    name: str,
    payload: Dict[str, Any],
    event_type: str = "create",
    source: Optional[str] = None,
) -> EntityEvent:
    """Create a company entity event."""
    return EntityEvent(
        entity_id=company_id,
        event_type=event_type,
        entity_type="company",
        payload=payload,
        text_for_embedding=name,  # Company name for vector search
        source=source,
    )
