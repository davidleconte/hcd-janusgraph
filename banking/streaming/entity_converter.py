"""
Entity to Event Converter
=========================

Utilities to convert generated entities (Person, Account, Transaction, etc.)
into EntityEvent objects for Pulsar publishing.

Created: 2026-02-06
Week 2: Event Schema & Producers
"""

from typing import Dict, Any, Optional, Union
from datetime import datetime

from .events import EntityEvent


def entity_to_dict(entity: Any) -> Dict[str, Any]:
    """
    Convert a Pydantic model or dataclass to dictionary.
    
    Args:
        entity: Entity object (Person, Account, Transaction, etc.)
    
    Returns:
        Dictionary representation of the entity
    """
    # Pydantic V2+ - use model_dump() directly (project requires pydantic>=2.0.0)
    if hasattr(entity, 'model_dump'):
        return entity.model_dump()
    elif hasattr(entity, '__dict__'):
        return {k: v for k, v in entity.__dict__.items() if not k.startswith('_')}
    else:
        raise ValueError(f"Cannot convert entity of type {type(entity)} to dict")


def get_entity_id(entity: Any) -> str:
    """
    Extract the primary ID from an entity.
    
    Args:
        entity: Entity object
    
    Returns:
        Entity ID as string
    """
    # Try common ID field names
    for field in ['id', 'entity_id', 'person_id', 'account_id', 'transaction_id', 
                  'company_id', 'communication_id', 'trade_id', 'travel_id', 'document_id']:
        if hasattr(entity, field):
            val = getattr(entity, field)
            if val is not None:
                return str(val)
    
    raise ValueError(f"Cannot find ID field on entity of type {type(entity)}")


def get_entity_type(entity: Any) -> str:
    """
    Determine the entity type from an entity object.
    
    Args:
        entity: Entity object
    
    Returns:
        Entity type string (person, account, transaction, etc.)
    """
    type_name = type(entity).__name__.lower()
    
    # Map class names to entity types
    type_mapping = {
        'person': 'person',
        'account': 'account',
        'transaction': 'transaction',
        'company': 'company',
        'communication': 'communication',
        'trade': 'trade',
        'travel': 'travel',
        'document': 'document',
    }
    
    for key, value in type_mapping.items():
        if key in type_name:
            return value
    
    return type_name


def get_text_for_embedding(entity: Any, entity_type: str) -> Optional[str]:
    """
    Extract text suitable for embedding generation.
    
    Args:
        entity: Entity object
        entity_type: Type of entity
    
    Returns:
        Text for embedding or None
    """
    if entity_type == 'person':
        parts = []
        for field in ['first_name', 'middle_name', 'last_name', 'full_name', 'name']:
            if hasattr(entity, field):
                val = getattr(entity, field)
                if val:
                    parts.append(str(val))
        return ' '.join(parts) if parts else None
    
    elif entity_type == 'company':
        for field in ['name', 'company_name', 'legal_name']:
            if hasattr(entity, field):
                val = getattr(entity, field)
                if val:
                    return str(val)
        return None
    
    elif entity_type == 'communication':
        for field in ['content', 'message', 'body', 'subject']:
            if hasattr(entity, field):
                val = getattr(entity, field)
                if val:
                    return str(val)[:1000]  # Limit length
        return None
    
    elif entity_type == 'document':
        for field in ['content', 'text', 'body', 'description']:
            if hasattr(entity, field):
                val = getattr(entity, field)
                if val:
                    return str(val)[:1000]
        return None
    
    # Transactions, accounts, trades, travels don't typically need embeddings
    return None


def convert_entity_to_event(
    entity: Any,
    event_type: str = 'create',
    source: str = None,
    version: int = 1,
    metadata: Optional[Dict[str, Any]] = None
) -> EntityEvent:
    """
    Convert a generated entity to an EntityEvent for Pulsar publishing.
    
    Args:
        entity: Entity object (Person, Account, Transaction, etc.)
        event_type: Operation type ('create', 'update', 'delete')
        source: Event source identifier
        version: Version number for optimistic concurrency
        metadata: Additional metadata
    
    Returns:
        EntityEvent ready for publishing
    
    Example:
        >>> person = person_generator.generate()
        >>> event = convert_entity_to_event(person, source="PersonGenerator")
        >>> producer.send(event)
    """
    entity_id = get_entity_id(entity)
    entity_type = get_entity_type(entity)
    payload = entity_to_dict(entity)
    text_for_embedding = get_text_for_embedding(entity, entity_type)
    
    # Determine source from entity type if not provided
    if source is None:
        source = f"{entity_type.title()}Generator"
    
    return EntityEvent(
        entity_id=entity_id,
        event_type=event_type,
        entity_type=entity_type,
        payload=payload,
        text_for_embedding=text_for_embedding,
        source=source,
        version=version,
        metadata=metadata
    )


def convert_entities_to_events(
    entities: list,
    event_type: str = 'create',
    source: str = None,
    metadata: Optional[Dict[str, Any]] = None
) -> list:
    """
    Convert a list of entities to EntityEvents.
    
    Args:
        entities: List of entity objects
        event_type: Operation type for all events
        source: Event source identifier
        metadata: Additional metadata for all events
    
    Returns:
        List of EntityEvent objects
    """
    return [
        convert_entity_to_event(entity, event_type, source, metadata=metadata)
        for entity in entities
    ]


__all__ = [
    'entity_to_dict',
    'get_entity_id',
    'get_entity_type',
    'get_text_for_embedding',
    'convert_entity_to_event',
    'convert_entities_to_events',
]
