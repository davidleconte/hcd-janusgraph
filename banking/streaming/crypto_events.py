"""
Crypto Event Helpers for Pulsar Streaming
==========================================

Helper functions to create EntityEvent instances for cryptocurrency entities.
Integrates with the existing EntityEvent schema for unified streaming.

Author: AI Assistant
Date: 2026-04-10
Phase: 7.2 - Crypto Streaming Integration
"""

from datetime import datetime
from typing import Any, Dict, Optional

from banking.streaming.events import EntityEvent


def create_wallet_event(
    wallet_id: str,
    wallet_data: Dict[str, Any],
    event_type: str = "create",
    source: str = "generator",
    metadata: Optional[Dict[str, Any]] = None,
) -> EntityEvent:
    """
    Create an EntityEvent for a cryptocurrency wallet.
    
    Args:
        wallet_id: Unique wallet identifier
        wallet_data: Complete wallet data dictionary
        event_type: Event type ('create', 'update', 'delete')
        source: Event source ('generator', 'notebook', 'api')
        metadata: Additional metadata
    
    Returns:
        EntityEvent ready for publishing to Pulsar
    
    Example:
        >>> wallet = {
        ...     "wallet_id": "wallet-ABC123",
        ...     "address": "0x1234...",
        ...     "currency": "BTC",
        ...     "balance": 1.5
        ... }
        >>> event = create_wallet_event("wallet-ABC123", wallet)
        >>> event.entity_type
        'crypto_wallet'
    """
    # Create text for embedding (for vector search)
    text_parts = [
        f"Cryptocurrency wallet {wallet_id}",
        f"Currency: {wallet_data.get('currency', 'unknown')}",
        f"Type: {wallet_data.get('wallet_type', 'unknown')}",
        f"Balance: {wallet_data.get('balance', 0)}",
    ]
    
    # Add risk indicators
    if wallet_data.get("is_mixer"):
        text_parts.append("MIXER WALLET - High Risk")
    if wallet_data.get("is_sanctioned"):
        text_parts.append("SANCTIONED WALLET - Blocked")
    
    text_for_embedding = " | ".join(text_parts)
    
    # Merge metadata
    event_metadata = {
        "currency": wallet_data.get("currency"),
        "wallet_type": wallet_data.get("wallet_type"),
        "is_mixer": wallet_data.get("is_mixer", False),
        "is_sanctioned": wallet_data.get("is_sanctioned", False),
        "risk_score": wallet_data.get("risk_score", 0.0),
    }
    if metadata:
        event_metadata.update(metadata)
    
    return EntityEvent(
        entity_id=wallet_id,
        event_type=event_type,
        entity_type="crypto_wallet",
        payload=wallet_data,
        text_for_embedding=text_for_embedding,
        source=source,
        metadata=event_metadata,
    )


def create_crypto_transaction_event(
    transaction_id: str,
    transaction_data: Dict[str, Any],
    event_type: str = "create",
    source: str = "generator",
    metadata: Optional[Dict[str, Any]] = None,
) -> EntityEvent:
    """
    Create an EntityEvent for a cryptocurrency transaction.
    
    Args:
        transaction_id: Unique transaction identifier
        transaction_data: Complete transaction data dictionary
        event_type: Event type ('create', 'update', 'delete')
        source: Event source ('generator', 'notebook', 'api')
        metadata: Additional metadata
    
    Returns:
        EntityEvent ready for publishing to Pulsar
    
    Example:
        >>> tx = {
        ...     "transaction_id": "ctx-XYZ789",
        ...     "from_wallet": "wallet-ABC123",
        ...     "to_wallet": "wallet-DEF456",
        ...     "amount": 0.5,
        ...     "currency": "BTC"
        ... }
        >>> event = create_crypto_transaction_event("ctx-XYZ789", tx)
        >>> event.entity_type
        'crypto_transaction'
    """
    # Create text for embedding
    text_parts = [
        f"Cryptocurrency transaction {transaction_id}",
        f"Currency: {transaction_data.get('currency', 'unknown')}",
        f"Type: {transaction_data.get('transaction_type', 'unknown')}",
        f"Amount: {transaction_data.get('amount', 0)}",
        f"From: {transaction_data.get('from_wallet', 'unknown')}",
        f"To: {transaction_data.get('to_wallet', 'unknown')}",
    ]
    
    # Add risk indicators
    if transaction_data.get("is_suspicious"):
        text_parts.append("SUSPICIOUS TRANSACTION - Requires Review")
    if transaction_data.get("involves_mixer"):
        text_parts.append("MIXER INVOLVED - High Risk")
    
    text_for_embedding = " | ".join(text_parts)
    
    # Merge metadata
    event_metadata = {
        "currency": transaction_data.get("currency"),
        "transaction_type": transaction_data.get("transaction_type"),
        "amount": transaction_data.get("amount"),
        "is_suspicious": transaction_data.get("is_suspicious", False),
        "involves_mixer": transaction_data.get("involves_mixer", False),
        "from_wallet": transaction_data.get("from_wallet"),
        "to_wallet": transaction_data.get("to_wallet"),
    }
    if metadata:
        event_metadata.update(metadata)
    
    return EntityEvent(
        entity_id=transaction_id,
        event_type=event_type,
        entity_type="crypto_transaction",
        payload=transaction_data,
        text_for_embedding=text_for_embedding,
        source=source,
        metadata=event_metadata,
    )


