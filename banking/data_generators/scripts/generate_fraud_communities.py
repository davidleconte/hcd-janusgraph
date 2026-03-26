#!/usr/bin/env python
"""
Deterministic Fraud Community Generator
========================================

Generates fraud ring patterns and loads them into JanusGraph
for community detection demonstrations.

Usage:
    python banking/data_generators/scripts/generate_fraud_communities.py [--verify] [--load]

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watsonx.Data Global Product Specialist (GPS)
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
DETERMINISTIC_COUNTER_START = 1000  # Start after UBO data

# Output paths
OUTPUT_DIR = project_root / "exports" / "fraud-communities"
MANIFEST_PATH = OUTPUT_DIR / "fraud_communities_manifest.json"

# Reference timestamp for deterministic dates
REFERENCE_TIMESTAMP = datetime(2026, 1, 15, 12, 0, 0)


def generate_fraud_communities_deterministic(
    seed: int = DETERMINISTIC_SEED,
    counter_start: int = DETERMINISTIC_COUNTER_START
) -> Dict[str, Any]:
    """
    Generate fraud communities deterministically.
    
    Args:
        seed: Random seed for Faker and random module
        counter_start: Starting value for seeded UUID counter
        
    Returns:
        Dict with communities, vertices, edges, and checksums
    """
    # Reset deterministic counter with seed
    reset_counter(counter_start, seed=seed)
    
    # Reset random state
    random.seed(seed)
    Faker.seed(seed)
    
    faker = Faker("en_US")
    faker.seed_instance(seed)
    
    # Define fraud community scenarios
    scenarios = {
        "money_mule_ring": {
            "description": "Money mule network with hub-and-spoke pattern",
            "member_count": 12,
            "pattern_type": "hub_and_spoke",
            "risk_score": 0.85
        },
        "synthetic_identity_ring": {
            "description": "Synthetic identity fraud ring",
            "member_count": 8,
            "pattern_type": "distributed",
            "risk_score": 0.70
        },
        "bust_out_ring": {
            "description": "Bust-out fraud coordinated across accounts",
            "member_count": 6,
            "pattern_type": "coordinated",
            "risk_score": 0.75
        },
        "collusion_ring": {
            "description": "Collusion network with triangle patterns",
            "member_count": 9,
            "pattern_type": "triangle",
            "risk_score": 0.65
        },
        "account_takeover_ring": {
            "description": "Account takeover network",
            "member_count": 7,
            "pattern_type": "hub_and_spoke",
            "risk_score": 0.80
        },
        # Additional fraud patterns for exhaustive coverage
        "circular_ownership_ring": {
            "description": "Circular company ownership for UBI hiding",
            "member_count": 5,
            "pattern_type": "cycle",
            "risk_score": 0.88
        },
        "cross_border_layering": {
            "description": "Multi-jurisdictional money laundering layering",
            "member_count": 10,
            "pattern_type": "multi_hub",
            "risk_score": 0.92
        },
        "smurfing_network": {
            "description": "Distributed small-amount structuring network",
            "member_count": 15,
            "pattern_type": "distributed",
            "risk_score": 0.72
        },
        "shell_company_chain": {
            "description": "Long ownership chain for obfuscation",
            "member_count": 8,
            "pattern_type": "chain",
            "risk_score": 0.85
        },
        "burst_dormancy_pattern": {
            "description": "Time-based burst activity followed by dormancy",
            "member_count": 6,
            "pattern_type": "temporal",
            "risk_score": 0.78
        },
        # Extended fraud patterns for comprehensive coverage
        "ponzi_scheme": {
            "description": "Ponzi/pyramid scheme with hierarchical recruitment",
            "member_count": 12,
            "pattern_type": "tree",
            "risk_score": 0.90
        },
        "invoice_fraud_network": {
            "description": "Invoice fraud with fake vendor network",
            "member_count": 8,
            "pattern_type": "bipartite",
            "risk_score": 0.78
        },
        "bec_chain": {
            "description": "Business email compromise impersonation chain",
            "member_count": 6,
            "pattern_type": "directed_chain",
            "risk_score": 0.85
        }
    }
    
    vertices = []
    edges = []
    seen_vertices = set()
    
    community_data = {}
    
    for scenario_name, scenario_config in scenarios.items():
        community_id = seeded_uuid_hex("comm-")
        member_count = scenario_config["member_count"]
        pattern_type = scenario_config["pattern_type"]
        
        # Generate orchestrator (central actor)
        orchestrator_id = seeded_uuid_hex("orch-")
        orchestrator_name = faker.name()
        
        if orchestrator_id not in seen_vertices:
            vertices.append({
                "id": orchestrator_id,
                "label": "Person",
                "properties": {
                    "personId": orchestrator_id,
                    "name": orchestrator_name,
                    "role": "orchestrator",
                    "riskScore": scenario_config["risk_score"]
                }
            })
            seen_vertices.add(orchestrator_id)
        
        # Generate members based on pattern type
        members = []
        for i in range(member_count - 1):  # -1 for orchestrator
            member_id = seeded_uuid_hex(f"member-{scenario_name[:3]}-{i}")
            member_name = faker.name()
            is_mule = pattern_type == "hub_and_spoke" and i < 3
            
            if member_id not in seen_vertices:
                vertices.append({
                    "id": member_id,
                    "label": "Person",
                    "properties": {
                        "personId": member_id,
                        "name": member_name,
                        "role": "mule" if is_mule else "participant",
                        "riskScore": scenario_config["risk_score"] * random.uniform(0.5, 0.9)
                    }
                })
                seen_vertices.add(member_id)
            
            members.append(member_id)
        
        # Generate edges based on pattern type
        if pattern_type == "hub_and_spoke":
            # Orchestrator connected to all mules, mules to other members
            for member_id in members:
                edges.append({
                    "outV": orchestrator_id,
                    "inV": member_id,
                    "label": "knows",
                    "properties": {"strength": random.uniform(0.6, 1.0)}
                })
            # Connect mules to each other
            for i, m1 in enumerate(members[:3]):
                for m2 in members[i+1:4]:
                    edges.append({
                        "outV": m1,
                        "inV": m2,
                        "label": "knows",
                        "properties": {"strength": random.uniform(0.3, 0.7)}
                    })
        
        elif pattern_type == "triangle":
            # Create triangle patterns (A-B-C-A)
            for i in range(0, len(members) - 2, 3):
                triangle = members[i:i+3]
                for j, m1 in enumerate(triangle):
                    for m2 in triangle[j+1:]:
                        edges.append({
                            "outV": m1,
                            "inV": m2,
                            "label": "knows",
                            "properties": {"strength": random.uniform(0.7, 1.0)}
                        })
                # Connect orchestrator to triangle
                edges.append({
                    "outV": orchestrator_id,
                    "inV": triangle[0],
                    "label": "knows",
                    "properties": {"strength": 0.9}
                })
        
        elif pattern_type == "distributed":
            # Mesh-like connections
            for i, m1 in enumerate(members):
                # Connect to orchestrator
                edges.append({
                    "outV": orchestrator_id,
                    "inV": m1,
                    "label": "knows",
                    "properties": {"strength": random.uniform(0.4, 0.8)}
                })
                # Connect to some other members
                for m2 in random.sample(members, min(2, len(members))):
                    if m1 != m2:
                        edges.append({
                            "outV": m1,
                            "inV": m2,
                            "label": "knows",
                            "properties": {"strength": random.uniform(0.2, 0.6)}
                        })
        
        elif pattern_type == "coordinated":
            # Linear chain with orchestrator at top
            prev_id = orchestrator_id
            for member_id in members:
                edges.append({
                    "outV": prev_id,
                    "inV": member_id,
                    "label": "knows",
                    "properties": {"strength": 0.8}
                })
                prev_id = member_id
        
        # === Additional patterns for exhaustive coverage ===
        
        elif pattern_type == "cycle":
            # Circular ownership: A -> B -> C -> ... -> A (loops back to start)
            all_ids = [orchestrator_id] + members
            for i in range(len(all_ids)):
                next_idx = (i + 1) % len(all_ids)
                edges.append({
                    "outV": all_ids[i],
                    "inV": all_ids[next_idx],
                    "label": "knows",
                    "properties": {"strength": 0.95}
                })
        
        elif pattern_type == "multi_hub":
            # Multiple hubs (cross-border layering): orchestrator + regional coordinators
            # First 3 members are regional coordinators
            regional_coordinators = members[:3] if len(members) >= 3 else members
            # Connect orchestrator to all regional coordinators
            for coord_id in regional_coordinators:
                edges.append({
                    "outV": orchestrator_id,
                    "inV": coord_id,
                    "label": "knows",
                    "properties": {"strength": 0.9}
                })
            # Each regional coordinator connects to their local members
            remaining_members = members[3:] if len(members) > 3 else []
            members_per_region = len(remaining_members) // len(regional_coordinators) if regional_coordinators else 0
            for idx, coord_id in enumerate(regional_coordinators):
                start = idx * members_per_region
                end = start + members_per_region if idx < len(regional_coordinators) - 1 else len(remaining_members)
                for member_id in remaining_members[start:end]:
                    edges.append({
                        "outV": coord_id,
                        "inV": member_id,
                        "label": "knows",
                        "properties": {"strength": random.uniform(0.7, 0.9)}
                    })
            # Connect regional coordinators to each other
            for i, c1 in enumerate(regional_coordinators):
                for c2 in regional_coordinators[i+1:]:
                    edges.append({
                        "outV": c1,
                        "inV": c2,
                        "label": "knows",
                        "properties": {"strength": random.uniform(0.5, 0.7)}
                    })
        
        elif pattern_type == "chain":
            # Long ownership chain: Orchestrator -> A -> B -> C -> ... (no loop)
            all_ids = [orchestrator_id] + members
            for i in range(len(all_ids) - 1):
                edges.append({
                    "outV": all_ids[i],
                    "inV": all_ids[i + 1],
                    "label": "knows",
                    "properties": {"strength": 0.85}
                })
        
        elif pattern_type == "temporal":
            # Burst/dormancy pattern: tight cluster with dormant connections
            # Core active group (first 3 members)
            active_members = members[:3] if len(members) >= 3 else members
            for m1 in active_members:
                # Connect orchestrator to all active members
                edges.append({
                    "outV": orchestrator_id,
                    "inV": m1,
                    "label": "knows",
                    "properties": {"strength": 0.9}
                })
                # Dense connections among active members
                for m2 in active_members:
                    if m1 != m2:
                        edges.append({
                            "outV": m1,
                            "inV": m2,
                            "label": "knows",
                            "properties": {"strength": random.uniform(0.8, 1.0)}
                        })
            # Dormant members (weak connections)
            dormant_members = members[3:] if len(members) > 3 else []
            for member_id in dormant_members:
                edges.append({
                    "outV": orchestrator_id,
                    "inV": member_id,
                    "label": "knows",
                    "properties": {"strength": 0.3}  # Weak = dormant
                })
        
        # === Extended patterns for comprehensive coverage ===
        
        elif pattern_type == "tree":
            # Ponzi/Pyramid scheme: hierarchical recruitment tree
            # Level 0: orchestrator (root)
            # Level 1: first recruiters (connected to orchestrator)
            # Level 2+: victims recruited by recruiters
            levels = [[orchestrator_id]]  # Level 0
            remaining = list(members)
            branching_factor = 3  # Each recruiter brings in 3 victims
            
            # Build tree levels
            level_idx = 0
            while remaining and level_idx < 3:
                current_level = levels[level_idx]
                next_level = []
                for parent in current_level:
                    for _ in range(branching_factor):
                        if remaining:
                            child = remaining.pop(0)
                            next_level.append(child)
                            edges.append({
                                "outV": parent,
                                "inV": child,
                                "label": "knows",
                                "properties": {"strength": random.uniform(0.7, 0.95)}
                            })
                if next_level:
                    levels.append(next_level)
                level_idx += 1
            # Connect any remaining members to last level
            last_level = levels[-1] if levels else [orchestrator_id]
            for member_id in remaining:
                parent = random.choice(last_level)
                edges.append({
                    "outV": parent,
                    "inV": member_id,
                    "label": "knows",
                    "properties": {"strength": random.uniform(0.5, 0.7)}
                })
        
        elif pattern_type == "bipartite":
            # Invoice fraud: two sets - fake vendors and complicit insiders
            # First half are vendors, second half are company insiders
            mid_point = len(members) // 2
            vendors = members[:mid_point]
            insiders = members[mid_point:]
            
            # Connect orchestrator to all
            for member_id in members:
                edges.append({
                    "outV": orchestrator_id,
                    "inV": member_id,
                    "label": "knows",
                    "properties": {"strength": 0.85}
                })
            
            # Each vendor connects to specific insiders (fake invoices)
            for vendor in vendors:
                # Each vendor works with 2-3 insiders
                insider_targets = random.sample(insiders, min(3, len(insiders)))
                for insider in insider_targets:
                    edges.append({
                        "outV": vendor,
                        "inV": insider,
                        "label": "knows",
                        "properties": {"strength": random.uniform(0.6, 0.9)}
                    })
            
            # Insiders also connect to each other (collusion)
            for i, ins1 in enumerate(insiders):
                for ins2 in insiders[i+1:]:
                    edges.append({
                        "outV": ins1,
                        "inV": ins2,
                        "label": "knows",
                        "properties": {"strength": random.uniform(0.4, 0.7)}
                    })
        
        elif pattern_type == "directed_chain":
            # BEC chain: Impersonator -> Compromised Account -> Target
            # Uses directed edges to show attack flow
            # First member is impersonator, last is target, middle are compromised
            if len(members) >= 2:
                impersonator = members[0]
                target = members[-1]
                compromised = members[1:-1] if len(members) > 2 else []
                
                # Orchestrator controls impersonator
                edges.append({
                    "outV": orchestrator_id,
                    "inV": impersonator,
                    "label": "knows",
                    "properties": {"strength": 0.95}
                })
                
                # Attack chain: impersonator -> compromised accounts -> target
                prev_id = impersonator
                for comp_id in compromised:
                    edges.append({
                        "outV": prev_id,
                        "inV": comp_id,
                        "label": "knows",
                        "properties": {"strength": 0.8}
                    })
                    prev_id = comp_id
                
                # Final link to target
                edges.append({
                    "outV": prev_id,
                    "inV": target,
                    "label": "knows",
                    "properties": {"strength": 0.7}
                })
        
        # Store community data
        community_data[scenario_name] = {
            "community_id": community_id,
            "description": scenario_config["description"],
            "member_count": member_count,
            "orchestrator_id": orchestrator_id,
            "risk_score": scenario_config["risk_score"],
            "pattern_type": pattern_type
        }
    
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
        "scenarios": community_data,
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
    """Save fraud communities manifest to exports directory."""
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
    Load fraud communities into JanusGraph.
    
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
                    prop_strs.append(f".property('{k}', '{v}')")
                elif isinstance(v, float):
                    # Cast float to avoid BigDecimal error in JanusGraph
                    prop_strs.append(f".property('{k}', {v}f)")
                else:
                    prop_strs.append(f".property('{k}', {v})")
            
            query = f"""
                g.V().has('personId', '{vertex["id"]}').fold().coalesce(
                    unfold(),
                    addV('{label}'){"".join(prop_strs)}
                )
            """
            client.execute(query)
            vertices_created += 1
        
        # Create edges
        for edge in data["edges"]:
            strength = edge["properties"]["strength"]
            query = f"""
                g.V().has('personId', '{edge["outV"]}').as('source').
                V().has('personId', '{edge["inV"]}').
                coalesce(
                    inE('knows').where(outV().as('source')),
                    addE('knows').from('source')
                        .property('strength', {strength}f)
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
         "from banking.data_generators.scripts.generate_fraud_communities import generate_fraud_communities_deterministic; "
         "import json; data = generate_fraud_communities_deterministic(seed=42); "
         "print(json.dumps(data['checksums']))"],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    checksums1 = json.loads(result1.stdout.strip())
    
    print("Running second generation in isolated process...")
    result2 = subprocess.run(
        [sys.executable, "-c", 
         "from banking.data_generators.scripts.generate_fraud_communities import generate_fraud_communities_deterministic; "
         "import json; data = generate_fraud_communities_deterministic(seed=42); "
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
    parser = argparse.ArgumentParser(description="Generate deterministic fraud communities")
    parser.add_argument("--verify", action="store_true", help="Verify determinism")
    parser.add_argument("--load", action="store_true", help="Load data into JanusGraph")
    parser.add_argument("--seed", type=int, default=DETERMINISTIC_SEED, help="Random seed")
    args = parser.parse_args()
    
    if args.verify:
        success = verify_determinism()
        sys.exit(0 if success else 1)
    
    # Generate data
    print(f"Generating fraud communities with seed={args.seed}...")
    data = generate_fraud_communities_deterministic(seed=args.seed)
    
    # Save manifest
    manifest_path = save_manifest(data)
    print(f"Saved manifest to: {manifest_path}")
    
    # Print summary
    print(f"\nGenerated {data['checksums']['total_vertices']} vertices and {data['checksums']['total_edges']} edges")
    print(f"Communities: {len(data['scenarios'])}")
    
    for name, community in data['scenarios'].items():
        print(f"  {name}: {community['member_count']} members, risk={community['risk_score']:.2f}, pattern={community['pattern_type']}")
    
    # Load into JanusGraph if requested
    if args.load:
        print("\nLoading into JanusGraph...")
        counts = load_into_janusgraph(data)
        print(f"Created {counts['vertices']} vertices and {counts['edges']} edges")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
