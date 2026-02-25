#!/usr/bin/env python3
"""
Load sample sanctions data into OpenSearch for the Sanctions Screening demo.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src/python"))

from utils.embedding_generator import EmbeddingGenerator
from opensearchpy import OpenSearch

OPENSEARCH_HOST = "opensearch"
OPENSEARCH_PORT = 9200
INDEX_NAME = "sanctions_list"

# Sample sanctions data (OFAC, EU, UN lists)
SANCTIONS_DATA = [
    {"name": "VLADIMIR PUTIN", "entity_id": "OFAC-001", "list": "OFAC", "type": "Individual"},
    {"name": "ALEXEI MOROZOV", "entity_id": "OFAC-002", "list": "OFAC", "type": "Individual"},
    {"name": "DMITRY MEDVEDEV", "entity_id": "OFAC-003", "list": "OFAC", "type": "Individual"},
    {"name": "SERGEI SHOIGU", "entity_id": "OFAC-004", "list": "OFAC", "type": "Individual"},
    {"name": "NIKOLAI PATRUSHEV", "entity_id": "OFAC-005", "list": "OFAC", "type": "Individual"},
    {"name": "BANKI RA",
     "entity_id": "OFAC-006", "list": "OFAC", "type": "Entity"},
    {"name": "ROSSELKHOZBANK", "entity_id": "OFAC-007", "list": "OFAC", "type": "Entity"},
    {"name": "GAZPROMBANK", "entity_id": "OFAC-008", "list": "OFAC", "type": "Entity"},
    {"name": "SBERBANK", "entity_id": "OFAC-009", "list": "OFAC", "type": "Entity"},
    {"name": "VTB BANK", "entity_id": "OFAC-010", "list": "OFAC", "type": "Entity"},
    {"name": "ALEXANDER ZOLOTAREV", "entity_id": "EU-001", "list": "EU", "type": "Individual"},
    {"name": "ANDREY KRIVORUCHKO", "entity_id": "EU-002", "list": "EU", "type": "Individual"},
    {"name": "MIKHAIL MIZINTSEV", "entity_id": "EU-003", "list": "EU", "type": "Individual"},
    {"name": "OLEG DERIPASKA", "entity_id": "EU-004", "list": "EU", "type": "Individual"},
    {"name": "ALISHER USMANOV", "entity_id": "EU-005", "list": "EU", "type": "Individual"},
    {"name": "ROMAN ABRAMOVICH", "entity_id": "EU-006", "list": "EU", "type": "Individual"},
    {"name": "YEVGENY PRIMAKOV", "entity_id": "UN-001", "list": "UN", "type": "Individual"},
    {"name": "GENERAL OIL", "entity_id": "UN-002", "list": "UN", "type": "Entity"},
    {"name": "AL-MADINA COMPANY", "entity_id": "UN-003", "list": "UN", "type": "Entity"},
    {"name": "KIM JONG-UN", "entity_id": "UN-004", "list": "UN", "type": "Individual"},
    {"name": "KIM JONG-IL", "entity_id": "UN-005", "list": "UN", "type": "Individual"},
    {"name": "ALEJANDRO GARCIA", "entity_id": "OFAC-011", "list": "OFAC", "type": "Individual"},
    {"name": "JOSE GOMEZ", "entity_id": "OFAC-012", "list": "OFAC", "type": "Individual"},
    {"name": "CARLOS RUIZ", "entity_id": "EU-007", "list": "EU", "type": "Individual"},
    {"name": "MARIA FERNANDEZ", "entity_id": "EU-008", "list": "EU", "type": "Individual"},
    {"name": "AHMED HASSAN", "entity_id": "UN-006", "list": "UN", "type": "Individual"},
    {"name": "MOHAMMED KHALIF", "entity_id": "UN-007", "list": "UN", "type": "Individual"},
    {"name": "JOHN SMITH", "entity_id": "TEST-001", "list": "TEST", "type": "Individual"},
    {"name": "JOHN SMYTH", "entity_id": "TEST-002", "list": "TEST", "type": "Individual"},
    {"name": "JON SMITH", "entity_id": "TEST-003", "list": "TEST", "type": "Individual"},
    # Add synthetic names matching generated persons for testing
    {"name": "JOSHUA FRENCH", "entity_id": "SYNTH-001", "list": "INTERNAL", "type": "Individual"},
    {"name": "BILLY WARNER", "entity_id": "SYNTH-002", "list": "INTERNAL", "type": "Individual"},
    {"name": "PAUL BROWN", "entity_id": "SYNTH-003", "list": "INTERNAL", "type": "Individual"},
    {"name": "JAMES SPENCE", "entity_id": "SYNTH-004", "list": "INTERNAL", "type": "Individual"},
    {"name": "PHILLIP GARRETT", "entity_id": "SYNTH-005", "list": "INTERNAL", "type": "Individual"},
    {"name": "ROBERT COLLINS", "entity_id": "SYNTH-006", "list": "INTERNAL", "type": "Individual"},
    {"name": "JEFFERY JOSEPH", "entity_id": "SYNTH-007", "list": "INTERNAL", "type": "Individual"},
    {"name": "JEFFREY HARRIS", "entity_id": "SYNTH-008", "list": "INTERNAL", "type": "Individual"},
    {"name": "KRISTEN POWELL", "entity_id": "SYNTH-009", "list": "INTERNAL", "type": "Individual"},
    {"name": "MICHELE BENDER", "entity_id": "SYNTH-010", "list": "INTERNAL", "type": "Individual"},
]


def create_index(client):
    """Create the sanctions_list index with k-NN vector field."""
    if client.indices.exists(index=INDEX_NAME):
        print(f"Index {INDEX_NAME} already exists, deleting...")
        client.indices.delete(index=INDEX_NAME)
    
    index_body = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 1,
            "index": {
                "knn": True,
                "knn.algo_param.ef_search": 512
            }
        },
        "mappings": {
            "properties": {
                "name": {"type": "text"},
                "entity_id": {"type": "keyword"},
                "list": {"type": "keyword"},
                "type": {"type": "keyword"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": 384,
                    "method": {
                        "name": "hnsw",
                        "engine": "faiss",
                        "space_type": "l2"
                    }
                }
            }
        }
    }
    
    client.indices.create(index=INDEX_NAME, body=index_body)
    print(f"Created index: {INDEX_NAME}")


def load_sanctions_data():
    """Load sanctions data into OpenSearch."""
    print("Connecting to OpenSearch...")
    client = OpenSearch(
        hosts=[{"host": OPENSEARCH_HOST, "port": OPENSEARCH_PORT}],
        use_ssl=False,
        verify_certs=False,
        ssl_show_warn=False
    )
    
    # Create index
    create_index(client)
    
    # Generate embeddings
    print("Generating embeddings for sanctions data...")
    generator = EmbeddingGenerator(model_name="mini")
    names = [s["name"] for s in SANCTIONS_DATA]
    embeddings = generator.encode_batch(names)
    
    # Index documents
    print(f"Indexing {len(SANCTIONS_DATA)} sanctions entities...")
    for i, sanction in enumerate(SANCTIONS_DATA):
        doc = {
            "name": sanction["name"],
            "entity_id": sanction["entity_id"],
            "list": sanction["list"],
            "type": sanction["type"],
            "embedding": embeddings[i].tolist()
        }
        client.index(index=INDEX_NAME, id=sanction["entity_id"], body=doc)
    
    # Refresh index
    client.indices.refresh(index=INDEX_NAME)
    
    # Verify
    result = client.count(index=INDEX_NAME)
    print(f"✅ Loaded {result['count']} sanctions entities into {INDEX_NAME}")


if __name__ == "__main__":
    load_sanctions_data()
