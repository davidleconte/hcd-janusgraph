"""
Gremlin Batch Writer

This module provides utilities for building idempotent Gremlin batch scripts
for atomic graph writes.

Features:
- Idempotent vertex creation (fold/coalesce pattern)
- Batch transaction wrapping
- Property type handling
- Error-safe script generation
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class GremlinBatchBuilder:
    """
    Builder for creating idempotent Gremlin batch scripts.
    
    Usage:
        builder = GremlinBatchBuilder()
        script = builder.build_transaction_batch(events)
        result = gremlin_client.submit(script).all().result()
    """
    
    @staticmethod
    def build_transaction_batch(events: List[Dict[str, Any]]) -> str:
        """
        Build Gremlin script for batch transaction insertion.
        
        Args:
            events: List of transaction events
        
        Returns:
            Gremlin script with atomic transaction
        
        Example:
            events = [
                {
                    "event_id": "evt_001",
                    "event_type": "transaction",
                    "timestamp": "2026-01-30T15:30:45.123Z",
                    "payload": {
                        "transaction_id": "TXN_001",
                        "from_account_id": "ACC_123",
                        "to_account_id": "ACC_456",
                        "amount": 9500.00,
                        "currency": "USD"
                    }
                }
            ]
        """
        lines = []
        
        for event in events:
            if event['event_type'] == 'transaction':
                payload = event['payload']
                
                # Idempotent vertex creation + edge creation
                vertex_script = GremlinBatchBuilder._create_transaction_edge(
                    from_account=payload['from_account_id'],
                    to_account=payload['to_account_id'],
                    transaction_id=payload['transaction_id'],
                    amount=payload['amount'],
                    currency=payload.get('currency', 'USD'),
                    timestamp=event['timestamp'],
                    event_id=event['event_id']
                )
                lines.append(vertex_script)
        
        # Wrap in transaction
        script = ";\n".join(lines) + ";\ng.tx().commit()"
        return script
    
    @staticmethod
    def _create_transaction_edge(
        from_account: str,
        to_account: str,
        transaction_id: str,
        amount: float,
        currency: str,
        timestamp: str,
        event_id: str
    ) -> str:
        """
        Create transaction edge with idempotent vertex creation.
        
        Uses fold().coalesce() pattern:
        - fold(): Convert stream to list (empty if no vertices)
        - coalesce(): If list empty, create vertex; else use existing
        - This ensures no duplicate vertices
        """
        return f"""
        from_v = g.V().has('account', 'account_id', '{from_account}')
                      .fold()
                      .coalesce(
                          unfold(),
                          addV('account').property('account_id', '{from_account}')
                      ).next()
        to_v = g.V().has('account', 'account_id', '{to_account}')
                    .fold()
                    .coalesce(
                        unfold(),
                        addV('account').property('account_id', '{to_account}')
                    ).next()
        from_v.addEdge('transfer', to_v,
            'transaction_id', '{transaction_id}',
            'amount', {amount},
            'currency', '{currency}',
            'timestamp', '{timestamp}',
            'event_id', '{event_id}'
        )
        """
    
    @staticmethod
    def escape_string(value: str) -> str:
        """Escape special characters for Gremlin"""
        return value.replace("'", "\\'").replace('"', '\\"')


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example events
    events = [
        {
            "event_id": "evt_20260130_153045_001",
            "event_type": "transaction",
            "timestamp": "2026-01-30T15:30:45.123Z",
            "payload": {
                "transaction_id": "TXN_987654321",
                "from_account_id": "ACC_123456",
                "to_account_id": "ACC_789012",
                "amount": 9500.00,
                "currency": "USD"
            }
        },
        {
            "event_id": "evt_20260130_153046_002",
            "event_type": "transaction",
            "timestamp": "2026-01-30T15:30:46.123Z",
            "payload": {
                "transaction_id": "TXN_987654322",
                "from_account_id": "ACC_789012",
                "to_account_id": "ACC_111222",
                "amount": 2500.00,
                "currency": "USD"
            }
        }
    ]
    
    # Build batch script
    builder = GremlinBatchBuilder()
    script = builder.build_transaction_batch(events)
    
    print("Generated Gremlin script:")
    print(script)
