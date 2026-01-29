"""
Orchestration Package
=====================

Central coordination and batch generation utilities for synthetic data generation.

Components:
- MasterOrchestrator: Coordinate all generators
- GenerationConfig: Configuration management
- GenerationStats: Statistics tracking

Author: IBM Bob
Date: 2026-01-28
"""

from .master_orchestrator import (
    MasterOrchestrator,
    GenerationConfig,
    GenerationStats
)

__all__ = [
    'MasterOrchestrator',
    'GenerationConfig',
    'GenerationStats',
]

