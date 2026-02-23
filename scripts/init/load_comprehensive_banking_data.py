#!/usr/bin/env python3
"""
Comprehensive Banking Data Loader
==================================

Generates and loads realistic banking data into JanusGraph and OpenSearch.
Uses the MasterOrchestrator for data generation and JanusGraphLoader for loading.

This creates:
- 500 persons (with risk profiles)
- 50 companies
- 500 accounts
- 5,000 transactions
- 500 communications
- Inject fraud/AML patterns (structuring, fraud rings, etc.)
- Sanctions data in OpenSearch

Usage:
    python scripts/init/load_comprehensive_banking_data.py
"""

import sys
import os
import time
import json

# Add project to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from banking.data_generators.orchestration import GenerationConfig, MasterOrchestrator
from banking.data_generators.loaders.janusgraph_loader import JanusGraphLoader
from banking.data_generators.utils.data_models import Person, Company, Account, Transaction, Communication

# Also load sanctions into OpenSearch
from src.python.utils.embedding_generator import EmbeddingGenerator
from opensearchpy import OpenSearch

OPENSEARCH_HOST = "localhost"
OPENSEARCH_PORT = 9200
SANCTIONS_INDEX = "sanctions_list"

# Comprehensive sanctions data
SANCTIONS_DATA = [
    {"name": "VLADIMIR PUTIN", "entity_id": "OFAC-001", "list": "OFAC", "type": "Individual"},
    {"name": "ALEXEI MOROZOV", "entity_id": "OFAC-002", "list": "OFAC", "type": "Individual"},
    {"name": "DMITRY MEDVEDEV", "entity_id": "OFAC-003", "list": "OFAC", "type": "Individual"},
    {"name": "SERGEI SHOIGU", "entity_id": "OFAC-004", "list": "OFAC", "type": "Individual"},
    {"name": "NIKOLAI PATRUSHEV", "entity_id": "OFAC-005", "list": "OFAC", "type": "Individual"},
    {"name": "BANKI RA", "entity_id": "OFAC-006", "list": "OFAC", "type": "Entity"},
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
    {"name": "JOHNNY SMITH", "entity_id": "TEST-004", "list": "TEST", "type": "Individual"},
    {"name": "JUAN GARCIA", "entity_id": "OFAC-013", "list": "OFAC", "type": "Individual"},
    {"name": "IVANOV ANDREI", "entity_id": "OFAC-014", "list": "OFAC", "type": "Individual"},
    {"name": "ZHANG WEI", "entity_id": "OFAC-015", "list": "OFAC", "type": "Individual"},
    {"name": "ALI KHAN", "entity_id": "OFAC-016", "list": "OFAC", "type": "Individual"},
    {"name": "RUSSIAN OIL COMPANY", "entity_id": "OFAC-017", "list": "OFAC", "type": "Entity"},
    {"name": "GLOBAL TRADING LLC", "entity_id": "EU-009", "list": "EU", "type": "Entity"},
    {"name": "ASIA PACIFIC HOLDINGS", "entity_id": "EU-010", "list": "EU", "type": "Entity"},
    {"name": "MIDDLE EAST INVESTMENTS", "entity_id": "UN-008", "list": "UN", "type": "Entity"},
    {"name": "HAMAS FOUNDATION", "entity_id": "UN-009", "list": "UN", "type": "Entity"},
    {"name": "HEZBOLLAH TRADING", "entity_id": "UN-010", "list": "UN", "type": "Entity"},
]


def load_sanctions_to_opensearch():
    """Load sanctions data into OpenSearch."""
    print("\n📥 Loading sanctions data to OpenSearch...")
    
    client = OpenSearch(
        hosts=[{"host": OPENSEARCH_HOST, "port": OPENSEARCH_PORT}],
        use_ssl=False,
        verify_certs=False,
        ssl_show_warn=False
    )
    
    # Delete and recreate index
    if client.indices.exists(index=SANCTIONS_INDEX):
        client.indices.delete(index=SANCTIONS_INDEX)
    
    client.indices.create(index=SANCTIONS_INDEX, body={
        "settings": {"number_of_shards": 1, "number_of_replicas": 1, "index": {"knn": True}},
        "mappings": {
            "properties": {
                "name": {"type": "text"},
                "entity_id": {"type": "keyword"},
                "list": {"type": "keyword"},
                "type": {"type": "keyword"},
                "embedding": {"type": "knn_vector", "dimension": 384, "method": {"name": "hnsw", "engine": "faiss"}}
            }
        }
    })
    
    # Generate embeddings
    generator = EmbeddingGenerator(model_name="mini")
    names = [s["name"] for s in SANCTIONS_DATA]
    embeddings = generator.encode_batch(names)
    
    # Index documents
    for i, sanction in enumerate(SANCTIONS_DATA):
        doc = {
            "name": sanction["name"],
            "entity_id": sanction["entity_id"],
            "list": sanction["list"],
            "type": sanction["type"],
            "embedding": embeddings[i].tolist()
        }
        client.index(index=SANCTIONS_INDEX, id=sanction["entity_id"], body=doc)
    
    client.indices.refresh(index=SANCTIONS_INDEX)
    result = client.count(index=SANCTIONS_INDEX)
    print(f"   ✅ Loaded {result['count']} sanctions entities")


