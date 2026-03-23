#!/usr/bin/env python
"""
Deterministic UBO Ownership Chain Generator and Loader
======================================================

Generates multi-layer ownership structures and loads them into JanusGraph
in a fully deterministic manner.

Usage:
    python banking/data_generators/scripts/generate_ubo_ownership_chains.py [--verify]

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watsonx.Data Global Product Specialist (GPS)
Date: 2026-03-23
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from banking.data_generators.patterns.ownership_chain_generator import OwnershipChainGenerator
from banking.data_generators.utils.deterministic import reset_counter


# Deterministic configuration
DETERMINISTIC_SEED = 42
DETERMINISTIC_COUNTER_START = 0

# Output paths
OUTPUT_DIR = project_root / "exports" / "ubo-ownership-chains"
MANIFEST_PATH = OUTPUT_DIR / "ownership_manifest.json"


def generate_ownership_chains_deterministic(
    seed: int = DETERMINISTIC_SEED,
    counter_start: int = DETERMINISTIC_COUNTER_START
) -> Dict[str, Any]:
    """
    Generate ownership chains deterministically.
    
    Args:
        seed: Random seed for Faker and random module
        counter_start: Starting value for seeded UUID counter
        
    Returns:
        Dict with scenarios, vertices, edges, and checksums
    """
    # Reset deterministic counter with seed for guaranteed reproducibility
    reset_counter(counter_start, seed=seed)
    
    # Reset random state BEFORE creating generator (Faker affects global random)
    import random
    from faker import Faker
    random.seed(seed)
    Faker.seed(seed)
    
    # Create generator with seed
    generator = OwnershipChainGenerator(seed=seed)
    
    # Generate all demo scenarios
    scenarios = generator.generate_all_demo_scenarios()
    
    # Build vertices and edges lists
    vertices = []
    edges = []
    seen_vertices = set()
    seen_edges = set()
    
    for scenario_name, structure in scenarios.items():
        # Target company vertex
        target_id = structure.target_company_id
        if target_id not in seen_vertices:
            vertices.append({
                "id": target_id,
                "label": "Company",
                "properties": {
                    "companyId": target_id,
                    "name": structure.target_company_name,
                    "type": "target"
                }
            })
            seen_vertices.add(target_id)
        
        # Process ownership chains
        for chain in structure.ownership_chains:
            for link in chain.chain_links:
                # Owner vertex
                owner_id = link.owner_id
                if owner_id not in seen_vertices:
                    if link.owner_type == "person":
                        vertices.append({
                            "id": owner_id,
                            "label": "Person",
                            "properties": {
                                "personId": owner_id,
                                "name": link.owner_name
                            }
                        })
                    else:
                        vertices.append({
                            "id": owner_id,
                            "label": "Company",
                            "properties": {
                                "companyId": owner_id,
                                "name": link.owner_name,
                                "jurisdiction": link.jurisdiction
                            }
                        })
                    seen_vertices.add(owner_id)
                
                # Edge (ownership relationship)
                edge_key = f"{owner_id}->{link.target_id}"
                if edge_key not in seen_edges:
                    edges.append({
                        "outV": owner_id,
                        "inV": link.target_id,
                        "label": "owns_company",
                        "properties": {
                            "percentage": int(link.ownership_percentage),
                            "type": link.ownership_type
                        }
                    })
                    seen_edges.add(edge_key)
    
    # Calculate checksums for determinism verification
    vertices_checksum = hashlib.sha256(
        json.dumps(sorted(vertices, key=lambda x: x["id"]), sort_keys=True).encode()
    ).hexdigest()[:16]
    
    edges_checksum = hashlib.sha256(
        json.dumps(sorted(edges, key=lambda x: f"{x['outV']}->{x['inV']}"), sort_keys=True).encode()
    ).hexdigest()[:16]
    
    return {
        "seed": seed,
        "counter_start": counter_start,
        "scenarios": {name: {
            "target": s.target_company_name,
            "chains": len(s.ownership_chains),
            "ubos": len(s.all_ubos),
            "risk_score": s.overall_risk_score
        } for name, s in scenarios.items()},
        "vertices": vertices,
        "edges": edges,
        "checksums": {
            "vertices": vertices_checksum,
            "edges": edges_checksum,
            "total_vertices": len(vertices),
            "total_edges": len(edges)
        }
    }


def save_manifest(data: Dict[str, Any]) -> Path:
    """Save ownership manifest to exports directory."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(MANIFEST_PATH, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    
    return MANIFEST_PATH


