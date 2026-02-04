"""
JanusGraph Data Loaders
=======================

Loaders for populating JanusGraph with synthetic data.
"""

from .janusgraph_loader import JanusGraphLoader, generate_and_load

__all__ = ["JanusGraphLoader", "generate_and_load"]