def generate_and_load_janusgraph():
    """Generate banking data and load to JanusGraph."""
    print("\n🏦 Generating banking data...")
    print("   This will create:")
    print("   - 500 persons with risk profiles")
    print("   - 50 companies")
    print("   - 500 accounts")
    print("   - 5,000 transactions")
    print("   - 500 communications")
    print("   - Fraud/AML patterns")
    
    # Configuration
    config = GenerationConfig(
        seed=42,
        person_count=500,
        company_count=50,
        account_count=500,
        transaction_count=5000,
        communication_count=500,
        # Pattern counts - inject financial crimes
        structuring_patterns=3,
        fraud_ring_patterns=3,
        insider_trading_patterns=2,
        tbml_patterns=2,
        cato_patterns=2,
        duration_days=365,
        output_dir=Path("./output"),
    )
    
    # Generate data
    print("\n🔄 Generating synthetic data...")
    orchestrator = MasterOrchestrator(config)
    result = orchestrator.generate_all()
    
    # Read data from output files and convert to model objects
    output_dir = config.output_dir
    
    with open(output_dir / "persons.json") as f:
        persons_data = json.load(f)
    with open(output_dir / "companies.json") as f:
        companies_data = json.load(f)
    with open(output_dir / "accounts.json") as f:
        accounts_data = json.load(f)
    with open(output_dir / "transactions.json") as f:
        transactions_data = json.load(f)
    with open(output_dir / "communications.json") as f:
        communications_data = json.load(f)
    
    # Convert to model objects
    data = {
        'persons': [Person(**p) for p in persons_data],
        'companies': [Company(**c) for c in companies_data],
        'accounts': [Account(**a) for a in accounts_data],
        'transactions': [Transaction(**t) for t in transactions_data],
        'communications': [Communication(**c) for c in communications_data],
    }
    
    print(f"   Generated:")
    print(f"   - {len(data['persons'])} persons")
    print(f"   - {len(data['companies'])} companies")
    print(f"   - {len(data['accounts'])} accounts")
    print(f"   - {len(data['transactions'])} transactions")
    print(f"   - {len(data['communications'])} communications")
    
    # Load to JanusGraph
    print("\n📊 Loading to JanusGraph...")
    loader = JanusGraphLoader(
        url="ws://localhost:18182/gremlin"
    )
    loader.connect()
    
    # Clear existing data
    loader.clear_graph()
    
    # Load in dependency order
    person_id_map = loader.load_persons(data['persons'])
    print(f"   ✅ Loaded {len(person_id_map)} persons")
    
    company_id_map = loader.load_companies(data['companies'])
    print(f"   ✅ Loaded {len(company_id_map)} companies")
    
    account_id_map = loader.load_accounts(data['accounts'], person_id_map, company_id_map)
    print(f"   ✅ Loaded {len(account_id_map)} accounts")
    
    loader.load_transactions(data['transactions'], account_id_map)
    print(f"   ✅ Loaded transactions")
    
    loader.load_communications(data['communications'], person_id_map)
    print(f"   ✅ Loaded communications")
    
    stats = {"vertices_loaded": loader.stats["vertices_created"], "edges_loaded": loader.stats["edges_created"]}
    
    print(f"   ✅ Loaded to JanusGraph:")
    print(f"   - {stats.get('vertices_loaded', 0)} vertices")
    print(f"   - {stats.get('edges_loaded', 0)} edges")
    
    return stats


def main():
    """Main execution."""
    print("=" * 70)
    print("COMPREHENSIVE BANKING DATA LOADER")
    print("=" * 70)
    
    start_time = time.time()
    
    # Load JanusGraph data
    generate_and_load_janusgraph()
    
    # Load OpenSearch data
    load_sanctions_to_opensearch()
    
    elapsed = time.time() - start_time
    print(f"\n⏱️  Total time: {elapsed:.1f} seconds")
    print("\n✅ Data loading complete!")
    print("\n📋 Summary:")
    print("   - JanusGraph: Full banking graph with persons, companies, accounts, transactions")
    print("   - OpenSearch: Sanctions list with vector embeddings for fuzzy matching")
    print("   - Ready for notebook exploration!")


if __name__ == "__main__":
    from pathlib import Path
    main()
