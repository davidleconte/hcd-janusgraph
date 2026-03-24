#!/usr/bin/env python
"""
Deterministic Graph ML Data Generator
======================================

Generates graph data optimized for machine learning:
1. Structured communities with known cluster membership
2. Anomalous nodes for detection testing
3. Risk-labeled nodes for prediction validation
4. Diverse node types and relationship patterns

Usage:
    python banking/data_generators/scripts/generate_graph_ml_data.py [--verify] [--load]

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-03-23
"""

import argparse
import hashlib
import json
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set

from faker import Faker

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from banking.data_generators.utils.deterministic import reset_counter, seeded_uuid_hex

# Deterministic configuration
DETERMINISTIC_SEED = 42
DETERMINISTIC_COUNTER_START = 4000  # Start after entity resolution data

# Output paths
OUTPUT_DIR = project_root / "exports" / "graph-ml"
MANIFEST_PATH = OUTPUT_DIR / "graph_ml_manifest.json"


def generate_graph_ml_data_deterministic(
    seed: int = DETERMINISTIC_SEED,
    counter_start: int = DETERMINISTIC_COUNTER_START
) -> Dict[str, Any]:
    """
    Generate graph data for ML training and testing.
    
    Creates:
    1. Distinct communities (clusters) for embedding validation
    2. Known anomalies for detection testing
    3. Risk-labeled nodes for prediction benchmarking
    4. Mixed node types (Person, Company, Account)
    
    Args:
        seed: Random seed
        counter_start: Starting counter for UUIDs
        
    Returns:
        Dict with vertices, edges, and ground truth
    """
    reset_counter(counter_start, seed=seed)
    random.seed(seed)
    Faker.seed(seed)
    
    faker = Faker("en_US")
    faker.seed_instance(seed)
    
    vertices = []
    edges = []
    
    # Ground truth tracking
    ground_truth = {
        "clusters": {},  # cluster_id -> list of node_ids
        "anomalies": [],  # node_ids of known anomalies
        "risk_labels": {},  # node_id -> risk_level
    }
    
    # ========================================
    # CLUSTER 1: Low-risk retail customers
    # ========================================
    cluster_1_members = []
    
    # Create a cohesive group of retail customers
    cluster_1_base_id = seeded_uuid_hex("gml-c1-")
    for i in range(12):
        person_id = seeded_uuid_hex(f"gml-c1-p{i}-")
        name = faker.name()
        
        vertices.append({
            "id": person_id,
            "label": "Person",
            "properties": {
                "personId": person_id,
                "name": name,
                "dateOfBirth": f"198{random.randint(0,9)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "phone": faker.phone_number(),
                "email": f"{name.lower().replace(' ', '.')}@email.com",
                "role": "retail_customer",
                "riskScore": round(random.uniform(0.05, 0.20), 2),
                "segment": "retail"
            }
        })
        cluster_1_members.append(person_id)
        ground_truth["risk_labels"][person_id] = "low"
    
    # Create accounts for cluster 1
    for i, person_id in enumerate(cluster_1_members):
        account_id = seeded_uuid_hex(f"gml-c1-a{i}-")
        vertices.append({
            "id": account_id,
            "label": "Account",
            "properties": {
                "accountId": account_id,
                "accountNumber": f"100{random.randint(100000, 999999)}",
                "accountType": "checking",
                "balance": round(random.uniform(1000, 25000), 2),
                "openedDate": f"202{random.randint(0,5)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
            }
        })
        
        edges.append({
            "outV": person_id,
            "inV": account_id,
            "label": "owns_account",
            "properties": {"since": "2023-01-01"}
        })
        
        cluster_1_members.append(account_id)
        ground_truth["risk_labels"][account_id] = "low"
    
    # Create internal connections (knows relationships)
    for i in range(len(cluster_1_members) // 2 - 1):
        edges.append({
            "outV": cluster_1_members[i],
            "inV": cluster_1_members[i + 1],
            "label": "knows",
            "properties": {"since": "2022-06-15"}
        })
    
    ground_truth["clusters"]["cluster_1_retail"] = cluster_1_members
    
    # ========================================
    # CLUSTER 2: Medium-risk SME business network
    # ========================================
    cluster_2_members = []
    
    # SME company
    sme_company_id = seeded_uuid_hex("gml-c2-co-")
    vertices.append({
        "id": sme_company_id,
        "label": "Company",
        "properties": {
            "companyId": sme_company_id,
            "name": "TechStart Solutions LLC",
            "jurisdiction": "US",
            "incorporationDate": "2020-03-15",
            "industry": "technology",
            "employeeCount": 45,
            "annualRevenue": 5000000
        }
    })
    cluster_2_members.append(sme_company_id)
    ground_truth["risk_labels"][sme_company_id] = "medium"
    
    # Directors and employees
    for i in range(8):
        person_id = seeded_uuid_hex(f"gml-c2-p{i}-")
        name = faker.name()
        role = "director" if i < 2 else "employee"
        
        vertices.append({
            "id": person_id,
            "label": "Person",
            "properties": {
                "personId": person_id,
                "name": name,
                "dateOfBirth": f"197{random.randint(0,9)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "phone": faker.phone_number(),
                "email": f"{name.lower().replace(' ', '.')}@techstart.com",
                "role": role,
                "riskScore": round(random.uniform(0.15, 0.35), 2),
                "segment": "sme"
            }
        })
        
        # Director relationship
        edges.append({
            "outV": person_id,
            "inV": sme_company_id,
            "label": "director_of" if role == "director" else "employed_by",
            "properties": {"since": f"202{random.randint(0,3)}-01-01"}
        })
        
        cluster_2_members.append(person_id)
        ground_truth["risk_labels"][person_id] = "medium"
    
    # Business account
    business_account_id = seeded_uuid_hex("gml-c2-ba-")
    vertices.append({
        "id": business_account_id,
        "label": "Account",
        "properties": {
            "accountId": business_account_id,
            "accountNumber": "200123456",
            "accountType": "business",
            "balance": 150000.00,
            "openedDate": "2020-04-01"
        }
    })
    
    edges.append({
        "outV": sme_company_id,
        "inV": business_account_id,
        "label": "owns_account",
        "properties": {"since": "2020-04-01"}
    })
    cluster_2_members.append(business_account_id)
    ground_truth["risk_labels"][business_account_id] = "medium"
    
    ground_truth["clusters"]["cluster_2_sme"] = cluster_2_members
    
    # ========================================
    # CLUSTER 3: High-risk international trading
    # ========================================
    cluster_3_members = []
    
    # Multiple shell companies
    for i in range(3):
        company_id = seeded_uuid_hex(f"gml-c3-co{i}-")
        jurisdictions = ["VG", "KY", "SC"]
        names = ["Global Trade Ventures Ltd", "Oceanic Holdings International", "Pacific Commerce Group"]
        
        vertices.append({
            "id": company_id,
            "label": "Company",
            "properties": {
                "companyId": company_id,
                "name": names[i],
                "jurisdiction": jurisdictions[i],
                "incorporationDate": f"201{8+i}-06-01",
                "industry": "trading",
                "employeeCount": 0,
                "annualRevenue": 0,
                "shellCompany": True
            }
        })
        cluster_3_members.append(company_id)
        ground_truth["risk_labels"][company_id] = "high"
    
    # UBO behind the network
    ubo_id = seeded_uuid_hex("gml-c3-ubo-")
    vertices.append({
        "id": ubo_id,
        "label": "Person",
        "properties": {
            "personId": ubo_id,
            "name": "Viktor Petrov",
            "nationality": "RU",
            "dateOfBirth": "1975-08-22",
            "passport": "RU12345678",
            "role": "ubo",
            "riskScore": 0.85,
            "pep": True,
            "segment": "international"
        }
    })
    cluster_3_members.append(ubo_id)
    ground_truth["risk_labels"][ubo_id] = "critical"
    
    # Ownership chain
    for i, company_id in enumerate(cluster_3_members[:3]):
        edges.append({
            "outV": ubo_id,
            "inV": company_id,
            "label": "owns_share",
            "properties": {"percentage": 100 if i == 0 else 50}
        })
        
        # Inter-company ownership
        if i > 0:
            edges.append({
                "outV": cluster_3_members[i-1],
                "inV": company_id,
                "label": "owns_share",
                "properties": {"percentage": 50}
            })
    
    # Trading accounts
    for i in range(3):
        account_id = seeded_uuid_hex(f"gml-c3-a{i}-")
        vertices.append({
            "id": account_id,
            "label": "Account",
            "properties": {
                "accountId": account_id,
                "accountNumber": f"300{100 + i}",
                "accountType": "business",
                "balance": round(random.uniform(500000, 2000000), 2),
                "openedDate": "2022-01-15"
            }
        })
        
        edges.append({
            "outV": cluster_3_members[i],
            "inV": account_id,
            "label": "owns_account",
            "properties": {"since": "2022-01-15"}
        })
        cluster_3_members.append(account_id)
        ground_truth["risk_labels"][account_id] = "high"
    
    ground_truth["clusters"]["cluster_3_intl"] = cluster_3_members
    
    # ========================================
    # ANOMALIES: Isolated high-degree nodes (hub anomalies)
    # ========================================
    for i in range(3):
        anomaly_id = seeded_uuid_hex(f"gml-anom-{i}-")
        vertices.append({
            "id": anomaly_id,
            "label": "Person",
            "properties": {
                "personId": anomaly_id,
                "name": faker.name(),
                "dateOfBirth": f"199{random.randint(0,9)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "phone": faker.phone_number(),
                "email": faker.email(),
                "role": "unknown",
                "riskScore": 0.60,
                "anomalyType": "isolated_hub"
            }
        })
        ground_truth["anomalies"].append(anomaly_id)
        ground_truth["risk_labels"][anomaly_id] = "medium"
        
        # Connect to multiple accounts (high degree but isolated from communities)
        for j in range(random.randint(5, 8)):
            mule_account_id = seeded_uuid_hex(f"gml-mule-{i}-{j}-")
            vertices.append({
                "id": mule_account_id,
                "label": "Account",
                "properties": {
                    "accountId": mule_account_id,
                    "accountNumber": f"400{random.randint(100, 999)}",
                    "accountType": "checking",
                    "balance": round(random.uniform(100, 5000), 2),
                    "openedDate": "2024-06-01"
                }
            })
            
            edges.append({
                "outV": anomaly_id,
                "inV": mule_account_id,
                "label": "owns_account",
                "properties": {"since": "2024-06-01"}
            })
            
            ground_truth["risk_labels"][mule_account_id] = "medium"
    
    # ========================================
    # INTER-CLUSTER EDGES (weak links)
    # ========================================
    # Some legitimate cross-cluster relationships
    
    # Cluster 1 -> Cluster 2 (retail customer works at SME)
    edges.append({
        "outV": cluster_1_members[0],
        "inV": sme_company_id,
        "label": "employed_by",
        "properties": {"since": "2023-06-01"}
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
        "ground_truth": ground_truth,
        "statistics": {
            "total_clusters": len(ground_truth["clusters"]),
            "total_anomalies": len(ground_truth["anomalies"]),
            "risk_distribution": {
                "low": sum(1 for v in ground_truth["risk_labels"].values() if v == "low"),
                "medium": sum(1 for v in ground_truth["risk_labels"].values() if v == "medium"),
                "high": sum(1 for v in ground_truth["risk_labels"].values() if v == "high"),
                "critical": sum(1 for v in ground_truth["risk_labels"].values() if v == "critical")
            }
        },
        "vertices": vertices,
        "edges": edges,
        "checksums": {
            "vertices": vertices_checksum,
            "edges": edges_checksum,
            "total_vertices": len(vertices),
            "total_edges": len(edges),
            "total_persons": len([v for v in vertices if v["label"] == "Person"]),
            "total_companies": len([v for v in vertices if v["label"] == "Company"]),
            "total_accounts": len([v for v in vertices if v["label"] == "Account"])
        }
    }


def save_manifest(data: Dict[str, Any]) -> Path:
    """Save graph ML manifest."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(MANIFEST_PATH, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    
    return MANIFEST_PATH


def load_into_janusgraph(data: Dict[str, Any], host: str = "localhost", port: int = 18182) -> Dict[str, int]:
    """Load graph ML data into JanusGraph."""
    from src.python.client.janusgraph_client import JanusGraphClient
    
    vertices_created = 0
    edges_created = 0
    
    with JanusGraphClient(host=host, port=port, use_ssl=False, verify_certs=False) as client:
        # Create vertices
        for vertex in data["vertices"]:
            label = vertex["label"]
            props = vertex["properties"]
            
            prop_strs = []
            id_prop = f"{label.lower()}Id"
            
            for k, v in props.items():
                if isinstance(v, str):
                    v_escaped = v.replace("'", "\\'")
                    prop_strs.append(f".property('{k}', '{v_escaped}')")
                elif isinstance(v, bool):
                    prop_strs.append(f".property('{k}', {str(v).lower()})")
                elif isinstance(v, float):
                    prop_strs.append(f".property('{k}', {v}f)")
                else:
                    prop_strs.append(f".property('{k}', {v})")
            
            query = f"""
                g.V().has('{id_prop}', '{vertex["id"]}').fold().coalesce(
                    unfold(),
                    addV('{label}'){"".join(prop_strs)}
                )
            """
            client.execute(query)
            vertices_created += 1
        
        # Create edges
        for edge in data["edges"]:
            # Determine source/target types
            source_type = "person"
            target_type = "account"
            
            if edge["label"] in ["director_of", "employed_by"]:
                target_type = "company"
            elif edge["label"] in ["owns_share"]:
                source_type = "person"
                target_type = "company"
            
            source_id_prop = f"{source_type}Id"
            target_id_prop = f"{target_type}Id"
            
            props = edge.get("properties", {})
            prop_strs = []
            for k, v in props.items():
                if isinstance(v, str):
                    v_escaped = v.replace("'", "\\'")
                    prop_strs.append(f".property('{k}', '{v_escaped}')")
                elif isinstance(v, (int, float)):
                    prop_strs.append(f".property('{k}', {v}f)" if isinstance(v, float) else f".property('{k}', {v})")
            
            query = f"""
                g.V().has('{source_id_prop}', '{edge["outV"]}').as('source').
                V().has('{target_id_prop}', '{edge["inV"]}').
                coalesce(
                    inE('{edge["label"]}').where(outV().as('source')),
                    addE('{edge["label"]}').from('source'){"".join(prop_strs)}
                )
            """
            client.execute(query)
            edges_created += 1
    
    return {"vertices": vertices_created, "edges": edges_created}


def verify_determinism() -> bool:
    """Verify determinism using subprocess isolation."""
    import subprocess
    
    print("Running first generation in isolated process...")
    result1 = subprocess.run(
        [sys.executable, "-c", 
         "from banking.data_generators.scripts.generate_graph_ml_data import generate_graph_ml_data_deterministic; "
         "import json; data = generate_graph_ml_data_deterministic(seed=42); "
         "print(json.dumps(data['checksums']))"],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    checksums1 = json.loads(result1.stdout.strip())
    
    print("Running second generation in isolated process...")
    result2 = subprocess.run(
        [sys.executable, "-c", 
         "from banking.data_generators.scripts.generate_graph_ml_data import generate_graph_ml_data_deterministic; "
         "import json; data = generate_graph_ml_data_deterministic(seed=42); "
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
    parser = argparse.ArgumentParser(description="Generate graph ML data")
    parser.add_argument("--verify", action="store_true", help="Verify determinism")
    parser.add_argument("--load", action="store_true", help="Load into JanusGraph")
    parser.add_argument("--seed", type=int, default=DETERMINISTIC_SEED)
    args = parser.parse_args()
    
    if args.verify:
        success = verify_determinism()
        sys.exit(0 if success else 1)
    
    print(f"Generating graph ML data with seed={args.seed}...")
    data = generate_graph_ml_data_deterministic(seed=args.seed)
    
    manifest_path = save_manifest(data)
    print(f"Saved manifest to: {manifest_path}")
    
    print(f"\nGenerated {data['checksums']['total_vertices']} vertices and {data['checksums']['total_edges']} edges")
    
    print("\nStatistics:")
    print(f"  Clusters: {data['statistics']['total_clusters']}")
    print(f"  Anomalies: {data['statistics']['total_anomalies']}")
    print(f"  Risk Distribution: {data['statistics']['risk_distribution']}")
    
    if args.load:
        print("\nLoading into JanusGraph...")
        counts = load_into_janusgraph(data)
        print(f"Created {counts['vertices']} vertices and {counts['edges']} edges")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
