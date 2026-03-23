"""
Ownership Chain Pattern Generator
=================================

Generates multi-layer ownership structures for UBO (Ultimate Beneficial Owner)
discovery demonstrations. Creates complex corporate hierarchies including:
- Direct ownership (Person -> Company)
- Multi-layer holding companies
- Shell companies in tax havens
- Nominee arrangements
- Cross-border ownership chains

Regulatory Background:
- EU 5AMLD: 25% ownership threshold for beneficial ownership
- FATF Recommendations: Risk-based approach to ownership identification
- FinCEN CDD Rule: Identification of beneficial owners with 25%+ ownership

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watsonx.Data Global Product Specialist (GPS)
Date: 2026-03-23
"""

import random
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from ..core.base_generator import BaseGenerator
from ..utils.constants import TAX_HAVENS, HIGH_RISK_COUNTRIES
from ..utils.deterministic import seeded_uuid_hex


@dataclass
class OwnershipLink:
    """Represents a single ownership relationship"""
    owner_id: str
    owner_type: str  # 'person' or 'company'
    owner_name: str
    target_id: str
    target_type: str  # 'company'
    target_name: str
    ownership_percentage: float
    ownership_type: str  # 'direct', 'indirect', 'nominee', 'trust'
    jurisdiction: str
    is_shell_company: bool = False
    is_pep: bool = False
    is_sanctioned: bool = False
    effective_ownership: float = 0.0  # Calculated for chains


@dataclass
class OwnershipChain:
    """Represents a complete ownership chain from UBO to target company"""
    target_company_id: str
    target_company_name: str
    ultimate_beneficial_owner_id: str
    ultimate_beneficial_owner_name: str
    chain_length: int
    effective_ownership_percentage: float
    chain_links: List[OwnershipLink]
    risk_indicators: List[str] = field(default_factory=list)
    jurisdictions: List[str] = field(default_factory=list)
    
    def exceeds_threshold(self, threshold: float = 25.0) -> bool:
        """Check if effective ownership exceeds regulatory threshold"""
        return self.effective_ownership_percentage >= threshold


@dataclass
class OwnershipStructure:
    """Complete ownership structure for a target company"""
    target_company_id: str
    target_company_name: str
    ownership_chains: List[OwnershipChain]
    all_ubos: List[Dict[str, Any]]
    high_risk_indicators: List[str]
    overall_risk_score: float
    total_layers: int


# Predefined demo scenarios for compelling demonstrations
DEMO_SCENARIOS = {
    "simple_direct": {
        "description": "Simple direct ownership - Person owns 60% of company",
        "chains": [
            {"layers": 1, "ownership": 60.0, "type": "direct"}
        ]
    },
    "two_layer_holding": {
        "description": "Two-layer holding structure - UBO through holding company",
        "chains": [
            {"layers": 2, "ownership_path": [80.0, 70.0], "type": "indirect"}
        ]
    },
    "shell_company_chain": {
        "description": "Shell company chain with tax haven jurisdiction",
        "chains": [
            {"layers": 3, "ownership_path": [100.0, 100.0, 60.0], "type": "shell", "jurisdictions": ["VG", "KY", "US"]}
        ]
    },
    "complex_multi_ubo": {
        "description": "Multiple UBOs through different ownership paths",
        "chains": [
            {"layers": 2, "ownership_path": [50.0, 60.0], "type": "indirect"},
            {"layers": 1, "ownership_path": [35.0], "type": "direct"},
            {"layers": 3, "ownership_path": [100.0, 80.0, 25.0], "type": "shell"}
        ]
    },
    "pep_sanctioned": {
        "description": "High-risk UBO (PEP) through complex structure",
        "chains": [
            {"layers": 4, "ownership_path": [100.0, 100.0, 100.0, 40.0], "type": "pep", "jurisdictions": ["RU", "CY", "VG", "US"]}
        ]
    },
    "nominee_arrangement": {
        "description": "Nominee shareholder arrangement (hidden ownership)",
        "chains": [
            {"layers": 2, "ownership_path": [100.0, 55.0], "type": "nominee"}
        ]
    },
    "regulatory_threshold": {
        "description": "Ownership just above/below 25% threshold",
        "chains": [
            {"layers": 2, "ownership_path": [51.0, 50.0], "type": "threshold"},  # 25.5% - EXCEEDS
            {"layers": 2, "ownership_path": [49.0, 50.0], "type": "threshold"}   # 24.5% - BELOW
        ]
    },
    "circular_ownership": {
        "description": "Circular ownership (Company A owns B, B owns A)",
        "chains": [
            {"layers": 2, "ownership_path": [60.0, 40.0], "type": "circular"}
        ]
    }
}


