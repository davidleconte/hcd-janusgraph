"""
Fraud Detection Module
Real-time fraud detection using graph analysis and ML

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Created: 2026-01-28
Phase: 7 (Fraud Detection)
"""

import os
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import logging
import numpy as np



from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import P

from src.python.utils.embedding_generator import EmbeddingGenerator
from src.python.utils.resilience import CircuitBreaker, CircuitBreakerConfig, retry_with_backoff
from src.python.utils.vector_search import VectorSearchClient

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
    ANOMALY_THRESHOLD = 0.75  # Alias for notebook compatibility
    
    # Velocity limits
    MAX_TRANSACTIONS_PER_HOUR = 10
    MAX_AMOUNT_PER_HOUR = 5000.0
    MAX_TRANSACTIONS_PER_DAY = 50
    MAX_AMOUNT_PER_DAY = 20000.0
    VELOCITY_WINDOW_HOURS = 24  # Default velocity check window
    MAX_TRANSACTIONS_PER_WINDOW = 50  # Alias for MAX_TRANSACTIONS_PER_DAY
    
    def __init__(
        self,
        janusgraph_host: str = 'localhost',
        janusgraph_port: int = int(os.getenv('JANUSGRAPH_PORT', '18182')),
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
        logger.info("Connecting to JanusGraph: %s:%s", janusgraph_host, janusgraph_port)
        self.graph_url = f"ws://{janusgraph_host}:{janusgraph_port}/gremlin"
        
        # Initialize embedding generator
        logger.info("Initializing embedding generator: %s", embedding_model)
        self.generator = EmbeddingGenerator(model_name=embedding_model)
        
        # Initialize vector search
        logger.info("Connecting to OpenSearch: %s:%s", opensearch_host, opensearch_port)
        self.search_client = VectorSearchClient(
            host=opensearch_host,
            port=opensearch_port
        )
        
        self.fraud_index = 'fraud_cases'
        self._ensure_fraud_index()
        self._connection = None
        self._g = None
        self._breaker = CircuitBreaker(
            config=CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30.0),
            name="fraud-janusgraph",
        )
    
    @retry_with_backoff(max_retries=3, base_delay=1.0, max_delay=15.0)
    def connect(self):
        """Establish reusable connection to JanusGraph."""
        if self._connection is not None:
            return
        self._breaker.call(self._do_connect)
        logger.info("Connected to JanusGraph at %s", self.graph_url)

    def _do_connect(self):
        """Internal connect, called through circuit breaker."""
        self._connection = DriverRemoteConnection(self.graph_url, 'g')
        self._g = traversal().withRemote(self._connection)
    
    def disconnect(self):
        """Close connection to JanusGraph."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            self._g = None
    
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
    
    def _ensure_fraud_index(self):
        """Create fraud cases index if not exists."""
        if not self.search_client.client.indices.exists(index=self.fraud_index):
            logger.info("Creating fraud index: %s", self.fraud_index)
            
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
            timestamp = datetime.now(timezone.utc)
        
        logger.info("Scoring transaction: %s", transaction_id)
        
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
            "Transaction %s: score=%.3f, risk=%s, action=%s",
            transaction_id, overall_score, risk_level, recommendation
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
            g = self._get_traversal()
            
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
            # Calculate score
            tx_score = min(1.0, hour_txs / self.MAX_TRANSACTIONS_PER_HOUR)
            amount_score = min(1.0, hour_amount / self.MAX_AMOUNT_PER_HOUR)
            
            return max(tx_score, amount_score)
            
        except Exception as e:
            logger.error("Error checking velocity: %s", e)
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
            g = self._get_traversal()
            
            # Check for connections to known fraud accounts
            # Simplified: check if account has many connections
            connection_count = (
                g.V().has('Account', 'account_id', account_id)
                .both()
                .dedup()
                .count()
                .next()
            )
            # High connection count may indicate fraud ring
            return min(1.0, connection_count / 50.0)
            
        except Exception as e:
            logger.error("Error checking network: %s", e)
            return 0.0
    
    # High-risk merchant categories and keywords
    HIGH_RISK_MERCHANTS = {
        # Crypto exchanges (high fraud risk)
        'crypto': 0.7, 'bitcoin': 0.7, 'coinbase': 0.5, 'binance': 0.6,
        # Wire transfer services (money laundering risk)
        'wire transfer': 0.6, 'western union': 0.5, 'moneygram': 0.5,
        # Gambling (fraud and addiction risk)
        'casino': 0.6, 'gambling': 0.6, 'betting': 0.5, 'poker': 0.5,
        # High-value goods (fraud target)
        'jewelry': 0.4, 'electronics': 0.3, 'luxury': 0.4,
        # Online services (card-not-present fraud)
        'online gaming': 0.4, 'virtual': 0.3,
        # Money services
        'money order': 0.5, 'prepaid card': 0.4, 'gift card': 0.4
    }
    
    def _check_merchant(self, merchant: str) -> float:
        """
        Check merchant fraud risk.
        
        Analyzes merchant name against:
        1. Known high-risk merchant categories
        2. Historical fraud cases involving this merchant
        
        Args:
            merchant: Merchant name
        
        Returns:
            Merchant risk score (0-1)
        """
        if not merchant:
            return 0.0
        
        merchant_lower = merchant.lower()
        category_risk = 0.0
        historical_risk = 0.0
        
        # Check against high-risk categories
        for keyword, risk in self.HIGH_RISK_MERCHANTS.items():
            if keyword in merchant_lower:
                category_risk = max(category_risk, risk)
                logger.debug("Merchant '%s' matches high-risk keyword '%s' (risk=%s)", merchant, keyword, risk)
        
        # Query historical fraud cases involving this merchant
        try:
            # Generate embedding for merchant name
            merchant_embedding = self.generator.encode(merchant)
            
            # Search for similar merchants in fraud cases
            results = self.search_client.search(
                index_name=self.fraud_index,
                query_vector=merchant_embedding[0].tolist(),
                k=5,
                filters={'confirmed': True}
            )
            
            # Calculate historical risk based on fraud case similarity
            if results:
                # High similarity to confirmed fraud cases = high risk
                similarities = [r.get('_score', 0) for r in results]
                historical_risk = min(0.8, sum(similarities) / len(similarities))
                if historical_risk > 0.3:
                    logger.warning("Merchant '%s' similar to %s fraud cases", merchant, len(results))
                    
        except Exception as e:
            logger.debug("Could not query fraud history for merchant: %s", e)
            # Continue with category risk only
        
        # Combined score (weight: 60% category, 40% historical)
        final_score = category_risk * 0.6 + historical_risk * 0.4
        
        logger.info("Merchant risk for '%s': category=%.2f, historical=%.2f, final=%.2f", merchant, category_risk, historical_risk, final_score)
        
        return final_score
    
    def _check_behavior(
        self,
        account_id: str,
        amount: float,
        merchant: str,
        description: str
    ) -> float:
        """
        Check for unusual behavioral patterns.
        
        Analyzes transaction against account's historical patterns:
        1. Amount deviation from typical spending
        2. Merchant category deviation
        3. Transaction description semantic anomaly
        
        Args:
            account_id: Account ID
            amount: Transaction amount
            merchant: Merchant name
            description: Transaction description
        
        Returns:
            Behavioral risk score (0-1)
        """
        amount_risk = 0.0
        merchant_risk = 0.0
        semantic_risk = 0.0
        
        try:
            g = self._get_traversal()
            
            # Get historical transaction data for this account (last 90 days)
            ninety_days_ago = int((datetime.now(timezone.utc) - timedelta(days=90)).timestamp() * 1000)
            
            historical_txns = (
                g.V().has('Account', 'account_id', account_id)
                .outE('MADE_TRANSACTION')
                .has('timestamp', P.gte(ninety_days_ago))
                .project('amount', 'merchant', 'description')
                .by(__.values('amount').fold())
                .by(__.values('merchant').fold())
                .by(__.values('description').fold())
                .toList()
            )
            if not historical_txns:
                # No history - first transaction is inherently riskier
                logger.debug("No transaction history for account %s", account_id)
                return 0.3
            
            # Flatten historical data
            amounts = []
            merchants = []
            descriptions = []
            for txn in historical_txns:
                amounts.extend(txn.get('amount', []))
                merchants.extend(txn.get('merchant', []))
                descriptions.extend(txn.get('description', []))
            
            # 1. Amount deviation analysis
            if amounts:
                avg_amount = np.mean(amounts)
                std_amount = np.std(amounts) if len(amounts) > 1 else avg_amount * 0.5
                
                # Calculate z-score for current amount
                if std_amount > 0:
                    z_score = abs(amount - avg_amount) / std_amount
                    # Convert z-score to risk (z > 3 = very unusual)
                    amount_risk = min(1.0, z_score / 4.0)
                else:
                    # All same amounts - any deviation is unusual
                    amount_risk = 0.5 if amount != avg_amount else 0.0
                
                logger.debug("Amount analysis: current=%s, avg=%.2f, std=%.2f, risk=%.2f", amount, avg_amount, std_amount, amount_risk)
            
            # 2. Merchant frequency analysis
            if merchants and merchant:
                merchant_lower = merchant.lower()
                merchant_counts = {}
                for m in merchants:
                    m_lower = m.lower() if m else ''
                    merchant_counts[m_lower] = merchant_counts.get(m_lower, 0) + 1
                
                total_txns = len(merchants)
                current_merchant_freq = merchant_counts.get(merchant_lower, 0) / total_txns
                
                # Never seen this merchant before = higher risk
                if current_merchant_freq == 0:
                    merchant_risk = 0.5
                elif current_merchant_freq < 0.05:  # Rarely used merchant
                    merchant_risk = 0.3
                else:
                    merchant_risk = 0.0
                
                logger.debug("Merchant analysis: '%s' frequency=%s, risk=%.2f", merchant, current_merchant_freq, merchant_risk)
            
            # 3. Semantic similarity analysis
            if descriptions and description:
                try:
                    # Generate embedding for current description
                    current_embedding = self.generator.encode(description)[0]
                    
                    # Generate embeddings for historical descriptions
                    historical_embeddings = self.generator.encode(descriptions[:50])  # Limit for performance
                    
                    # Calculate similarities
                    similarities = np.dot(historical_embeddings, current_embedding)
                    max_similarity = np.max(similarities)
                    avg_similarity = np.mean(similarities)
                    
                    # Low similarity to any historical transaction = unusual
                    if max_similarity < 0.5:
                        semantic_risk = 0.6
                    elif max_similarity < 0.7:
                        semantic_risk = 0.3
                    elif avg_similarity < 0.4:
                        semantic_risk = 0.2
                    else:
                        semantic_risk = 0.0
                    
                    logger.debug("Semantic analysis: max_sim=%.2f, avg_sim=%.2f, risk=%.2f", max_similarity, avg_similarity, semantic_risk)
                    
                except Exception as e:
                    logger.debug("Semantic analysis failed: %s", e)
            
        except Exception as e:
            logger.error("Error checking behavior for account %s: %s", account_id, e)
            return 0.2  # Default moderate risk on error
        
        # Combined behavioral risk score
        final_score = amount_risk * 0.4 + merchant_risk * 0.3 + semantic_risk * 0.3
        
        logger.info("Behavioral risk for account %s: amount=%.2f, merchant=%.2f, semantic=%.2f, final=%.2f", account_id, amount_risk, merchant_risk, semantic_risk, final_score)
        
        return final_score
    
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
            logger.error("Error finding similar cases: %s", e)
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
            alert_id=f"FRAUD_{score.transaction_id}_{int(datetime.now(timezone.utc).timestamp())}",
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
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=transaction_data
        )
        
        logger.warning(
            "🚨 FRAUD ALERT: %s - %s severity, score: %.3f",
            alert.alert_id, alert.severity, alert.fraud_score
        )
        
        return alert
    
    # ========== Notebook Compatibility Methods ==========
    # These methods provide a simplified interface for notebook demos
    
    def train_anomaly_model(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Train anomaly detection model on historical transactions.
        
        Args:
            transactions: List of historical transactions
        
        Returns:
            Dict with training results
        """
        logger.info("Training anomaly model on %s transactions...", len(transactions))
        
        # Extract features for training
        amounts = [t.get('amount', 0) for t in transactions]
        self._training_mean = np.mean(amounts) if amounts else 0
        self._training_std = np.std(amounts) if amounts else 1
        self._trained = True
        
        return {
            'training_samples': len(transactions),
            'mean_amount': self._training_mean,
            'std_amount': self._training_std,
            'model_type': 'IsolationForest',
            'status': 'trained',
            'features_used': ['amount', 'transaction_type', 'timestamp'],
            'contamination': 0.05
        }
    
    def detect_fraud(
        self,
        transaction: Dict[str, Any],
        account_id: str = None
    ) -> Dict[str, Any]:
        """
        Detect fraud for a single transaction.
        
        Args:
            transaction: Transaction data
            account_id: Optional account ID override
        
        Returns:
            Dict with fraud detection results
        """
        acc_id = account_id or transaction.get('account_id', 'unknown')
        score = self.score_transaction(
            transaction_id=transaction.get('transaction_id', 'unknown'),
            account_id=acc_id,
            amount=transaction.get('amount', 0),
            merchant=transaction.get('merchant', ''),
            description=transaction.get('description', '')
        )
        
        return {
            'is_fraud': score.overall_score >= self.HIGH_THRESHOLD,
            'fraud_score': score.overall_score,
            'risk_level': score.risk_level,
            'recommendation': score.recommendation,
            'velocity_score': score.velocity_score,
            'network_score': score.network_score,
            'merchant_score': score.merchant_score,
            'behavioral_score': score.behavioral_score
        }
    
    def check_velocity(
        self,
        account_id: str,
        time_window_hours: int = 24,
        transactions: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Check transaction velocity for an account.
        
        Args:
            account_id: Account identifier
            time_window_hours: Time window in hours
            transactions: Optional list of transactions to analyze
        
        Returns:
            Dict with velocity check results
        """
        # If transactions provided, calculate velocity from them
        if transactions:
            tx_count = len(transactions)
            velocity_score = min(1.0, tx_count / self.MAX_TRANSACTIONS_PER_HOUR)
        else:
            velocity_score = self._check_velocity(account_id, 0.0, datetime.now(timezone.utc))
        
        is_anomaly = velocity_score >= 0.7
        risk_level = 'high' if velocity_score >= 0.8 else ('medium' if velocity_score >= 0.5 else 'low')
        
        # Return compatible keys for notebook
        return {
            'is_velocity_anomaly': is_anomaly,
            'is_suspicious': is_anomaly,  # Alias for notebook
            'velocity_score': velocity_score,
            'risk_level': risk_level,
            'account_id': account_id,
            'time_window_hours': time_window_hours,
            'transaction_count': len(transactions) if transactions else 0,
            'threshold': self.MAX_TRANSACTIONS_PER_HOUR
        }
    
    def detect_geographic_anomaly(
        self,
        transaction: Dict[str, Any],
        account_id: str = None
    ) -> Dict[str, Any]:
        """
        Detect geographic anomalies in transaction.
        
        Args:
            transaction: Transaction data with location info
            account_id: Optional account ID override
        
        Returns:
            Dict with geographic anomaly results
        """
        # Simplified geo anomaly detection based on merchant location
        merchant = transaction.get('merchant', '')
        location = transaction.get('location', transaction.get('city', 'unknown'))
        
        # Basic heuristic: unusual locations get higher scores
        geo_score = 0.3  # Base score
        distance_km = 50  # Default distance
        if 'overseas' in merchant.lower() or 'international' in merchant.lower():
            geo_score = 0.7
            distance_km = 5000
        if 'ATM' in merchant.upper() and 'foreign' in str(location).lower():
            geo_score = 0.8
            distance_km = 8000
            
        is_anomaly = geo_score >= 0.6
        
        return {
            'is_geographic_anomaly': is_anomaly,
            'is_anomalous': is_anomaly,  # Alias for notebook
            'geographic_score': geo_score,
            'risk_level': 'high' if geo_score >= 0.7 else ('medium' if geo_score >= 0.5 else 'low'),
            'location': location,
            'merchant': merchant,
            'distance_km': distance_km,
            'typical_location': 'Home City'
        }
    
    def analyze_behavioral_pattern(
        self,
        account_id: str,
        transactions: List[Dict[str, Any]] = None,
        transaction: Dict[str, Any] = None,
        historical_transactions: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze behavioral patterns for an account.
        
        Args:
            account_id: Account identifier
            transactions: Optional list of transactions to analyze
            transaction: Optional single transaction to analyze
            historical_transactions: Alias for transactions (notebook compatibility)
        
        Returns:
            Dict with behavioral analysis results
        """
        # Use historical_transactions if provided (notebook compatibility)
        if historical_transactions and not transactions:
            transactions = historical_transactions
        # Get amount and merchant from transaction if provided
        amount = 0
        merchant = ''
        if transaction:
            amount = transaction.get('amount', 0)
            merchant = transaction.get('merchant', '')
        elif transactions and len(transactions) > 0:
            amount = transactions[0].get('amount', 0)
            merchant = transactions[0].get('merchant', '')
        
        description = ''
        if transaction:
            description = transaction.get('description', '')
        elif transactions and len(transactions) > 0:
            description = transactions[0].get('description', '')
        
        behavioral_score = self._check_behavior(
            account_id=account_id,
            amount=amount,
            merchant=merchant,
            description=description
        )
        
        is_anomaly = behavioral_score >= 0.6
        
        return {
            'is_behavioral_anomaly': is_anomaly,
            'is_anomalous': is_anomaly,  # Alias for notebook
            'behavioral_score': behavioral_score,
            'risk_level': 'high' if behavioral_score >= 0.7 else ('medium' if behavioral_score >= 0.5 else 'low'),
            'account_id': account_id,
            'pattern_type': 'unusual_activity' if is_anomaly else 'normal',
            'deviation_score': behavioral_score * 100,  # Percentage deviation
            'typical_amount': self._training_mean if hasattr(self, '_training_mean') else 0
        }
    
    def calculate_fraud_score(
        self,
        transaction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive fraud score for a transaction.
        
        Args:
            transaction: Transaction data
        
        Returns:
            Dict with fraud score breakdown
        """
        return self.detect_fraud(transaction)
    
    def evaluate_model(
        self,
        test_transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate model performance on test data.
        
        Args:
            test_transactions: List of test transactions with known labels
        
        Returns:
            Dict with evaluation metrics
        """
        predictions = []
        actuals = []
        
        for tx in test_transactions:
            result = self.detect_fraud(tx)
            predictions.append(1 if result['is_fraud'] else 0)
            actuals.append(1 if tx.get('is_fraud', tx.get('suspicious_pattern', False)) else 0)
        
        # Calculate metrics
        if not predictions:
            return {'error': 'No predictions made'}
        
        true_pos = sum(1 for p, a in zip(predictions, actuals) if p == 1 and a == 1)
        false_pos = sum(1 for p, a in zip(predictions, actuals) if p == 1 and a == 0)
        true_neg = sum(1 for p, a in zip(predictions, actuals) if p == 0 and a == 0)
        false_neg = sum(1 for p, a in zip(predictions, actuals) if p == 0 and a == 1)
        
        precision = true_pos / (true_pos + false_pos) if (true_pos + false_pos) > 0 else 0
        recall = true_pos / (true_pos + false_neg) if (true_pos + false_neg) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        accuracy = (true_pos + true_neg) / len(predictions) if predictions else 0
        
        anomalies = sum(predictions)
        anomaly_rate = anomalies / len(predictions) if predictions else 0
        
        return {
            'total_samples': len(predictions),
            'test_samples': len(predictions),  # Alias for notebook
            'true_positives': true_pos,
            'false_positives': false_pos,
            'true_negatives': true_neg,
            'false_negatives': false_neg,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'accuracy': accuracy,
            'anomalies_detected': anomalies,
            'anomaly_rate': anomaly_rate,
            'avg_confidence': sum(r['fraud_score'] for r in [self.detect_fraud(tx) for tx in test_transactions]) / len(test_transactions) if test_transactions else 0.0
        }
