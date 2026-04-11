"""
Bust-Out Scheme Detector
========================

Detects bust-out fraud schemes where fraudsters rapidly build credit,
max out all available credit, and then disappear without repayment.

Bust-out schemes typically follow this pattern:
1. Create synthetic identity
2. Build credit history (6-24 months)
3. Rapidly increase credit limits
4. Max out all credit simultaneously
5. Disappear (no payments, no contact)

Features:
- Temporal credit analysis
- Velocity detection (rapid credit building)
- Maxing-out detection
- Disappearance indicators
- Risk scoring

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.2 - Synthetic Identity Fraud Detection
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class BustOutIndicator:
    """Individual bust-out fraud indicator."""
    indicator_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    score: int  # Contribution to overall risk score


@dataclass
class BustOutDetectionResult:
    """Result of bust-out detection analysis."""
    identity_id: str
    is_bust_out: bool
    bust_out_score: int  # 0-100 (higher = more likely bust-out)
    risk_level: str  # 'low', 'medium', 'high', 'critical'
    indicators: List[BustOutIndicator]
    recommendations: List[str]
    
    # Detailed metrics
    credit_velocity: float  # Credit growth rate
    utilization_spike: bool  # Sudden utilization increase
    recent_inactivity: bool  # No recent activity
    max_out_percentage: float  # Percentage of accounts maxed out


class BustOutDetector:
    """
    Detect bust-out fraud schemes through behavioral analysis.
    
    A bust-out scheme is characterized by:
    - Rapid credit building (high velocity)
    - Sudden maxing out of all credit
    - Disappearance (no payments, no contact)
    - Short credit history (typically < 24 months)
    
    Example:
        >>> detector = BustOutDetector()
        >>> result = detector.detect(identity)
        >>> if result.is_bust_out:
        ...     print(f"Bust-out detected! Score: {result.bust_out_score}")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize bust-out detector.
        
        Args:
            config: Configuration options:
                - bust_out_threshold: Minimum score for bust-out (default: 70)
                - high_velocity_threshold: Credit growth rate threshold (default: 5000/month)
                - max_out_threshold: Utilization threshold (default: 0.90)
                - recent_file_months: Recent credit file threshold (default: 24)
                - critical_score_threshold: Critical risk threshold (default: 85)
        """
        self.config = config or {}
        
        # Thresholds
        self.bust_out_threshold = self.config.get("bust_out_threshold", 70)
        self.high_velocity_threshold = self.config.get("high_velocity_threshold", 5000)
        self.max_out_threshold = self.config.get("max_out_threshold", 0.90)
        self.recent_file_months = self.config.get("recent_file_months", 24)
        self.critical_score_threshold = self.config.get("critical_score_threshold", 85)
        
        logger.info(
            f"BustOutDetector initialized with "
            f"bust_out_threshold={self.bust_out_threshold}, "
            f"high_velocity_threshold={self.high_velocity_threshold}"
        )
    
    def detect(self, identity: Dict[str, Any]) -> BustOutDetectionResult:
        """
        Detect bust-out scheme for a single identity.
        
        Args:
            identity: Identity dictionary from SyntheticIdentityGenerator
            
        Returns:
            BustOutDetectionResult with detection details
        """
        identity_id = identity["identity_id"]
        
        # Analyze credit behavior
        credit_velocity = self._calculate_credit_velocity(identity)
        utilization_spike = self._detect_utilization_spike(identity)
        recent_inactivity = self._detect_recent_inactivity(identity)
        max_out_percentage = self._calculate_max_out_percentage(identity)
        
        # Collect indicators
        indicators = self._collect_indicators(
            identity, credit_velocity, utilization_spike, 
            recent_inactivity, max_out_percentage
        )
        
        # Calculate bust-out score
        bust_out_score = self._calculate_bust_out_score(indicators)
        
        # Determine risk level
        risk_level = self._determine_risk_level(bust_out_score)
        
        # Determine if bust-out
        is_bust_out = bust_out_score >= self.bust_out_threshold
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            is_bust_out, bust_out_score, risk_level, indicators
        )
        
        return BustOutDetectionResult(
            identity_id=identity_id,
            is_bust_out=is_bust_out,
            bust_out_score=bust_out_score,
            risk_level=risk_level,
            indicators=indicators,
            recommendations=recommendations,
            credit_velocity=credit_velocity,
            utilization_spike=utilization_spike,
            recent_inactivity=recent_inactivity,
            max_out_percentage=max_out_percentage,
        )
    
    def detect_batch(self, identities: List[Dict[str, Any]]) -> List[BustOutDetectionResult]:
        """
        Detect bust-out schemes for multiple identities.
        
        Args:
            identities: List of identity dictionaries
            
        Returns:
            List of BustOutDetectionResult
        """
        return [self.detect(identity) for identity in identities]
    
    def get_high_risk_identities(
        self, identities: List[Dict[str, Any]], min_score: int = 70
    ) -> List[BustOutDetectionResult]:
        """
        Get identities with high bust-out risk.
        
        Args:
            identities: List of identity dictionaries
            min_score: Minimum bust-out score threshold
            
        Returns:
            List of high-risk BustOutDetectionResult, sorted by score
        """
        results = self.detect_batch(identities)
        high_risk = [r for r in results if r.bust_out_score >= min_score]
        high_risk.sort(key=lambda r: r.bust_out_score, reverse=True)
        return high_risk
    
    def get_statistics(self, results: List[BustOutDetectionResult]) -> Dict[str, Any]:
        """
        Get detection statistics.
        
        Args:
            results: List of BustOutDetectionResult
            
        Returns:
            Dictionary of statistics including:
            - total_identities: Total number analyzed
            - bust_out_count: Number flagged as bust-out
            - bust_out_rate: Percentage flagged
            - average_bust_out_score: Mean score
            - risk_level_distribution: Count by risk level
            - top_indicators: Most common indicators
            - average_credit_velocity: Mean velocity
            - max_credit_velocity: Maximum velocity
            - high_utilization_count: Count with >90% utilization
        """
        if not results:
            return {
                "total_identities": 0,
                "bust_out_count": 0,
                "bust_out_rate": 0.0,
                "average_bust_out_score": 0.0,
                "risk_level_distribution": {},
                "top_indicators": [],
                "average_credit_velocity": 0.0,
                "max_credit_velocity": 0.0,
                "high_utilization_count": 0,
            }
        
        # Basic counts
        bust_out_count = sum(1 for r in results if r.is_bust_out)
        avg_score = sum(r.bust_out_score for r in results) / len(results)
        
        # Risk level distribution
        risk_distribution = {}
        for result in results:
            risk_distribution[result.risk_level] = risk_distribution.get(result.risk_level, 0) + 1
        
        # Top indicators
        indicator_counts = {}
        for result in results:
            for indicator in result.indicators:
                indicator_counts[indicator.indicator_type] = indicator_counts.get(indicator.indicator_type, 0) + 1
        top_indicators = sorted(indicator_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Credit velocity stats
        velocities = [r.credit_velocity for r in results]
        avg_velocity = sum(velocities) / len(velocities)
        max_velocity = max(velocities)
        
        # High utilization count
        high_util_count = sum(1 for r in results if r.utilization_spike)
        
        return {
            "total_identities": len(results),
            "bust_out_count": bust_out_count,
            "bust_out_rate": bust_out_count / len(results),
            "average_bust_out_score": avg_score,
            "risk_level_distribution": risk_distribution,
            "top_indicators": top_indicators,
            "average_credit_velocity": avg_velocity,
            "max_credit_velocity": max_velocity,
            "high_utilization_count": high_util_count,
        }
    
    def _calculate_credit_velocity(self, identity: Dict[str, Any]) -> float:
        """Calculate credit growth velocity ($/month)."""
        credit_limit = identity.get("total_credit_limit", 0)
        file_age_months = identity.get("credit_file_age_months", 1)
        
        if file_age_months == 0:
            file_age_months = 1  # Avoid division by zero
        
        # Velocity = total credit / months
        velocity = credit_limit / file_age_months
        return velocity
    
    def _detect_utilization_spike(self, identity: Dict[str, Any]) -> bool:
        """Detect sudden utilization spike (maxing out)."""
        utilization = identity.get("credit_utilization", 0)
        return utilization >= self.max_out_threshold
    
    def _detect_recent_inactivity(self, identity: Dict[str, Any]) -> bool:
        """Detect recent inactivity (disappearance indicator)."""
        # In a real system, this would check for:
        # - No recent payments
        # - No recent transactions
        # - No contact attempts answered
        # For synthetic data, we use high utilization + recent file as proxy
        utilization = identity.get("credit_utilization", 0)
        file_age = identity.get("credit_file_age_months", 999)
        
        # Recent file + maxed out = potential disappearance
        return utilization >= 0.85 and file_age < 18
    
    def _calculate_max_out_percentage(self, identity: Dict[str, Any]) -> float:
        """Calculate percentage of accounts maxed out."""
        utilization = identity.get("credit_utilization", 0)
        
        # Simplified: if utilization > 0.90, assume most accounts maxed
        if utilization >= 0.95:
            return 1.0
        elif utilization >= 0.90:
            return 0.80
        elif utilization >= 0.80:
            return 0.50
        else:
            return 0.0
    
    def _collect_indicators(
        self,
        identity: Dict[str, Any],
        credit_velocity: float,
        utilization_spike: bool,
        recent_inactivity: bool,
        max_out_percentage: float,
    ) -> List[BustOutIndicator]:
        """Collect all bust-out indicators."""
        indicators = []
        
        # High credit velocity
        if credit_velocity >= self.high_velocity_threshold:
            severity = "critical" if credit_velocity >= self.high_velocity_threshold * 2 else "high"
            indicators.append(BustOutIndicator(
                indicator_type="high_credit_velocity",
                severity=severity,
                description=f"Rapid credit building: ${credit_velocity:.0f}/month",
                score=30 if severity == "critical" else 20,
            ))
        
        # Recent credit file
        file_age = identity.get("credit_file_age_months", 999)
        if file_age < self.recent_file_months:
            severity = "high" if file_age < 12 else "medium"
            indicators.append(BustOutIndicator(
                indicator_type="recent_credit_file",
                severity=severity,
                description=f"Recent credit file: {file_age} months",
                score=20 if severity == "high" else 10,
            ))
        
        # Utilization spike (maxing out)
        if utilization_spike:
            indicators.append(BustOutIndicator(
                indicator_type="utilization_spike",
                severity="critical",
                description=f"High utilization: {identity.get('credit_utilization', 0)*100:.1f}%",
                score=30,
            ))
        
        # Multiple accounts maxed out
        if max_out_percentage >= 0.80:
            indicators.append(BustOutIndicator(
                indicator_type="multiple_accounts_maxed",
                severity="critical",
                description=f"{max_out_percentage*100:.0f}% of accounts maxed out",
                score=25,
            ))
        
        # Recent inactivity (disappearance)
        if recent_inactivity:
            indicators.append(BustOutIndicator(
                indicator_type="recent_inactivity",
                severity="critical",
                description="No recent activity detected",
                score=20,
            ))
        
        # Authorized user history (piggybacking)
        if identity.get("has_authorized_user_history", False):
            indicators.append(BustOutIndicator(
                indicator_type="authorized_user_piggybacking",
                severity="medium",
                description="Authorized user history detected",
                score=10,
            ))
        
        # Synthetic identity
        if identity.get("is_synthetic", False):
            indicators.append(BustOutIndicator(
                indicator_type="synthetic_identity",
                severity="high",
                description=f"Synthetic identity: {identity.get('identity_type', 'unknown')}",
                score=15,
            ))
        
        # Shared attributes
        shared_attrs = identity.get("shared_attributes", [])
        if shared_attrs:
            severity = "high" if len(shared_attrs) >= 2 else "medium"
            indicators.append(BustOutIndicator(
                indicator_type="shared_attributes",
                severity=severity,
                description=f"Shared attributes: {', '.join(shared_attrs)}",
                score=15 if severity == "high" else 10,
            ))
        
        return indicators
    
    def _calculate_bust_out_score(self, indicators: List[BustOutIndicator]) -> int:
        """Calculate overall bust-out score from indicators."""
        total_score = sum(ind.score for ind in indicators)
        return min(100, total_score)
    
    def _determine_risk_level(self, bust_out_score: int) -> str:
        """Determine risk level from bust-out score."""
        if bust_out_score >= self.critical_score_threshold:
            return "critical"
        elif bust_out_score >= 70:
            return "high"
        elif bust_out_score >= 50:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendations(
        self,
        is_bust_out: bool,
        bust_out_score: int,
        risk_level: str,
        indicators: List[BustOutIndicator],
    ) -> List[str]:
        """Generate recommendations based on detection results."""
        recommendations = []
        
        if is_bust_out:
            recommendations.append("ALERT: High probability of bust-out scheme")
            recommendations.append("ACTION: Freeze all credit accounts immediately")
            recommendations.append("ACTION: Initiate fraud investigation")
        elif bust_out_score >= 50:
            recommendations.append("WARNING: Elevated bust-out risk detected")
            recommendations.append("ACTION: Enhanced monitoring required")
            recommendations.append("ACTION: Verify identity and contact information")
        else:
            recommendations.append("MONITOR: Continue standard monitoring")
        
        # Specific recommendations based on indicators
        critical_indicators = [ind for ind in indicators if ind.severity == "critical"]
        if critical_indicators:
            recommendations.append(
                f"CRITICAL: {len(critical_indicators)} critical indicators detected"
            )
        
        if any(ind.indicator_type == "utilization_spike" for ind in indicators):
            recommendations.append("ALERT: Accounts maxed out - potential bust-out in progress")
        
        if any(ind.indicator_type == "high_credit_velocity" for ind in indicators):
            recommendations.append("WARNING: Rapid credit building detected")
        
        if any(ind.indicator_type == "recent_inactivity" for ind in indicators):
            recommendations.append("ALERT: Recent inactivity - possible disappearance")
        
        return recommendations


__all__ = ["BustOutDetector", "BustOutDetectionResult", "BustOutIndicator"]

# Made with Bob