class OwnershipChainGenerator(BaseGenerator[OwnershipStructure]):
    """
    Generator for multi-layer ownership chain patterns.
    
    Creates realistic corporate ownership structures for:
    - UBO discovery testing
    - Regulatory compliance demonstrations
    - Risk scoring validation
    - Deal-winning visualizations
    
    Example:
        >>> generator = OwnershipChainGenerator(seed=42)
        >>> structure = generator.generate_complex_structure(
        ...     target_name="Acme Holdings Ltd",
        ...     scenario="complex_multi_ubo"
        ... )
        >>> for chain in structure.ownership_chains:
        ...     print(f"UBO: {chain.ultimate_beneficial_owner_name}")
        ...     print(f"Effective Ownership: {chain.effective_ownership_percentage:.1f}%")
    """
    
    # Regulatory thresholds
    OWNERSHIP_THRESHOLD = 25.0  # EU 5AMLD
    
    # High-risk jurisdictions for shell companies
    TAX_HAVEN_JURISDICTIONS = ["VG", "KY", "PA", "BZ", "SC", "CY", "MT", "LU", "NL", "IE"]
    HIGH_RISK_JURISDICTIONS = ["RU", "BY", "IR", "KP", "SY", "MM", "VE", "ZW"]
    
    # Common company suffixes by type
    COMPANY_SUFFIXES = {
        "holding": ["Holdings Ltd", "Holdings Inc", "Group Ltd", "Group SA"],
        "shell": ["Ltd", "Inc", "Corp", "GmbH", "Sarl", "SL"],
        "operating": ["Corp", "Inc", "PLC", "AG", "NV"],
        "investment": ["Investments Ltd", "Capital Ltd", "Partners LP", "Fund SP"]
    }
    
    def __init__(
        self,
        seed: Optional[int] = None,
        ownership_threshold: float = OWNERSHIP_THRESHOLD,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Ownership Chain Generator.
        
        Args:
            seed: Random seed for reproducibility
            ownership_threshold: Minimum % for UBO identification (default: 25%)
            config: Additional configuration
        """
        super().__init__(seed, config=config)
        self.ownership_threshold = ownership_threshold
        
    def generate(self) -> OwnershipStructure:
        """Generate a single ownership structure (default: complex_multi_ubo scenario)"""
        return self.generate_complex_structure(scenario="complex_multi_ubo")
    
    def generate_complex_structure(
        self,
        target_name: Optional[str] = None,
        target_id: Optional[str] = None,
        scenario: str = "complex_multi_ubo",
        custom_chains: Optional[List[Dict]] = None
    ) -> OwnershipStructure:
        """
        Generate a complex ownership structure based on a predefined scenario.
        
        Args:
            target_name: Name of the target company
            target_id: ID of the target company
            scenario: Predefined scenario name from DEMO_SCENARIOS
            custom_chains: Custom chain definitions (overrides scenario)
            
        Returns:
            OwnershipStructure with complete ownership chains
        """
        # Get scenario or use custom
        if custom_chains:
            scenario_config = {"description": "Custom scenario", "chains": custom_chains}
        else:
            scenario_config = DEMO_SCENARIOS.get(scenario, DEMO_SCENARIOS["complex_multi_ubo"])
        
        # Generate target company
        target_company_id = target_id or seeded_uuid_hex("target")
        target_company_name = target_name or self._generate_company_name("operating")
        
        ownership_chains = []
        all_ubos = []
        high_risk_indicators = []
        
        for idx, chain_config in enumerate(scenario_config["chains"]):
            # Generate ownership chain
            chain = self._generate_chain(
                target_company_id=target_company_id,
                target_company_name=target_company_name,
                chain_config=chain_config,
                chain_index=idx
            )
            
            ownership_chains.append(chain)
            
            # Track UBOs that exceed threshold
            if chain.exceeds_threshold(self.ownership_threshold):
                all_ubos.append({
                    "person_id": chain.ultimate_beneficial_owner_id,
                    "name": chain.ultimate_beneficial_owner_name,
                    "ownership_percentage": chain.effective_ownership_percentage,
                    "ownership_type": chain.chain_links[0].ownership_type if chain.chain_links else "unknown",
                    "chain_length": chain.chain_length,
                    "jurisdictions": chain.jurisdictions
                })
            
            # Collect high-risk indicators
            high_risk_indicators.extend(chain.risk_indicators)
        
        # Calculate overall risk score
        overall_risk_score = self._calculate_overall_risk_score(
            ownership_chains, high_risk_indicators
        )
        
        # Determine maximum layers
        total_layers = max((c.chain_length for c in ownership_chains), default=0)
        
        return OwnershipStructure(
            target_company_id=target_company_id,
            target_company_name=target_company_name,
            ownership_chains=ownership_chains,
            all_ubos=all_ubos,
            high_risk_indicators=list(set(high_risk_indicators)),
            overall_risk_score=overall_risk_score,
            total_layers=total_layers
        )
    
    def _generate_chain(
        self,
        target_company_id: str,
        target_company_name: str,
        chain_config: Dict[str, Any],
        chain_index: int
    ) -> OwnershipChain:
        """Generate a single ownership chain based on configuration."""
        layers = chain_config.get("layers", 2)
        ownership_path = chain_config.get("ownership_path", [100.0] * layers)
        chain_type = chain_config.get("type", "indirect")
        jurisdictions = chain_config.get("jurisdictions", ["US"] * (layers + 1))
        
        # Ensure we have enough ownership percentages
        while len(ownership_path) < layers:
            ownership_path.append(random.uniform(50.0, 100.0))
        
        # Ensure we have enough jurisdictions
        while len(jurisdictions) < layers + 1:
            jurisdictions.append(random.choice(self.TAX_HAVEN_JURISDICTIONS + ["US", "GB", "DE"]))
        
        chain_links = []
        current_target_id = target_company_id
        current_target_name = target_company_name
        current_target_type = "company"
        
        # Track chain properties
        is_shell_chain = chain_type in ["shell", "nominee"]
        is_pep_chain = chain_type == "pep"
        
        # Generate intermediate companies and final UBO
        for layer_idx in range(layers):
            is_final_layer = (layer_idx == layers - 1)
            ownership_pct = ownership_path[layer_idx]
            jurisdiction = jurisdictions[layer_idx]
            
            if is_final_layer:
                # Final layer: Person (UBO)
                owner_id = seeded_uuid_hex(f"ubo_{chain_index}")
                owner_type = "person"
                owner_name = self.faker.name()
                
                # Add PEP/sanctioned status for high-risk scenarios
                is_pep = is_pep_chain and layer_idx == 0
                is_sanctioned = chain_type == "sanctioned"
            else:
                # Intermediate layer: Company (holding/shell)
                owner_id = seeded_uuid_hex(f"holding_{chain_index}_{layer_idx}")
                owner_type = "company"
                owner_name = self._generate_company_name(
                    "shell" if is_shell_chain else "holding"
                )
                is_pep = False
                is_sanctioned = False
            
            link = OwnershipLink(
                owner_id=owner_id,
                owner_type=owner_type,
                owner_name=owner_name,
                target_id=current_target_id,
                target_type=current_target_type,
                target_name=current_target_name,
                ownership_percentage=ownership_pct,
                ownership_type=chain_type,
                jurisdiction=jurisdiction,
                is_shell_company=is_shell_chain and not is_final_layer,
                is_pep=is_pep,
                is_sanctioned=is_sanctioned
            )
            
            chain_links.append(link)
            
            # Move up the chain
            current_target_id = owner_id
            current_target_name = owner_name
            current_target_type = owner_type
        
        # Calculate effective ownership
        effective_ownership = self._calculate_effective_ownership(chain_links)
        for link in chain_links:
            link.effective_ownership = effective_ownership
        
        # Reverse to get UBO -> target order
        chain_links.reverse()
        
        # Build risk indicators
        risk_indicators = []
        jurisdictions_list = list(set(jurisdictions))
        
        if is_pep_chain:
            risk_indicators.append(f"PEP identified: {chain_links[0].owner_name}")
        if is_shell_chain:
            risk_indicators.append("Shell company structure detected")
        if any(j in self.TAX_HAVEN_JURISDICTIONS for j in jurisdictions):
            risk_indicators.append("Tax haven jurisdiction in ownership chain")
        if any(j in self.HIGH_RISK_JURISDICTIONS for j in jurisdictions):
            risk_indicators.append("High-risk jurisdiction in ownership chain")
        if len(chain_links) > 3:
            risk_indicators.append(f"Complex ownership structure ({len(chain_links)} layers)")
        
        return OwnershipChain(
            target_company_id=target_company_id,
            target_company_name=target_company_name,
            ultimate_beneficial_owner_id=chain_links[0].owner_id,
            ultimate_beneficial_owner_name=chain_links[0].owner_name,
            chain_length=len(chain_links),
            effective_ownership_percentage=effective_ownership,
            chain_links=chain_links,
            risk_indicators=risk_indicators,
            jurisdictions=jurisdictions_list
        )
    
    def _generate_company_name(self, company_type: str) -> str:
        """Generate a realistic company name"""
        base_name = self.faker.company()
        suffix = random.choice(self.COMPANY_SUFFIXES.get(company_type, ["Ltd"]))
        return f"{base_name} {suffix}"
    
    def _calculate_effective_ownership(self, chain_links: List[OwnershipLink]) -> float:
        """
        Calculate effective ownership through the chain.
        
        Formula: Product of all ownership percentages
        Example: A owns 60% of B, B owns 80% of C -> A effectively owns 48% of C
        """
        effective = 100.0
        for link in chain_links:
            effective *= link.ownership_percentage / 100.0
        return effective
    
    def _calculate_overall_risk_score(
        self,
        chains: List[OwnershipChain],
        indicators: List[str]
    ) -> float:
        """
        Calculate overall risk score (0-100).
        
        Factors:
        - Number of ownership layers
        - Presence of PEPs/sanctioned individuals
        - High-risk/tax haven jurisdictions
        - Structure complexity
        """
        score = 20.0  # Base score
        
        # Complexity factor
        max_layers = max((c.chain_length for c in chains), default=0)
        score += min(max_layers * 8, 25)  # Up to 25 points
        
        # Jurisdiction risk
        tax_haven_count = sum(
            1 for c in chains 
            for j in c.jurisdictions 
            if j in self.TAX_HAVEN_JURISDICTIONS
        )
        score += min(tax_haven_count * 5, 15)  # Up to 15 points
        
        # PEP/sanctioned risk
        if any("PEP" in ind for ind in indicators):
            score += 20
        if any("sanctioned" in ind.lower() for ind in indicators):
            score += 25
        
        # Shell company risk
        shell_count = sum(
            1 for c in chains 
            for link in c.chain_links 
            if link.is_shell_company
        )
        score += min(shell_count * 3, 15)  # Up to 15 points
        
        return min(score, 100.0)
    
    def generate_gremlin_load_script(
        self,
        structure: OwnershipStructure
    ) -> str:
        """
        Generate Gremlin script to load ownership structure into JanusGraph.
        
        Args:
            structure: Ownership structure to load
            
        Returns:
            Gremlin Groovy script as string
        """
        lines = [
            "// Ownership Chain Data Load",
            f"// Target: {structure.target_company_name}",
            f"// Generated: {date.today().isoformat()}",
            f"// Total UBOs: {len(structure.all_ubos)}",
            f"// Risk Score: {structure.overall_risk_score:.1f}/100",
            "",
            "// Ensure target company exists",
            f"target = g.V().has('company_id', '{structure.target_company_id}').tryNext().orElseGet{{",
            f"  graph.addVertex('company').property('company_id', '{structure.target_company_id}').property('legal_name', '{structure.target_company_name}')",
            "}",
            "",
        ]
        
        # Track created entities to avoid duplicates
        created_entities = {structure.target_company_id}
        
        for chain_idx, chain in enumerate(structure.ownership_chains):
            lines.append(f"// Chain {chain_idx + 1}: {chain.ultimate_beneficial_owner_name} ({chain.effective_ownership_percentage:.1f}%)")
            
            prev_id = structure.target_company_id
            
            for link in reversed(chain.chain_links):  # UBO -> target order
                if link.owner_id not in created_entities:
                    if link.owner_type == "person":
                        lines.append(f"""
person_{chain_idx} = graph.addVertex('person')
  .property('person_id', '{link.owner_id}')
  .property('full_name', '{link.owner_name}')
  .property('is_pep', {str(link.is_pep).lower()})
  .property('is_sanctioned', {str(link.is_sanctioned).lower()})""")
                    else:
                        lines.append(f"""
company_{chain_idx} = graph.addVertex('company')
  .property('company_id', '{link.owner_id}')
  .property('legal_name', '{link.owner_name}')
  .property('registration_country', '{link.jurisdiction}')
  .property('is_shell_company', {str(link.is_shell_company).lower()})""")
                    created_entities.add(link.owner_id)
                
                # Add ownership edge
                edge_type = "beneficial_owner" if link.owner_type == "person" else "owns_company"
                lines.append(f"""
g.V().has('{link.owner_type == "person" and "person_id" or "company_id"}', '{link.owner_id}')
  .addE('{edge_type}')
  .to(g.V().has('company_id', '{prev_id}'))
  .property('ownership_percentage', {link.ownership_percentage})
  .property('ownership_type', '{link.ownership_type}')
  .property('jurisdiction', '{link.jurisdiction}')
  .next()""")
                
                prev_id = link.owner_id
            
            lines.append("")
        
        lines.extend([
            "graph.tx().commit()",
            "",
            f"println '✅ Loaded ownership structure for {structure.target_company_name}'",
            f"println '   Total ownership chains: {len(structure.ownership_chains)}'",
            f"println '   UBOs exceeding 25% threshold: {len(structure.all_ubos)}'",
            f"println '   Risk indicators: {len(structure.high_risk_indicators)}'"
        ])
        
        return "\n".join(lines)
    
    def generate_all_demo_scenarios(self) -> Dict[str, OwnershipStructure]:
        """
        Generate all predefined demo scenarios.
        
        Returns:
            Dictionary mapping scenario names to OwnershipStructure objects
        """
        scenarios = {}
        for scenario_name in DEMO_SCENARIOS:
            scenarios[scenario_name] = self.generate_complex_structure(scenario=scenario_name)
        return scenarios


def create_demo_ownership_data(
    seed: int = 42,
    output_dir: str = "exports/ownership_chains"
) -> Dict[str, Any]:
    """
    Create comprehensive demo ownership data for UBO discovery.
    
    Args:
        seed: Random seed for reproducibility
        output_dir: Directory to save generated data
        
    Returns:
        Dictionary with all generated structures and metadata
    """
    import json
    from pathlib import Path
    
    generator = OwnershipChainGenerator(seed=seed)
    
    # Generate all scenarios
    all_scenarios = generator.generate_all_demo_scenarios()
    
    # Prepare output
    output = {
        "metadata": {
            "generator": "OwnershipChainGenerator",
            "seed": seed,
            "generated_date": date.today().isoformat(),
            "ownership_threshold": 25.0,
            "regulatory_basis": ["EU 5AMLD", "FATF Recommendations", "FinCEN CDD Rule"],
            "total_scenarios": len(all_scenarios)
        },
        "scenarios": {}
    }
    
    for scenario_name, structure in all_scenarios.items():
        output["scenarios"][scenario_name] = {
            "description": DEMO_SCENARIOS[scenario_name]["description"],
            "target_company": {
                "id": structure.target_company_id,
                "name": structure.target_company_name
            },
            "ubos_identified": len(structure.all_ubos),
            "ubo_details": structure.all_ubos,
            "total_chains": len(structure.ownership_chains),
            "max_layers": structure.total_layers,
            "risk_score": structure.overall_risk_score,
            "high_risk_indicators": structure.high_risk_indicators
        }
    
    # Save to file
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    with open(output_path / "ownership_structures.json", "w") as f:
        json.dump(output, f, indent=2)
    
    # Generate Gremlin load scripts
    scripts_dir = output_path / "gremlin_scripts"
    scripts_dir.mkdir(exist_ok=True)
    
    for scenario_name, structure in all_scenarios.items():
        script = generator.generate_gremlin_load_script(structure)
        with open(scripts_dir / f"{scenario_name}.groovy", "w") as f:
            f.write(script)
    
    return output


if __name__ == "__main__":
    # CLI interface for generating demo data
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate UBO ownership chain demo data")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="exports/ownership_chains", help="Output directory")
    parser.add_argument("--scenario", type=str, help="Generate specific scenario only")
    
    args = parser.parse_args()
    
    generator = OwnershipChainGenerator(seed=args.seed)
    
    if args.scenario:
        structure = generator.generate_complex_structure(scenario=args.scenario)
        print(f"\n📊 Generated: {args.scenario}")
        print(f"   Target: {structure.target_company_name}")
        print(f"   UBOs: {len(structure.all_ubos)}")
        print(f"   Risk Score: {structure.overall_risk_score:.1f}/100")
    else:
        result = create_demo_ownership_data(seed=args.seed, output_dir=args.output)
        print(f"\n✅ Generated {result['metadata']['total_scenarios']} ownership scenarios")
        print(f"   Output: {args.output}/")
