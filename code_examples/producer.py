"""
Apache Pulsar Transaction Producer

This module implements a production-ready Pulsar producer for transaction events
with deduplication, batching, and compression.

Features:
- Message deduplication via sequence_id
- Key-based routing for ordering guarantees
- ZSTD compression for network efficiency
- Batching for throughput optimization
- Error handling and retries
"""

from pulsar import Client, CompressionType
import json
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class TransactionProducer:
    """
    Production-ready Pulsar producer for transaction events.
    
    Usage:
        producer = TransactionProducer(pulsar_url="pulsar://localhost:6650")
        producer.send_transaction_event(transaction)
        producer.close()
    """
    
    def __init__(self, pulsar_url: str = "pulsar://localhost:6650"):
        """
        Initialize Pulsar producer with optimizations.
        
        Args:
            pulsar_url: Pulsar broker URL
        """
        self.client = Client(
            pulsar_url,
            operation_timeout_seconds=30,
            connection_timeout_ms=10000
        )
        
        # Create producer with production settings
        self.producer = self.client.create_producer(
            topic='persistent://banking/transactions/txn-events',
            producer_name='txn-producer-01',
            
            # Compression: ZSTD offers best compression ratio
            compression_type=CompressionType.ZSTD,
            
            # Batching: Trade latency for throughput
            batching_enabled=True,
            batching_max_messages=1000,
            batching_max_publish_delay_ms=10,  # Max 10ms delay
            
            # Backpressure: Block if queue full
            block_if_queue_full=True,
            max_pending_messages=10000,
            
            # Properties for monitoring
            properties={
                "application": "banking-core",
                "version": "2.0",
                "environment": "production"
            }
        )
        
        logger.info("Pulsar producer initialized")
    
    def send_transaction_event(self, transaction: Dict[str, Any]) -> None:
        """
        Send transaction event with deduplication and ordering.
        
        Args:
            transaction: Transaction event payload
                Required fields:
                - event_id: Unique event identifier
                - payload.from_account_id: Source account
                - payload.to_account_id: Target account
                - payload.amount: Transaction amount
                - timestamp: ISO 8601 timestamp
        
        Example:
            transaction = {
                "event_id": "evt_20260130_153045_001",
                "event_type": "transaction",
                "timestamp": "2026-01-30T15:30:45.123Z",
                "payload": {
                    "transaction_id": "TXN_987654321",
                    "from_account_id": "ACC_123456",
                    "to_account_id": "ACC_789012",
                    "amount": 9500.00,
                    "currency": "USD",
                    "transaction_type": "withdrawal"
                }
            }
        """
        # Partition key: Ensures all transactions from same account
        # go to same partition (and same consumer via Key_Shared)
        partition_key = transaction['payload']['from_account_id']
        
        # Sequence ID: Unique per transaction for deduplication
        # If producer retries, broker will drop duplicate
        sequence_id = transaction['event_id']
        
        # Event timestamp for time-based operations
        event_timestamp = int(
            datetime.fromisoformat(
                transaction['timestamp'].replace('Z', '+00:00')
            ).timestamp() * 1000
        )
        
        try:
            # Send to Pulsar
            self.producer.send(
                content=json.dumps(transaction).encode('utf-8'),
                partition_key=partition_key,  # Key-based routing
                sequence_id=sequence_id,  # Deduplication key
                event_timestamp=event_timestamp,  # Event time
                properties={
                    'source': transaction.get('source', 'unknown'),
                    'event_type': transaction['event_type']
                }
            )
            
            logger.debug(f"Sent event: {transaction['event_id']}")
            
        except Exception as e:
            logger.error(f"Failed to send event {transaction['event_id']}: {e}")
            raise
    
    def close(self):
        """Cleanup resources"""
        self.producer.close()
        self.client.close()
        logger.info("Pulsar producer closed")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize producer
    producer = TransactionProducer()
    
    # Example transaction
    transaction = {
        "event_id": "evt_20260130_153045_001",
        "event_type": "transaction",
        "timestamp": "2026-01-30T15:30:45.123Z",
        "source": "atm_network",
        "payload": {
            "transaction_id": "TXN_987654321",
            "from_account_id": "ACC_123456",
            "to_account_id": "ACC_789012",
            "amount": 9500.00,
            "currency": "USD",
            "transaction_type": "withdrawal",
            "atm_location": "NYC_42ST_001"
        }
    }
    
    # Send transaction
    producer.send_transaction_event(transaction)
    
    # Cleanup
    producer.close()
