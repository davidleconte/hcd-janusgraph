"""
Base Generator Class
====================

Abstract base class for all entity generators providing common functionality
for configuration, seed management, batch generation, and error handling.

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

import random
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime, timezone

from faker import Faker

# Type variable for generated entity type
T = TypeVar('T')


class BaseGenerator(ABC, Generic[T]):
    """
    Abstract base class for all entity generators.
    
    Provides common functionality:
    - Configuration management
    - Seed management for reproducibility
    - Batch generation
    - Progress tracking
    - Error handling
    - Logging
    """
    
    def __init__(
        self,
        seed: Optional[int] = None,
        locale: str = "en_US",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the base generator.
        
        Args:
            seed: Random seed for reproducibility
            locale: Faker locale for data generation
            config: Additional configuration parameters
        
        Note:
            Faker.seed() is a global operation that affects all Faker instances
            in the same process. If multiple generators with different seeds are
            created in the same process, they may interfere with each other.
            For true isolation, use separate processes or accept that seed
            reproducibility is best-effort within a single process.
        """
        self.seed = seed
        self.locale = locale
        self.config = config or {}
        
        # Initialize Faker with seed
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)
        self.faker = Faker(locale)
        if seed is not None:
            self.faker.seed_instance(seed)
        
        # Setup logging
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Statistics
        self.generated_count = 0
        self.error_count = 0
        self.start_time: Optional[datetime] = None
        
    @abstractmethod
    def generate(self) -> T:
        """
        Generate a single entity.
        
        Returns:
            Generated entity
        """
    
    def generate_batch(self, count: int, show_progress: bool = False) -> List[T]:
        """
        Generate a batch of entities.
        
        Args:
            count: Number of entities to generate
            show_progress: Whether to show progress
            
        Returns:
            List of generated entities
        """
        self.start_time = datetime.now(timezone.utc)
        entities = []
        
        for i in range(count):
            try:
                entity = self.generate()
                entities.append(entity)
                self.generated_count += 1
                
                if show_progress and (i + 1) % 100 == 0:
                    self.logger.info("Generated %d/%d entities", i + 1, count)
                    
            except Exception as e:
                self.error_count += 1
                self.logger.error("Error generating entity %d: %s", i + 1, e)
                if self.config.get('raise_on_error', False):
                    raise
        
        return entities
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get generation statistics.
        
        Returns:
            Dictionary of statistics
        """
        elapsed_time = None
        rate = None
        
        if self.start_time:
            elapsed_time = (datetime.now(timezone.utc) - self.start_time).total_seconds()
            if elapsed_time > 0:
                rate = self.generated_count / elapsed_time
        
        return {
            'generated_count': self.generated_count,
            'error_count': self.error_count,
            'elapsed_time_seconds': elapsed_time,
            'generation_rate_per_second': rate,
            'seed': self.seed,
            'locale': self.locale
        }
    
    def reset_statistics(self):
        """Reset generation statistics."""
        self.generated_count = 0
        self.error_count = 0
        self.start_time = None
    
    def set_seed(self, seed: int):
        """
        Set a new random seed.
        
        Args:
            seed: New random seed
        """
        self.seed = seed
        Faker.seed(seed)
        random.seed(seed)
    
    def update_config(self, config: Dict[str, Any]):
        """
        Update configuration.
        
        Args:
            config: Configuration updates
        """
        self.config.update(config)


__all__ = ['BaseGenerator']

