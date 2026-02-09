"""
Structuring Pattern Generator (Smurfing)

Generates AML structuring patterns with just-below-threshold transactions,
temporal analysis, geographic distribution, and coordinated deposit detection.

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

import random
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from decimal import Decimal

from ..core.base_generator import BaseGenerator
from ..events.transaction_generator import TransactionGenerator
from ..utils.data_models import Pattern, RiskLevel
from ..utils.helpers import (
    random_datetime_between,
    random_choice_weighted,
    calculate_pattern_confidence
)


class StructuringPatternGenerator(BaseGenerator[Pattern]):
    """
    Generates structuring (smurfing) patterns for AML detection.
    
    Features:
    - Just-below-threshold transaction detection
    - Temporal clustering analysis
    - Geographic distribution patterns
    - Multiple account usage
    - Coordinated deposit detection
    - Velocity analysis
    - Smurf identification
    
    Pattern Types:
    1. Classic structuring: Multiple deposits just below $10K threshold
    2. Smurfing: Multiple people making structured deposits
    3. Geographic smurfing: Deposits across multiple locations
    4. Temporal smurfing: Deposits clustered in time
    5. Account hopping: Structuring across multiple accounts
    
    Use Cases:
    - AML compliance (BSA/CTR reporting)
    - Structuring detection
    - Money laundering prevention
    - Regulatory compliance
    """
    
    def __init__(
        self,
        seed: Optional[int] = None,
        locale: str = "en_US",
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize StructuringPatternGenerator."""
        super().__init__(seed, locale, config)
        
        self.txn_gen = TransactionGenerator(seed=seed, locale=locale, config=config)
        
        self.pattern_type_weights = {
            "classic_structuring": 0.35,
            "smurfing": 0.30,
            "geographic_smurfing": 0.15,
            "temporal_smurfing": 0.10,
            "account_hopping": 0.10
        }
        
    def generate(
        self,
        pattern_type: Optional[str] = None,
        smurf_count: Optional[int] = None,
        transaction_count: Optional[int] = None,
        time_window_hours: Optional[int] = None
    ) -> Pattern:
        """Generate a structuring pattern."""
        if pattern_type is None:
            pattern_type = random_choice_weighted(list(self.pattern_type_weights.items()))
        
        assert pattern_type is not None
            
        if smurf_count is None:
            smurf_count = random.randint(1, 10)
        if transaction_count is None:
            transaction_count = random.randint(5, 30)
        if time_window_hours is None:
            time_window_hours = random.randint(24, 168)  # 1-7 days
            
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(hours=time_window_hours)
        
        entity_ids = [f"PER-{self.faker.uuid4()[:8]}" for _ in range(smurf_count)]
        account_ids = [f"ACC-{self.faker.uuid4()[:8]}" for _ in range(smurf_count)]
        
        transactions = self._generate_structuring_transactions(
            account_ids,
            transaction_count,
            start_date,
            end_date,
            pattern_type
        )
        
        total_value: Decimal = sum((Decimal(str(t.amount)) for t in transactions), Decimal("0.00"))
        
        indicators = self._generate_indicators(pattern_type, transactions, smurf_count)
        red_flags = self._generate_red_flags(pattern_type, transactions, total_value)
        
        confidence_score = calculate_pattern_confidence(
            indicators, red_flags, total_value, time_window_hours // 24
        )
        
        risk_level = self._determine_risk_level(confidence_score, total_value)
        severity_score = self._calculate_severity_score(
            confidence_score, total_value, smurf_count, len(indicators)
        )
        
        return Pattern(
            pattern_id=f"PTN-STRUCT-{self.faker.uuid4()[:12]}",
            pattern_type="structuring",
            detection_date=datetime.now(timezone.utc),
            detection_method=f"structuring_analysis_{pattern_type}",
            confidence_score=confidence_score,
            entity_ids=entity_ids,
            entity_types=["person"] * smurf_count,
            transaction_ids=[t.id for t in transactions],
            communication_ids=[],
            start_date=start_date,
            end_date=end_date,
            duration_days=time_window_hours // 24,
            total_value=total_value,
            transaction_count=len(transactions),
            risk_level=risk_level,
            severity_score=severity_score,
            indicators=indicators,
            red_flags=red_flags,
            metadata={
                "pattern_subtype": pattern_type,
                "smurf_count": smurf_count,
                "time_window_hours": time_window_hours,
                "average_transaction": float(total_value / len(transactions)) if transactions else 0,
                "below_threshold_count": sum(1 for t in transactions if t.is_structuring)
            }
        )
        
    def _generate_structuring_transactions(
        self, account_ids: List[str], count: int, start: datetime, end: datetime, pattern_type: str
    ) -> List[Any]:
        """Generate structuring transactions."""
        transactions = []
        for i in range(count):
            account_id = random.choice(account_ids)
            txn_date = random_datetime_between(start, end)
            
            txn = self.txn_gen.generate(
                from_account_id=account_id,
                force_structuring=True
            )
            txn.transaction_date = txn_date
            txn.metadata["pattern_type"] = pattern_type
            txn.metadata["sequence"] = i + 1
            
            transactions.append(txn)
        return transactions
        
    def _generate_indicators(self, pattern_type: str, transactions: List[Any], smurf_count: int) -> List[str]:
        """Generate indicators."""
        indicators = ["structuring_detected", "below_threshold_transactions", "aml_red_flag"]
        
        if pattern_type == "smurfing":
            indicators.extend(["multiple_smurfs", "coordinated_deposits"])
        elif pattern_type == "geographic_smurfing":
            indicators.extend(["geographic_distribution", "multiple_locations"])
        elif pattern_type == "temporal_smurfing":
            indicators.extend(["temporal_clustering", "time_based_pattern"])
        elif pattern_type == "account_hopping":
            indicators.extend(["multiple_accounts", "account_switching"])
            
        if smurf_count >= 5:
            indicators.append("large_smurf_network")
        if len(transactions) >= 20:
            indicators.append("high_transaction_frequency")
            
        return list(set(indicators))
        
    def _generate_red_flags(self, pattern_type: str, transactions: List[Any], total_value: Decimal) -> List[str]:
        """Generate red flags."""
        red_flags = ["ctr_evasion_suspected", "money_laundering_indicator"]
        
        if total_value > 100000:
            red_flags.append("high_total_value")
        if len(transactions) > 15:
            red_flags.append("excessive_transaction_count")
            
        return red_flags
        
    def _determine_risk_level(self, confidence: float, value: Decimal) -> RiskLevel:
        """Determine risk level."""
        if confidence >= 0.8 and value > 100000:
            return RiskLevel.CRITICAL
        elif confidence >= 0.7 or value > 50000:
            return RiskLevel.HIGH
        elif confidence >= 0.5:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
        
    def _calculate_severity_score(
        self, confidence: float, value: Decimal, smurf_count: int, indicator_count: int
    ) -> float:
        """Calculate severity."""
        score = confidence * 0.5
        if value > 100000:
            score += 0.2
        if smurf_count >= 5:
            score += 0.2
        if indicator_count >= 5:
            score += 0.1
        return min(score, 1.0)

