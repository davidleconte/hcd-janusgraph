"""
Query Performance Profiler

Provides comprehensive query profiling, analysis, and optimization
recommendations for JanusGraph Gremlin queries.
"""

import time
import logging
import statistics
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import json
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Metrics for a single query execution."""
    query_id: str
    query_hash: str
    query_text: str
    execution_time_ms: float
    result_count: int
    traversal_steps: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    trace_id: Optional[str] = None
    
    # Detailed metrics
    compilation_time_ms: float = 0.0
    execution_time_ms_breakdown: Dict[str, float] = field(default_factory=dict)
    memory_used_mb: float = 0.0
    vertices_scanned: int = 0
    edges_scanned: int = 0
    index_hits: int = 0
    index_misses: int = 0
    
    # Performance indicators
    is_slow: bool = False
    is_expensive: bool = False
    optimization_hints: List[str] = field(default_factory=list)


@dataclass
class QueryStatistics:
    """Aggregated statistics for a query pattern."""
    query_hash: str
    query_pattern: str
    execution_count: int = 0
    total_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    median_time_ms: float = 0.0
    p95_time_ms: float = 0.0
    p99_time_ms: float = 0.0
    std_dev_ms: float = 0.0
    
    # Result statistics
    avg_result_count: float = 0.0
    max_result_count: int = 0
    
    # Resource usage
    avg_memory_mb: float = 0.0
    avg_vertices_scanned: float = 0.0
    avg_edges_scanned: float = 0.0
    
    # Performance indicators
    slow_query_count: int = 0
    error_count: int = 0
    
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)


class QueryProfiler:
    """Profiles and analyzes query performance."""
    
    def __init__(
        self,
        slow_query_threshold_ms: float = 1000.0,
        expensive_query_threshold_scans: int = 10000
    ):
        """
        Initialize query profiler.
        
        Args:
            slow_query_threshold_ms: Threshold for slow queries in milliseconds
            expensive_query_threshold_scans: Threshold for expensive queries (vertex/edge scans)
        """
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.expensive_query_threshold_scans = expensive_query_threshold_scans
        
        # Storage for metrics
        self.query_metrics: List[QueryMetrics] = []
        self.query_statistics: Dict[str, QueryStatistics] = {}
        self.execution_times: Dict[str, List[float]] = defaultdict(list)
        
        logger.info("Query Profiler initialized")
    
    def profile_query(
        self,
        query_text: str,
        execution_func,
        *args,
        user_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        **kwargs
    ) -> Tuple[Any, QueryMetrics]:
        """
        Profile a query execution.
        
        Args:
            query_text: Gremlin query string
            execution_func: Function to execute query
            *args: Arguments for execution function
            user_id: Optional user identifier
            trace_id: Optional trace identifier
            **kwargs: Keyword arguments for execution function
        
        Returns:
            Tuple of (query result, query metrics)
        """
        query_hash = self._hash_query(query_text)
        query_id = f"{query_hash}_{int(time.time() * 1000)}"
        
        # Start profiling
        start_time = time.perf_counter()
        start_memory = self._get_memory_usage()
        
        try:
            # Execute query
            result = execution_func(*args, **kwargs)
            
            # Calculate metrics
            end_time = time.perf_counter()
            end_memory = self._get_memory_usage()
            
            execution_time_ms = (end_time - start_time) * 1000
            memory_used_mb = max(0, end_memory - start_memory)
            
            # Get result count
            if isinstance(result, list):
                result_count = len(result)
            else:
                result_count = 1
            
            # Create metrics
            metrics = QueryMetrics(
                query_id=query_id,
                query_hash=query_hash,
                query_text=query_text,
                execution_time_ms=execution_time_ms,
                result_count=result_count,
                traversal_steps=self._count_traversal_steps(query_text),
                user_id=user_id,
                trace_id=trace_id,
                memory_used_mb=memory_used_mb
            )
            
            # Analyze performance
            self._analyze_performance(metrics)
            
            # Store metrics
            self._store_metrics(metrics)
            
            logger.info(
                f"Query profiled: {query_id} - "
                f"{execution_time_ms:.2f}ms, {result_count} results"
            )
            
            return result, metrics
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def _hash_query(self, query_text: str) -> str:
        """
        Generate hash for query pattern.
        
        Args:
            query_text: Query string
        
        Returns:
            Query hash
        """
        # Normalize query (remove whitespace, lowercase)
        normalized = ' '.join(query_text.lower().split())
        
        # Generate hash
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    def _count_traversal_steps(self, query_text: str) -> int:
        """
        Count traversal steps in query.
        
        Args:
            query_text: Query string
        
        Returns:
            Number of steps
        """
        # Simple heuristic: count method calls
        steps = query_text.count('.') + query_text.count('(')
        return max(1, steps)
    
    def _get_memory_usage(self) -> float:
        """
        Get current memory usage in MB.
        
        Returns:
            Memory usage in MB
        """
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
    
    def _analyze_performance(self, metrics: QueryMetrics):
        """
        Analyze query performance and generate optimization hints.
        
        Args:
            metrics: Query metrics to analyze
        """
        # Check if slow
        if metrics.execution_time_ms > self.slow_query_threshold_ms:
            metrics.is_slow = True
            metrics.optimization_hints.append(
                f"Slow query: {metrics.execution_time_ms:.2f}ms > "
                f"{self.slow_query_threshold_ms}ms threshold"
            )
        
        # Check if expensive
        total_scans = metrics.vertices_scanned + metrics.edges_scanned
        if total_scans > self.expensive_query_threshold_scans:
            metrics.is_expensive = True
            metrics.optimization_hints.append(
                f"Expensive query: {total_scans} scans > "
                f"{self.expensive_query_threshold_scans} threshold"
            )
        
        # Check for missing indexes
        if metrics.index_misses > metrics.index_hits:
            metrics.optimization_hints.append(
                "Consider adding indexes: more index misses than hits"
            )
        
        # Check for large result sets
        if metrics.result_count > 1000:
            metrics.optimization_hints.append(
                f"Large result set: {metrics.result_count} results. "
                "Consider pagination or filtering"
            )
        
        # Check for complex traversals
        if metrics.traversal_steps > 10:
            metrics.optimization_hints.append(
                f"Complex traversal: {metrics.traversal_steps} steps. "
                "Consider simplifying or caching"
            )
    
    def _store_metrics(self, metrics: QueryMetrics):
        """
        Store query metrics and update statistics.
        
        Args:
            metrics: Query metrics to store
        """
        # Store individual metrics
        self.query_metrics.append(metrics)
        
        # Update execution times for statistics
        self.execution_times[metrics.query_hash].append(metrics.execution_time_ms)
        
        # Update or create statistics
        if metrics.query_hash not in self.query_statistics:
            self.query_statistics[metrics.query_hash] = QueryStatistics(
                query_hash=metrics.query_hash,
                query_pattern=self._extract_pattern(metrics.query_text)
            )
        
        stats = self.query_statistics[metrics.query_hash]
        self._update_statistics(stats, metrics)
    
    def _extract_pattern(self, query_text: str) -> str:
        """
        Extract query pattern (remove literals).
        
        Args:
            query_text: Query string
        
        Returns:
            Query pattern
        """
        # Simple pattern extraction: replace string literals with ?
        import re
        pattern = re.sub(r"'[^']*'", "'?'", query_text)
        pattern = re.sub(r'"[^"]*"', '"?"', pattern)
        pattern = re.sub(r'\b\d+\b', '?', pattern)
        return pattern
    
    def _update_statistics(self, stats: QueryStatistics, metrics: QueryMetrics):
        """
        Update query statistics with new metrics.
        
        Args:
            stats: Statistics to update
            metrics: New metrics
        """
        stats.execution_count += 1
        stats.total_time_ms += metrics.execution_time_ms
        stats.min_time_ms = min(stats.min_time_ms, metrics.execution_time_ms)
        stats.max_time_ms = max(stats.max_time_ms, metrics.execution_time_ms)
        stats.max_result_count = max(stats.max_result_count, metrics.result_count)
        stats.last_seen = metrics.timestamp
        
        if metrics.is_slow:
            stats.slow_query_count += 1
        
        # Calculate averages
        stats.avg_time_ms = stats.total_time_ms / stats.execution_count
        stats.avg_result_count = (
            (stats.avg_result_count * (stats.execution_count - 1) + metrics.result_count)
            / stats.execution_count
        )
        stats.avg_memory_mb = (
            (stats.avg_memory_mb * (stats.execution_count - 1) + metrics.memory_used_mb)
            / stats.execution_count
        )
        
        # Calculate percentiles
        times = self.execution_times[metrics.query_hash]
        if len(times) >= 2:
            stats.median_time_ms = statistics.median(times)
            stats.std_dev_ms = statistics.stdev(times)
            
            sorted_times = sorted(times)
            stats.p95_time_ms = sorted_times[int(len(sorted_times) * 0.95)]
            stats.p99_time_ms = sorted_times[int(len(sorted_times) * 0.99)]
    
    def get_slow_queries(self, limit: int = 10) -> List[QueryStatistics]:
        """
        Get slowest queries by average execution time.
        
        Args:
            limit: Maximum number of queries to return
        
        Returns:
            List of query statistics
        """
        sorted_stats = sorted(
            self.query_statistics.values(),
            key=lambda s: s.avg_time_ms,
            reverse=True
        )
        return sorted_stats[:limit]
    
    def get_frequent_queries(self, limit: int = 10) -> List[QueryStatistics]:
        """
        Get most frequently executed queries.
        
        Args:
            limit: Maximum number of queries to return
        
        Returns:
            List of query statistics
        """
        sorted_stats = sorted(
            self.query_statistics.values(),
            key=lambda s: s.execution_count,
            reverse=True
        )
        return sorted_stats[:limit]
    
    def get_expensive_queries(self, limit: int = 10) -> List[QueryStatistics]:
        """
        Get most expensive queries by resource usage.
        
        Args:
            limit: Maximum number of queries to return
        
        Returns:
            List of query statistics
        """
        sorted_stats = sorted(
            self.query_statistics.values(),
            key=lambda s: s.avg_vertices_scanned + s.avg_edges_scanned,
            reverse=True
        )
        return sorted_stats[:limit]
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.
        
        Returns:
            Performance report dictionary
        """
        total_queries = len(self.query_metrics)
        slow_queries = sum(1 for m in self.query_metrics if m.is_slow)
        expensive_queries = sum(1 for m in self.query_metrics if m.is_expensive)
        
        if total_queries > 0:
            avg_execution_time = statistics.mean(
                m.execution_time_ms for m in self.query_metrics
            )
            median_execution_time = statistics.median(
                m.execution_time_ms for m in self.query_metrics
            )
        else:
            avg_execution_time = 0
            median_execution_time = 0
        
        report = {
            'summary': {
                'total_queries': total_queries,
                'unique_patterns': len(self.query_statistics),
                'slow_queries': slow_queries,
                'expensive_queries': expensive_queries,
                'avg_execution_time_ms': avg_execution_time,
                'median_execution_time_ms': median_execution_time,
                'slow_query_percentage': (slow_queries / total_queries * 100) if total_queries > 0 else 0
            },
            'top_slow_queries': [
                {
                    'pattern': s.query_pattern,
                    'avg_time_ms': s.avg_time_ms,
                    'p95_time_ms': s.p95_time_ms,
                    'execution_count': s.execution_count
                }
                for s in self.get_slow_queries(5)
            ],
            'top_frequent_queries': [
                {
                    'pattern': s.query_pattern,
                    'execution_count': s.execution_count,
                    'avg_time_ms': s.avg_time_ms
                }
                for s in self.get_frequent_queries(5)
            ],
            'optimization_recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """
        Generate optimization recommendations.
        
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Analyze slow queries
        slow_queries = [s for s in self.query_statistics.values() if s.slow_query_count > 0]
        if slow_queries:
            recommendations.append(
                f"Found {len(slow_queries)} slow query patterns. "
                "Review and optimize these queries."
            )
        
        # Check for missing indexes
        high_scan_queries = [
            s for s in self.query_statistics.values()
            if s.avg_vertices_scanned + s.avg_edges_scanned > self.expensive_query_threshold_scans
        ]
        if high_scan_queries:
            recommendations.append(
                f"Found {len(high_scan_queries)} queries with high scan counts. "
                "Consider adding indexes on frequently queried properties."
            )
        
        # Check for large result sets
        large_result_queries = [
            s for s in self.query_statistics.values()
            if s.max_result_count > 1000
        ]
        if large_result_queries:
            recommendations.append(
                f"Found {len(large_result_queries)} queries returning large result sets. "
                "Implement pagination or result limiting."
            )
        
        # Check for frequently executed slow queries
        frequent_slow = [
            s for s in self.query_statistics.values()
            if s.execution_count > 100 and s.avg_time_ms > self.slow_query_threshold_ms
        ]
        if frequent_slow:
            recommendations.append(
                f"Found {len(frequent_slow)} frequently executed slow queries. "
                "These should be prioritized for optimization or caching."
            )
        
        return recommendations
    
    def export_metrics(self, filepath: str):
        """
        Export metrics to JSON file.
        
        Args:
            filepath: Path to export file
        """
        data = {
            'metrics': [
                {
                    'query_id': m.query_id,
                    'query_hash': m.query_hash,
                    'query_text': m.query_text,
                    'execution_time_ms': m.execution_time_ms,
                    'result_count': m.result_count,
                    'timestamp': m.timestamp.isoformat(),
                    'is_slow': m.is_slow,
                    'optimization_hints': m.optimization_hints
                }
                for m in self.query_metrics
            ],
            'statistics': {
                hash_val: {
                    'query_pattern': s.query_pattern,
                    'execution_count': s.execution_count,
                    'avg_time_ms': s.avg_time_ms,
                    'p95_time_ms': s.p95_time_ms,
                    'p99_time_ms': s.p99_time_ms,
                    'slow_query_count': s.slow_query_count
                }
                for hash_val, s in self.query_statistics.items()
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Metrics exported to {filepath}")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize profiler
    profiler = QueryProfiler(slow_query_threshold_ms=500.0)
    
    # Example query execution function
    def execute_query(query):
        time.sleep(0.1)  # Simulate query execution
        return [{'id': i} for i in range(100)]
    
    # Profile queries
    for i in range(10):
        query = f"g.V().has('name', 'user{i}').out('knows').limit(100)"
        result, metrics = profiler.profile_query(
            query,
            execute_query,
            query,
            user_id=f"user{i}"
        )
        print(f"Query {i}: {metrics.execution_time_ms:.2f}ms")
    
    # Generate report
    report = profiler.generate_report()
    print(json.dumps(report, indent=2))

# Made with Bob
