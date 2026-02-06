"""
Insider Trading Pattern Generator for Banking Compliance

Generates sophisticated insider trading patterns with 30+ dimensional analysis
including pre-announcement trading, coordinated activity, and unusual volume/price patterns.

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal

from ..core.base_generator import BaseGenerator
from ..events.trade_generator import TradeGenerator
from ..events.communication_generator import CommunicationGenerator
from ..utils.data_models import Pattern, RiskLevel
from ..utils.helpers import (
    random_datetime_between,
    random_choice_weighted,
    calculate_pattern_confidence
)


class InsiderTradingPatternGenerator(BaseGenerator[Pattern]):
    """
    Generates sophisticated insider trading patterns with multi-dimensional analysis.
    
    Features:
    - 30+ dimensional pattern analysis
    - Pre-announcement trading detection
    - Coordinated trading patterns
    - Unusual volume/price movement analysis
    - Communication correlation
    - Timing analysis (market hours, pre-market, after-hours)
    - Relationship network analysis
    - Beneficial ownership tracking
    - Executive trading patterns
    - Information asymmetry detection
    
    Pattern Dimensions:
    1. Temporal: Timing relative to announcements
    2. Volume: Unusual trading volume
    3. Price: Unusual price movements
    4. Coordination: Multiple parties trading simultaneously
    5. Communication: Suspicious communications before trades
    6. Relationship: Trading by connected parties
    7. Position: Large position changes
    8. Frequency: Unusual trading frequency
    9. Direction: Consistent buy/sell direction
    10. Profitability: Abnormal returns
    
    Use Cases:
    - SEC insider trading investigations
    - Market surveillance
    - Regulatory compliance (Rule 10b-5)
    - Corporate governance monitoring
    """
    
    def __init__(
        self,
        seed: Optional[int] = None,
        locale: str = "en_US",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize InsiderTradingPatternGenerator.
        
        Args:
            seed: Random seed for reproducibility
            locale: Faker locale
            config: Additional configuration options
        """
        super().__init__(seed, locale, config)
        
        # Initialize sub-generators
        self.trade_gen = TradeGenerator(seed=seed, locale=locale, config=config)
        self.comm_gen = CommunicationGenerator(seed=seed, locale=locale, config=config)
        
        # Pattern type distribution
        self.pattern_type_weights = {
            "pre_announcement_trading": 0.30,
            "coordinated_insider_trading": 0.25,
            "executive_trading_pattern": 0.20,
            "beneficial_owner_pattern": 0.15,
            "tipping_pattern": 0.10
        }
        
        # Insider relationship types
        self.insider_relationships = [
            "executive", "director", "beneficial_owner", "family_member",
            "business_associate", "attorney", "accountant", "consultant",
            "investment_banker", "analyst"
        ]
        
    def generate(
        self,
        pattern_type: Optional[str] = None,
        entity_count: Optional[int] = None,
        trade_count: Optional[int] = None,
        days_before_announcement: Optional[int] = None,
        existing_entity_ids: Optional[List[str]] = None
    ) -> Tuple[Pattern, List[Any], List[Any]]:
        """
        Generate a single insider trading pattern.
        
        Args:
            pattern_type: Type of insider trading pattern
            entity_count: Number of entities involved (2-10)
            trade_count: Number of trades in pattern (5-50)
            days_before_announcement: Days before public announcement (1-90)
            
        Returns:
            Tuple containing:
            - Pattern object
            - List of generated Trade objects
            - List of generated Communication objects
        """
        # Select pattern type (ensure not None)
        if pattern_type is None:
            pattern_type = random_choice_weighted(
                list(self.pattern_type_weights.items())
            )
        
        # Type assertion for type checker
        assert pattern_type is not None, "pattern_type must be set"
            
        # Set defaults
        if entity_count is None:
            entity_count = random.randint(2, 10)
        if trade_count is None:
            trade_count = random.randint(5, 50)
        if days_before_announcement is None:
            days_before_announcement = random.randint(1, 90)
            
        # Generate announcement date (future or recent past)
        announcement_date = datetime.utcnow() - timedelta(days=random.randint(0, 30))
        
        # Generate pattern start date
        start_date = announcement_date - timedelta(days=days_before_announcement)
        # Generate entities involved (or select from existing)
        if existing_entity_ids:
            # Ensure we don't try to sample more than available
            sample_count = min(entity_count, len(existing_entity_ids))
            entity_ids = random.sample(existing_entity_ids, sample_count)
            # If we need more than available, generate new ones
            if sample_count < entity_count:
                 entity_ids.extend([f"PER-{self.faker.uuid4()[:8]}" for _ in range(entity_count - sample_count)])
        else:
            entity_ids = [f"PER-{self.faker.uuid4()[:8]}" for _ in range(entity_count)]
        
        # Generate trades
        trades = self._generate_pattern_trades(
            entity_ids,
            trade_count,
            start_date,
            announcement_date,
            pattern_type
        )
        
        # Generate communications (if applicable)
        communications = self._generate_pattern_communications(
            entity_ids,
            start_date,
            announcement_date,
            pattern_type
        )
        
        # Calculate pattern characteristics
        total_value: Decimal
        if trades:
            total_value = sum((Decimal(str(t.total_value)) for t in trades), Decimal("0.00"))
        else:
            total_value = Decimal("0.00")
        duration_days = (announcement_date - start_date).days
        
        # Generate indicators
        indicators = self._generate_pattern_indicators(
            pattern_type,
            trades,
            communications,
            days_before_announcement
        )
        
        # Generate red flags
        red_flags = self._generate_red_flags(
            pattern_type,
            trades,
            communications,
            entity_count
        )
        
        # Calculate confidence score
        confidence_score = calculate_pattern_confidence(
            indicators,
            red_flags,
            total_value,
            duration_days
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(confidence_score, total_value)
        
        # Calculate severity score
        severity_score = self._calculate_severity_score(
            confidence_score,
            total_value,
            entity_count,
            days_before_announcement
        )
        
        pattern = Pattern(
            pattern_id=f"PTN-IT-{self.faker.uuid4()[:12]}",
            pattern_type="insider_trading",
            detection_date=datetime.utcnow(),
            detection_method=f"multi_dimensional_analysis_{pattern_type}",
            confidence_score=confidence_score,
            entity_ids=entity_ids,
            entity_types=["person"] * entity_count,
            transaction_ids=[t.id for t in trades],
            communication_ids=[c.id for c in communications],
            start_date=start_date,
            end_date=announcement_date,
            duration_days=duration_days,
            total_value=total_value,
            transaction_count=len(trades),
            risk_level=risk_level,
            severity_score=severity_score,
            indicators=indicators,
            red_flags=red_flags,
            is_investigated=False,
            investigation_status=None,
            investigator_id=None,
            investigation_notes=None,
            is_confirmed=None,
            outcome=None,
            action_taken=None,
            metadata={
                "pattern_subtype": pattern_type,
                "days_before_announcement": days_before_announcement,
                "entity_count": entity_count,
                "trade_count": trade_count,
                "communication_count": len(communications),
                "announcement_date": announcement_date.isoformat(),
                "average_trade_value": float(total_value / len(trades)) if trades else 0,
                "insider_relationships": random.sample(self.insider_relationships, k=min(entity_count, 5))
            }
        )
        
        return pattern, trades, communications
    def _generate_pattern_trades(
        self,
        entity_ids: List[str],
        trade_count: int,
        start_date: datetime,
        end_date: datetime,
        pattern_type: str
    ) -> List[Any]:
        """Generate trades forming the insider trading pattern."""
        trades = []
        symbol = self.trade_gen._generate_symbol("stock", "NYSE")
        
        # Distribute trades across time window
        time_delta = (end_date - start_date).total_seconds()
        
        for i in range(trade_count):
            # Select trader (weighted towards early entities)
            trader_id = random.choices(
                entity_ids,
                weights=[1.0 / (j + 1) for j in range(len(entity_ids))],
                k=1
            )[0]
            
            # Generate trade date (more trades closer to announcement)
            # Use exponential distribution to cluster trades near announcement
            progress = (i / trade_count) ** 2  # Quadratic to cluster at end
            trade_offset = time_delta * progress
            trade_date = start_date + timedelta(seconds=trade_offset)
            
            # Generate trade
            trade = self.trade_gen.generate(
                trader_id=trader_id,
                account_id=f"ACC-{trader_id[-8:]}",
                asset_type="stock",
                force_insider=True
            )
            
            # Override symbol and date
            trade.symbol = symbol
            trade.trade_date = trade_date
            trade.settlement_date = trade_date + timedelta(days=2)
            
            # Add pattern metadata
            trade.metadata["pattern_type"] = pattern_type
            trade.metadata["days_before_announcement"] = (end_date - trade_date).days
            trade.metadata["pattern_sequence"] = i + 1
            trade.metadata["pattern_total_trades"] = trade_count
            
            # Coordinated trading: same side for all trades
            if pattern_type == "coordinated_insider_trading":
                trade.side = "buy"  # All buying before good news
                
            trades.append(trade)
            
        return trades
        
    def _generate_pattern_communications(
        self,
        entity_ids: List[str],
        start_date: datetime,
        end_date: datetime,
        pattern_type: str
    ) -> List[Any]:
        """Generate communications associated with insider trading pattern."""
        communications = []
        
        # Generate 2-5 suspicious communications
        comm_count = random.randint(2, 5)
        
        for i in range(comm_count):
            # Select sender and recipient
            sender_id = random.choice(entity_ids)
            recipient_id = random.choice([e for e in entity_ids if e != sender_id])
            
            # Communication date (before trades)
            comm_date = random_datetime_between(
                start_date,
                start_date + timedelta(days=(end_date - start_date).days // 2)
            )
            
            # Generate communication
            comm = self.comm_gen.generate(
                sender_id=sender_id,
                recipient_id=recipient_id,
                force_suspicious=True
            )
            
            # Override date
            comm.timestamp = comm_date
            
            # Add pattern metadata
            comm.metadata["pattern_type"] = pattern_type
            comm.metadata["days_before_announcement"] = (end_date - comm_date).days
            
            communications.append(comm)
            
        return communications
        
    def _generate_pattern_indicators(
        self,
        pattern_type: str,
        trades: List[Any],
        communications: List[Any],
        days_before_announcement: int
    ) -> List[str]:
        """Generate pattern indicators."""
        indicators = [
            "pre_announcement_trading",
            "unusual_trading_volume",
            "timing_suspicious",
            "multiple_insiders_trading",
            "consistent_trade_direction"
        ]
        
        if len(communications) > 0:
            indicators.append("suspicious_communications_before_trades")
            
        if days_before_announcement <= 30:
            indicators.append("trades_within_30_days_of_announcement")
            
        if days_before_announcement <= 7:
            indicators.append("trades_within_7_days_of_announcement")
            
        if len(trades) > 20:
            indicators.append("high_frequency_trading")
            
        if pattern_type == "coordinated_insider_trading":
            indicators.extend([
                "coordinated_trading_pattern",
                "simultaneous_trades",
                "identical_trade_direction"
            ])
            
        if pattern_type == "tipping_pattern":
            indicators.extend([
                "information_sharing_detected",
                "tippee_trading_pattern",
                "communication_trade_correlation"
            ])
            
        return indicators
        
    def _generate_red_flags(
        self,
        pattern_type: str,
        trades: List[Any],
        communications: List[Any],
        entity_count: int
    ) -> List[str]:
        """Generate red flags."""
        red_flags = []
        
        # Calculate average trade value
        if trades:
            avg_value = sum(t.total_value for t in trades) / len(trades)
            if avg_value > 100000:
                red_flags.append("large_trade_values")
            if avg_value > 1000000:
                red_flags.append("very_large_trade_values")
                
        # Multiple entities
        if entity_count >= 5:
            red_flags.append("multiple_insiders_involved")
        if entity_count >= 10:
            red_flags.append("extensive_insider_network")
            
        # Communication patterns
        if len(communications) > 3:
            red_flags.append("frequent_communications")
            
        # Pattern-specific red flags
        if pattern_type == "coordinated_insider_trading":
            red_flags.extend([
                "coordinated_activity",
                "potential_conspiracy"
            ])
            
        if pattern_type == "executive_trading_pattern":
            red_flags.extend([
                "executive_level_involvement",
                "fiduciary_duty_concern"
            ])
            
        return red_flags
        
    def _determine_risk_level(
        self,
        confidence_score: float,
        total_value: Decimal
    ) -> RiskLevel:
        """Determine risk level based on confidence and value."""
        if confidence_score >= 0.8 and total_value > 10000000:
            return RiskLevel.CRITICAL
        elif confidence_score >= 0.7 or total_value > 5000000:
            return RiskLevel.HIGH
        elif confidence_score >= 0.5 or total_value > 1000000:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
            
    def _calculate_severity_score(
        self,
        confidence_score: float,
        total_value: Decimal,
        entity_count: int,
        days_before_announcement: int
    ) -> float:
        """Calculate severity score (0-1)."""
        score = confidence_score * 0.4  # Base from confidence
        
        # Value component
        if total_value > 10000000:
            score += 0.3
        elif total_value > 5000000:
            score += 0.2
        elif total_value > 1000000:
            score += 0.1
            
        # Entity count component
        if entity_count >= 10:
            score += 0.2
        elif entity_count >= 5:
            score += 0.1
            
        # Timing component (closer to announcement = more severe)
        if days_before_announcement <= 7:
            score += 0.1
            
        return min(score, 1.0)
        
    def generate_complex_insider_network(
        self,
        network_size: int = 10,
        trade_count: int = 50,
        days_before_announcement: int = 60
    ) -> Tuple[Pattern, List[Any], List[Any]]:
        """
        Generate a complex insider trading network with multiple layers.
        
        Args:
            network_size: Number of people in network
            trade_count: Total number of trades
            days_before_announcement: Days before announcement
            
        Returns:
            Tuple containing:
            - Pattern object
            - List of generated Trade objects
            - List of generated Communication objects
        """
        return self.generate(
            pattern_type="coordinated_insider_trading",
            entity_count=network_size,
            trade_count=trade_count,
            days_before_announcement=days_before_announcement
        )

