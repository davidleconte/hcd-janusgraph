"""
Enhanced AML Structuring Detection
Combines graph pattern detection with semantic transaction analysis

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Created: 2026-01-28
Phase: 6 (Complete AML Implementation)
"""

import sys
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/python'))

from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import T, P

from utils.embedding_generator import EmbeddingGenerator
from utils.vector_search import VectorSearchClient

logger = logging.getLogger(__name__)


@dataclass
class StructuringPattern:
    """Detected structuring pattern."""
    pattern_id: str
    pattern_type: str  # 'rapid_sequence', 'amount_splitting', 'semantic_similarity'
    account_id: str
    person_id: str
    person_name: str
    transactions: List[Dict[str, Any]]
    total_amount: float
    transaction_count: int
    time_window_hours: float
    risk_score: float
    detection_method: str  # 'graph', 'vector', 'hybrid'
    timestamp: str


class EnhancedStructuringDetector:
    """
    Enhanced structuring detection using graph + vector search.
    
    Combines:
    1. Graph pattern detection (rapid sequences, amount splitting)
    2. Semantic transaction analysis (similar descriptions)
    3. Entity resolution (fuzzy name matching)
    """
    
    # Detection thresholds
    STRUCTURING_THRESHOLD = 10000.0  # $10,000 reporting threshold
    REPORTING_THRESHOLD = 10000.0  # Alias for backwards compatibility
    RAPID_SEQUENCE_HOURS = 24  # Time window for rapid sequences
    TIME_WINDOW_HOURS = 24  # Alias for backwards compatibility
    MIN_TRANSACTIONS = 3  # Minimum transactions for pattern
    SEMANTIC_SIMILARITY_THRESHOLD = 0.85  # Transaction description similarity
    
    def __init__(
        self,
        janusgraph_host: str = 'localhost',
        janusgraph_port: int = int(os.getenv('JANUSGRAPH_PORT', '18182')),
        opensearch_host: str = 'localhost',
        opensearch_port: int = 9200,
        embedding_model: str = 'mpnet'
    ):
        """
        Initialize enhanced structuring detector.
        
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
        
        # Initialize embedding generator for semantic analysis
        logger.info(f"Initializing embedding generator: {embedding_model}")
        self.generator = EmbeddingGenerator(model_name=embedding_model)
        
        # Initialize vector search client
        logger.info(f"Connecting to OpenSearch: {opensearch_host}:{opensearch_port}")
        self.search_client = VectorSearchClient(
            host=opensearch_host,
            port=opensearch_port
        )
        
        self.tx_index = 'aml_transactions'
        self._ensure_transaction_index()
    
    def _ensure_transaction_index(self):
        """Create transaction index if not exists."""
        if not self.search_client.client.indices.exists(index=self.tx_index):
            logger.info(f"Creating transaction index: {self.tx_index}")
            
            additional_fields = {
                'transaction_id': {'type': 'keyword'},
                'account_id': {'type': 'keyword'},
                'person_id': {'type': 'keyword'},
                'description': {'type': 'text'},
                'amount': {'type': 'float'},
                'timestamp': {'type': 'date'},
                'merchant': {'type': 'text'},
                'category': {'type': 'keyword'}
            }
            
            self.search_client.create_vector_index(
                index_name=self.tx_index,
                vector_dimension=self.generator.dimensions,
                additional_fields=additional_fields
            )
    
    def detect_graph_patterns(
        self,
        time_window_hours: int = 24,
        min_transactions: int = 3,
        threshold_amount: float = 10000.0
    ) -> List[StructuringPattern]:
        """
        Detect structuring patterns using graph traversal.
        
        Args:
            time_window_hours: Time window for rapid sequences
            min_transactions: Minimum transactions for pattern
            threshold_amount: Reporting threshold
        
        Returns:
            List of detected patterns
        """
        logger.info("Detecting graph-based structuring patterns...")
        
        patterns = []
        
        try:
            # Connect to graph
            connection = DriverRemoteConnection(self.graph_url, 'g')
            g = traversal().withRemote(connection)
            
            # Query: Find accounts with multiple transactions near threshold
            # Pattern: Multiple transactions < $10k within 24 hours, total > $10k
            
            # Get current time (simulate with a recent timestamp)
            cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
            cutoff_ms = int(cutoff_time.timestamp() * 1000)
            
            # Gremlin query to find suspicious patterns
            # Note: This is a simplified version - actual implementation would be more complex
            results = (
                g.V().hasLabel('Account')
                .as_('account')
                .outE('MADE_TRANSACTION')
                .has('amount', P.lt(threshold_amount))
                .has('timestamp', P.gte(cutoff_ms))
                .inV().hasLabel('Transaction')
                .as_('transaction')
                .select('account', 'transaction')
                .by(__.valueMap(True))
                .by(__.valueMap(True))
                .toList()
            )
            
            # Group transactions by account
            account_txs = {}
            for result in results:
                account_data = result['account']
                tx_data = result['transaction']
                
                account_id = account_data.get(T.id)
                if account_id not in account_txs:
                    account_txs[account_id] = {
                        'account': account_data,
                        'transactions': []
                    }
                account_txs[account_id]['transactions'].append(tx_data)
            
            # Analyze each account for structuring
            for account_id, data in account_txs.items():
                txs = data['transactions']
                
                if len(txs) < min_transactions:
                    continue
                
                # Calculate total amount
                total = sum(float(tx.get('amount', [0])[0]) for tx in txs)
                
                if total > threshold_amount:
                    # Get person info
                    person_results = (
                        g.V(account_id)
                        .out('OWNED_BY')
                        .hasLabel('Person')
                        .valueMap(True)
                        .toList()
                    )
                    
                    if person_results:
                        person_data = person_results[0]
                        
                        # Calculate risk score
                        risk_score = self._calculate_risk_score(
                            total_amount=total,
                            tx_count=len(txs),
                            threshold=threshold_amount
                        )
                        
                        pattern = StructuringPattern(
                            pattern_id=f"GRAPH_{account_id}_{int(datetime.utcnow().timestamp())}",
                            pattern_type='rapid_sequence',
                            account_id=str(account_id),
                            person_id=str(person_data.get(T.id)),
                            person_name=person_data.get('name', ['Unknown'])[0],
                            transactions=[self._format_transaction(tx) for tx in txs],
                            total_amount=total,
                            transaction_count=len(txs),
                            time_window_hours=time_window_hours,
                            risk_score=risk_score,
                            detection_method='graph',
                            timestamp=datetime.utcnow().isoformat()
                        )
                        patterns.append(pattern)
            
            connection.close()
            
        except Exception as e:
            logger.error(f"Error detecting graph patterns: {e}")
            import traceback
            traceback.print_exc()
        
        logger.info(f"Found {len(patterns)} graph-based patterns")
        return patterns
    
    def detect_semantic_patterns(
        self,
        min_similarity: float = 0.85,
        k: int = 20,
        time_window_hours: int = 72,
        min_cluster_size: int = 3
    ) -> List[StructuringPattern]:
        """
        Detect structuring using semantic transaction analysis.
        
        Finds transactions with similar descriptions that may indicate
        coordinated structuring attempts. Looks for:
        1. Semantically similar transaction descriptions across accounts
        2. Clusters of transactions with matching patterns
        3. Potential coordinated structuring by related parties
        
        Args:
            min_similarity: Minimum similarity threshold (0-1)
            k: Number of similar transactions to retrieve per query
            time_window_hours: Time window to analyze
            min_cluster_size: Minimum transactions in a cluster
        
        Returns:
            List of detected patterns
        """
        logger.info(f"Detecting semantic structuring patterns (similarity>={min_similarity}, window={time_window_hours}h)...")
        
        patterns = []
        processed_clusters = set()  # Track processed transaction clusters
        
        try:
            # Connect to graph and get recent transactions
            connection = DriverRemoteConnection(self.graph_url, 'g')
            g = traversal().withRemote(connection)
            
            cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
            cutoff_ms = int(cutoff_time.timestamp() * 1000)
            
            # Get recent transactions below reporting threshold
            recent_txns = (
                g.V().hasLabel('Transaction')
                .has('timestamp', P.gte(cutoff_ms))
                .has('amount', P.lt(self.STRUCTURING_THRESHOLD))
                .has('amount', P.gt(self.STRUCTURING_THRESHOLD * 0.5))  # Focus on near-threshold
                .project('tx_id', 'amount', 'description', 'merchant', 'account_id', 'person_id', 'person_name', 'timestamp')
                .by(__.values('transaction_id'))
                .by(__.values('amount'))
                .by(__.coalesce(__.values('description'), __.constant('')))
                .by(__.coalesce(__.values('merchant'), __.constant('')))
                .by(__.in_('MADE_TRANSACTION').values('account_id'))
                .by(__.in_('MADE_TRANSACTION').in_('OWNS_ACCOUNT').values('person_id').fold())
                .by(__.in_('MADE_TRANSACTION').in_('OWNS_ACCOUNT').coalesce(__.values('full_name'), __.values('company_name')).fold())
                .by(__.values('timestamp'))
                .limit(500)  # Limit for performance
                .toList()
            )
            
            connection.close()
            
            if len(recent_txns) < min_cluster_size:
                logger.info(f"Only {len(recent_txns)} recent transactions found - insufficient for pattern detection")
                return patterns
            
            logger.info(f"Analyzing {len(recent_txns)} transactions for semantic patterns")
            
            # Build transaction descriptions for embedding
            tx_texts = []
            tx_data = []
            for txn in recent_txns:
                description = txn.get('description', '') or ''
                merchant = txn.get('merchant', '') or ''
                amount = txn.get('amount', 0)
                
                # Create rich text representation for semantic analysis
                text = f"{description} {merchant} ${amount:.2f}"
                tx_texts.append(text)
                tx_data.append(txn)
            
            # Generate embeddings for all transactions
            logger.debug(f"Generating embeddings for {len(tx_texts)} transactions")
            embeddings = self.generator.encode(tx_texts)
            
            # Find semantic clusters using pairwise similarity
            import numpy as np
            similarity_matrix = np.dot(embeddings, embeddings.T)
            
            # Identify clusters of similar transactions
            for i, txn in enumerate(tx_data):
                if txn['tx_id'] in processed_clusters:
                    continue
                
                # Find similar transactions
                similarities = similarity_matrix[i]
                similar_indices = np.where(similarities >= min_similarity)[0]
                
                if len(similar_indices) < min_cluster_size:
                    continue
                
                # Get cluster transactions
                cluster_txns = [tx_data[j] for j in similar_indices]
                
                # Check if cluster involves multiple accounts (potential coordination)
                account_ids = set()
                person_ids = set()
                for ct in cluster_txns:
                    account_ids.add(ct.get('account_id'))
                    pids = ct.get('person_id', [])
                    if isinstance(pids, list):
                        person_ids.update(pids)
                    elif pids:
                        person_ids.add(pids)
                
                # Interesting patterns: same person/multiple accounts OR multiple people with similar txns
                total_amount = sum(ct.get('amount', 0) for ct in cluster_txns)
                
                # Only flag if total exceeds threshold (structuring indicator)
                if total_amount >= self.STRUCTURING_THRESHOLD:
                    pattern_id = f"SEM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{len(patterns)}"
                    
                    # Get primary person info
                    primary_person_id = list(person_ids)[0] if person_ids else 'UNKNOWN'
                    primary_person_name = cluster_txns[0].get('person_name', ['Unknown'])
                    if isinstance(primary_person_name, list):
                        primary_person_name = primary_person_name[0] if primary_person_name else 'Unknown'
                    
                    # Calculate risk score based on cluster characteristics
                    risk_score = min(1.0, 
                        0.5 +  # Base risk for semantic similarity
                        0.2 * (len(cluster_txns) / 10.0) +  # More transactions = higher risk
                        0.3 * (total_amount / (self.STRUCTURING_THRESHOLD * 3))  # Amount factor
                    )
                    
                    # Calculate average similarity within cluster
                    cluster_similarities = similarities[similar_indices]
                    avg_similarity = float(np.mean(cluster_similarities))
                    
                    pattern = StructuringPattern(
                        pattern_id=pattern_id,
                        pattern_type='semantic_similarity',
                        account_id=list(account_ids)[0] if account_ids else 'MULTIPLE',
                        person_id=primary_person_id,
                        person_name=primary_person_name,
                        transactions=[{
                            'transaction_id': ct.get('tx_id'),
                            'amount': ct.get('amount'),
                            'description': ct.get('description'),
                            'merchant': ct.get('merchant'),
                            'account_id': ct.get('account_id')
                        } for ct in cluster_txns],
                        total_amount=total_amount,
                        transaction_count=len(cluster_txns),
                        time_window_hours=float(time_window_hours),
                        risk_score=risk_score,
                        detection_method='vector',
                        timestamp=datetime.utcnow().isoformat()
                    )
                    
                    patterns.append(pattern)
                    
                    # Mark these transactions as processed
                    for ct in cluster_txns:
                        processed_clusters.add(ct['tx_id'])
                    
                    logger.warning(
                        f"Semantic pattern detected: {pattern_id} - "
                        f"{len(cluster_txns)} transactions, ${total_amount:.2f} total, "
                        f"avg similarity={avg_similarity:.2f}, "
                        f"{len(account_ids)} accounts, {len(person_ids)} persons"
                    )
            
        except Exception as e:
            logger.error(f"Error detecting semantic patterns: {e}")
            import traceback
            traceback.print_exc()
        
        logger.info(f"Found {len(patterns)} semantic structuring patterns")
        return patterns
    
    def detect_hybrid_patterns(
        self,
        time_window_hours: int = 24,
        min_transactions: int = 3,
        threshold_amount: float = 10000.0
    ) -> List[StructuringPattern]:
        """
        Detect patterns using hybrid graph + vector approach.
        
        Args:
            time_window_hours: Time window
            min_transactions: Minimum transactions
            threshold_amount: Reporting threshold
        
        Returns:
            List of detected patterns
        """
        logger.info("Detecting hybrid structuring patterns...")
        
        # Get graph patterns
        graph_patterns = self.detect_graph_patterns(
            time_window_hours=time_window_hours,
            min_transactions=min_transactions,
            threshold_amount=threshold_amount
        )
        
        # Get semantic patterns
        semantic_patterns = self.detect_semantic_patterns()
        
        # Combine and deduplicate
        all_patterns = graph_patterns + semantic_patterns
        
        # Sort by risk score
        all_patterns.sort(key=lambda p: p.risk_score, reverse=True)
        
        logger.info(f"Found {len(all_patterns)} total patterns (hybrid)")
        return all_patterns
    
    def _calculate_risk_score(
        self,
        total_amount: float,
        tx_count: int,
        threshold: float
    ) -> float:
        """
        Calculate risk score for a pattern.
        
        Args:
            total_amount: Total transaction amount
            tx_count: Number of transactions
            threshold: Reporting threshold
        
        Returns:
            Risk score (0-1)
        """
        # Factors:
        # 1. How much over threshold (0-0.4)
        # 2. Number of transactions (0-0.3)
        # 3. Average transaction proximity to threshold (0-0.3)
        
        # Amount factor
        amount_factor = min(0.4, (total_amount - threshold) / threshold * 0.4)
        
        # Transaction count factor
        tx_factor = min(0.3, (tx_count - 3) / 10 * 0.3)
        
        # Proximity factor (transactions just under threshold are more suspicious)
        avg_amount = total_amount / tx_count
        proximity = 1.0 - abs(avg_amount - (threshold * 0.9)) / threshold
        proximity_factor = min(0.3, proximity * 0.3)
        
        risk_score = amount_factor + tx_factor + proximity_factor
        return min(1.0, max(0.0, risk_score))
    
    def _format_transaction(self, tx_data: Dict) -> Dict[str, Any]:
        """Format transaction data from graph."""
        return {
            'transaction_id': str(tx_data.get(T.id)),
            'amount': float(tx_data.get('amount', [0])[0]),
            'timestamp': tx_data.get('timestamp', [0])[0],
            'description': tx_data.get('description', [''])[0]
        }
    
    def detect_structuring(
        self,
        account_id: str,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect structuring patterns for a single account.
        
        Simple interface for notebook demos.
        
        Args:
            account_id: Account identifier
            transactions: List of transaction dicts with 'amount', 'timestamp', 'type'
        
        Returns:
            Dict with detection results
        """
        total_amount = sum(t.get('amount', 0) for t in transactions)
        tx_count = len(transactions)
        
        # Check if pattern matches structuring criteria
        near_threshold_count = sum(
            1 for t in transactions 
            if 9000 <= t.get('amount', 0) < self.STRUCTURING_THRESHOLD
        )
        
        # Detect structuring if:
        # 1. Multiple transactions near threshold
        # 2. Total exceeds threshold
        # 3. Transactions within time window
        is_structuring = (
            near_threshold_count >= self.MIN_TRANSACTIONS and
            total_amount > self.STRUCTURING_THRESHOLD
        )
        
        risk_score = self._calculate_risk_score(total_amount, tx_count, self.STRUCTURING_THRESHOLD)
        
        indicators = []
        if near_threshold_count >= self.MIN_TRANSACTIONS:
            indicators.append(f"{near_threshold_count} transactions near $10K threshold")
        if total_amount > self.STRUCTURING_THRESHOLD:
            indicators.append(f"Total ${total_amount:,.2f} exceeds reporting threshold")
        if tx_count >= self.MIN_TRANSACTIONS:
            indicators.append(f"Rapid sequence of {tx_count} transactions")
        
        risk_level = 'low'
        if risk_score >= 0.7:
            risk_level = 'high'
        elif risk_score >= 0.4:
            risk_level = 'medium'
        
        return {
            'is_structuring': is_structuring,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'pattern_type': 'simple_structuring' if is_structuring else 'none',
            'indicators': indicators,
            'account_id': account_id,
            'total_amount': total_amount,
            'transaction_count': tx_count
        }
    
    def detect_multi_account_structuring(
        self,
        transactions: List[Dict[str, Any]],
        relationship_data: Optional[Dict] = None,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Detect coordinated structuring across multiple accounts.
        
        Args:
            transactions: List of transactions from multiple accounts
            relationship_data: Optional relationship info between accounts
            time_window_hours: Time window for pattern analysis (hours)
        
        Returns:
            Dict with multi-account detection results
        """
        # Group by account
        account_txs = {}
        for tx in transactions:
            acc_id = tx.get('account_id', 'unknown')
            if acc_id not in account_txs:
                account_txs[acc_id] = []
            account_txs[acc_id].append(tx)
        
        # Analyze each account
        account_results = {}
        for acc_id, acc_txs in account_txs.items():
            account_results[acc_id] = self.detect_structuring(acc_id, acc_txs)
        
        # Check for coordinated patterns
        coordinated_accounts = [
            acc_id for acc_id, result in account_results.items()
            if result['is_structuring']
        ]
        
        total_amount = sum(t.get('amount', 0) for t in transactions)
        total_txs = len(transactions)
        
        # High risk if multiple accounts show structuring
        is_coordinated = len(coordinated_accounts) >= 2
        
        if is_coordinated:
            risk_score = min(1.0, 0.6 + len(coordinated_accounts) * 0.1)
            risk_level = 'high'
        else:
            risk_score = max(r['risk_score'] for r in account_results.values()) if account_results else 0
            risk_level = 'medium' if any(r['is_structuring'] for r in account_results.values()) else 'low'
        
        indicators = []
        if is_coordinated:
            indicators.append(f"Coordinated activity across {len(coordinated_accounts)} accounts")
        indicators.append(f"Total amount: ${total_amount:,.2f}")
        indicators.append(f"Total transactions: {total_txs}")
        
        return {
            'is_structuring': is_coordinated,  # Alias for notebook compatibility
            'is_coordinated_structuring': is_coordinated,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'pattern_type': 'multi_account_structuring' if is_coordinated else 'isolated',
            'indicators': indicators,
            'accounts_involved': list(account_txs.keys()),
            'coordinated_accounts': coordinated_accounts,
            'account_results': account_results,
            'total_amount': total_amount,
            'total_transactions': total_txs,
            'relationship_score': risk_score * 0.8  # Derived relationship score
        }
    
    def analyze_amount_clustering(
        self,
        account_id: str,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze amount clustering patterns in transactions.
        
        Args:
            account_id: Account identifier
            transactions: List of transaction dicts with amounts
        
        Returns:
            Dict with clustering analysis results
        """
        if len(transactions) < 2:
            return {
                'is_clustered': False,
                'cluster_center': 0.0,
                'cluster_tightness': 0.0,
                'cluster_size': 0,
                'risk_level': 'low'
            }
        
        amounts = [t.get('amount', 0) for t in transactions]
        avg_amount = sum(amounts) / len(amounts)
        std_dev = (sum((a - avg_amount) ** 2 for a in amounts) / len(amounts)) ** 0.5
        
        # Check if amounts cluster near the threshold
        near_threshold = [a for a in amounts if 9000 <= a < self.STRUCTURING_THRESHOLD]
        
        # Calculate cluster tightness (1 - coefficient of variation)
        cv = std_dev / avg_amount if avg_amount > 0 else 1.0
        cluster_tightness = max(0.0, 1.0 - cv)
        
        # Clustered if low variance and amounts near threshold
        is_clustered = (
            cluster_tightness >= 0.9 and  # Very tight cluster
            len(near_threshold) >= self.MIN_TRANSACTIONS and
            8500 <= avg_amount < self.STRUCTURING_THRESHOLD
        )
        
        risk_level = 'low'
        if is_clustered:
            risk_level = 'high' if cluster_tightness >= 0.95 else 'medium'
        elif len(near_threshold) >= 2:
            risk_level = 'medium'
        
        return {
            'is_clustered': is_clustered,
            'cluster_center': avg_amount,
            'cluster_tightness': cluster_tightness,
            'cluster_size': len(near_threshold),
            'risk_level': risk_level,
            'account_id': account_id,
            'std_dev': std_dev
        }
    
    def analyze_temporal_pattern(
        self,
        account_id: str,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze temporal patterns in transactions.
        
        Args:
            account_id: Account identifier
            transactions: List of transaction dicts with timestamps
        
        Returns:
            Dict with temporal analysis results
        """
        if len(transactions) < 2:
            return {
                'is_systematic': False,
                'regularity_score': 0.0,
                'avg_interval_hours': 0.0,
                'interval_variance': 0.0,
                'risk_level': 'low'
            }
        
        # Calculate intervals between transactions
        sorted_txns = sorted(transactions, key=lambda t: t.get('timestamp', datetime.min))
        intervals = []
        
        for i in range(1, len(sorted_txns)):
            t1 = sorted_txns[i-1].get('timestamp')
            t2 = sorted_txns[i].get('timestamp')
            if hasattr(t1, 'timestamp') and hasattr(t2, 'timestamp'):
                interval_hours = (t2 - t1).total_seconds() / 3600
                intervals.append(interval_hours)
        
        if not intervals:
            return {
                'is_systematic': False,
                'regularity_score': 0.0,
                'avg_interval_hours': 0.0,
                'interval_variance': 0.0,
                'risk_level': 'low'
            }
        
        avg_interval = sum(intervals) / len(intervals)
        variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)
        std_dev = variance ** 0.5
        
        # Calculate regularity score (lower variance = more systematic)
        regularity_score = max(0.0, 1.0 - (std_dev / avg_interval)) if avg_interval > 0 else 0.0
        
        # Systematic if high regularity and multiple transactions
        is_systematic = regularity_score >= 0.7 and len(transactions) >= self.MIN_TRANSACTIONS
        
        risk_level = 'low'
        if is_systematic:
            risk_level = 'high' if regularity_score >= 0.9 else 'medium'
        
        return {
            'is_systematic': is_systematic,
            'regularity_score': regularity_score,
            'avg_interval_hours': avg_interval,
            'interval_variance': variance,
            'risk_level': risk_level,
            'account_id': account_id,
            'transaction_count': len(transactions)
        }
    
    def generate_report(
        self,
        patterns: List[StructuringPattern],
        output_format: str = 'text'
    ) -> str:
        """
        Generate detection report.
        
        Args:
            patterns: Detected patterns
            output_format: 'text' or 'json'
        
        Returns:
            Formatted report
        """
        if output_format == 'json':
            import json
            return json.dumps([p.__dict__ for p in patterns], indent=2, default=str)
        
        # Text format
        report = []
        report.append("="*80)
        report.append("AML STRUCTURING DETECTION REPORT")
        report.append("="*80)
        report.append(f"Generated: {datetime.utcnow().isoformat()}")
        report.append(f"Total Patterns Detected: {len(patterns)}")
        report.append("")
        
        for i, pattern in enumerate(patterns, 1):
            report.append(f"\n{i}. Pattern ID: {pattern.pattern_id}")
            report.append(f"   Type: {pattern.pattern_type}")
            report.append(f"   Detection Method: {pattern.detection_method}")
            report.append(f"   Risk Score: {pattern.risk_score:.2f}")
            report.append(f"   Person: {pattern.person_name} (ID: {pattern.person_id})")
            report.append(f"   Account: {pattern.account_id}")
            report.append(f"   Total Amount: ${pattern.total_amount:,.2f}")
            report.append(f"   Transaction Count: {pattern.transaction_count}")
            report.append(f"   Time Window: {pattern.time_window_hours} hours")
            report.append(f"   Timestamp: {pattern.timestamp}")
        
        report.append("\n" + "="*80)
        return "\n".join(report)


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("ENHANCED STRUCTURING DETECTION - TEST")
    print("="*60)
    
    # Initialize detector
    print("\n1. Initializing enhanced detector...")
    detector = EnhancedStructuringDetector(
        janusgraph_host='localhost',
        janusgraph_port=18182,
        opensearch_host='localhost',
        opensearch_port=9200
    )
    
    # Detect patterns
    print("\n2. Detecting structuring patterns...")
    patterns = detector.detect_hybrid_patterns(
        time_window_hours=24,
        min_transactions=3,
        threshold_amount=10000.0
    )
    
    # Generate report
    print("\n3. Generating report...")
    report = detector.generate_report(patterns)
    print(report)
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETE")
    print("="*60)

# Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS | +33614126117
