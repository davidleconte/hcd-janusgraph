"""
Event Generators Package
========================

Event generators for banking compliance use cases including transactions,
communications, trades, travel, and documents.

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

from .transaction_generator import TransactionGenerator
from .communication_generator import CommunicationGenerator
from .trade_generator import TradeGenerator
from .travel_generator import TravelGenerator, TravelEvent
from .document_generator import DocumentGenerator, Document

__all__ = [
    'TransactionGenerator',
    'CommunicationGenerator',
    'TradeGenerator',
    'TravelGenerator',
    'TravelEvent',
    'DocumentGenerator',
    'Document'
]

