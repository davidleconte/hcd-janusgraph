#!/usr/bin/env python3
"""
JanusGraph Metrics Exporter for Prometheus
File: janusgraph_exporter.py
Created: 2026-01-29
Purpose: Export JanusGraph metrics to Prometheus format

This exporter collects metrics from JanusGraph via Gremlin queries
and exposes them in Prometheus format on port 8000.
"""

import os
import sys
import time
import logging
from typing import Dict, Any, Optional
from prometheus_client import start_http_server, Gauge, Counter, Histogram, Info
from gremlin_python.driver import client, serializer
from gremlin_python.driver.protocol import GremlinServerError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment
GREMLIN_URL = os.getenv('GREMLIN_URL', f'ws://localhost:{os.getenv("JANUSGRAPH_PORT", "18182")}/gremlin')
EXPORTER_PORT = int(os.getenv('EXPORTER_PORT', '8000'))
SCRAPE_INTERVAL = int(os.getenv('SCRAPE_INTERVAL', '15'))

# Define Prometheus metrics
janusgraph_vertices_total = Gauge(
    'janusgraph_vertices_total',
    'Total number of vertices in the graph'
)

janusgraph_edges_total = Gauge(
    'janusgraph_edges_total',
    'Total number of edges in the graph'
)

janusgraph_query_duration_seconds = Histogram(
    'janusgraph_query_duration_seconds',
    'Query execution time in seconds',
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
)

janusgraph_errors_total = Counter(
    'janusgraph_errors_total',
    'Total number of errors',
    ['error_type']
)

janusgraph_connection_status = Gauge(
    'janusgraph_connection_status',
    'Connection status (1=connected, 0=disconnected)'
)

janusgraph_vertex_labels = Gauge(
    'janusgraph_vertex_labels_count',
    'Number of vertices by label',
    ['label']
)

janusgraph_edge_labels = Gauge(
    'janusgraph_edge_labels_count',
    'Number of edges by label',
    ['label']
)

janusgraph_info = Info(
    'janusgraph',
    'JanusGraph instance information'
)


class JanusGraphExporter:
    """JanusGraph metrics exporter"""
    
    def __init__(self, gremlin_url: str):
        """Initialize the exporter"""
        self.gremlin_url = gremlin_url
        self.client: Optional[client.Client] = None
        self._connect()
    
    def _connect(self) -> None:
        """Connect to JanusGraph"""
        try:
            logger.info("Connecting to JanusGraph at %s", self.gremlin_url)
            self.client = client.Client(
                self.gremlin_url,
                'g',
                message_serializer=serializer.GraphSONSerializersV3d0()
            )
            janusgraph_connection_status.set(1)
            logger.info("Successfully connected to JanusGraph")
        except Exception as e:
            logger.error("Failed to connect to JanusGraph: %s", e)
            janusgraph_connection_status.set(0)
            janusgraph_errors_total.labels(error_type='connection').inc()
            self.client = None
    
    def _execute_query(self, query: str) -> Any:
        """Execute a Gremlin query with timing"""
        if not self.client:
            self._connect()
            if not self.client:
                raise ConnectionError("Not connected to JanusGraph")
        
        try:
            with janusgraph_query_duration_seconds.time():
                result = self.client.submit(query).all().result()
            return result
        except GremlinServerError as e:
            logger.error("Gremlin server error: %s", e)
            janusgraph_errors_total.labels(error_type='gremlin_server').inc()
            raise
        except Exception as e:
            logger.error("Query execution error: %s", e)
            janusgraph_errors_total.labels(error_type='query_execution').inc()
            raise
    
    def collect_basic_metrics(self) -> None:
        """Collect basic graph metrics"""
        try:
            # Count vertices
            vertex_count = self._execute_query('g.V().count()')[0]
            janusgraph_vertices_total.set(vertex_count)
            logger.debug("Vertices: %s", vertex_count)
            
            # Count edges
            edge_count = self._execute_query('g.E().count()')[0]
            janusgraph_edges_total.set(edge_count)
            logger.debug("Edges: %s", edge_count)
            
        except Exception as e:
            logger.error("Error collecting basic metrics: %s", e)
            janusgraph_errors_total.labels(error_type='metrics_collection').inc()
    
    def collect_label_metrics(self) -> None:
        """Collect metrics by vertex and edge labels"""
        try:
            # Count vertices by label
            vertex_labels = self._execute_query(
                'g.V().groupCount().by(label)'
            )[0]
            
            for label, count in vertex_labels.items():
                janusgraph_vertex_labels.labels(label=label).set(count)
                logger.debug("Vertex label %s: %s", label, count)
            
            # Count edges by label
            edge_labels = self._execute_query(
                'g.E().groupCount().by(label)'
            )[0]
            
            for label, count in edge_labels.items():
                janusgraph_edge_labels.labels(label=label).set(count)
                logger.debug("Edge label %s: %s", label, count)
                
        except Exception as e:
            logger.error("Error collecting label metrics: %s", e)
            janusgraph_errors_total.labels(error_type='label_metrics').inc()
    
    def collect_info(self) -> None:
        """Collect JanusGraph instance information"""
        try:
            janusgraph_info.info({
                'url': self.gremlin_url,
                'exporter_version': '1.0.0'
            })
        except Exception as e:
            logger.error("Error collecting info: %s", e)
    
    def collect_all_metrics(self) -> None:
        """Collect all metrics"""
        logger.info("Collecting metrics...")
        
        try:
            self.collect_basic_metrics()
            self.collect_label_metrics()
            self.collect_info()
            logger.info("Metrics collection complete")
        except Exception as e:
            logger.error("Error during metrics collection: %s", e)
            janusgraph_connection_status.set(0)
    
    def close(self) -> None:
        """Close the connection"""
        if self.client:
            try:
                self.client.close()
                logger.info("Connection closed")
            except Exception as e:
                logger.error("Error closing connection: %s", e)


def main():
    """Main entry point"""
    logger.info("Starting JanusGraph Exporter on port %s", EXPORTER_PORT)
    logger.info("Connecting to JanusGraph at %s", GREMLIN_URL)
    logger.info("Scrape interval: %s seconds", SCRAPE_INTERVAL)
    
    # Start Prometheus HTTP server
    start_http_server(EXPORTER_PORT)
    logger.info("Metrics available at http://localhost:%s/metrics", EXPORTER_PORT)
    
    # Create exporter instance
    exporter = JanusGraphExporter(GREMLIN_URL)
    
    try:
        # Main collection loop
        while True:
            exporter.collect_all_metrics()
            time.sleep(SCRAPE_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        sys.exit(1)
    finally:
        exporter.close()
        logger.info("Exporter stopped")


if __name__ == '__main__':
    main()