def create_mixer_detection_event(
    wallet_id: str,
    detection_result: Dict[str, Any],
    event_type: str = "create",
    source: str = "detector",
    metadata: Optional[Dict[str, Any]] = None,
) -> EntityEvent:
    """
    Create an EntityEvent for a mixer detection result.
    
    Args:
        wallet_id: Wallet being analyzed
        detection_result: Mixer detection result dictionary
        event_type: Event type ('create', 'update', 'delete')
        source: Event source ('detector', 'notebook', 'api')
        metadata: Additional metadata
    
    Returns:
        EntityEvent ready for publishing to Pulsar
    
    Example:
        >>> result = {
        ...     "wallet_id": "wallet-ABC123",
        ...     "is_mixer": False,
        ...     "has_mixer_interaction": True,
        ...     "risk_score": 0.7,
        ...     "recommendation": "review"
        ... }
        >>> event = create_mixer_detection_event("wallet-ABC123", result)
        >>> event.entity_type
        'mixer_detection'
    """
    # Create text for embedding
    risk_score = detection_result.get("risk_score", 0.0)
    recommendation = detection_result.get("recommendation", "unknown")
    
    text_parts = [
        f"Mixer detection for wallet {wallet_id}",
        f"Risk Score: {risk_score:.2f}",
        f"Recommendation: {recommendation.upper()}",
    ]
    
    if detection_result.get("is_mixer"):
        text_parts.append("IDENTIFIED AS MIXER")
    elif detection_result.get("has_mixer_interaction"):
        text_parts.append("HAS MIXER INTERACTION")
        if detection_result.get("closest_mixer_distance"):
            text_parts.append(f"Distance: {detection_result['closest_mixer_distance']} hops")
    
    text_for_embedding = " | ".join(text_parts)
    
    # Merge metadata
    event_metadata = {
        "risk_score": risk_score,
        "recommendation": recommendation,
        "is_mixer": detection_result.get("is_mixer", False),
        "has_mixer_interaction": detection_result.get("has_mixer_interaction", False),
        "detection_timestamp": datetime.now().isoformat(),
    }
    if metadata:
        event_metadata.update(metadata)
    
    return EntityEvent(
        entity_id=f"detection-{wallet_id}",
        event_type=event_type,
        entity_type="mixer_detection",
        payload=detection_result,
        text_for_embedding=text_for_embedding,
        source=source,
        metadata=event_metadata,
    )


def create_sanctions_screening_event(
    wallet_id: str,
    screening_result: Dict[str, Any],
    event_type: str = "create",
    source: str = "screener",
    metadata: Optional[Dict[str, Any]] = None,
) -> EntityEvent:
    """
    Create an EntityEvent for a sanctions screening result.
    
    Args:
        wallet_id: Wallet being screened
        screening_result: Sanctions screening result dictionary
        event_type: Event type ('create', 'update', 'delete')
        source: Event source ('screener', 'notebook', 'api')
        metadata: Additional metadata
    
    Returns:
        EntityEvent ready for publishing to Pulsar
    
    Example:
        >>> result = {
        ...     "wallet_id": "wallet-ABC123",
        ...     "is_sanctioned": False,
        ...     "risk_score": 0.6,
        ...     "recommendation": "review",
        ...     "matches": []
        ... }
        >>> event = create_sanctions_screening_event("wallet-ABC123", result)
        >>> event.entity_type
        'sanctions_screening'
    """
    # Create text for embedding
    risk_score = screening_result.get("risk_score", 0.0)
    recommendation = screening_result.get("recommendation", "unknown")
    matches = screening_result.get("matches", [])
    
    text_parts = [
        f"Sanctions screening for wallet {wallet_id}",
        f"Risk Score: {risk_score:.2f}",
        f"Recommendation: {recommendation.upper()}",
    ]
    
    if screening_result.get("is_sanctioned"):
        text_parts.append("SANCTIONED WALLET - BLOCKED")
        text_parts.append(f"Matches: {len(matches)}")
        for match in matches[:3]:  # First 3 matches
            text_parts.append(f"- {match.get('list_name', 'unknown')}: {match.get('match_type', 'unknown')}")
    elif screening_result.get("high_risk_jurisdiction"):
        text_parts.append("HIGH-RISK JURISDICTION")
    
    text_for_embedding = " | ".join(text_parts)
    
    # Merge metadata
    event_metadata = {
        "risk_score": risk_score,
        "recommendation": recommendation,
        "is_sanctioned": screening_result.get("is_sanctioned", False),
        "high_risk_jurisdiction": screening_result.get("high_risk_jurisdiction", False),
        "match_count": len(matches),
        "screening_timestamp": datetime.now().isoformat(),
    }
    if metadata:
        event_metadata.update(metadata)
    
    return EntityEvent(
        entity_id=f"screening-{wallet_id}",
        event_type=event_type,
        entity_type="sanctions_screening",
        payload=screening_result,
        text_for_embedding=text_for_embedding,
        source=source,
        metadata=event_metadata,
    )

# Made with Bob
