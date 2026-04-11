"""
Synthetic Identity Pattern Generator
====================================

Injects specific fraud patterns into synthetic identities for testing and validation.

This module provides pattern injection capabilities for:
- Bust-out schemes (rapid credit building → max out → disappear)
- Fraud rings (shared attributes across multiple identities)
- Identity theft patterns (stolen SSN + fake identity)
- Authorized user abuse (piggybacking on legitimate credit)
- Credit muling (using identities to facilitate fraud)

Patterns are deterministic and reproducible for testing purposes.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.3 - Synthetic Identity Fraud Detection
"""

import logging
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from banking.data_generators.core.base_generator import BaseGenerator
from banking.data_generators.utils.deterministic import seeded_uuid_hex
from banking.identity.synthetic_identity_generator import (
    CreditTier,
    IdentityType,
    SyntheticIdentityGenerator,
)

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of fraud patterns that can be injected."""
    BUST_OUT = "bust_out"
    FRAUD_RING = "fraud_ring"
    IDENTITY_THEFT = "identity_theft"
    AUTHORIZED_USER_ABUSE = "authorized_user_abuse"
    CREDIT_MULE = "credit_mule"


@dataclass
class PatternConfig:
    """Configuration for pattern injection."""
    pattern_type: PatternType
    intensity: float = 1.0  # 0.0-1.0, higher = more obvious pattern
    count: int = 1  # Number of identities to inject pattern into
    
    # Pattern-specific parameters
    shared_ssn: Optional[str] = None
    shared_phone: Optional[str] = None
    shared_address: Optional[Dict[str, str]] = None
    ring_size: int = 3  # For fraud rings
    velocity_multiplier: float = 2.0  # For bust-outs
    utilization_target: float = 0.95  # For bust-outs


class SyntheticIdentityPatternGenerator(BaseGenerator):
    """
    Generate synthetic identities with injected fraud patterns.
    
    This generator extends SyntheticIdentityGenerator to inject specific
    fraud patterns for testing detection algorithms.
    
    Example:
        >>> gen = SyntheticIdentityPatternGenerator(seed=42)
        >>> config = PatternConfig(
        ...     pattern_type=PatternType.BUST_OUT,
        ...     intensity=0.8,
        ...     count=5
        ... )
        >>> identities = gen.generate_with_pattern(config)
        >>> # All 5 identities will exhibit bust-out characteristics
    """
    
    def __init__(self, seed: Optional[int] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize pattern generator.
        
        Args:
            seed: Random seed for deterministic generation
            config: Configuration options (passed to SyntheticIdentityGenerator)
        """
        super().__init__(seed=seed)
        self.config = config or {}
        
        # Base generator for creating identities
        self.base_generator = SyntheticIdentityGenerator(seed=seed, config=config)
        
        # Pattern tracking
        self.injected_patterns: List[Dict[str, Any]] = []
        
        logger.info(f"SyntheticIdentityPatternGenerator initialized with seed={seed}")
    
    def generate(self) -> Dict[str, Any]:
        """
        Generate a single identity (delegates to base generator).
        
        Returns:
            Identity dictionary
        """
        return self.base_generator.generate()
    
    def generate_with_pattern(self, pattern_config: PatternConfig) -> List[Dict[str, Any]]:
        """
        Generate identities with specific fraud pattern injected.
        
        Args:
            pattern_config: Pattern configuration
            
        Returns:
            List of identities with pattern injected
        """
        # Generate base identities
        identities = self.base_generator.generate_batch(pattern_config.count)
        
        # Inject pattern based on type
        if pattern_config.pattern_type == PatternType.BUST_OUT:
            identities = self._inject_bust_out_pattern(identities, pattern_config)
        elif pattern_config.pattern_type == PatternType.FRAUD_RING:
            identities = self._inject_fraud_ring_pattern(identities, pattern_config)
        elif pattern_config.pattern_type == PatternType.IDENTITY_THEFT:
            identities = self._inject_identity_theft_pattern(identities, pattern_config)
        elif pattern_config.pattern_type == PatternType.AUTHORIZED_USER_ABUSE:
            identities = self._inject_authorized_user_pattern(identities, pattern_config)
        elif pattern_config.pattern_type == PatternType.CREDIT_MULE:
            identities = self._inject_credit_mule_pattern(identities, pattern_config)
        
        # Track injected patterns
        self.injected_patterns.append({
            "pattern_type": pattern_config.pattern_type.value,
            "count": len(identities),
            "intensity": pattern_config.intensity,
            "identity_ids": [id["identity_id"] for id in identities],
        })
        
        return identities
    
    def _inject_bust_out_pattern(
        self, identities: List[Dict[str, Any]], config: PatternConfig
    ) -> List[Dict[str, Any]]:
        """
        Inject bust-out scheme pattern.
        
        Characteristics:
        - Recent credit file (6-18 months)
        - High credit velocity (rapid limit growth)
        - High utilization (90-100%)
        - Multiple accounts maxed out
        """
        for identity in identities:
            # Make credit file recent
            base_age = int(6 + (12 * (1 - config.intensity)))
            identity["credit_file_age_months"] = base_age
            
            # Increase credit velocity (high limits for short history)
            current_limit = identity["total_credit_limit"]
            velocity_boost = config.velocity_multiplier * config.intensity
            identity["total_credit_limit"] = float(Decimal(str(current_limit)) * Decimal(str(velocity_boost)))
            
            # Max out utilization
            target_util = config.utilization_target * config.intensity
            identity["credit_utilization"] = max(target_util, 0.85)
            
            # Increase number of accounts (rapid account opening)
            if config.intensity > 0.7:
                identity["num_credit_accounts"] = self.faker.random.randint(5, 10)
            
            # Add bust-out marker
            identity["pattern_injected"] = "bust_out"
            identity["pattern_intensity"] = config.intensity
        
        return identities
    
    def _inject_fraud_ring_pattern(
        self, identities: List[Dict[str, Any]], config: PatternConfig
    ) -> List[Dict[str, Any]]:
        """
        Inject fraud ring pattern.
        
        Characteristics:
        - Shared SSN across multiple identities
        - Shared phone numbers
        - Shared addresses
        - Similar credit patterns
        """
        # Generate shared attributes
        shared_ssn = config.shared_ssn or self.faker.ssn()
        shared_phone = config.shared_phone or self.faker.phone_number()
        shared_address = config.shared_address or {
            "street": self.faker.street_address(),
            "city": self.faker.city(),
            "state": self.faker.state_abbr(),
            "zip": self.faker.zipcode(),
        }
        
        # Determine how many identities share each attribute
        ring_size = min(config.ring_size, len(identities))
        ssn_share_count = int(ring_size * config.intensity)
        phone_share_count = int(ring_size * config.intensity * 0.8)
        address_share_count = int(ring_size * config.intensity * 0.6)
        
        # Inject shared attributes
        for i, identity in enumerate(identities):
            shared_attrs = []
            
            if i < ssn_share_count:
                identity["ssn"] = shared_ssn
                shared_attrs.append("ssn")
            
            if i < phone_share_count:
                identity["phone"] = shared_phone
                shared_attrs.append("phone")
            
            if i < address_share_count:
                identity["address"] = shared_address
                shared_attrs.append("address")
            
            identity["shared_attributes"] = shared_attrs
            identity["pattern_injected"] = "fraud_ring"
            identity["pattern_intensity"] = config.intensity
            identity["ring_id"] = f"ring-{seeded_uuid_hex(seed=self.seed if self.seed else 0)[:8]}"
        
        return identities
    
    def _inject_identity_theft_pattern(
        self, identities: List[Dict[str, Any]], config: PatternConfig
    ) -> List[Dict[str, Any]]:
        """
        Inject identity theft pattern.
        
        Characteristics:
        - Real SSN (stolen) + fake name/DOB
        - Recent credit file (theft is recent)
        - Inconsistent credit history
        - Multiple address changes
        """
        # Generate a "stolen" SSN (same for all in this pattern)
        stolen_ssn = config.shared_ssn or self.faker.ssn()
        
        for identity in identities:
            # Use stolen SSN
            identity["ssn"] = stolen_ssn
            
            # Make it Frankenstein type (real SSN + fake identity)
            identity["identity_type"] = IdentityType.FRANKENSTEIN.value
            
            # Recent credit file (theft is recent)
            identity["credit_file_age_months"] = self.faker.random.randint(3, 12)
            
            # Add theft markers
            identity["pattern_injected"] = "identity_theft"
            identity["pattern_intensity"] = config.intensity
            identity["stolen_ssn"] = stolen_ssn
            
            # High intensity = more obvious theft
            if config.intensity > 0.7:
                # Multiple recent address changes
                identity["address_changes_last_year"] = self.faker.random.randint(3, 6)
                # Inconsistent credit behavior
                identity["credit_utilization"] = self.faker.random.uniform(0.7, 1.0)
        
        return identities
    
    def _inject_authorized_user_pattern(
        self, identities: List[Dict[str, Any]], config: PatternConfig
    ) -> List[Dict[str, Any]]:
        """
        Inject authorized user abuse pattern.
        
        Characteristics:
        - Has authorized user history (piggybacking)
        - Rapid credit score improvement
        - Recent credit file but high score
        - Multiple authorized user accounts
        """
        for identity in identities:
            # Enable authorized user history
            identity["has_authorized_user_history"] = True
            
            # Recent file but good credit (piggybacking effect)
            identity["credit_file_age_months"] = self.faker.random.randint(6, 18)
            
            # Boost credit score (piggybacking benefit)
            base_score = identity["credit_score"]
            score_boost = int(100 * config.intensity)
            identity["credit_score"] = min(base_score + score_boost, 850)
            
            # Update credit tier based on new score
            if identity["credit_score"] >= 750:
                identity["credit_tier"] = CreditTier.EXCELLENT.value
            elif identity["credit_score"] >= 700:
                identity["credit_tier"] = CreditTier.GOOD.value
            
            # Increase credit limit (piggybacking benefit)
            current_limit = identity["total_credit_limit"]
            identity["total_credit_limit"] = float(Decimal(str(current_limit)) * Decimal("1.5"))
            
            # Add pattern markers
            identity["pattern_injected"] = "authorized_user_abuse"
            identity["pattern_intensity"] = config.intensity
            identity["authorized_user_accounts"] = self.faker.random.randint(2, 5)
        
        return identities
    
    def _inject_credit_mule_pattern(
        self, identities: List[Dict[str, Any]], config: PatternConfig
    ) -> List[Dict[str, Any]]:
        """
        Inject credit mule pattern.
        
        Characteristics:
        - Used to facilitate fraud for others
        - Rapid account opening and closing
        - High transaction velocity
        - Multiple failed applications
        """
        for identity in identities:
            # Recent credit file (mule is new)
            identity["credit_file_age_months"] = self.faker.random.randint(3, 12)
            
            # Many accounts opened recently
            identity["num_credit_accounts"] = self.faker.random.randint(5, 12)
            identity["accounts_opened_last_6_months"] = self.faker.random.randint(3, 8)
            
            # High utilization (facilitating fraud)
            identity["credit_utilization"] = self.faker.random.uniform(0.7, 0.95)
            
            # Multiple failed applications (trying many lenders)
            identity["failed_applications_last_year"] = self.faker.random.randint(3, 10)
            
            # Add pattern markers
            identity["pattern_injected"] = "credit_mule"
            identity["pattern_intensity"] = config.intensity
            
            # High intensity = more obvious mule behavior
            if config.intensity > 0.7:
                identity["rapid_account_cycling"] = True
                identity["suspicious_transaction_patterns"] = True
        
        return identities
    
    def generate_mixed_batch(
        self, 
        total_count: int,
        pattern_distribution: Dict[PatternType, float],
        base_intensity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Generate batch with mixed fraud patterns.
        
        Args:
            total_count: Total number of identities to generate
            pattern_distribution: Distribution of patterns (must sum to <= 1.0)
            base_intensity: Base intensity for all patterns
            
        Returns:
            List of identities with mixed patterns
            
        Example:
            >>> gen = SyntheticIdentityPatternGenerator(seed=42)
            >>> identities = gen.generate_mixed_batch(
            ...     total_count=100,
            ...     pattern_distribution={
            ...         PatternType.BUST_OUT: 0.20,
            ...         PatternType.FRAUD_RING: 0.15,
            ...         PatternType.IDENTITY_THEFT: 0.10,
            ...     }
            ... )
            >>> # 20% bust-out, 15% fraud ring, 10% identity theft, 55% clean
        """
        all_identities = []
        remaining_count = total_count
        
        # Generate identities for each pattern
        for pattern_type, proportion in pattern_distribution.items():
            pattern_count = int(total_count * proportion)
            if pattern_count > 0:
                config = PatternConfig(
                    pattern_type=pattern_type,
                    intensity=base_intensity,
                    count=pattern_count
                )
                pattern_identities = self.generate_with_pattern(config)
                all_identities.extend(pattern_identities)
                remaining_count -= pattern_count
        
        # Generate clean identities for remainder
        if remaining_count > 0:
            clean_identities = self.base_generator.generate_batch(remaining_count)
            for identity in clean_identities:
                identity["pattern_injected"] = "none"
                identity["pattern_intensity"] = 0.0
            all_identities.extend(clean_identities)
        
        # Shuffle to mix patterns
        self.faker.random.shuffle(all_identities)
        
        return all_identities
    
    def get_pattern_summary(self) -> Dict[str, Any]:
        """
        Get summary of injected patterns.
        
        Returns:
            Dictionary with pattern statistics
        """
        if not self.injected_patterns:
            return {
                "total_patterns": 0,
                "total_identities": 0,
                "patterns_by_type": {},
            }
        
        patterns_by_type = {}
        total_identities = 0
        
        for pattern in self.injected_patterns:
            pattern_type = pattern["pattern_type"]
            count = pattern["count"]
            
            if pattern_type not in patterns_by_type:
                patterns_by_type[pattern_type] = {
                    "count": 0,
                    "identities": 0,
                    "avg_intensity": 0.0,
                }
            
            patterns_by_type[pattern_type]["count"] += 1
            patterns_by_type[pattern_type]["identities"] += count
            patterns_by_type[pattern_type]["avg_intensity"] += pattern["intensity"]
            total_identities += count
        
        # Calculate averages
        for pattern_type in patterns_by_type:
            count = patterns_by_type[pattern_type]["count"]
            patterns_by_type[pattern_type]["avg_intensity"] /= count
        
        return {
            "total_patterns": len(self.injected_patterns),
            "total_identities": total_identities,
            "patterns_by_type": patterns_by_type,
        }

# Made with Bob
