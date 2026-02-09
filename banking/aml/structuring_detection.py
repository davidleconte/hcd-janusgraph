"""
AML Structuring Detection Module
Detects structuring (smurfing) patterns in financial transactions

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Created: 2026-01-28
Phase: Week 1 Remediation (CRITICAL-001)
"""

import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging



from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import T, P

logger = logging.getLogger(__name__)


@dataclass
class StructuringPattern:
    """Represents a detected structuring pattern."""
    pattern_id: str
    pattern_type: str  # 'smurfing', 'layering', 'integration'
    account_ids: List[str]
    transaction_ids: List[str]
    total_amount: Decimal
    transaction_count: int
    time_window_hours: float
    confidence_score: float  # 0-1
    risk_level: str  # 'critical', 'high', 'medium', 'low'
    indicators: List[str]
    detected_at: str
    metadata: Dict[str, Any]


@dataclass
class StructuringAlert:
    """Alert for detected structuring activity."""
    alert_id: str
    alert_type: str
    severity: str
    patterns: List[StructuringPattern]
    accounts_involved: List[str]
    total_amount: Decimal
    recommendation: str
    timestamp: str


class StructuringDetector:
    """
    Detects structuring (smurfing) patterns in financial transactions.
    
    Structuring is the practice of breaking up large transactions into
    smaller amounts to avoid reporting thresholds (e.g., $10,000 CTR threshold).
    
    Detection Methods:
    1. Velocity Analysis: Multiple transactions just below threshold
    2. Pattern Recognition: Regular amounts, timing patterns
    3. Network Analysis: Coordinated activity across accounts
    4. Behavioral Analysis: Deviation from normal patterns
    """
    
    # Regulatory thresholds
    CTR_THRESHOLD = Decimal('10000.00')  # Currency Transaction Report threshold
    SUSPICIOUS_THRESHOLD = Decimal('9000.00')  # Just below CTR
    
    # Detection parameters
    MAX_TIME_WINDOW_HOURS = 24
    MIN_TRANSACTIONS_FOR_PATTERN = 3
    HIGH_CONFIDENCE_THRESHOLD = 0.85
    MEDIUM_CONFIDENCE_THRESHOLD = 0.70
    
    def __init__(
        self,
        janusgraph_host: str = 'localhost',
        janusgraph_port: int = int(os.getenv('JANUSGRAPH_PORT', '18182')),
        ctr_threshold: Optional[Decimal] = None
    ):
        """
        Initialize structuring detector.
        
        Args:
            janusgraph_host: JanusGraph host
            janusgraph_port: JanusGraph port
            ctr_threshold: Custom CTR threshold (default: $10,000)
        """
        self.graph_url = f"ws://{janusgraph_host}:{janusgraph_port}/gremlin"
        self.ctr_threshold = ctr_threshold or self.CTR_THRESHOLD
        self.suspicious_threshold = self.ctr_threshold * Decimal('0.9')
        self._connection = None
        self._g = None
        
        logger.info("Initialized StructuringDetector: threshold=$%s", self.ctr_threshold)
    
    def connect(self):
        """Establish reusable connection to JanusGraph."""
        if self._connection is not None:
            return
        self._connection = DriverRemoteConnection(self.graph_url, 'g')
        self._g = traversal().withRemote(self._connection)
        logger.info("Connected to JanusGraph at %s", self.graph_url)
    
    def disconnect(self):
        """Close connection to JanusGraph."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            self._g = None
            logger.info("Disconnected from JanusGraph")
    
    def _get_traversal(self):
        """Get graph traversal, connecting if needed."""
        if self._g is None:
            self.connect()
        return self._g
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
    
    def detect_smurfing(
        self,
        account_id: str,
        time_window_hours: int = 24,
        min_transactions: int = 3
    ) -> List[StructuringPattern]:
        """
        Detect smurfing patterns for a specific account.
        
        Smurfing: Multiple small transactions just below reporting threshold
        within a short time window.
        
        Args:
            account_id: Account ID to analyze
            time_window_hours: Time window for analysis
            min_transactions: Minimum transactions to constitute a pattern
        
        Returns:
            List of detected structuring patterns
        """
        logger.info("Analyzing account %s for smurfing patterns...", account_id)
        
        try:
            g = self._get_traversal()
            
            # Get recent transactions just below threshold
            cutoff_time = int((datetime.now(timezone.utc) - timedelta(hours=time_window_hours)).timestamp() * 1000)
            
            transactions = (
                g.V().has('Account', 'account_id', account_id)
                .outE('MADE_TRANSACTION')
                .has('timestamp', P.gte(cutoff_time))
                .has('amount', P.between(float(self.suspicious_threshold), float(self.ctr_threshold)))
                .project('id', 'amount', 'timestamp', 'to_account')
                .by(T.id)
                .by('amount')
                .by('timestamp')
                .by(__.inV().values('account_id'))
                .toList()
            )
            if len(transactions) < min_transactions:
                logger.info("No smurfing pattern detected (only %s transactions)", len(transactions))
                return []
            
            # Analyze pattern
            pattern = self._analyze_smurfing_pattern(
                account_id, transactions, time_window_hours
            )
            
            if pattern:
                logger.warning("⚠️  SMURFING DETECTED: %s transactions, "
                             f"total $%s", len(transactions), pattern.total_amount)
                return [pattern]
            
            return []
            
        except Exception as e:
            logger.error("Error detecting smurfing: %s", e)
            return []
    
    def detect_layering(
        self,
        account_ids: List[str],
        time_window_hours: int = 48
    ) -> List[StructuringPattern]:
        """
        Detect layering patterns across multiple accounts.
        
        Layering: Complex series of transactions to obscure the money trail.
        
        Args:
            account_ids: List of account IDs to analyze
            time_window_hours: Time window for analysis
        
        Returns:
            List of detected layering patterns
        """
        logger.info("Analyzing %s accounts for layering patterns...", len(account_ids))
        
        try:
            g = self._get_traversal()
            
            cutoff_time = int((datetime.now(timezone.utc) - timedelta(hours=time_window_hours)).timestamp() * 1000)
            
            # Find circular transaction patterns
            patterns = []
            for account_id in account_ids:
                # Check for rapid back-and-forth transactions
                circular_txs = (
                    g.V().has('Account', 'account_id', account_id)
                    .outE('MADE_TRANSACTION')
                    .has('timestamp', P.gte(cutoff_time))
                    .as_('tx1')
                    .inV()
                    .outE('MADE_TRANSACTION')
                    .has('timestamp', P.gte(cutoff_time))
                    .where(__.inV().has('account_id', account_id))
                    .select('tx1')
                    .project('id', 'amount', 'timestamp')
                    .by(T.id)
                    .by('amount')
                    .by('timestamp')
                    .toList()
                )
                
                if len(circular_txs) >= 2:
                    pattern = self._analyze_layering_pattern(
                        account_id, circular_txs, time_window_hours
                    )
                    if pattern:
                        patterns.append(pattern)
            if patterns:
                logger.warning("⚠️  LAYERING DETECTED: %s patterns found", len(patterns))
            
            return patterns
            
        except Exception as e:
            logger.error("Error detecting layering: %s", e)
            return []
    
    def detect_network_structuring(
        self,
        seed_account_id: str,
        max_hops: int = 3,
        time_window_hours: int = 24
    ) -> List[StructuringPattern]:
        """
        Detect coordinated structuring across a network of accounts.
        
        Args:
            seed_account_id: Starting account for network analysis
            max_hops: Maximum hops in the network
            time_window_hours: Time window for analysis
        
        Returns:
            List of detected network structuring patterns
        """
        logger.info("Analyzing network structuring from account %s...", seed_account_id)
        
        try:
            g = self._get_traversal()
            
            cutoff_time = int((datetime.now(timezone.utc) - timedelta(hours=time_window_hours)).timestamp() * 1000)
            
            # Find connected accounts with suspicious transactions
            network_accounts = (
                g.V().has('Account', 'account_id', seed_account_id)
                .repeat(__.both('MADE_TRANSACTION', 'RECEIVED_TRANSACTION').simplePath())
                .times(max_hops)
                .dedup()
                .values('account_id')
                .toList()
            )
            
            if len(network_accounts) < 3:
                return []
            
            # Check for coordinated suspicious transactions
            suspicious_txs = []
            for account_id in network_accounts:
                txs = (
                    g.V().has('Account', 'account_id', account_id)
                    .outE('MADE_TRANSACTION')
                    .has('timestamp', P.gte(cutoff_time))
                    .has('amount', P.between(float(self.suspicious_threshold), float(self.ctr_threshold)))
                    .project('id', 'amount', 'timestamp', 'account')
                    .by(T.id)
                    .by('amount')
                    .by('timestamp')
                    .by(__.outV().values('account_id'))
                    .toList()
                )
                suspicious_txs.extend(txs)
            if len(suspicious_txs) >= self.MIN_TRANSACTIONS_FOR_PATTERN * len(network_accounts) / 2:
                pattern = self._analyze_network_pattern(
                    network_accounts, suspicious_txs, time_window_hours
                )
                if pattern:
                    logger.warning("⚠️  NETWORK STRUCTURING DETECTED: %s accounts, "
                                 f"%s transactions", len(network_accounts), len(suspicious_txs))
                    return [pattern]
            
            return []
            
        except Exception as e:
            logger.error("Error detecting network structuring: %s", e)
            return []
    
    def _analyze_smurfing_pattern(
        self,
        account_id: str,
        transactions: List[Dict],
        time_window_hours: int
    ) -> Optional[StructuringPattern]:
        """Analyze transactions for smurfing pattern."""
        if not transactions:
            return None
        
        # Calculate metrics
        amounts = [Decimal(str(tx['amount'])) for tx in transactions]
        total_amount: Decimal = sum(amounts)  # type: ignore
        avg_amount: Decimal = total_amount / Decimal(str(len(amounts)))
        
        # Calculate confidence score
        indicators = []
        confidence = 0.0
        
        # Indicator 1: Multiple transactions just below threshold
        below_threshold_count = sum(1 for amt in amounts if amt < self.ctr_threshold)
        if below_threshold_count >= len(amounts) * 0.8:
            indicators.append(f"{below_threshold_count} transactions just below ${self.ctr_threshold}")
            confidence += 0.3
        
        # Indicator 2: Similar amounts (low variance)
        amount_variance: Decimal = sum((amt - avg_amount) ** 2 for amt in amounts) / Decimal(str(len(amounts)))  # type: ignore
        threshold_variance: Decimal = (avg_amount * Decimal('0.1')) ** 2
        if amount_variance < threshold_variance:
            indicators.append("Similar transaction amounts (low variance)")
            confidence += 0.25
        
        # Indicator 3: Short time window
        if time_window_hours <= 12:
            indicators.append(f"Rapid transactions within {time_window_hours} hours")
            confidence += 0.25
        
        # Indicator 4: Total amount significantly exceeds threshold
        if total_amount > self.ctr_threshold * 2:
            indicators.append(f"Total amount ${total_amount} exceeds threshold")
            confidence += 0.2
        
        # Determine risk level
        if confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
            risk_level = 'critical'
        elif confidence >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            risk_level = 'high'
        else:
            risk_level = 'medium'
        
        return StructuringPattern(
            pattern_id=f"SMURF_{account_id}_{int(datetime.now(timezone.utc).timestamp())}",
            pattern_type='smurfing',
            account_ids=[account_id],
            transaction_ids=[str(tx['id']) for tx in transactions],
            total_amount=total_amount if total_amount else Decimal('0'),
            transaction_count=len(transactions),
            time_window_hours=time_window_hours,
            confidence_score=confidence,
            risk_level=risk_level,
            indicators=indicators,
            detected_at=datetime.now(timezone.utc).isoformat(),
            metadata={
                'avg_amount': float(avg_amount),
                'threshold': float(self.ctr_threshold),
                'variance': float(amount_variance)
            }
        )
    
    def _analyze_layering_pattern(
        self,
        account_id: str,
        transactions: List[Dict],
        time_window_hours: int
    ) -> Optional[StructuringPattern]:
        """Analyze transactions for layering pattern."""
        if len(transactions) < 2:
            return None
        
        total_amount = sum(Decimal(str(tx['amount'])) for tx in transactions)
        
        indicators = [
            "Circular transaction pattern detected",
            f"{len(transactions)} back-and-forth transactions",
            f"Total amount: ${total_amount}"
        ]
        
        confidence = 0.7 + (len(transactions) * 0.05)  # Higher confidence with more transactions
        confidence = min(confidence, 1.0)
        
        return StructuringPattern(
            pattern_id=f"LAYER_{account_id}_{int(datetime.now(timezone.utc).timestamp())}",
            pattern_type='layering',
            account_ids=[account_id],
            transaction_ids=[str(tx['id']) for tx in transactions],
            total_amount=total_amount if total_amount else Decimal('0'),
            transaction_count=len(transactions),
            time_window_hours=time_window_hours,
            confidence_score=confidence,
            risk_level='high' if confidence >= 0.8 else 'medium',
            indicators=indicators,
            detected_at=datetime.now(timezone.utc).isoformat(),
            metadata={'circular_pattern': True}
        )
    
    def _analyze_network_pattern(
        self,
        account_ids: List[str],
        transactions: List[Dict],
        time_window_hours: int
    ) -> Optional[StructuringPattern]:
        """Analyze transactions for network structuring pattern."""
        if not transactions:
            return None
        
        total_amount = sum(Decimal(str(tx['amount'])) for tx in transactions)
        
        indicators = [
            f"Coordinated activity across {len(account_ids)} accounts",
            f"{len(transactions)} suspicious transactions",
            f"Total amount: ${total_amount}"
        ]
        
        confidence = 0.75 + (len(account_ids) * 0.03)
        confidence = min(confidence, 1.0)
        
        return StructuringPattern(
            pattern_id=f"NETWORK_{int(datetime.now(timezone.utc).timestamp())}",
            pattern_type='network_structuring',
            account_ids=account_ids,
            transaction_ids=[str(tx['id']) for tx in transactions],
            total_amount=total_amount if total_amount else Decimal('0'),
            transaction_count=len(transactions),
            time_window_hours=time_window_hours,
            confidence_score=confidence,
            risk_level='critical' if confidence >= 0.85 else 'high',
            indicators=indicators,
            detected_at=datetime.now(timezone.utc).isoformat(),
            metadata={'network_size': len(account_ids)}
        )
    
    def generate_alert(
        self,
        patterns: List[StructuringPattern]
    ) -> Optional[StructuringAlert]:
        """
        Generate alert from detected patterns.
        
        Args:
            patterns: List of detected patterns
        
        Returns:
            StructuringAlert if patterns warrant an alert
        """
        if not patterns:
            return None
        
        # Aggregate information
        all_accounts = list(set(acc for p in patterns for acc in p.account_ids))
        total_amount = sum(p.total_amount for p in patterns)
        
        # Determine severity
        max_confidence = max(p.confidence_score for p in patterns)
        if max_confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
            severity = 'critical'
            recommendation = 'File SAR immediately and freeze accounts'
        elif max_confidence >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            severity = 'high'
            recommendation = 'Investigate immediately and prepare SAR'
        else:
            severity = 'medium'
            recommendation = 'Monitor closely and gather additional evidence'
        
        alert = StructuringAlert(
            alert_id=f"STRUCT_ALERT_{int(datetime.now(timezone.utc).timestamp())}",
            alert_type='structuring',
            severity=severity,
            patterns=patterns,
            accounts_involved=all_accounts,
            total_amount=total_amount if total_amount else Decimal('0'),
            recommendation=recommendation,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        logger.warning(
            f"🚨 STRUCTURING ALERT: {alert.alert_id} - "
            f"{severity} severity, {len(patterns)} patterns, "
            f"{len(all_accounts)} accounts, ${total_amount}"
        )
        
        return alert


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("STRUCTURING DETECTION MODULE - TEST")
    print("="*60)
    
    # Initialize detector
    print("\n1. Initializing structuring detector...")
    detector = StructuringDetector(
        janusgraph_host='localhost',
        janusgraph_port=18182
    )
    
    # Test smurfing detection
    print("\n2. Testing smurfing detection...")
    test_account = "ACC-12345"
    patterns = detector.detect_smurfing(
        account_id=test_account,
        time_window_hours=24,
        min_transactions=3
    )
    
    if patterns:
        print(f"   ⚠️  Detected {len(patterns)} smurfing pattern(s)")
        for pattern in patterns:
            print(f"      - Pattern ID: {pattern.pattern_id}")
            print(f"      - Confidence: {pattern.confidence_score:.2f}")
            print(f"      - Risk Level: {pattern.risk_level}")
            print(f"      - Total Amount: ${pattern.total_amount}")
    else:
        print("   ✅ No smurfing patterns detected")
    
    # Test network structuring
    print("\n3. Testing network structuring detection...")
    network_patterns = detector.detect_network_structuring(
        seed_account_id=test_account,
        max_hops=3,
        time_window_hours=24
    )
    
    if network_patterns:
        print(f"   ⚠️  Detected {len(network_patterns)} network pattern(s)")
    else:
        print("   ✅ No network structuring detected")
    
    # Generate alert if patterns found
    all_patterns = patterns + network_patterns
    if all_patterns:
        print("\n4. Generating alert...")
        alert = detector.generate_alert(all_patterns)
        if alert:
            print(f"   🚨 ALERT: {alert.alert_id}")
            print(f"      Severity: {alert.severity}")
            print(f"      Accounts: {len(alert.accounts_involved)}")
            print(f"      Recommendation: {alert.recommendation}")
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETE")
    print("="*60)

# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS | +33614126117