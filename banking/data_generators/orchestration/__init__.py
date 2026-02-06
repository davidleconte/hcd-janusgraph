"""
Orchestration Package
=====================

Central coordination and batch generation utilities for synthetic data generation.

Components:
- MasterOrchestrator: Coordinate all generators
- GenerationConfig: Configuration management
- GenerationStats: Statistics tracking

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
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

