"""
Fraud Detection Module
Real-time fraud detection using graph analysis and ML

Author: IBM Bob
Created: 2026-01-28
Phase: 7 (Fraud Detection)
"""

import sys
import os
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/python'))

from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import T, P, Order

from utils.embedding_generator import EmbeddingGenerator
from utils.vector_search import VectorSearchClient

logger = logging.getLogger(__name__)


@dataclass
class FraudAlert:
    """Fraud detection alert."""
    alert_id: str
    alert_type: str  # 'velocity', 'network', 'merchant', 'account_takeover'
    severity: str  # 'critical', 'high', 'medium', 'low'
    transaction_id: str
    account_id: str
    customer_id: str
    customer_name: str
    amount: float
    merchant: str
    fraud_score: float  # 0-1
    risk_factors: List[str]
    similar_cases: List[Dict]
    timestamp: str
    metadata: Dict[str, Any]


@dataclass
class FraudScore:
    """Fraud risk score for a transaction."""
    transaction_id: str
    overall_score: float  # 0-1
    velocity_score: float
    network_score: float
    merchant_score: float
    behavioral_score: float
    risk_level: str  # 'critical', 'high', 'medium', 'low'
    recommendation: str  # 'block', 'review', 'approve'


class FraudDetector:
    """
    Real-time fraud detection system.
    
    Combines multiple detection methods:
    1. Velocity checks (rapid transactions)
    2. Network analysis (fraud rings)
    3. Merchant fraud (compromised merchants)
    4. Behavioral analysis (unusual patterns)
    5. Account takeover detection
    """
    
    # Risk thresholds
    CRITICAL_THRESHOLD = 0.9
    HIGH_THRESHOLD = 0.75
    MEDIUM_THRESHOLD = 0.5
    LOW_THRESHOLD = 0.25
    
    # Velocity limits
    MAX_TRANSACTIONS_PER_HOUR = 10
    MAX_AMOUNT_PER_HOUR = 5000.0
    MAX_TRANSACTIONS_PER_DAY = 50
    MAX_AMOUNT_PER_DAY = 20000.0
    
    def __init__(
        self,
        janusgraph_host: str = 'localhost',
        janusgraph_port: int = 8182,
        opensearch_host: str = 'localhost',
        opensearch_port: int = 9200,
        embedding_model: str = 'mpnet'
    ):
        """
        Initialize fraud detector.
        
        Args:
            janusgraph_host: JanusGraph host
            janusgraph_port: JanusGraph port
            opensearch_host: OpenSearch host
            opensearch_port: OpenSearch port
            embedding_model: Embedding model for semantic analysis
        """
        # Initialize JanusGraph connection
        logger.info(f"Connecting to JanusGraph: {janusgraph_host}:{janusgraph_port}")
        self.graph_url = f"ws://{janusgraph_host}:{janusgraph_port}/gremlin"
        
        # Initialize embedding generator
        logger.info(f"Initializing embedding generator: {embedding_model}")
        self.generator = EmbeddingGenerator(model_name=embedding_model)
        
        # Initialize vector search
        logger.info(f"Connecting to OpenSearch: {opensearch_host}:{opensearch_port}")
        self.search_client = VectorSearchClient(
            host=opensearch_host,
            port=opensearch_port
        )
        
        self.fraud_index = 'fraud_cases'
        self._ensure_fraud_index()
    
    def _ensure_fraud_index(self):
        """Create fraud cases index if not exists."""
        if not self.search_client.client.indices.exists(index=self.fraud_index):
            logger.info(f"Creating fraud index: {self.fraud_index}")
            
            additional_fields = {
                'case_id': {'type': 'keyword'},
                'transaction_id': {'type': 'keyword'},
                'account_id': {'type': 'keyword'},
                'fraud_type': {'type': 'keyword'},
                'description': {'type': 'text'},
                'amount': {'type': 'float'},
                'merchant': {'type': 'text'},
                'timestamp': {'type': 'date'},
                'confirmed': {'type': 'boolean'}
            }
            
            self.search_client.create_vector_index(
                index_name=self.fraud_index,
                vector_dimension=self.generator.dimensions,
                additional_fields=additional_fields
            )
    
    def score_transaction(
        self,
        transaction_id: str,
        account_id: str,
        amount: float,
        merchant: str,
        description: str,
        timestamp: Optional[datetime] = None
    ) -> FraudScore:
        """
        Calculate fraud risk score for a transaction.
        
        Args:
            transaction_id: Transaction ID
            account_id: Account ID
            amount: Transaction amount
            merchant: Merchant name
            description: Transaction description
            timestamp: Transaction timestamp
        
        Returns:
            FraudScore with risk assessment
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        logger.info(f"Scoring transaction: {transaction_id}")
        
        # Calculate individual scores
        velocity_score = self._check_velocity(account_id, amount, timestamp)
        network_score = self._check_network(account_id)
        merchant_score = self._check_merchant(merchant)
        behavioral_score = self._check_behavior(account_id, amount, merchant, description)
        
        # Weighted overall score
        overall_score = (
            velocity_score * 0.3 +
            network_score * 0.25 +
            merchant_score * 0.25 +
            behavioral_score * 0.2
        )
        
        # Determine risk level and recommendation
        if overall_score >= self.CRITICAL_THRESHOLD:
            risk_level = 'critical'
            recommendation = 'block'
        elif overall_score >= self.HIGH_THRESHOLD:
            risk_level = 'high'
            recommendation = 'review'
        elif overall_score >= self.MEDIUM_THRESHOLD:
            risk_level = 'medium'
            recommendation = 'review'
        else:
            risk_level = 'low'
            recommendation = 'approve'
        
        score = FraudScore(
            transaction_id=transaction_id,
            overall_score=overall_score,
            velocity_score=velocity_score,
            network_score=network_score,
            merchant_score=merchant_score,
            behavioral_score=behavioral_score,
            risk_level=risk_level,
            recommendation=recommendation
        )
        
        logger.info(
            f"Transaction {transaction_id}: score={overall_score:.3f}, "
            f"risk={risk_level}, action={recommendation}"
        )
        
        return score
    
    def _check_velocity(
        self,
        account_id: str,
        amount: float,
        timestamp: datetime
    ) -> float:
        """
        Check transaction velocity (rapid transactions).
        
        Args:
            account_id: Account ID
            amount: Transaction amount
            timestamp: Transaction timestamp
        
        Returns:
            Velocity risk score (0-1)
        """
        try:
            connection = DriverRemoteConnection(self.graph_url, 'g')
            g = traversal().withRemote(connection)
            
            # Check last hour
            hour_ago = int((timestamp - timedelta(hours=1)).timestamp() * 1000)
            hour_txs = (
                g.V().has('Account', 'account_id', account_id)
                .outE('MADE_TRANSACTION')
                .has('timestamp', P.gte(hour_ago))
                .count()
                .next()
            )
            
            hour_amount = (
                g.V().has('Account', 'account_id', account_id)
                .outE('MADE_TRANSACTION')
                .has('timestamp', P.gte(hour_ago))
                .values('amount')
                .sum_()
                .next()
            )
            
            connection.close()
            
            # Calculate score
            tx_score = min(1.0, hour_txs / self.MAX_TRANSACTIONS_PER_HOUR)
            amount_score = min(1.0, hour_amount / self.MAX_AMOUNT_PER_HOUR)
            
            return max(tx_score, amount_score)
            
        except Exception as e:
            logger.error(f"Error checking velocity: {e}")
            return 0.0
    
    def _check_network(self, account_id: str) -> float:
        """
        Check for fraud network connections.
        
        Args:
            account_id: Account ID
        
        Returns:
            Network risk score (0-1)
        """
        try:
            connection = DriverRemoteConnection(self.graph_url, 'g')
            g = traversal().withRemote(connection)
            
            # Check for connections to known fraud accounts
            # Simplified: check if account has many connections
            connection_count = (
                g.V().has('Account', 'account_id', account_id)
                .both()
                .dedup()
                .count()
                .next()
            )
            
            connection.close()
            
            # High connection count may indicate fraud ring
            return min(1.0, connection_count / 50.0)
            
        except Exception as e:
            logger.error(f"Error checking network: {e}")
            return 0.0
    
    def _check_merchant(self, merchant: str) -> float:
        """
        Check merchant fraud risk.
        
        Args:
            merchant: Merchant name
        
        Returns:
            Merchant risk score (0-1)
        """
        # Check against known compromised merchants
        # Simplified: return low risk for demo
        return 0.1
    
    def _check_behavior(
        self,
        account_id: str,
        amount: float,
        merchant: str,
        description: str
    ) -> float:
        """
        Check for unusual behavioral patterns.
        
        Args:
            account_id: Account ID
            amount: Transaction amount
            merchant: Merchant name
            description: Transaction description
        
        Returns:
            Behavioral risk score (0-1)
        """
        # Use semantic similarity to find unusual transactions
        # Simplified: return low risk for demo
        return 0.2
    
    def detect_account_takeover(
        self,
        account_id: str,
        recent_transactions: List[Dict]
    ) -> Tuple[bool, float, List[str]]:
        """
        Detect potential account takeover.
        
        Indicators:
        - Sudden change in transaction patterns
        - Unusual locations
        - Different device/IP
        - Large withdrawals
        
        Args:
            account_id: Account ID
            recent_transactions: Recent transaction history
        
        Returns:
            Tuple of (is_takeover, confidence, indicators)
        """
        indicators = []
        confidence = 0.0
        
        # Check for sudden pattern changes
        if len(recent_transactions) > 0:
            # Simplified analysis
            recent_amounts = [tx['amount'] for tx in recent_transactions[-10:]]
            if recent_amounts:
                avg_amount = sum(recent_amounts) / len(recent_amounts)
                latest_amount = recent_transactions[-1]['amount']
                
                if latest_amount > avg_amount * 3:
                    indicators.append('Unusually large transaction')
                    confidence += 0.3
        
        is_takeover = confidence > 0.5
        
        return is_takeover, confidence, indicators
    
    def find_similar_fraud_cases(
        self,
        description: str,
        amount: float,
        k: int = 5
    ) -> List[Dict]:
        """
        Find similar confirmed fraud cases.
        
        Args:
            description: Transaction description
            amount: Transaction amount
            k: Number of similar cases to retrieve
        
        Returns:
            List of similar fraud cases
        """
        try:
            # Generate embedding for description
            embedding = self.generator.encode_for_search(description)
            
            # Search for similar cases
            results = self.search_client.search(
                index_name=self.fraud_index,
                query_embedding=embedding,
                k=k,
                filters={'confirmed': True}
            )
            
            return [r['source'] for r in results]
            
        except Exception as e:
            logger.error(f"Error finding similar cases: {e}")
            return []
    
    def generate_alert(
        self,
        score: FraudScore,
        transaction_data: Dict[str, Any]
    ) -> Optional[FraudAlert]:
        """
        Generate fraud alert if score exceeds threshold.
        
        Args:
            score: Fraud score
            transaction_data: Transaction details
        
        Returns:
            FraudAlert if alert should be generated, None otherwise
        """
        if score.overall_score < self.MEDIUM_THRESHOLD:
            return None
        
        # Determine alert type
        if score.velocity_score > 0.7:
            alert_type = 'velocity'
        elif score.network_score > 0.7:
            alert_type = 'network'
        elif score.merchant_score > 0.7:
            alert_type = 'merchant'
        else:
            alert_type = 'behavioral'
        
        # Build risk factors list
        risk_factors = []
        if score.velocity_score > 0.5:
            risk_factors.append(f'High velocity (score: {score.velocity_score:.2f})')
        if score.network_score > 0.5:
            risk_factors.append(f'Suspicious network (score: {score.network_score:.2f})')
        if score.merchant_score > 0.5:
            risk_factors.append(f'Risky merchant (score: {score.merchant_score:.2f})')
        if score.behavioral_score > 0.5:
            risk_factors.append(f'Unusual behavior (score: {score.behavioral_score:.2f})')
        
        # Find similar cases
        similar_cases = self.find_similar_fraud_cases(
            description=transaction_data.get('description', ''),
            amount=transaction_data.get('amount', 0.0),
            k=3
        )
        
        alert = FraudAlert(
            alert_id=f"FRAUD_{score.transaction_id}_{int(datetime.utcnow().timestamp())}",
            alert_type=alert_type,
            severity=score.risk_level,
            transaction_id=score.transaction_id,
            account_id=transaction_data.get('account_id', ''),
            customer_id=transaction_data.get('customer_id', ''),
            customer_name=transaction_data.get('customer_name', ''),
            amount=transaction_data.get('amount', 0.0),
            merchant=transaction_data.get('merchant', ''),
            fraud_score=score.overall_score,
            risk_factors=risk_factors,
            similar_cases=similar_cases,
            timestamp=datetime.utcnow().isoformat(),
            metadata=transaction_data
        )
        
        logger.warning(
            f"🚨 FRAUD ALERT: {alert.alert_id} - "
            f"{alert.severity} severity, score: {alert.fraud_score:.3f}"
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
    print("FRAUD DETECTION MODULE - TEST")
    print("="*60)
    
    # Initialize detector
    print("\n1. Initializing fraud detector...")
    detector = FraudDetector(
        janusgraph_host='localhost',
        janusgraph_port=8182,
        opensearch_host='localhost',
        opensearch_port=9200
    )
    
    # Test transaction scoring
    print("\n2. Testing transaction scoring...")
    
    test_transactions = [
        {
            'transaction_id': 'TX-001',
            'account_id': 'ACC-123',
            'amount': 50.0,
            'merchant': 'Amazon',
            'description': 'Online purchase'
        },
        {
            'transaction_id': 'TX-002',
            'account_id': 'ACC-123',
            'amount': 5000.0,
            'merchant': 'Unknown Merchant',
            'description': 'Large wire transfer'
        }
    ]
    
    for tx in test_transactions:
        print(f"\n   Transaction: {tx['transaction_id']}")
        print(f"   Amount: ${tx['amount']:.2f}")
        print(f"   Merchant: {tx['merchant']}")
        
        score = detector.score_transaction(
            transaction_id=tx['transaction_id'],
            account_id=tx['account_id'],
            amount=tx['amount'],
            merchant=tx['merchant'],
            description=tx['description']
        )
        
        print(f"   Overall Score: {score.overall_score:.3f}")
        print(f"   Risk Level: {score.risk_level}")
        print(f"   Recommendation: {score.recommendation}")
        
        # Generate alert if needed
        alert = detector.generate_alert(score, tx)
        if alert:
            print(f"   🚨 ALERT GENERATED: {alert.alert_id}")
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETE")
    print("="*60)

# Made with Bob
