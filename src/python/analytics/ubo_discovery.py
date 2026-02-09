"""
Ultimate Beneficial Owner (UBO) Discovery Module
=================================================

Provides graph traversal queries to discover ultimate beneficial owners
through complex ownership structures including shell companies and
layered holding patterns.

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-04

Regulatory Background:
- EU 5AMLD: 25% ownership threshold for beneficial ownership
- FATF Recommendations: Risk-based approach to ownership identification
- FinCEN CDD Rule: Identification of beneficial owners with 25%+ ownership
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from gremlin_python.driver import serializer
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import P, T

logger = logging.getLogger(__name__)


class OwnershipType(str, Enum):
    """Types of ownership relationships"""

    DIRECT = "direct"  # Person directly owns shares
    INDIRECT = "indirect"  # Through holding company
    NOMINEE = "nominee"  # Nominee arrangement
    TRUST = "trust"  # Through trust structure
    BEARER = "bearer"  # Bearer shares (high risk)


@dataclass
class OwnershipLink:
    """Represents a single ownership link in the chain"""

    entity_id: str
    entity_type: str  # 'person' or 'company'
    entity_name: str
    ownership_percentage: float
    ownership_type: OwnershipType
    jurisdiction: Optional[str] = None
    is_pep: bool = False
    is_sanctioned: bool = False


@dataclass
class UBOResult:
    """Result of UBO discovery for an entity"""

    target_entity_id: str
    target_entity_name: str
    ubos: List[Dict[str, Any]]
    ownership_chains: List[List[OwnershipLink]]
    total_layers: int
    high_risk_indicators: List[str]
    risk_score: float


class UBODiscovery:
    """
    UBO Discovery engine using graph traversals.

    Implements regulatory-compliant beneficial ownership identification
    with configurable thresholds and risk scoring.
    """

    # Regulatory thresholds
    DEFAULT_OWNERSHIP_THRESHOLD = 25.0  # EU 5AMLD threshold
    MAX_TRAVERSAL_DEPTH = 10  # Prevent infinite loops

    # High-risk jurisdictions (sample list)
    HIGH_RISK_JURISDICTIONS = {
        "VG",
        "KY",
        "PA",
        "BZ",
        "SC",  # Tax havens
        "RU",
        "BY",
        "IR",
        "KP",
        "SY",  # Sanctioned
    }

    def __init__(
        self,
        host: str = "localhost",
        port: int = 18182,
        ownership_threshold: float = DEFAULT_OWNERSHIP_THRESHOLD,
    ):
        """
        Initialize UBO Discovery engine.

        Args:
            host: JanusGraph server host
            port: JanusGraph Gremlin port
            ownership_threshold: Minimum ownership % to consider (default: 25%)
        """
        self.host = host
        self.port = port
        self.ownership_threshold = ownership_threshold
        self.g = None
        self.connection = None

    def connect(self) -> bool:
        """Establish connection to JanusGraph"""
        try:
            self.connection = DriverRemoteConnection(
                f"ws://{self.host}:{self.port}/gremlin",
                "g",
                message_serializer=serializer.GraphSONSerializersV3d0(),
            )
            self.g = traversal().withRemote(self.connection)
            logger.info("Connected to JanusGraph at %s:%s", self.host, self.port)
            return True
        except Exception as e:
            logger.error("Failed to connect to JanusGraph: %s", e)
            return False

    def close(self):
        """Close connection"""
        if self.connection:
            self.connection.close()
            logger.info("Connection closed")

    def find_ubos_for_company(
        self, company_id: str, include_indirect: bool = True, max_depth: int = None
    ) -> UBOResult:
        """
        Find all Ultimate Beneficial Owners for a company.

        Traverses ownership chains through:
        - Direct beneficial_owner edges
        - Indirect ownership via owns_company edges
        - Multi-layer holding structures

        Args:
            company_id: Target company ID
            include_indirect: Include indirect ownership through holding companies
            max_depth: Maximum traversal depth (default: MAX_TRAVERSAL_DEPTH)

        Returns:
            UBOResult with identified UBOs and ownership chains
        """
        if not self.g:
            raise RuntimeError("Not connected. Call connect() first.")

        max_depth = max_depth or self.MAX_TRAVERSAL_DEPTH

        # Get target company info
        company_info = self._get_company_info(company_id)
        if not company_info:
            raise ValueError(f"Company not found: {company_id}")

        ubos = []
        ownership_chains = []
        high_risk_indicators = []

        # Find direct beneficial owners (Person -> Company)
        direct_owners = self._find_direct_owners(company_id)
        for owner in direct_owners:
            if owner["ownership_percentage"] >= self.ownership_threshold:
                ubos.append(
                    {
                        "person_id": owner["person_id"],
                        "name": owner["name"],
                        "ownership_percentage": owner["ownership_percentage"],
                        "ownership_type": "direct",
                        "chain_length": 1,
                    }
                )
                ownership_chains.append(
                    [
                        OwnershipLink(
                            entity_id=owner["person_id"],
                            entity_type="person",
                            entity_name=owner["name"],
                            ownership_percentage=owner["ownership_percentage"],
                            ownership_type=OwnershipType.DIRECT,
                            is_pep=owner.get("is_pep", False),
                            is_sanctioned=owner.get("is_sanctioned", False),
                        )
                    ]
                )

                if owner.get("is_pep"):
                    high_risk_indicators.append(f"PEP: {owner['name']}")
                if owner.get("is_sanctioned"):
                    high_risk_indicators.append(f"Sanctioned: {owner['name']}")

        # Find indirect owners through holding companies
        if include_indirect:
            indirect_chains = self._find_indirect_owners(company_id, max_depth)
            for chain in indirect_chains:
                effective_ownership = self._calculate_effective_ownership(chain)
                if effective_ownership >= self.ownership_threshold:
                    ubo = chain[0]  # The person at the top of the chain
                    ubos.append(
                        {
                            "person_id": ubo.entity_id,
                            "name": ubo.entity_name,
                            "ownership_percentage": effective_ownership,
                            "ownership_type": "indirect",
                            "chain_length": len(chain),
                        }
                    )
                    ownership_chains.append(chain)

                    # Check for high-risk indicators in chain
                    for link in chain:
                        if link.jurisdiction in self.HIGH_RISK_JURISDICTIONS:
                            high_risk_indicators.append(
                                f"High-risk jurisdiction: {link.entity_name} ({link.jurisdiction})"
                            )

        # Calculate risk score
        risk_score = self._calculate_risk_score(ubos, ownership_chains, high_risk_indicators)

        return UBOResult(
            target_entity_id=company_id,
            target_entity_name=company_info.get("legal_name", "Unknown"),
            ubos=ubos,
            ownership_chains=ownership_chains,
            total_layers=max(len(c) for c in ownership_chains) if ownership_chains else 0,
            high_risk_indicators=high_risk_indicators,
            risk_score=risk_score,
        )

    def _get_company_info(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get company information"""
        try:
            result = self.g.V().has("company_id", company_id).valueMap(True).toList()
            if result:
                return self._flatten_value_map(result[0])
            return None
        except Exception as e:
            logger.error("Error getting company info: %s", e)
            return None

    def _find_direct_owners(self, company_id: str) -> List[Dict[str, Any]]:
        """Find persons who directly own the company"""
        try:
            # Traverse: Person -[beneficial_owner]-> Company
            # Note: Avoid Python lambdas in Gremlin - they don't serialize to server
            results = (
                self.g.V()
                .has("company_id", company_id)
                .inE("beneficial_owner")
                .project(
                    "person_id",
                    "first_name",
                    "last_name",
                    "full_name",
                    "ownership_percentage",
                    "is_pep",
                    "is_sanctioned",
                )
                .by(__.outV().values("person_id"))
                .by(__.outV().coalesce(__.values("first_name"), __.constant("")))
                .by(__.outV().coalesce(__.values("last_name"), __.constant("")))
                .by(__.outV().coalesce(__.values("full_name"), __.constant("")))
                .by(__.coalesce(__.values("ownership_percentage"), __.constant(0.0)))
                .by(__.outV().coalesce(__.values("is_pep"), __.constant(False)))
                .by(__.outV().coalesce(__.values("is_sanctioned"), __.constant(False)))
                .toList()
            )

            # Format names in Python (server-side lambdas not supported)
            formatted_results = []
            for r in results:
                name = (
                    r.get("full_name")
                    or f"{r.get('first_name', '')} {r.get('last_name', '')}".strip()
                )
                formatted_results.append(
                    {
                        "person_id": r["person_id"],
                        "name": name or "Unknown",
                        "ownership_percentage": r["ownership_percentage"],
                        "is_pep": r["is_pep"],
                        "is_sanctioned": r["is_sanctioned"],
                    }
                )

            return formatted_results
        except Exception as e:
            logger.error("Error finding direct owners: %s", e)
            return []

    def _find_indirect_owners(self, company_id: str, max_depth: int) -> List[List[OwnershipLink]]:
        """
        Find persons who indirectly own the company through holding companies.

        Uses recursive traversal: Company <-[owns_company]- Company <-[beneficial_owner]- Person
        """
        chains = []

        try:
            # Find parent companies with ownership chain
            # This query finds all paths from the target company up to ultimate persons
            results = (
                self.g.V()
                .has("company_id", company_id)
                .repeat(__.inE("owns_company", "beneficial_owner").outV().simplePath())
                .until(__.or_(__.hasLabel("person"), __.loops().is_(P.gte(max_depth))))
                .hasLabel("person")
                .path()
                .by(__.valueMap(True))
                .toList()
            )

            for path in results:
                chain = self._convert_path_to_chain(path)
                if chain:
                    chains.append(chain)

        except Exception as e:
            logger.error("Error finding indirect owners: %s", e)

        return chains

    def _convert_path_to_chain(self, path) -> List[OwnershipLink]:
        """Convert a Gremlin path to a list of OwnershipLinks"""
        chain = []
        objects = list(path.objects) if hasattr(path, "objects") else path

        for obj in objects:
            if isinstance(obj, dict):
                flat = self._flatten_value_map(obj)

                if flat.get("person_id"):
                    chain.append(
                        OwnershipLink(
                            entity_id=flat["person_id"],
                            entity_type="person",
                            entity_name=flat.get(
                                "full_name",
                                f"{flat.get('first_name', '')} {flat.get('last_name', '')}",
                            ),
                            ownership_percentage=flat.get("ownership_percentage", 100.0),
                            ownership_type=OwnershipType.INDIRECT,
                            is_pep=flat.get("is_pep", False),
                            is_sanctioned=flat.get("is_sanctioned", False),
                        )
                    )
                elif flat.get("company_id"):
                    chain.append(
                        OwnershipLink(
                            entity_id=flat["company_id"],
                            entity_type="company",
                            entity_name=flat.get("legal_name", flat.get("company_name", "Unknown")),
                            ownership_percentage=flat.get("ownership_percentage", 100.0),
                            ownership_type=OwnershipType.INDIRECT,
                            jurisdiction=flat.get("registration_country"),
                        )
                    )

        return chain

    def _calculate_effective_ownership(self, chain: List[OwnershipLink]) -> float:
        """
        Calculate effective ownership percentage through a chain.

        Formula: Product of all ownership percentages in the chain
        Example: A owns 60% of B, B owns 80% of C -> A effectively owns 48% of C
        """
        if not chain:
            return 0.0

        effective = 100.0
        for link in chain:
            effective *= link.ownership_percentage / 100.0

        return effective

    def _calculate_risk_score(
        self, ubos: List[Dict], chains: List[List[OwnershipLink]], indicators: List[str]
    ) -> float:
        """
        Calculate overall risk score (0-100) based on:
        - Number of ownership layers
        - Presence of PEPs/sanctioned individuals
        - High-risk jurisdictions
        - Complex structures
        """
        score = 0.0

        # Base score from structure complexity
        max_layers = max(len(c) for c in chains) if chains else 0
        score += min(max_layers * 10, 30)  # Up to 30 points for complexity

        # PEP/Sanctions risk
        for ubo in ubos:
            if ubo.get("is_pep"):
                score += 15
            if ubo.get("is_sanctioned"):
                score += 25

        # High-risk jurisdiction indicators
        score += min(len(indicators) * 5, 25)

        # No identified UBOs is a red flag
        if not ubos:
            score += 20

        return min(score, 100.0)

    def _flatten_value_map(self, value_map: Dict) -> Dict:
        """Flatten JanusGraph valueMap (lists to single values)"""
        flat = {}
        for key, value in value_map.items():
            if key == T.id:
                flat["id"] = value
            elif key == T.label:
                flat["label"] = value
            elif isinstance(value, list) and len(value) == 1:
                flat[key] = value[0]
            else:
                flat[key] = value
        return flat

    # =========================================================================
    # Additional UBO Queries
    # =========================================================================

    def find_shared_ubos(self, company_ids: List[str]) -> Dict[str, List[str]]:
        """
        Find persons who are UBOs of multiple companies.

        Useful for detecting:
        - Common ownership networks
        - Potential shell company structures
        - Related party transactions

        Args:
            company_ids: List of company IDs to analyze

        Returns:
            Dict mapping person_id to list of companies they own
        """
        shared = {}

        try:
            # Optimized: Single aggregated query instead of O(n) calls
            # Find all direct beneficial owners across all specified companies
            results = (
                self.g.V()
                .has("company_id", P.within(company_ids))
                .inE("beneficial_owner")
                .where(__.values("ownership_percentage").is_(P.gte(self.ownership_threshold)))
                .project("person_id", "company_id")
                .by(__.outV().values("person_id"))
                .by(__.inV().values("company_id"))
                .toList()
            )

            # Group by person
            for r in results:
                person_id = r["person_id"]
                company_id = r["company_id"]
                if person_id not in shared:
                    shared[person_id] = []
                if company_id not in shared[person_id]:
                    shared[person_id].append(company_id)

        except Exception as e:
            logger.warning("Error in optimized shared UBO query: %s", e)
            # Fallback to individual queries (slower but more robust)
            for company_id in company_ids:
                try:
                    result = self.find_ubos_for_company(company_id)
                    for ubo in result.ubos:
                        person_id = ubo["person_id"]
                        if person_id not in shared:
                            shared[person_id] = []
                        if company_id not in shared[person_id]:
                            shared[person_id].append(company_id)
                except Exception as e2:
                    logger.warning("Error analyzing company %s: %s", company_id, e2)

        # Filter to only those with multiple companies
        return {k: v for k, v in shared.items() if len(v) > 1}

    def get_ownership_network(
        self, entity_id: str, entity_type: str = "company", depth: int = 3
    ) -> Dict[str, Any]:
        """
        Get the full ownership network around an entity.

        Returns a graph structure suitable for visualization.

        Args:
            entity_id: Starting entity ID
            entity_type: 'company' or 'person'
            depth: How many hops to traverse

        Returns:
            Dict with 'nodes' and 'edges' for visualization
        """
        nodes = []
        edges = []
        visited = set()

        id_field = f"{entity_type}_id"

        try:
            # Get the starting entity and its neighborhood
            results = (
                self.g.V()
                .has(id_field, entity_id)
                .repeat(
                    __.bothE("beneficial_owner", "owns_company", "owns_account")
                    .bothV()
                    .simplePath()
                )
                .times(depth)
                .path()
                .by(__.valueMap(True))
                .toList()
            )

            for path in results:
                objects = list(path.objects) if hasattr(path, "objects") else path
                for i, obj in enumerate(objects):
                    if isinstance(obj, dict):
                        flat = self._flatten_value_map(obj)
                        node_id = (
                            flat.get("person_id")
                            or flat.get("company_id")
                            or flat.get("account_id")
                        )

                        if node_id and node_id not in visited:
                            visited.add(node_id)
                            nodes.append(
                                {
                                    "id": node_id,
                                    "label": flat.get("label", "unknown"),
                                    "name": flat.get("full_name")
                                    or flat.get("legal_name")
                                    or flat.get("account_number", "Unknown"),
                                    "properties": flat,
                                }
                            )

            # Get edges between visited nodes
            for node in nodes:
                node_id = node["id"]
                for id_field in ["person_id", "company_id", "account_id"]:
                    try:
                        edge_results = (
                            self.g.V()
                            .has(id_field, node_id)
                            .outE("beneficial_owner", "owns_company", "owns_account")
                            .project("source", "target", "label", "properties")
                            .by(__.outV().id())
                            .by(__.inV().id())
                            .by(__.label())
                            .by(__.valueMap())
                            .toList()
                        )

                        for edge in edge_results:
                            edges.append(edge)
                        break
                    except:
                        continue

        except Exception as e:
            logger.error("Error getting ownership network: %s", e)

        return {"nodes": nodes, "edges": edges, "center": entity_id}


# Convenience functions for direct usage
def discover_ubos(company_id: str, host: str = "localhost", port: int = 18182) -> UBOResult:
    """
    Convenience function to discover UBOs for a company.

    Example:
        result = discover_ubos('COMP-12345')
        for ubo in result.ubos:
            print(f"{ubo['name']}: {ubo['ownership_percentage']:.1f}%")
    """
    engine = UBODiscovery(host=host, port=port)
    if not engine.connect():
        raise RuntimeError("Failed to connect to JanusGraph")

    try:
        return engine.find_ubos_for_company(company_id)
    finally:
        engine.close()
