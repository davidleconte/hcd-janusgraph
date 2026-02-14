"""
Event Generators Package
========================

Event generators for banking compliance use cases including transactions,
communications, trades, travel, and documents.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

from .communication_generator import CommunicationGenerator
from .document_generator import Document, DocumentGenerator
from .trade_generator import TradeGenerator
from .transaction_generator import TransactionGenerator
from .travel_generator import TravelEvent, TravelGenerator

__all__ = [
    "TransactionGenerator",
    "CommunicationGenerator",
    "TradeGenerator",
    "TravelGenerator",
    "TravelEvent",
    "DocumentGenerator",
    "Document",
]
