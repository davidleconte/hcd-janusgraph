#!/usr/bin/env python
"""
Deterministic Time-Travel Data Generator
=========================================

Generates temporal graph data with validFrom/validTo properties
for time-travel query demonstrations.

Usage:
    python banking/data_generators/scripts/generate_time_travel_data.py [--verify] [--load]

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-03-23
"""

import argparse
import hashlib
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from faker import Faker

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from banking.data_generators.utils.deterministic import reset_counter, seeded_uuid_hex

# Deterministic configuration
DETERMINISTIC_SEED = 42
DETERMINISTIC_COUNTER_START = 2000  # Start after fraud communities data

# Output paths
OUTPUT_DIR = project_root / "exports" / "time-travel"
MANIFEST_PATH = OUTPUT_DIR / "time_travel_manifest.json"

# Reference timestamp for deterministic dates
REFERENCE_TIMESTAMP = datetime(2026, 1, 15, 12, 0, 0)


def generate_time_travel_data_deterministic(
    seed: int = DETERMINISTIC_SEED,
    counter_start: int = DETERMINISTIC_COUNTER_START
) -> Dict[str, Any]:
    """
    Generate temporal graph data for time-travel demonstrations.
    
    Creates vertices and edges with validFrom/validTo properties
    that allow querying the graph state at any historical point.
    
    Args:
        seed: Random seed for Faker and random module
        counter_start: Starting value for seeded UUID counter
        
    Returns:
        Dict with temporal vertices, edges, and checksums
    """
    # Reset deterministic counter with seed
    reset_counter(counter_start, seed=seed)
    
    # Reset random state
    random.seed(seed)
    Faker.seed(seed)
    
    faker = Faker("en_US")
    faker.seed_instance(seed)
    
    # Define time periods for evolution
    periods = [
        {
            "name": "initial",
            "start": datetime(2026, 1, 1, 0, 0, 0),
            "end": datetime(2026, 1, 7, 23, 59, 59),
            "description": "Initial graph state"
        },
        {
            "name": "growth",
            "start": datetime(2026, 1, 8, 0, 0, 0),
            "end": datetime(2026, 1, 14, 23, 59, 59),
            "description": "Network expansion"
        },
        {
            "name": "peak",
            "start": datetime(2026, 1, 15, 0, 0, 0),
            "end": datetime(2026, 1, 21, 23, 59, 59),
            "description": "Peak activity"
        },
        {
            "name": "suspicious",
            "start": datetime(2026, 1, 22, 0, 0, 0),
            "end": datetime(2026, 1, 28, 23, 59, 59),
            "description": "Suspicious pattern emergence"
        },
        {
            "name": "current",
            "start": datetime(2026, 1, 29, 0, 0, 0),
            "end": datetime(2026, 2, 4, 23, 59, 59),
            "description": "Current state"
        }
    ]
    
    vertices = []
    edges = []
    seen_vertices = set()
    
    # Generate persons with temporal validity
    person_count = 20
    
    for i in range(person_count):
        person_id = seeded_uuid_hex(f"tt-person-{i}")
        person_name = faker.name()
        
        # Assign to a period based on index
        period_idx = min(i // 5, len(periods) - 1)
        period = periods[period_idx]
        
        # Add some variance within period
        day_offset = random.randint(0, 6)
        valid_from = period["start"] + timedelta(days=day_offset)
        
        # Most vertices are still valid, some have expired
        if i < person_count - 3:  # Last 3 are "deleted"
            valid_to = datetime(2026, 12, 31, 23, 59, 59)
        else:
            valid_to = periods[period_idx + 1]["start"] if period_idx + 1 < len(periods) else datetime(2026, 2, 4, 23, 59, 59)
        
        risk_score = random.uniform(0.1, 0.9) if i >= 15 else random.uniform(0.05, 0.3)  # Last 5 are higher risk
        
        vertices.append({
            "id": person_id,
            "label": "Person",
            "properties": {
                "personId": person_id,
                "name": person_name,
                "role": "customer",
                "riskScore": round(risk_score, 2),
                "validFrom": valid_from.isoformat(),
                "validTo": valid_to.isoformat(),
                "createdAt": valid_from.isoformat()
            }
        })
        seen_vertices.add(person_id)
    
    # Generate accounts linked to persons
    person_ids = [v["id"] for v in vertices]
    
    for i, person_id in enumerate(person_ids):
        account_id = seeded_uuid_hex(f"tt-account-{i}")
        account_number = faker.iban()[:20]
        
        # Match account validity to person
        person_vertex = next(v for v in vertices if v["id"] == person_id)
        valid_from = datetime.fromisoformat(person_vertex["properties"]["validFrom"]) + timedelta(days=random.randint(0, 3))
        valid_to = person_vertex["properties"]["validTo"]
        
        vertices.append({
            "id": account_id,
            "label": "Account",
            "properties": {
                "accountId": account_id,
                "accountNumber": account_number,
                "balance": round(random.uniform(1000, 100000), 2),
                "validFrom": valid_from.isoformat(),
                "validTo": valid_to,
                "createdAt": valid_from.isoformat()
            }
        })
        
        # Create OWNS edge
        edges.append({
            "outV": person_id,
            "inV": account_id,
            "label": "owns",
            "properties": {
                "validFrom": valid_from.isoformat(),
                "validTo": valid_to,
                "strength": 1.0
            }
        })
    
    # Generate transactions between accounts with temporal validity
    account_ids = [v["id"] for v in vertices if v["label"] == "Account"]
    
    transaction_count = 30
    for i in range(transaction_count):
        source_idx = random.randint(0, len(account_ids) - 1)
        target_idx = random.randint(0, len(account_ids) - 1)
        
        if source_idx == target_idx:
            continue
        
        source_id = account_ids[source_idx]
        target_id = account_ids[target_idx]
        
        # Determine transaction timing
        period_idx = random.randint(0, len(periods) - 1)
        period = periods[period_idx]
        
        day_offset = random.randint(0, 6)
        hour_offset = random.randint(0, 23)
        valid_from = period["start"] + timedelta(days=day_offset, hours=hour_offset)
        valid_to = datetime(2026, 12, 31, 23, 59, 59)  # Transactions persist
        
        # Higher amount for suspicious period
        if period["name"] == "suspicious":
            amount = round(random.uniform(9000, 15000), 2)  # Just under reporting threshold
        else:
            amount = round(random.uniform(100, 5000), 2)
        
        edges.append({
            "outV": source_id,
            "inV": target_id,
            "label": "transferred",
            "properties": {
                "amount": amount,
                "currency": "USD",
                "validFrom": valid_from.isoformat(),
                "validTo": valid_to.isoformat(),
                "createdAt": valid_from.isoformat()
            }
        })
    
    # Calculate checksums
    vertices_checksum = hashlib.sha256(
        json.dumps(sorted(vertices, key=lambda x: x["id"]), sort_keys=True).encode()
    ).hexdigest()[:16]
    
    edges_checksum = hashlib.sha256(
        json.dumps(sorted(edges, key=lambda x: f"{x['outV']}->{x['inV']}"), sort_keys=True).encode()
    ).hexdigest()[:16]
    
    return {
        "seed": seed,
        "counter_start": counter_start,
        "periods": [{"name": p["name"], "start": p["start"].isoformat(), "end": p["end"].isoformat(), "description": p["description"]} for p in periods],
        "vertices": vertices,
        "edges": edges,
        "checksums": {
            "vertices": vertices_checksum,
            "edges": edges_checksum,
            "total_vertices": len(vertices),
            "total_edges": len(edges),
            "total_persons": len([v for v in vertices if v["label"] == "Person"]),
            "total_accounts": len([v for v in vertices if v["label"] == "Account"]),
            "total_transactions": len([e for e in edges if e["label"] == "transferred"])
        }
    }


def save_manifest(data: Dict[str, Any]) -> Path:
    """Save time-travel manifest to exports directory."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(MANIFEST_PATH, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    
    return MANIFEST_PATH


def _detect_janusgraph_host_port() -> tuple:
    """Auto-detect JanusGraph host and port based on environment."""
    import os
    import socket
    
    # Check environment variables first
    env_host = os.getenv("JANUSGRAPH_HOST")
    env_port = os.getenv("JANUSGRAPH_PORT")
    if env_host and env_port:
        return env_host, int(env_port)
    
    # Try to detect container environment
    try:
        socket.gethostbyname("janusgraph-server")
        return "janusgraph-server", 8182  # Internal container port
    except socket.gaierror:
        pass
    
    # Fallback to localhost with mapped port
    return "localhost", 18182


def load_into_janusgraph(data: Dict[str, Any], host: str = None, port: int = None) -> Dict[str, int]:
    """
    Load time-travel data into JanusGraph.
    
    Returns:
        Dict with vertex and edge counts
    """
    from src.python.client.janusgraph_client import JanusGraphClient
    
    # Auto-detect host/port if not provided
    if host is None or port is None:
        detected_host, detected_port = _detect_janusgraph_host_port()
        host = host or detected_host
        port = port or detected_port
    
    vertices_created = 0
    edges_created = 0
    
    with JanusGraphClient(host=host, port=port, use_ssl=False, verify_certs=False) as client:
        # Create vertices
        for vertex in data["vertices"]:
            label = vertex["label"]
            props = vertex["properties"]
            
            prop_strs = []
            for k, v in props.items():
                if isinstance(v, str):
                    # Escape single quotes in strings
                    v_escaped = v.replace("'", "\\'")
                    prop_strs.append(f".property('{k}', '{v_escaped}')")
                elif isinstance(v, float):
                    prop_strs.append(f".property('{k}', {v}f)")
                else:
                    prop_strs.append(f".property('{k}', {v})")
            
            query = f"""
                g.V().has('{label.lower()}Id', '{vertex["id"]}').fold().coalesce(
                    unfold(),
                    addV('{label}'){"".join(prop_strs)}
                )
            """
            client.execute(query)
            vertices_created += 1
        
        # Create edges
        for edge in data["edges"]:
            source_label = "person" if edge["label"] == "owns" else "account"
            target_label = "account"
            
            props = edge.get("properties", {})
            prop_strs = []
            for k, v in props.items():
                if isinstance(v, str):
                    v_escaped = v.replace("'", "\\'")
                    prop_strs.append(f".property('{k}', '{v_escaped}')")
                elif isinstance(v, float):
                    prop_strs.append(f".property('{k}', {v}f)")
                else:
                    prop_strs.append(f".property('{k}', {v})")
            
            query = f"""
                g.V().has('{source_label}Id', '{edge["outV"]}').as('source').
                V().has('{target_label}Id', '{edge["inV"]}').
                coalesce(
                    inE('{edge["label"]}').where(outV().as('source')),
                    addE('{edge["label"]}').from('source'){"".join(prop_strs)}
                )
            """
            client.execute(query)
            edges_created += 1
    
    return {"vertices": vertices_created, "edges": edges_created}


def verify_determinism() -> bool:
    """
    Verify that generation is deterministic using subprocess isolation.
    """
    import subprocess
    
    print("Running first generation in isolated process...")
    result1 = subprocess.run(
        [sys.executable, "-c", 
         "from banking.data_generators.scripts.generate_time_travel_data import generate_time_travel_data_deterministic; "
         "import json; data = generate_time_travel_data_deterministic(seed=42); "
         "print(json.dumps(data['checksums']))"],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    checksums1 = json.loads(result1.stdout.strip())
    
    print("Running second generation in isolated process...")
    result2 = subprocess.run(
        [sys.executable, "-c", 
         "from banking.data_generators.scripts.generate_time_travel_data import generate_time_travel_data_deterministic; "
         "import json; data = generate_time_travel_data_deterministic(seed=42); "
         "print(json.dumps(data['checksums']))"],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    checksums2 = json.loads(result2.stdout.strip())
    
    if checksums1 != checksums2:
        print(f"❌ NON-DETERMINISTIC: Checksums differ!")
        print(f"   Run 1: {checksums1}")
        print(f"   Run 2: {checksums2}")
        return False
    
    print(f"✅ DETERMINISTIC: Checksums match!")
    print(f"   Vertices: {checksums1['total_vertices']} (checksum: {checksums1['vertices']})")
    print(f"   Edges: {checksums1['total_edges']} (checksum: {checksums1['edges']})")
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate deterministic time-travel data")
    parser.add_argument("--verify", action="store_true", help="Verify determinism")
    parser.add_argument("--load", action="store_true", help="Load data into JanusGraph")
    parser.add_argument("--seed", type=int, default=DETERMINISTIC_SEED, help="Random seed")
    args = parser.parse_args()
    
    if args.verify:
        success = verify_determinism()
        sys.exit(0 if success else 1)
    
    # Generate data
    print(f"Generating time-travel data with seed={args.seed}...")
    data = generate_time_travel_data_deterministic(seed=args.seed)
    
    # Save manifest
    manifest_path = save_manifest(data)
    print(f"Saved manifest to: {manifest_path}")
    
    # Print summary
    print(f"\nGenerated {data['checksums']['total_vertices']} vertices and {data['checksums']['total_edges']} edges")
    print(f"Persons: {data['checksums']['total_persons']}")
    print(f"Accounts: {data['checksums']['total_accounts']}")
    print(f"Transactions: {data['checksums']['total_transactions']}")
    
    print("\nTime periods:")
    for period in data["periods"]:
        print(f"  {period['name']}: {period['start']} to {period['end']} - {period['description']}")
    
    # Load into JanusGraph if requested
    if args.load:
        print("\nLoading into JanusGraph...")
        counts = load_into_janusgraph(data)
        print(f"Created {counts['vertices']} vertices and {counts['edges']} edges")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
