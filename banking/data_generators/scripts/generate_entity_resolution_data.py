#!/usr/bin/env python
"""
Deterministic Entity Resolution Data Generator
===============================================

Generates data for all three entity resolution complexity levels:
1. Standard: Customer duplicates with name variants
2. High: Multi-jurisdictional UBO/sanctions evasion
3. Ultra-High: Synthetic identity fraud ring

Usage:
    python banking/data_generators/scripts/generate_entity_resolution_data.py [--verify] [--load]

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
DETERMINISTIC_COUNTER_START = 3000  # Start after time-travel data

# Output paths
OUTPUT_DIR = project_root / "exports" / "entity-resolution"
MANIFEST_PATH = OUTPUT_DIR / "entity_resolution_manifest.json"

# Reference timestamp
REFERENCE_TIMESTAMP = datetime(2026, 1, 15, 12, 0, 0)


def generate_entity_resolution_data_deterministic(
    seed: int = DETERMINISTIC_SEED,
    counter_start: int = DETERMINISTIC_COUNTER_START
) -> Dict[str, Any]:
    """
    Generate comprehensive entity resolution data for all complexity levels.
    
    Creates:
    1. Standard duplicates (same person, different representations)
    2. High-complexity UBO structure (multi-jurisdictional)
    3. Ultra-high synthetic identity ring
    
    Args:
        seed: Random seed
        counter_start: Starting counter for UUIDs
        
    Returns:
        Dict with vertices, edges, and scenarios
    """
    reset_counter(counter_start, seed=seed)
    random.seed(seed)
    Faker.seed(seed)
    
    faker = Faker("en_US")
    faker.seed_instance(seed)
    
    vertices = []
    edges = []
    
    # ========================================
    # SCENARIO 1: STANDARD CUSTOMER DUPLICATES
    # ========================================
    standard_entities = []
    
    # Original customer
    original_id = seeded_uuid_hex("er-std-1-")
    original_ssn = "123-45-6789"
    original_dob = "1985-03-15"
    original_phone = "555-1234"
    original_name = "John A. Smith"
    
    vertices.append({
        "id": original_id,
        "label": "Person",
        "properties": {
            "personId": original_id,
            "name": original_name,
            "ssn": original_ssn,
            "dateOfBirth": original_dob,
            "phone": original_phone,
            "email": "john.smith@yahoo.com",
            "role": "customer",
            "riskScore": 0.15
        }
    })
    standard_entities.append(original_id)
    
    # Duplicate with slight variations (same SSN, different name format)
    dup1_id = seeded_uuid_hex("er-std-2-")
    vertices.append({
        "id": dup1_id,
        "label": "Person",
        "properties": {
            "personId": dup1_id,
            "name": "Jonathan Smith",
            "ssn": original_ssn,  # Same SSN
            "dateOfBirth": original_dob,  # Same DOB
            "phone": original_phone,  # Same phone
            "email": "jon.s@gmail.com",  # Different email
            "role": "customer",
            "riskScore": 0.18
        }
    })
    standard_entities.append(dup1_id)
    
    # Duplicate with nickname
    dup2_id = seeded_uuid_hex("er-std-3-")
    vertices.append({
        "id": dup2_id,
        "label": "Person",
        "properties": {
            "personId": dup2_id,
            "name": "Jack Smith",  # Jack is nickname for John
            "ssn": original_ssn,
            "dateOfBirth": original_dob,
            "phone": "555-5678",  # Different phone
            "email": "jack.smith@outlook.com",
            "role": "customer",
            "riskScore": 0.12
        }
    })
    standard_entities.append(dup2_id)
    
    # ========================================
    # SCENARIO 2: HIGH-COMPLEXITY UBO/SANCTIONS
    # ========================================
    high_complexity_entities = []
    
    # Ultimate Beneficial Owner with multiple identities
    ubo_base_id = seeded_uuid_hex("er-ubo-")
    ubo_dob = "1965-03-15"
    
    # Identity 1: UK
    identity_uk_id = seeded_uuid_hex("er-ubo-uk-")
    vertices.append({
        "id": identity_uk_id,
        "label": "Person",
        "properties": {
            "personId": identity_uk_id,
            "name": "John Smith",
            "passport": "GB123456789",
            "nationality": "GB",
            "dateOfBirth": ubo_dob,
            "role": "director",
            "riskScore": 0.25,
            "isUBO": True
        }
    })
    high_complexity_entities.append(identity_uk_id)
    
    # Identity 2: BVI (variant name)
    identity_bvi_id = seeded_uuid_hex("er-ubo-bvi-")
    vertices.append({
        "id": identity_bvi_id,
        "label": "Person",
        "properties": {
            "personId": identity_bvi_id,
            "name": "Jon Smythe",
            "passport": "VG987654321",
            "nationality": "VG",
            "dateOfBirth": ubo_dob,
            "role": "director",
            "riskScore": 0.28,
            "isUBO": True
        }
    })
    high_complexity_entities.append(identity_bvi_id)
    
    # Identity 3: Cyprus (variant name)
    identity_cyprus_id = seeded_uuid_hex("er-ubo-cy-")
    vertices.append({
        "id": identity_cyprus_id,
        "label": "Person",
        "properties": {
            "personId": identity_cyprus_id,
            "name": "Hans Schmidt",
            "passport": "CY456789123",
            "nationality": "CY",
            "dateOfBirth": ubo_dob,
            "role": "director",
            "riskScore": 0.30,
            "isUBO": True
        }
    })
    high_complexity_entities.append(identity_cyprus_id)
    
    # Identity 4: Russia (SANCTIONED)
    identity_ru_id = seeded_uuid_hex("er-ubo-ru-")
    vertices.append({
        "id": identity_ru_id,
        "label": "Person",
        "properties": {
            "personId": identity_ru_id,
            "name": "Ivan Smirnov",
            "passport": "RU789123456",
            "nationality": "RU",
            "dateOfBirth": ubo_dob,
            "role": "director",
            "riskScore": 0.95,
            "isUBO": True,
            "sanctioned": True,
            "sanctionsList": "OFAC SDN"
        }
    })
    high_complexity_entities.append(identity_ru_id)
    
    # Companies
    company_uk_id = seeded_uuid_hex("er-co-uk-")
    vertices.append({
        "id": company_uk_id,
        "label": "Company",
        "properties": {
            "companyId": company_uk_id,
            "name": "Smith Holdings Ltd",
            "jurisdiction": "GB",
            "incorporationDate": "2020-01-15"
        }
    })
    high_complexity_entities.append(company_uk_id)
    
    company_bvi_id = seeded_uuid_hex("er-co-bvi-")
    vertices.append({
        "id": company_bvi_id,
        "label": "Company",
        "properties": {
            "companyId": company_bvi_id,
            "name": "Smythe Ventures Ltd",
            "jurisdiction": "VG",
            "incorporationDate": "2021-03-20"
        }
    })
    high_complexity_entities.append(company_bvi_id)
    
    company_cyprus_id = seeded_uuid_hex("er-co-cy-")
    vertices.append({
        "id": company_cyprus_id,
        "label": "Company",
        "properties": {
            "companyId": company_cyprus_id,
            "name": "Schmidt GmbH",
            "jurisdiction": "CY",
            "incorporationDate": "2022-06-10"
        }
    })
    high_complexity_entities.append(company_cyprus_id)
    
    # Trust
    trust_id = seeded_uuid_hex("er-trust-")
    vertices.append({
        "id": trust_id,
        "label": "Trust",
        "properties": {
            "trustId": trust_id,
            "name": "Alpha Trust",
            "jurisdiction": "VG",
            "establishedDate": "2020-06-01"
        }
    })
    high_complexity_entities.append(trust_id)
    
    # Law firm (shared trustee)
    lawfirm_id = seeded_uuid_hex("er-law-")
    vertices.append({
        "id": lawfirm_id,
        "label": "Company",
        "properties": {
            "companyId": lawfirm_id,
            "name": "Offshore Legal Associates",
            "jurisdiction": "VG",
            "role": "trustee"
        }
    })
    high_complexity_entities.append(lawfirm_id)
    
    # Ownership edges
    edges.append({
        "outV": identity_uk_id,
        "inV": company_uk_id,
        "label": "director_of",
        "properties": {"since": "2020-01-15"}
    })
    
    edges.append({
        "outV": identity_bvi_id,
        "inV": company_bvi_id,
        "label": "director_of",
        "properties": {"since": "2021-03-20"}
    })
    
    edges.append({
        "outV": identity_cyprus_id,
        "inV": company_cyprus_id,
        "label": "director_of",
        "properties": {"since": "2022-06-10"}
    })
    
    # Company ownership through trust
    edges.append({
        "outV": trust_id,
        "inV": company_uk_id,
        "label": "owns_share",
        "properties": {"percentage": 100}
    })
    
    edges.append({
        "outV": trust_id,
        "inV": company_bvi_id,
        "label": "owns_share",
        "properties": {"percentage": 100}
    })
    
    edges.append({
        "outV": trust_id,
        "inV": company_cyprus_id,
        "label": "owns_share",
        "properties": {"percentage": 100}
    })
    
    # UBO owns trust
    edges.append({
        "outV": identity_uk_id,
        "inV": trust_id,
        "label": "beneficiary_of",
        "properties": {"percentage": 100}
    })
    
    # Law firm is trustee
    edges.append({
        "outV": lawfirm_id,
        "inV": trust_id,
        "label": "trustee_of",
        "properties": {"since": "2020-06-01"}
    })
    
    # ========================================
    # SCENARIO 3: ULTRA-HIGH SYNTHETIC IDENTITIES
    # ========================================
    ultra_high_entities = []
    
    # Shared address
    address_id = seeded_uuid_hex("er-addr-")
    vertices.append({
        "id": address_id,
        "label": "Address",
        "properties": {
            "addressId": address_id,
            "street": "123 Oak Street",
            "unit": "4B",
            "city": "Miami",
            "state": "FL",
            "zipCode": "33101",
            "country": "US"
        }
    })
    ultra_high_entities.append(address_id)
    
    # Create synthetic identities (10 for demo)
    synthetic_ids = []
    base_ssn = 100000000
    
    for i in range(10):
        synth_id = seeded_uuid_hex(f"er-synth-{i}-")
        synthetic_ids.append(synth_id)
        
        # Sequential SSNs (stolen from same source)
        ssn = f"{base_ssn + i:09d}"
        ssn_formatted = f"{ssn[:3]}-{ssn[3:5]}-{ssn[5:]}"
        
        # Sequential DOBs (fabricated pattern)
        dob_month = 3 + i
        dob = f"1995-{dob_month:02d}-15"
        
        # Sequential phones
        phone = f"555-{1000 + i:04d}"
        
        # Same last name pattern
        first_names = ["Marcus", "Maria", "Miguel", "Marta", "Mario",
                       "Marina", "Mateo", "Lucia", "Luis", "Laura"]
        
        vertices.append({
            "id": synth_id,
            "label": "Person",
            "properties": {
                "personId": synth_id,
                "name": f"{first_names[i]} Johnson",
                "ssn": ssn_formatted,
                "dateOfBirth": dob,
                "phone": phone,
                "email": f"{first_names[i].lower()}.johnson@email.com",
                "role": "customer",
                "riskScore": 0.20 + (i * 0.02),
                "synthetic": True  # Hidden flag for demo
            }
        })
        ultra_high_entities.append(synth_id)
        
        # Link to shared address
        edges.append({
            "outV": synth_id,
            "inV": address_id,
            "label": "has_address",
            "properties": {"since": "2025-06-01"}
        })
    
    # Device fingerprint (shared)
    device_id = seeded_uuid_hex("er-device-")
    vertices.append({
        "id": device_id,
        "label": "Device",
        "properties": {
            "deviceId": device_id,
            "fingerprint": "a1b2c3d4e5f6",
            "type": "laptop",
            "browser": "Chrome"
        }
    })
    ultra_high_entities.append(device_id)
    
    # Link all synthetic identities to same device
    for synth_id in synthetic_ids:
        edges.append({
            "outV": synth_id,
            "inV": device_id,
            "label": "used_device",
            "properties": {"count": random.randint(5, 20)}
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
        "scenarios": {
            "standard": {
                "description": "Customer duplicates with name variants",
                "complexity": "standard",
                "entity_count": len(standard_entities),
                "expected_resolution": "All 3 records should resolve to same person"
            },
            "high_complexity": {
                "description": "Multi-jurisdictional UBO with sanctions evasion",
                "complexity": "high",
                "entity_count": len(high_complexity_entities),
                "expected_resolution": "4 identities resolve to 1 UBO (sanctioned)"
            },
            "ultra_high": {
                "description": "Synthetic identity fraud ring",
                "complexity": "ultra_high",
                "entity_count": len(ultra_high_entities),
                "expected_resolution": "10 synthetic identities detected as fraud ring"
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
            "total_addresses": len([v for v in vertices if v["label"] == "Address"])
        }
    }


def save_manifest(data: Dict[str, Any]) -> Path:
    """Save entity resolution manifest."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(MANIFEST_PATH, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    
    return MANIFEST_PATH


