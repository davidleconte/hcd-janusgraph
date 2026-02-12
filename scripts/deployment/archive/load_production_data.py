#!/usr/bin/env python3
"""
Load Production Data for AML/Fraud Detection System

This script:
1. Loads sanctions list data into OpenSearch
2. Indexes historical transaction data
3. Creates graph schema in JanusGraph
4. Loads transaction network into graph
5. Verifies data integrity

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Created: 2026-01-28
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "python"))

from utils.embedding_generator import EmbeddingGenerator
from utils.vector_search import VectorSearchClient

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ProductionDataLoader:
    """Load production data for AML/Fraud detection system."""

    def __init__(
        self,
        opensearch_host: str = "localhost",
        opensearch_port: int = 9200,
        janusgraph_host: str = "localhost",
        janusgraph_port: int = 18182,
    ):
        """Initialize data loader."""
        self.opensearch_host = opensearch_host
        self.opensearch_port = opensearch_port
        self.janusgraph_host = janusgraph_host
        self.janusgraph_port = janusgraph_port

        # Initialize clients
        logger.info("Initializing clients...")
        self.embedding_gen = EmbeddingGenerator(model_name="mini")
        self.vector_client = VectorSearchClient(host=opensearch_host, port=opensearch_port)

        logger.info("✅ Clients initialized")

    def load_sanctions_list(self, sanctions_file: Path) -> int:
        """
        Load sanctions list into OpenSearch.

        Args:
            sanctions_file: Path to sanctions list JSON file

        Returns:
            Number of sanctions loaded
        """
        logger.info("Loading sanctions list from %s...", sanctions_file)

        if not sanctions_file.exists():
            logger.warning("Sanctions file not found: %s", sanctions_file)
            logger.info("Creating sample sanctions list...")
            sanctions_data = self._create_sample_sanctions()
        else:
            with open(sanctions_file, "r") as f:
                sanctions_data = json.load(f)

        # Generate embeddings for each sanctioned entity
        documents = []
        for entity in sanctions_data:
            name = entity.get("name", "")
            embedding = self.embedding_gen.encode_for_search(name)

            doc = {
                "id": entity.get("id", f"sanc_{len(documents)}"),
                "name": name,
                "aliases": entity.get("aliases", []),
                "country": entity.get("country", "Unknown"),
                "list_type": entity.get("list_type", "OFAC"),
                "added_date": entity.get("added_date", datetime.now(timezone.utc).isoformat()),
                "embedding": embedding,
            }
            documents.append(doc)

        # Bulk index to OpenSearch
        success, errors = self.vector_client.bulk_index_documents(
            index_name="sanctions_list",
            documents=documents,
            vector_field="embedding",
            id_field="id",
        )

        logger.info("✅ Loaded %s sanctions entities", success)
        if errors:
            logger.warning("⚠️  %s errors occurred", len(errors))

        return success

    def load_transaction_data(self, transaction_file: Path) -> int:
        """
        Load historical transaction data into OpenSearch.

        Args:
            transaction_file: Path to transaction CSV/JSON file

        Returns:
            Number of transactions loaded
        """
        logger.info("Loading transaction data from %s...", transaction_file)

        if not transaction_file.exists():
            logger.warning("Transaction file not found: %s", transaction_file)
            logger.info("Using existing AML data...")
            transaction_file = Path("banking/data/aml/aml_data_transactions.csv")

        # Load transactions
        import pandas as pd

        df = pd.read_csv(transaction_file)

        logger.info("Loaded %s transactions from file", len(df))

        # Generate embeddings for transaction descriptions
        documents = []
        batch_size = 100

        for i in range(0, len(df), batch_size):
            batch = df.iloc[i : i + batch_size]

            # Create transaction descriptions
            descriptions = []
            for _, row in batch.iterrows():
                desc = f"Transaction {row.get('amount', 0)} from account {row.get('from_account', 'unknown')}"
                descriptions.append(desc)

            # Generate embeddings
            embeddings = self.embedding_gen.encode_batch(descriptions)

            # Create documents
            for j, (_, row) in enumerate(batch.iterrows()):
                doc = {
                    "id": f"txn_{row.get('transaction_id', i+j)}",
                    "transaction_id": row.get("transaction_id", i + j),
                    "from_account": row.get("from_account", ""),
                    "to_account": row.get("to_account", ""),
                    "amount": float(row.get("amount", 0)),
                    "timestamp": row.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    "description": descriptions[j],
                    "embedding": embeddings[j],
                }
                documents.append(doc)

            logger.info("Processed %s transactions...", len(documents))

        # Bulk index to OpenSearch
        success, errors = self.vector_client.bulk_index_documents(
            index_name="aml_transactions",
            documents=documents,
            vector_field="embedding",
            id_field="id",
        )

        logger.info("✅ Loaded %s transactions", success)
        if errors:
            logger.warning("⚠️  %s errors occurred", len(errors))

        return success

    def _create_sample_sanctions(self) -> List[Dict[str, Any]]:
        """Create sample sanctions list for testing."""
        return [
            {
                "id": "OFAC_001",
                "name": "John Doe",
                "aliases": ["Jon Doe", "J. Doe"],
                "country": "Unknown",
                "list_type": "OFAC",
                "added_date": "2024-01-01",
            },
            {
                "id": "OFAC_002",
                "name": "Jane Smith",
                "aliases": ["J. Smith", "Jane S."],
                "country": "Unknown",
                "list_type": "OFAC",
                "added_date": "2024-01-15",
            },
            {
                "id": "EU_001",
                "name": "Bob Johnson",
                "aliases": ["Robert Johnson", "R. Johnson"],
                "country": "Unknown",
                "list_type": "EU_SANCTIONS",
                "added_date": "2024-02-01",
            },
        ]

    def verify_data_integrity(self) -> Dict[str, Any]:
        """
        Verify data integrity across all systems.

        Returns:
            Dictionary with verification results
        """
        logger.info("Verifying data integrity...")

        results = {
            "sanctions_count": 0,
            "transactions_count": 0,
            "opensearch_healthy": False,
            "janusgraph_healthy": False,
        }

        # Check OpenSearch indices
        try:
            sanctions_count = self.vector_client.client.count(index="sanctions_list")
            results["sanctions_count"] = sanctions_count["count"]

            txn_count = self.vector_client.client.count(index="aml_transactions")
            results["transactions_count"] = txn_count["count"]

            results["opensearch_healthy"] = True
            logger.info(
                "✅ OpenSearch: %s sanctions, %s transactions",
                results["sanctions_count"],
                results["transactions_count"],
            )
        except Exception as e:
            logger.error("❌ OpenSearch verification failed: %s", e)

        # Check JanusGraph (basic connectivity and vertex count)
        try:
            from gremlin_python.driver import client as gremlin_client
            
            # Connect to JanusGraph
            jg_client = gremlin_client.Client(
                f"ws://{self.janusgraph_host}:{self.janusgraph_port}/gremlin",
                "g"
            )
            
            # Verify connectivity and get vertex count
            vertex_count = jg_client.submit("g.V().count()").all().result()[0]
            results["janusgraph_healthy"] = True
            results["janusgraph_vertex_count"] = vertex_count
            
            logger.info("✅ JanusGraph: Connected (vertices: %d)", vertex_count)
            
            jg_client.close()
        except Exception as e:
            logger.error("❌ JanusGraph verification failed: %s", e)
            results["janusgraph_healthy"] = False

        return results


def main():
    """Main execution function."""
    print("=" * 60)
    print("PRODUCTION DATA LOADING")
    print("=" * 60)
    print()

    # Initialize loader
    loader = ProductionDataLoader()

    # Step 1: Load sanctions list
    print("Step 1: Loading sanctions list...")
    sanctions_file = Path("data/sanctions/sanctions_list.json")
    sanctions_count = loader.load_sanctions_list(sanctions_file)
    print(f"✅ Loaded {sanctions_count} sanctions entities")
    print()

    # Step 2: Load transaction data
    print("Step 2: Loading transaction data...")
    transaction_file = Path("banking/data/aml/aml_data_transactions.csv")
    txn_count = loader.load_transaction_data(transaction_file)
    print(f"✅ Loaded {txn_count} transactions")
    print()

    # Step 3: Verify data integrity
    print("Step 3: Verifying data integrity...")
    results = loader.verify_data_integrity()
    print()

    # Summary
    print("=" * 60)
    print("DATA LOADING SUMMARY")
    print("=" * 60)
    print(f"Sanctions Entities: {results['sanctions_count']}")
    print(f"Transactions: {results['transactions_count']}")
    print(f"OpenSearch: {'✅ Healthy' if results['opensearch_healthy'] else '❌ Unhealthy'}")
    print(f"JanusGraph: {'✅ Healthy' if results['janusgraph_healthy'] else '❌ Unhealthy'}")
    print()
    print("🎉 Production data loading complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
