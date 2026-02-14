"""
Orchestration Package
=====================

Central coordination and batch generation utilities for synthetic data generation.

Components:
- MasterOrchestrator: Coordinate all generators
- GenerationConfig: Configuration management
- GenerationStats: Statistics tracking

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

from .master_orchestrator import GenerationConfig, GenerationStats, MasterOrchestrator

__all__ = [
    "MasterOrchestrator",
    "GenerationConfig",
    "GenerationStats",
]
