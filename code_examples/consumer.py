"""
Apache Pulsar Graph Loader Consumer

This module implements a production-ready Pulsar consumer using Key_Shared subscription
for parallel graph loading with per-account ordering guarantees.

Features:
- Key_Shared subscription for high parallelism
- Batch aggregation (1000 messages)
- Atomic Gremlin transactions
- Error handling with negative ACKs
- Metrics tracking
"""

import json
import logging
import time
from typing import Any, Dict, List

from gremlin_python.driver import client as gremlin_client
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
from pulsar import Client, ConsumerType

logger = logging.getLogger(__name__)


class GraphLoaderConsumer:
    """
    Graph loader worker using Pulsar Key_Shared subscription.

    Key_Shared enables:
    - Multiple consumers (100+ workers) for parallelism
    - Per-key ordering: All messages with same key -> same consumer
    - Higher throughput than Exclusive/Failover subscriptions

    Usage:
        loader = GraphLoaderConsumer(worker_id=1)
        loader.process_messages()  # Runs forever
    """

    def __init__(
        self,
        pulsar_url: str = "pulsar://localhost:6650",
        gremlin_url: str = "ws://localhost:18182/gremlin",
        worker_id: int = 1,
    ):
        """
        Initialize Pulsar consumer and Gremlin client.

        Args:
            pulsar_url: Pulsar broker URL
            gremlin_url: JanusGraph Gremlin Server URL
            worker_id: Unique worker identifier
        """
        self.worker_id = worker_id
        self.pulsar_client = Client(pulsar_url)
        self.gremlin_client = gremlin_client.Client(gremlin_url, "g")

        # Key_Shared subscription: THE CRITICAL FEATURE
        # - Multiple consumers in parallel (scale to 100+ workers)
        # - Messages with same partition_key -> same consumer (ordering)
        # - Messages with different keys -> different consumers (parallelism)
        self.consumer = self.pulsar_client.subscribe(
            topic="persistent://banking/transactions/txn-events",
            subscription_name="graph-loader-subscription",
            # KEY_SHARED: Enables parallel processing with ordering
            consumer_type=ConsumerType.Key_Shared,
            # Unique consumer name for tracking
            consumer_name=f"graph-loader-{worker_id:03d}",
            # Acknowledgment batching for efficiency
            acknowledgment_grouping_time_ms=100,
            acknowledgment_grouping_max_size=1000,
            # Negative acknowledgment redelivery
            negative_ack_redelivery_delay_ms=60000,  # 1 minute
            # Consumer properties for monitoring
            properties={"worker_id": str(worker_id), "role": "graph_loader"},
        )

        # Batch buffer for write optimization
        self.batch_buffer: List[Dict[str, Any]] = []
        self.batch_size = 1000
        self.batch_timeout_ms = 100

        # Metrics
        self.messages_processed = 0
        self.batches_flushed = 0
        self.errors = 0

        logger.info("Worker %s initialized", worker_id)

    def process_messages(self):
        """
        Main processing loop.

        1. Receive messages from Pulsar
        2. Accumulate in batch buffer
        3. Flush batch to JanusGraph when full
        4. Acknowledge messages after successful write
        """
        logger.info("Worker %s started processing", self.worker_id)

        while True:
            try:
                # Receive message (blocking with timeout)
                msg = self.consumer.receive(timeout_millis=5000)

                # Parse event
                event = json.loads(msg.data().decode("utf-8"))
                logger.debug("Received event: %s", event["event_id"])

                # Add to batch buffer
                self.batch_buffer.append(
                    {"event": event, "msg": msg}  # Store message for acknowledgment
                )

                # Flush batch when full or timeout
                if len(self.batch_buffer) >= self.batch_size:
                    self._flush_batch()

            except Exception as e:
                logger.error("Error processing message: %s", e)
                if msg:
                    # Negative acknowledge -> message will be redelivered
                    self.consumer.negative_acknowledge(msg)
                    self.errors += 1

    def _flush_batch(self):
        """
        Flush batch to JanusGraph with ACID transaction.
        """
        if not self.batch_buffer:
            return

        logger.info("Flushing batch of %s events", len(self.batch_buffer))

        # Extract events and messages
        events = [item["event"] for item in self.batch_buffer]
        messages = [item["msg"] for item in self.batch_buffer]

        # Build Gremlin batch script
        script = self._build_batch_script(events)

        try:
            # Execute batch transaction
            result = self.gremlin_client.submit(script).all().result()
            logger.info("Batch loaded successfully: %s events", len(events))

            # Acknowledge ALL messages after successful commit
            for msg in messages:
                self.consumer.acknowledge(msg)

            # Update metrics
            self.messages_processed += len(events)
            self.batches_flushed += 1

            # Clear buffer
            self.batch_buffer = []

        except Exception as e:
            logger.error("Batch load failed: %s", e)

            # Negative acknowledge ALL messages -> redelivery
            for msg in messages:
                self.consumer.negative_acknowledge(msg)

            # Clear buffer (will retry on redelivery)
            self.batch_buffer = []
            self.errors += 1

    def _build_batch_script(self, events: List[Dict[str, Any]]) -> str:
        """
        Build Gremlin script for batch insert with idempotent pattern.

        Creates:
        - Account vertices (if not exist)
        - Transaction edges between accounts
        - Properties on edges (amount, timestamp, etc.)

        Uses fold().coalesce() pattern for idempotency.
        """
        lines = []

        for event in events:
            if event["event_type"] == "transaction":
                payload = event["payload"]

                # Create transaction edge with idempotent vertex creation
                lines.append(
                    f"""
                from_v = g.V().has('account', 'account_id', '{payload['from_account_id']}')
                              .fold()
                              .coalesce(
                                  unfold(),
                                  addV('account').property('account_id', '{payload['from_account_id']}')
                              ).next()
                to_v = g.V().has('account', 'account_id', '{payload['to_account_id']}')
                            .fold()
                            .coalesce(
                                unfold(),
                                addV('account').property('account_id', '{payload['to_account_id']}')
                            ).next()
                from_v.addEdge('transfer', to_v,
                    'transaction_id', '{payload['transaction_id']}',
                    'amount', {payload['amount']},
                    'currency', '{payload.get('currency', 'USD')}',
                    'timestamp', '{event['timestamp']}',
                    'event_id', '{event['event_id']}'
                )
                """
                )

        # Wrap in transaction with commit
        script = ";\n".join(lines) + ";\ng.tx().commit()"
        return script

    def get_metrics(self) -> Dict[str, int]:
        """Return current metrics"""
        return {
            "worker_id": self.worker_id,
            "messages_processed": self.messages_processed,
            "batches_flushed": self.batches_flushed,
            "errors": self.errors,
            "buffer_size": len(self.batch_buffer),
        }

    def close(self):
        """Cleanup resources"""
        self._flush_batch()  # Flush remaining messages
        self.consumer.close()
        self.gremlin_client.close()
        self.pulsar_client.close()
        logger.info("Worker %s closed", self.worker_id)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Initialize consumer
    loader = GraphLoaderConsumer(worker_id=1)

    try:
        # Process messages forever
        loader.process_messages()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        loader.close()
