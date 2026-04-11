"""
Identity Validator
==================

Validates identity authenticity and detects synthetic identity fraud patterns
through cross-validation and shared attribute analysis.

Features:
- Shared attribute detection (SSN, phone, address, email)
- Identity authenticity scoring
- Cross-validation across multiple identities
- Fraud pattern identification
- Risk assessment

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.2 - Synthetic Identity Fraud Detection
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class SharedAttributeCluster:
    """Cluster of identities sharing an attribute."""
    attribute_type: str  # 'ssn', 'phone', 'address', 'email'
    attribute_value: str
    identity_ids: List[str]
    risk_score: int  # 0-100
    
    def __post_init__(self):
        """Calculate risk score based on cluster size."""
        # More identities sharing = higher risk
        cluster_size = len(self.identity_ids)
        if cluster_size >= 5:
            self.risk_score = 100
        elif cluster_size >= 3:
            self.risk_score = 80
        elif cluster_size >= 2:
            self.risk_score = 60
        else:
            self.risk_score = 0


@dataclass
class ValidationResult:
    """Result of identity validation."""
    identity_id: str
    is_authentic: bool
    authenticity_score: int  # 0-100 (higher = more authentic)
    risk_score: int  # 0-100 (higher = more risky)
    shared_attributes: List[str]
    fraud_indicators: List[str]
    recommendations: List[str]


class IdentityValidator:
    """
    Validate identity authenticity and detect synthetic identity fraud.
    
    This validator analyzes identities for:
    - Shared SSNs across multiple identities
    - Shared phone numbers
    - Shared addresses
    - Shared email domains
    - Credit profile anomalies
    - Bust-out risk patterns
    
    Example:
        >>> validator = IdentityValidator()
        >>> validator.add_identity(identity1)
        >>> validator.add_identity(identity2)
        >>> result = validator.validate(identity1['identity_id'])
        >>> print(result.authenticity_score)
        45  # Low score indicates likely synthetic
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize identity validator.
        
        Args:
            config: Configuration options:
                - min_authenticity_threshold: Minimum score for authentic (default: 70)
                - max_risk_threshold: Maximum acceptable risk (default: 50)
                - shared_ssn_weight: Weight for shared SSN (default: 40)
                - shared_phone_weight: Weight for shared phone (default: 20)
                - shared_address_weight: Weight for shared address (default: 20)
                - credit_anomaly_weight: Weight for credit anomalies (default: 20)
        """
        self.config = config or {}
        
        # Thresholds
        self.min_authenticity_threshold = self.config.get("min_authenticity_threshold", 70)
        self.max_risk_threshold = self.config.get("max_risk_threshold", 50)
        
        # Weights for risk scoring
        self.shared_ssn_weight = self.config.get("shared_ssn_weight", 40)
        self.shared_phone_weight = self.config.get("shared_phone_weight", 20)
        self.shared_address_weight = self.config.get("shared_address_weight", 20)
        self.credit_anomaly_weight = self.config.get("credit_anomaly_weight", 20)
        
        # Identity storage
        self._identities: Dict[str, Dict[str, Any]] = {}
        
        # Shared attribute indexes
        self._ssn_index: Dict[str, List[str]] = defaultdict(list)
        self._phone_index: Dict[str, List[str]] = defaultdict(list)
        self._address_index: Dict[str, List[str]] = defaultdict(list)
        self._email_domain_index: Dict[str, List[str]] = defaultdict(list)
        
        logger.info(
            f"IdentityValidator initialized with "
            f"authenticity_threshold={self.min_authenticity_threshold}, "
            f"risk_threshold={self.max_risk_threshold}"
        )
    
    def add_identity(self, identity: Dict[str, Any]) -> None:
        """
        Add an identity to the validator for analysis.
        
        Args:
            identity: Identity dictionary from SyntheticIdentityGenerator
        """
        identity_id = identity["identity_id"]
        
        # Store identity
        self._identities[identity_id] = identity
        
        # Index shared attributes
        self._ssn_index[identity["ssn"]].append(identity_id)
        self._phone_index[identity["phone"]].append(identity_id)
        
        # Index address (as string for comparison)
        address = identity["address"]
        address_key = f"{address['street']}|{address['city']}|{address['state']}|{address['zip_code']}"
        self._address_index[address_key].append(identity_id)
        
        # Index email domain
        email_domain = identity["email"].split("@")[1]
        self._email_domain_index[email_domain].append(identity_id)
        
        logger.debug(f"Added identity {identity_id} to validator")
    
    def add_identities(self, identities: List[Dict[str, Any]]) -> None:
        """
        Add multiple identities to the validator.
        
        Args:
            identities: List of identity dictionaries
        """
        for identity in identities:
            self.add_identity(identity)
    
    def validate(self, identity_id: str) -> ValidationResult:
        """
        Validate a specific identity.
        
        Args:
            identity_id: ID of identity to validate
            
        Returns:
            ValidationResult with authenticity score and fraud indicators
            
        Raises:
            ValueError: If identity_id not found
        """
        if identity_id not in self._identities:
            raise ValueError(f"Identity {identity_id} not found in validator")
        
        identity = self._identities[identity_id]
        
        # Detect shared attributes
        shared_attributes = self._detect_shared_attributes(identity)
        
        # Calculate authenticity score
        authenticity_score = self._calculate_authenticity_score(identity, shared_attributes)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(identity, shared_attributes)
        
        # Identify fraud indicators
        fraud_indicators = self._identify_fraud_indicators(identity, shared_attributes)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            authenticity_score, risk_score, fraud_indicators
        )
        
        # Determine if authentic
        is_authentic = (
            authenticity_score >= self.min_authenticity_threshold
            and risk_score <= self.max_risk_threshold
        )
        
        return ValidationResult(
            identity_id=identity_id,
            is_authentic=is_authentic,
            authenticity_score=authenticity_score,
            risk_score=risk_score,
            shared_attributes=shared_attributes,
            fraud_indicators=fraud_indicators,
            recommendations=recommendations,
        )
    
    def validate_all(self) -> List[ValidationResult]:
        """
        Validate all identities in the validator.
        
        Returns:
            List of ValidationResult for all identities
        """
        return [self.validate(identity_id) for identity_id in self._identities.keys()]
    
    def get_shared_attribute_clusters(self) -> List[SharedAttributeCluster]:
        """
        Get all shared attribute clusters.
        
        Returns:
            List of SharedAttributeCluster objects
        """
        clusters = []
        
        # SSN clusters
        for ssn, identity_ids in self._ssn_index.items():
            if len(identity_ids) > 1:
                clusters.append(SharedAttributeCluster(
                    attribute_type="ssn",
                    attribute_value=ssn,
                    identity_ids=identity_ids,
                    risk_score=0  # Will be calculated in __post_init__
                ))
        
        # Phone clusters
        for phone, identity_ids in self._phone_index.items():
            if len(identity_ids) > 1:
                clusters.append(SharedAttributeCluster(
                    attribute_type="phone",
                    attribute_value=phone,
                    identity_ids=identity_ids,
                    risk_score=0
                ))
        
        # Address clusters
        for address_key, identity_ids in self._address_index.items():
            if len(identity_ids) > 1:
                clusters.append(SharedAttributeCluster(
                    attribute_type="address",
                    attribute_value=address_key,
                    identity_ids=identity_ids,
                    risk_score=0
                ))
        
        # Sort by risk score (highest first)
        clusters.sort(key=lambda c: c.risk_score, reverse=True)
        
        return clusters
    
    def get_high_risk_identities(self, min_risk_score: int = 70) -> List[ValidationResult]:
        """
        Get identities with high risk scores.
        
        Args:
            min_risk_score: Minimum risk score threshold (default: 70)
            
        Returns:
            List of ValidationResult for high-risk identities
        """
        results = self.validate_all()
        high_risk = [r for r in results if r.risk_score >= min_risk_score]
        high_risk.sort(key=lambda r: r.risk_score, reverse=True)
        return high_risk
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get validation statistics.
        
        Returns:
            Dictionary of statistics
        """
        if not self._identities:
            return {
                "total_identities": 0,
                "authentic_count": 0,
                "synthetic_count": 0,
                "high_risk_count": 0,
                "shared_ssn_clusters": 0,
                "shared_phone_clusters": 0,
                "shared_address_clusters": 0,
            }
        
        results = self.validate_all()
        
        authentic_count = sum(1 for r in results if r.is_authentic)
        synthetic_count = len(results) - authentic_count
        high_risk_count = sum(1 for r in results if r.risk_score >= 70)
        
        clusters = self.get_shared_attribute_clusters()
        ssn_clusters = sum(1 for c in clusters if c.attribute_type == "ssn")
        phone_clusters = sum(1 for c in clusters if c.attribute_type == "phone")
        address_clusters = sum(1 for c in clusters if c.attribute_type == "address")
        
        return {
            "total_identities": len(self._identities),
            "authentic_count": authentic_count,
            "synthetic_count": synthetic_count,
            "high_risk_count": high_risk_count,
            "shared_ssn_clusters": ssn_clusters,
            "shared_phone_clusters": phone_clusters,
            "shared_address_clusters": address_clusters,
            "authenticity_rate": authentic_count / len(results) if results else 0,
        }
    
    def _detect_shared_attributes(self, identity: Dict[str, Any]) -> List[str]:
        """Detect which attributes are shared with other identities."""
        shared = []
        identity_id = identity["identity_id"]
        
        # Check SSN
        ssn_identities = self._ssn_index[identity["ssn"]]
        if len(ssn_identities) > 1:
            shared.append("ssn")
        
        # Check phone
        phone_identities = self._phone_index[identity["phone"]]
        if len(phone_identities) > 1:
            shared.append("phone")
        
        # Check address
        address = identity["address"]
        address_key = f"{address['street']}|{address['city']}|{address['state']}|{address['zip_code']}"
        address_identities = self._address_index[address_key]
        if len(address_identities) > 1:
            shared.append("address")
        
        return shared
    
    def _calculate_authenticity_score(
        self, identity: Dict[str, Any], shared_attributes: List[str]
    ) -> int:
        """Calculate authenticity score (0-100, higher = more authentic)."""
        score = 100
        
        # Penalize for being marked as synthetic
        if identity.get("is_synthetic", False):
            score -= 50
        
        # Penalize for shared attributes
        if "ssn" in shared_attributes:
            score -= self.shared_ssn_weight
        if "phone" in shared_attributes:
            score -= self.shared_phone_weight
        if "address" in shared_attributes:
            score -= self.shared_address_weight
        
        # Penalize for recent credit file
        if identity.get("credit_file_age_months", 999) < 12:
            score -= 15
        
        # Penalize for authorized user history (piggybacking)
        if identity.get("has_authorized_user_history", False):
            score -= 10
        
        # Penalize for high credit utilization
        if identity.get("credit_utilization", 0) > 0.80:
            score -= 10
        
        return max(0, min(100, score))
    
    def _calculate_risk_score(
        self, identity: Dict[str, Any], shared_attributes: List[str]
    ) -> int:
        """Calculate risk score (0-100, higher = more risky)."""
        score = 0
        
        # Add risk for shared attributes
        if "ssn" in shared_attributes:
            score += self.shared_ssn_weight
        if "phone" in shared_attributes:
            score += self.shared_phone_weight
        if "address" in shared_attributes:
            score += self.shared_address_weight
        
        # Add risk for credit anomalies
        if identity.get("credit_file_age_months", 999) < 12:
            score += 15
        if identity.get("has_authorized_user_history", False):
            score += 10
        if identity.get("credit_utilization", 0) > 0.80:
            score += 15
        
        # Add bust-out risk
        bust_out_risk = identity.get("bust_out_risk_score", 0)
        score += int(bust_out_risk * 0.2)  # Scale down bust-out risk
        
        return min(100, score)
    
    def _identify_fraud_indicators(
        self, identity: Dict[str, Any], shared_attributes: List[str]
    ) -> List[str]:
        """Identify specific fraud indicators."""
        indicators = []
        
        if identity.get("is_synthetic", False):
            indicators.append(f"synthetic_identity_{identity.get('identity_type', 'unknown')}")
        
        if "ssn" in shared_attributes:
            ssn_count = len(self._ssn_index[identity["ssn"]])
            indicators.append(f"shared_ssn_with_{ssn_count}_identities")
        
        if "phone" in shared_attributes:
            phone_count = len(self._phone_index[identity["phone"]])
            indicators.append(f"shared_phone_with_{phone_count}_identities")
        
        if "address" in shared_attributes:
            address = identity["address"]
            address_key = f"{address['street']}|{address['city']}|{address['state']}|{address['zip_code']}"
            address_count = len(self._address_index[address_key])
            indicators.append(f"shared_address_with_{address_count}_identities")
        
        if identity.get("credit_file_age_months", 999) < 12:
            indicators.append("recent_credit_file")
        
        if identity.get("has_authorized_user_history", False):
            indicators.append("authorized_user_piggybacking")
        
        if identity.get("credit_utilization", 0) > 0.80:
            indicators.append("high_credit_utilization")
        
        if identity.get("bust_out_risk_score", 0) >= 70:
            indicators.append("high_bust_out_risk")
        
        return indicators
    
    def _generate_recommendations(
        self, authenticity_score: int, risk_score: int, fraud_indicators: List[str]
    ) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        if authenticity_score < 50:
            recommendations.append("REJECT: High probability of synthetic identity")
        elif authenticity_score < 70:
            recommendations.append("REVIEW: Manual verification required")
        else:
            recommendations.append("APPROVE: Identity appears authentic")
        
        if risk_score >= 70:
            recommendations.append("HIGH RISK: Immediate investigation required")
        elif risk_score >= 50:
            recommendations.append("MEDIUM RISK: Enhanced monitoring recommended")
        
        if any("shared_ssn" in ind for ind in fraud_indicators):
            recommendations.append("ALERT: SSN shared across multiple identities")
        
        if any("bust_out" in ind for ind in fraud_indicators):
            recommendations.append("WARNING: Potential bust-out scheme detected")
        
        if any("piggybacking" in ind for ind in fraud_indicators):
            recommendations.append("NOTE: Authorized user history detected")
        
        return recommendations


__all__ = ["IdentityValidator", "ValidationResult", "SharedAttributeCluster"]

# Made with Bob