def load_into_janusgraph(data: Dict[str, Any], host: str = "localhost", port: int = 18182) -> Dict[str, int]:
    """
    Load ownership chains into JanusGraph.
    
    Returns:
        Dict with vertex and edge counts
    """
    from src.python.client.janusgraph_client import JanusGraphClient
    
    vertices_created = 0
    edges_created = 0
    
    with JanusGraphClient(host=host, port=port, use_ssl=False, verify_certs=False) as client:
        # Create vertices
        for vertex in data["vertices"]:
            label = vertex["label"]
            props = vertex["properties"]
            
            # Build property string
            prop_strs = []
            for k, v in props.items():
                if isinstance(v, str):
                    prop_strs.append(f".property('{k}', '{v}')")
                else:
                    prop_strs.append(f".property('{k}', {v})")
            
            id_prop = "personId" if label == "Person" else "companyId"
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
            # Find the correct ID property for the owner
            owner = next((v for v in data["vertices"] if v["id"] == edge["outV"]), None)
            id_prop = "personId" if owner["label"] == "Person" else "companyId"
            
            query = f"""
                g.V().has('{id_prop}', '{edge["outV"]}').as('owner').
                V().has('companyId', '{edge["inV"]}').
                coalesce(
                    inE('owns_company').where(outV().as('owner')),
                    addE('owns_company').from('owner')
                        .property('percentage', {edge["properties"]["percentage"]})
                        .property('type', '{edge["properties"]["type"]}')
                )
            """
            client.execute(query)
            edges_created += 1
    
    return {"vertices": vertices_created, "edges": edges_created}


def verify_determinism() -> bool:
    """
    Verify that generation is deterministic by running twice in isolated processes.
    
    Uses subprocess isolation to avoid Faker's global state pollution between runs.
    """
    import subprocess
    
    print("Running first generation in isolated process...")
    result1 = subprocess.run(
        [sys.executable, "-c", 
         "from banking.data_generators.scripts.generate_ubo_ownership_chains import generate_ownership_chains_deterministic; "
         "import json; data = generate_ownership_chains_deterministic(seed=42); "
         "print(json.dumps(data['checksums']))"],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    checksums1 = json.loads(result1.stdout.strip())
    
    print("Running second generation in isolated process...")
    result2 = subprocess.run(
        [sys.executable, "-c", 
         "from banking.data_generators.scripts.generate_ubo_ownership_chains import generate_ownership_chains_deterministic; "
         "import json; data = generate_ownership_chains_deterministic(seed=42); "
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
    parser = argparse.ArgumentParser(description="Generate deterministic UBO ownership chains")
    parser.add_argument("--verify", action="store_true", help="Verify determinism by running twice")
    parser.add_argument("--load", action="store_true", help="Load data into JanusGraph")
    parser.add_argument("--seed", type=int, default=DETERMINISTIC_SEED, help="Random seed")
    args = parser.parse_args()
    
    if args.verify:
        success = verify_determinism()
        sys.exit(0 if success else 1)
    
    # Generate data
    print(f"Generating ownership chains with seed={args.seed}...")
    data = generate_ownership_chains_deterministic(seed=args.seed)
    
    # Save manifest
    manifest_path = save_manifest(data)
    print(f"Saved manifest to: {manifest_path}")
    
    # Print summary
    print(f"\nGenerated {data['checksums']['total_vertices']} vertices and {data['checksums']['total_edges']} edges")
    print(f"Scenarios: {len(data['scenarios'])}")
    
    for name, scenario in data['scenarios'].items():
        print(f"  {name}: {scenario['target']} - {scenario['ubos']} UBOs, risk={scenario['risk_score']}")
    
    # Load into JanusGraph if requested
    if args.load:
        print("\nLoading into JanusGraph...")
        counts = load_into_janusgraph(data)
        print(f"Created {counts['vertices']} vertices and {counts['edges']} edges")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