def load_into_janusgraph(data: Dict[str, Any], host: str = "localhost", port: int = 18182) -> Dict[str, int]:
    """Load entity resolution data into JanusGraph."""
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
            source_label = "person"
            target_label = "company"
            
            # Determine labels based on edge type
            if edge["label"] in ["has_address"]:
                target_label = "address"
            elif edge["label"] in ["used_device"]:
                target_label = "device"
            elif edge["label"] in ["trustee_of", "owns_share"]:
                source_label = "company"
            elif edge["label"] in ["beneficiary_of"]:
                target_label = "trust"
            
            source_id_prop = f"{source_label}Id"
            target_id_prop = f"{target_label}Id"
            
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
         "from banking.data_generators.scripts.generate_entity_resolution_data import generate_entity_resolution_data_deterministic; "
         "import json; data = generate_entity_resolution_data_deterministic(seed=42); "
         "print(json.dumps(data['checksums']))"],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    checksums1 = json.loads(result1.stdout.strip())
    
    print("Running second generation in isolated process...")
    result2 = subprocess.run(
        [sys.executable, "-c", 
         "from banking.data_generators.scripts.generate_entity_resolution_data import generate_entity_resolution_data_deterministic; "
         "import json; data = generate_entity_resolution_data_deterministic(seed=42); "
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
    parser = argparse.ArgumentParser(description="Generate entity resolution data")
    parser.add_argument("--verify", action="store_true", help="Verify determinism")
    parser.add_argument("--load", action="store_true", help="Load into JanusGraph")
    parser.add_argument("--seed", type=int, default=DETERMINISTIC_SEED)
    args = parser.parse_args()
    
    if args.verify:
        success = verify_determinism()
        sys.exit(0 if success else 1)
    
    print(f"Generating entity resolution data with seed={args.seed}...")
    data = generate_entity_resolution_data_deterministic(seed=args.seed)
    
    manifest_path = save_manifest(data)
    print(f"Saved manifest to: {manifest_path}")
    
    print(f"\nGenerated {data['checksums']['total_vertices']} vertices and {data['checksums']['total_edges']} edges")
    
    print("\nScenarios:")
    for name, scenario in data["scenarios"].items():
        print(f"  {name}: {scenario['description']} ({scenario['entity_count']} entities)")
    
    if args.load:
        print("\nLoading into JanusGraph...")
        counts = load_into_janusgraph(data)
        print(f"Created {counts['vertices']} vertices and {counts['edges']} edges")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
