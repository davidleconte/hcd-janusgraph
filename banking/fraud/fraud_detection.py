"""
Fraud Detection Module
Real-time fraud detection using graph analysis and ML

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Created: 2026-01-28
Phase: 7 (Fraud Detection)
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import P

from src.python.utils.embedding_generator import EmbeddingGenerator
from src.python.utils.resilience import CircuitBreaker, CircuitBreakerConfig, retry_with_backoff
from src.python.utils.vector_search import VectorSearchClient

from .models import HIGH_RISK_MERCHANTS, FraudAlert, FraudScore
from .notebook_compat import NotebookCompatMixin

logger = logging.getLogger(__name__)


class FraudDetector(NotebookCompatMixin):
    """
    Real-time fraud detection system.

    Combines multiple detection methods:
    1. Velocity checks (rapid transactions)
    2. Network analysis (fraud rings)
    3. Merchant fraud (compromised merchants)
    4. Behavioral analysis (unusual patterns)
    5. Account takeover detection
    """

    CRITICAL_THRESHOLD = 0.9
    HIGH_THRESHOLD = 0.75
    MEDIUM_THRESHOLD = 0.5
    LOW_THRESHOLD = 0.25
    ANOMALY_THRESHOLD = 0.75

    MAX_TRANSACTIONS_PER_HOUR = 10
    MAX_AMOUNT_PER_HOUR = 5000.0
    MAX_TRANSACTIONS_PER_DAY = 50
    MAX_AMOUNT_PER_DAY = 20000.0
    VELOCITY_WINDOW_HOURS = 24
    MAX_TRANSACTIONS_PER_WINDOW = 50

    HIGH_RISK_MERCHANTS = HIGH_RISK_MERCHANTS

    def __init__(
        self,
        janusgraph_host: str = "localhost",
        janusgraph_port: int = int(os.getenv("JANUSGRAPH_PORT", "18182")),
        opensearch_host: str = "localhost",
        opensearch_port: int = 9200,
        embedding_model: str = "mpnet",
        use_ssl: bool = os.getenv("JANUSGRAPH_USE_SSL", "false").lower() == "true",
    ):
        """Initialize fraud detector."""
        logger.info("Connecting to JanusGraph: %s:%s (SSL: %s)", janusgraph_host, janusgraph_port, use_ssl)
        protocol = "wss" if use_ssl else "ws"
        self.graph_url = f"{protocol}://{janusgraph_host}:{janusgraph_port}/gremlin"

        logger.info("Initializing embedding generator: %s", embedding_model)
        self.generator = EmbeddingGenerator(model_name=embedding_model)

        logger.info("Connecting to OpenSearch: %s:%s", opensearch_host, opensearch_port)
        self.search_client = VectorSearchClient(host=opensearch_host, port=opensearch_port)

        self.fraud_index = "fraud_cases"
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
        if self._breaker.state.value == "open":
            raise ConnectionError("Circuit breaker is open for JanusGraph")
        try:
            self._do_connect()
            self._breaker.record_success()
        except Exception:
            self._breaker.record_failure()
            raise
        logger.info("Connected to JanusGraph at %s", self.graph_url)

    def _do_connect(self):
        """Internal connect, called through circuit breaker."""
        self._connection = DriverRemoteConnection(self.graph_url, "g")
        self._g = traversal().with_remote(self._connection)

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
                "case_id": {"type": "keyword"},
                "transaction_id": {"type": "keyword"},
                "account_id": {"type": "keyword"},
                "fraud_type": {"type": "keyword"},
                "description": {"type": "text"},
                "amount": {"type": "float"},
                "merchant": {"type": "text"},
                "timestamp": {"type": "date"},
                "confirmed": {"type": "boolean"},
            }

            self.search_client.create_vector_index(
                index_name=self.fraud_index,
                vector_dimension=self.generator.dimensions,
                additional_fields=additional_fields,
            )

    def score_transaction(
        self,
        transaction_id: str,
        account_id: str,
        amount: float,
        merchant: str,
        description: str,
        timestamp: Optional[datetime] = None,
    ) -> FraudScore:
        """Calculate fraud risk score for a transaction."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        logger.info("Scoring transaction: %s", transaction_id)

        velocity_score = self._check_velocity(account_id, amount, timestamp)
        network_score = self._check_network(account_id)
        merchant_score = self._check_merchant(merchant)
        behavioral_score = self._check_behavior(account_id, amount, merchant, description)

        overall_score = (
            velocity_score * 0.3
            + network_score * 0.25
            + merchant_score * 0.25
            + behavioral_score * 0.2
        )

        if overall_score >= self.CRITICAL_THRESHOLD:
            risk_level = "critical"
            recommendation = "block"
        elif overall_score >= self.HIGH_THRESHOLD:
            risk_level = "high"
            recommendation = "review"
        elif overall_score >= self.MEDIUM_THRESHOLD:
            risk_level = "medium"
            recommendation = "review"
        else:
            risk_level = "low"
            recommendation = "approve"

        score = FraudScore(
            transaction_id=transaction_id,
            overall_score=overall_score,
            velocity_score=velocity_score,
            network_score=network_score,
            merchant_score=merchant_score,
            behavioral_score=behavioral_score,
            risk_level=risk_level,
            recommendation=recommendation,
        )

        logger.info(
            "Transaction %s: score=%.3f, risk=%s, action=%s",
            transaction_id,
            overall_score,
            risk_level,
            recommendation,
        )

        return score

    def _check_velocity(self, account_id: str, amount: float, timestamp: datetime) -> float:
        """Check transaction velocity (rapid transactions)."""
        try:
            g = self._get_traversal()

            hour_ago = int((timestamp - timedelta(hours=1)).timestamp() * 1000)
            hour_txs = (
                g.V()
                .has("Account", "account_id", account_id)
                .out_e("MADE_TRANSACTION")
                .has("timestamp", P.gte(hour_ago))
                .count()
                .next()
            )

            hour_amount = (
                g.V()
                .has("Account", "account_id", account_id)
                .out_e("MADE_TRANSACTION")
                .has("timestamp", P.gte(hour_ago))
                .values("amount")
                .sum_()
                .next()
            )

            tx_score = min(1.0, hour_txs / self.MAX_TRANSACTIONS_PER_HOUR)
            amount_score = min(1.0, hour_amount / self.MAX_AMOUNT_PER_HOUR)

            return max(tx_score, amount_score)

        except Exception as e:
            logger.error("Error checking velocity: %s", e)
            return 0.0

    def _check_network(self, account_id: str) -> float:
        """Check for fraud network connections."""
        try:
            g = self._get_traversal()

            connection_count = (
                g.V().has("Account", "account_id", account_id).both().dedup().count().next()
            )

            return min(1.0, connection_count / 50.0)

        except Exception as e:
            logger.error("Error checking network: %s", e)
            return 0.0

    def _check_merchant(self, merchant: str) -> float:
        """Check merchant fraud risk."""
        if not merchant:
            return 0.0

        merchant_lower = merchant.lower()
        category_risk = 0.0
        historical_risk = 0.0

        for keyword, risk in self.HIGH_RISK_MERCHANTS.items():
            if keyword in merchant_lower:
                category_risk = max(category_risk, risk)
                logger.debug(
                    "Merchant '%s' matches high-risk keyword '%s' (risk=%s)",
                    merchant,
                    keyword,
                    risk,
                )

        try:
            merchant_embedding = self.generator.encode(merchant)

            results = self.search_client.search(
                index_name=self.fraud_index,
                query_vector=merchant_embedding[0].tolist(),
                k=5,
                filters={"confirmed": True},
            )

            if results:
                similarities = [r.get("_score", 0) for r in results]
                historical_risk = min(0.8, sum(similarities) / len(similarities))
                if historical_risk > 0.3:
                    logger.warning(
                        "Merchant '%s' similar to %s fraud cases", merchant, len(results)
                    )

        except Exception as e:
            logger.debug("Could not query fraud history for merchant: %s", e)

        final_score = category_risk * 0.6 + historical_risk * 0.4

        logger.info(
            "Merchant risk for '%s': category=%.2f, historical=%.2f, final=%.2f",
            merchant,
            category_risk,
            historical_risk,
            final_score,
        )

        return final_score

    def _check_behavior(
        self, account_id: str, amount: float, merchant: str, description: str
    ) -> float:
        """Check for unusual behavioral patterns."""
        amount_risk = 0.0
        merchant_risk = 0.0
        semantic_risk = 0.0

        try:
            g = self._get_traversal()

            ninety_days_ago = int(
                (datetime.now(timezone.utc) - timedelta(days=90)).timestamp() * 1000
            )

            historical_txns = (
                g.V()
                .has("Account", "account_id", account_id)
                .out_e("MADE_TRANSACTION")
                .has("timestamp", P.gte(ninety_days_ago))
                .project("amount", "merchant", "description")
                .by(__.values("amount").fold())
                .by(__.values("merchant").fold())
                .by(__.values("description").fold())
                .toList()
            )
            if not historical_txns:
                logger.debug("No transaction history for account %s", account_id)
                return 0.3

            amounts = []
            merchants = []
            descriptions = []
            for txn in historical_txns:
                amounts.extend(txn.get("amount", []))
                merchants.extend(txn.get("merchant", []))
                descriptions.extend(txn.get("description", []))

            if amounts:
                avg_amount = np.mean(amounts)
                std_amount = np.std(amounts) if len(amounts) > 1 else avg_amount * 0.5

                if std_amount > 0:
                    z_score = abs(amount - avg_amount) / std_amount
                    amount_risk = min(1.0, z_score / 4.0)
                else:
                    amount_risk = 0.5 if amount != avg_amount else 0.0

                logger.debug(
                    "Amount analysis: current=%s, avg=%.2f, std=%.2f, risk=%.2f",
                    amount,
                    avg_amount,
                    std_amount,
                    amount_risk,
                )

            if merchants and merchant:
                merchant_lower = merchant.lower()
                merchant_counts = {}
                for m in merchants:
                    m_lower = m.lower() if m else ""
                    merchant_counts[m_lower] = merchant_counts.get(m_lower, 0) + 1

                total_txns = len(merchants)
                current_merchant_freq = merchant_counts.get(merchant_lower, 0) / total_txns

                if current_merchant_freq == 0:
                    merchant_risk = 0.5
                elif current_merchant_freq < 0.05:
                    merchant_risk = 0.3
                else:
                    merchant_risk = 0.0

                logger.debug(
                    "Merchant analysis: '%s' frequency=%s, risk=%.2f",
                    merchant,
                    current_merchant_freq,
                    merchant_risk,
                )

            if descriptions and description:
                try:
                    current_embedding = self.generator.encode(description)[0]

                    historical_embeddings = self.generator.encode(descriptions[:50])

                    similarities = np.dot(historical_embeddings, current_embedding)
                    max_similarity = np.max(similarities)
                    avg_similarity = np.mean(similarities)

                    if max_similarity < 0.5:
                        semantic_risk = 0.6
                    elif max_similarity < 0.7:
                        semantic_risk = 0.3
                    elif avg_similarity < 0.4:
                        semantic_risk = 0.2
                    else:
                        semantic_risk = 0.0

                    logger.debug(
                        "Semantic analysis: max_sim=%.2f, avg_sim=%.2f, risk=%.2f",
                        max_similarity,
                        avg_similarity,
                        semantic_risk,
                    )

                except Exception as e:
                    logger.debug("Semantic analysis failed: %s", e)

        except Exception as e:
            logger.error("Error checking behavior for account %s: %s", account_id, e)
            return 0.2

        final_score = amount_risk * 0.4 + merchant_risk * 0.3 + semantic_risk * 0.3

        logger.info(
            "Behavioral risk for account %s: amount=%.2f, merchant=%.2f, semantic=%.2f, final=%.2f",
            account_id,
            amount_risk,
            merchant_risk,
            semantic_risk,
            final_score,
        )

        return final_score

    def detect_account_takeover(
        self, account_id: str, recent_transactions: List[Dict]
    ) -> Tuple[bool, float, List[str]]:
        """Detect potential account takeover."""
        indicators = []
        confidence = 0.0

        if len(recent_transactions) > 0:
            recent_amounts = [tx["amount"] for tx in recent_transactions[-10:]]
            if recent_amounts:
                avg_amount = sum(recent_amounts) / len(recent_amounts)
                latest_amount = recent_transactions[-1]["amount"]

                if latest_amount > avg_amount * 3:
                    indicators.append("Unusually large transaction")
                    confidence += 0.3

        is_takeover = confidence > 0.5

        return is_takeover, confidence, indicators

    def find_similar_fraud_cases(self, description: str, amount: float, k: int = 5) -> List[Dict]:
        """Find similar confirmed fraud cases."""
        try:
            embedding = self.generator.encode_for_search(description)

            results = self.search_client.search(
                index_name=self.fraud_index,
                query_embedding=embedding,
                k=k,
                filters={"confirmed": True},
            )

            return [r["source"] for r in results]

        except Exception as e:
            logger.error("Error finding similar cases: %s", e)
            return []

    def generate_alert(
        self, score: FraudScore, transaction_data: Dict[str, Any]
    ) -> Optional[FraudAlert]:
        """Generate fraud alert if score exceeds threshold."""
        if score.overall_score < self.MEDIUM_THRESHOLD:
            return None

        if score.velocity_score > 0.7:
            alert_type = "velocity"
        elif score.network_score > 0.7:
            alert_type = "network"
        elif score.merchant_score > 0.7:
            alert_type = "merchant"
        else:
            alert_type = "behavioral"

        risk_factors = []
        if score.velocity_score > 0.5:
            risk_factors.append(f"High velocity (score: {score.velocity_score:.2f})")
        if score.network_score > 0.5:
            risk_factors.append(f"Suspicious network (score: {score.network_score:.2f})")
        if score.merchant_score > 0.5:
            risk_factors.append(f"Risky merchant (score: {score.merchant_score:.2f})")
        if score.behavioral_score > 0.5:
            risk_factors.append(f"Unusual behavior (score: {score.behavioral_score:.2f})")

        similar_cases = self.find_similar_fraud_cases(
            description=transaction_data.get("description", ""),
            amount=transaction_data.get("amount", 0.0),
            k=3,
        )

        alert = FraudAlert(
            alert_id=f"FRAUD_{score.transaction_id}_{int(datetime.now(timezone.utc).timestamp())}",
            alert_type=alert_type,
            severity=score.risk_level,
            transaction_id=score.transaction_id,
            account_id=transaction_data.get("account_id", ""),
            customer_id=transaction_data.get("customer_id", ""),
            customer_name=transaction_data.get("customer_name", ""),
            amount=transaction_data.get("amount", 0.0),
            merchant=transaction_data.get("merchant", ""),
            fraud_score=score.overall_score,
            risk_factors=risk_factors,
            similar_cases=similar_cases,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=transaction_data,
        )

        logger.warning(
            "🚨 FRAUD ALERT: %s - %s severity, score: %.3f",
            alert.alert_id,
            alert.severity,
            alert.fraud_score,
        )

        return alert
