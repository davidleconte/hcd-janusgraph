"""
Banking Streaming Module - Event-Sourced Architecture

This module provides Pulsar-based event streaming for data ingestion
into JanusGraph and OpenSearch with guaranteed consistency.

Components:
    - events: EntityEvent dataclass and event schema
    - producer: EntityProducer for publishing events
    - graph_consumer: Leg 1 consumer for JanusGraph
    - vector_consumer: Leg 2 consumer for OpenSearch
    - dlq_handler: Dead Letter Queue handler

Topics:
    - persistent://public/banking/persons-events
    - persistent://public/banking/accounts-events
    - persistent://public/banking/transactions-events
    - persistent://public/banking/companies-events
    - persistent://public/banking/communications-events
    - persistent://public/banking/dlq-events

Created: 2026-02-04
"""

from .events import EntityEvent, EntityEventBatch, create_person_event, create_account_event, create_transaction_event, create_company_event
from .producer import EntityProducer, MockEntityProducer, get_producer
from .graph_consumer import GraphConsumer
from .vector_consumer import VectorConsumer
from .entity_converter import (
    convert_entity_to_event,
    convert_entities_to_events,
    entity_to_dict,
    get_entity_id,
    get_entity_type,
    get_text_for_embedding,
)
from .streaming_orchestrator import StreamingOrchestrator, StreamingConfig, StreamingStats
from .dlq_handler import DLQHandler, DLQMessage, DLQStats, MockDLQHandler, get_dlq_handler
from .metrics import StreamingMetrics, streaming_metrics, timed_publish, timed_consume, get_metrics_output

__all__ = [
    # Events
    'EntityEvent',
    'EntityEventBatch',
    'create_person_event',
    'create_account_event',
    'create_transaction_event',
    'create_company_event',
    # Producer
    'EntityProducer',
    'MockEntityProducer',
    'get_producer',
    # Consumers
    'GraphConsumer',
    'VectorConsumer',
    # Entity Converter
    'convert_entity_to_event',
    'convert_entities_to_events',
    'entity_to_dict',
    'get_entity_id',
    'get_entity_type',
    'get_text_for_embedding',
    # Streaming Orchestrator
    'StreamingOrchestrator',
    'StreamingConfig',
    'StreamingStats',
    # DLQ Handler
    'DLQHandler',
    'DLQMessage',
    'DLQStats',
    'MockDLQHandler',
    'get_dlq_handler',
    # Metrics
    'StreamingMetrics',
    'streaming_metrics',
    'timed_publish',
    'timed_consume',
    'get_metrics_output',
]
