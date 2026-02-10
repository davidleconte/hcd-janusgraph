"""
Graph Repository Layer
======================

Centralizes all JanusGraph/Gremlin traversals behind a typed interface,
keeping API routers and business logic free of query details.
"""

from src.python.repository.graph_repository import GraphRepository

__all__ = ["GraphRepository"]
