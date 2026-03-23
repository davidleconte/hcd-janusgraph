"""
Community Detection for Fraud Ring Analysis
============================================

Graph analytics module for detecting fraud communities, collusion networks,
and organized financial crime patterns using JanusGraph and Gremlin.

Features:
- Connected Components detection for fraud clusters
- PageRank for identifying central orchestrators
- Triangle Counting for collusion detection
- Community-level risk scoring
- Fraud ring visualization data

Regulatory Background:
- FinCEN SAR Reporting: Requires identification of coordinated activity
- FATF Recommendation 20: Reporting of suspicious transactions
- EU AMLD6: Criminal liability for aiding money laundering

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watsonx.Data Global Product Specialist (GPS)
Date: 2026-03-23
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class CommunityRiskLevel(str, Enum):
    """Risk levels for detected communities."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


@dataclass
class CommunityMember:
    """Represents a member of a detected fraud community."""
    vertex_id: str
    label: str
    name: str
    role: str  # 'orchestrator', 'hub', 'mule', 'peripheral'
    pagerank_score: float
    triangle_count: int
    degree: int
    risk_score: float
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FraudCommunity:
    """Represents a detected fraud community/ring."""
    community_id: str
    member_count: int
    members: List[CommunityMember]
    total_transactions: int
    total_value: float
    orchestrators: List[str]  # IDs of central actors
    mule_accounts: List[str]  # IDs of money mules
    risk_level: CommunityRiskLevel
    risk_score: float
    detection_timestamp: datetime
    indicators: List[str]
    subgraph_density: float
    modularity: float


@dataclass
class CommunityDetectionResult:
    """Complete results from community detection analysis."""
    total_communities: int
    communities: List[FraudCommunity]
    high_risk_communities: int
    total_fraud_actors: int
    orchestrators_identified: int
    mule_accounts_identified: int
    analysis_timestamp: datetime
    graph_stats: Dict[str, Any]


class CommunityDetector:
    """
    Detects fraud communities using graph analytics algorithms.
    
    Uses JanusGraph Gremlin traversals to:
    1. Find connected components of suspicious accounts
    2. Calculate PageRank to identify orchestrators
    3. Count triangles for collusion detection
    4. Score communities by risk
    
    Example:
        >>> detector = CommunityDetector(client)
        >>> results = detector.detect_fraud_communities(min_size=3)
        >>> for community in results.communities:
        ...     print(f"Community {community.community_id}: {community.member_count} members, risk={community.risk_level}")
    """
    
    # Risk scoring weights
    ORCHESTRATOR_PAGERANK_THRESHOLD = 0.01
    MULE_DEGREE_THRESHOLD = 5
    TRIANGLE_COLLUSION_THRESHOLD = 3
    
    def __init__(self, client: Any, min_community_size: int = 3):
        """
        Initialize Community Detector.
        
        Args:
            client: JanusGraph client with execute() method
            min_community_size: Minimum members for a valid community
        """
        self.client = client
        self.min_community_size = min_community_size
        self._results: Optional[CommunityDetectionResult] = None
    
    def detect_fraud_communities(
        self,
        include_transactions: bool = True,
        min_risk_score: float = 0.3
    ) -> CommunityDetectionResult:
        """
        Perform full community detection analysis.
        
        Args:
            include_transactions: Include transaction analysis
            min_risk_score: Minimum risk score to include community
            
        Returns:
            CommunityDetectionResult with all detected communities
        """
        logger.info("Starting fraud community detection...")
        
        # Step 1: Find connected components
        components = self._find_connected_components()
        logger.info(f"Found {len(components)} connected components")
        
        # Step 2: Analyze each component
        communities = []
        for component_id, vertex_ids in enumerate(components):
            if len(vertex_ids) < self.min_community_size:
                continue
            
            community = self._analyze_community(
                community_id=f"COMM-{component_id:04d}",
                vertex_ids=vertex_ids,
                include_transactions=include_transactions
            )
            
            if community and community.risk_score >= min_risk_score:
                communities.append(community)
        
        # Step 3: Build final results
        self._results = CommunityDetectionResult(
            total_communities=len(communities),
            communities=sorted(communities, key=lambda c: c.risk_score, reverse=True),
            high_risk_communities=sum(1 for c in communities if c.risk_level in [CommunityRiskLevel.CRITICAL, CommunityRiskLevel.HIGH]),
            total_fraud_actors=sum(c.member_count for c in communities),
            orchestrators_identified=sum(len(c.orchestrators) for c in communities),
            mule_accounts_identified=sum(len(c.mule_accounts) for c in communities),
            analysis_timestamp=datetime.utcnow(),
            graph_stats=self._get_graph_stats()
        )
        
        logger.info(f"Detected {self._results.total_communities} fraud communities")
        return self._results
    
    def _find_connected_components(self) -> List[List[str]]:
        """
        Find connected components in the graph.
        
        Uses Gremlin to identify clusters of connected vertices.
        Returns list of vertex ID lists, one per component.
        """
        # Get all vertices with transaction edges
        query = """
        g.V().hasLabel('person', 'company', 'account')
            .where(outE('owns_account', 'transfers_to', 'receives_from', 'knows').limit(1))
            .group().by('component').by(id())
            .unfold()
            .select(values)
        """
        
        try:
            result = self.client.execute(query)
            # Parse results - each component is a list of vertex IDs
            components = []
            for component in result:
                if isinstance(component, list):
                    components.append([str(v) for v in component])
            return components
        except Exception as e:
            logger.warning(f"Component query failed, using fallback: {e}")
            return self._find_components_fallback()
    
    def _find_components_fallback(self) -> List[List[str]]:
        """
        Fallback connected components using BFS.
        
        Used when JanusGraph doesn't have component() step enabled.
        """
        # Get all relevant vertices
        vertices_query = "g.V().hasLabel('person', 'company', 'account').id()"
        all_vertices = self.client.execute(vertices_query)
        
        visited = set()
        components = []
        
        for vertex_id in all_vertices:
            if str(vertex_id) in visited:
                continue
            
            # BFS to find connected component
            component = self._bfs_component(str(vertex_id), visited)
            if component:
                components.append(component)
        
        return components
    
    def _bfs_component(self, start_id: str, visited: Set[str]) -> List[str]:
        """BFS to find all vertices connected to start_id."""
        component = []
        queue = [start_id]
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            
            visited.add(current)
            component.append(current)
            
            # Get neighbors
            neighbors_query = f"""
            g.V('{current}').both('owns_account', 'transfers_to', 'receives_from', 'knows', 'owns_company').id()
            """
            neighbors = self.client.execute(neighbors_query)
            
            for neighbor in neighbors:
                neighbor_str = str(neighbor)
                if neighbor_str not in visited:
                    queue.append(neighbor_str)
        
        return component
    
    def _analyze_community(
        self,
        community_id: str,
        vertex_ids: List[str],
        include_transactions: bool
    ) -> Optional[FraudCommunity]:
        """Analyze a single community for fraud indicators."""
        
        # Get vertex details
        members = []
        for vid in vertex_ids:
            member = self._get_member_details(vid)
            if member:
                members.append(member)
        
        if len(members) < self.min_community_size:
            return None
        
        # Calculate PageRank (simplified - degree-based for now)
        self._calculate_pagerank(members)
        
        # Count triangles for each member
        self._count_triangles(members)
        
        # Classify roles
        orchestrators = []
        mule_accounts = []
        for member in members:
            if member.pagerank_score > self.ORCHESTRATOR_PAGERANK_THRESHOLD:
                member.role = "orchestrator"
                orchestrators.append(member.vertex_id)
            elif member.degree >= self.MULE_DEGREE_THRESHOLD:
                member.role = "hub"
            else:
                member.role = "peripheral"
        
        # Get transactions if requested
        total_transactions = 0
        total_value = 0.0
        if include_transactions:
            total_transactions, total_value = self._get_community_transactions(vertex_ids)
        
        # Calculate risk score
        risk_score = self._calculate_community_risk(
            members, total_transactions, total_value
        )
        
        # Determine risk level
        if risk_score >= 0.8:
            risk_level = CommunityRiskLevel.CRITICAL
        elif risk_score >= 0.6:
            risk_level = CommunityRiskLevel.HIGH
        elif risk_score >= 0.4:
            risk_level = CommunityRiskLevel.MEDIUM
        elif risk_score >= 0.2:
            risk_level = CommunityRiskLevel.LOW
        else:
            risk_level = CommunityRiskLevel.MINIMAL
        
        # Generate indicators
        indicators = self._generate_indicators(members, total_value)
        
        # Calculate subgraph density
        density = self._calculate_density(members)
        
        return FraudCommunity(
            community_id=community_id,
            member_count=len(members),
            members=members,
            total_transactions=total_transactions,
            total_value=total_value,
            orchestrators=orchestrators,
            mule_accounts=mule_accounts,
            risk_level=risk_level,
            risk_score=risk_score,
            detection_timestamp=datetime.utcnow(),
            indicators=indicators,
            subgraph_density=density,
            modularity=0.0  # Calculated globally
        )
    
    def _get_member_details(self, vertex_id: str) -> Optional[CommunityMember]:
        """Get details for a community member vertex."""
        query = f"""
        g.V('{vertex_id}').valueMap(true).unfold().group().by(keys).by(values)
        """
        
        try:
            result = self.client.execute(query)
            if not result:
                return None
            
            props = result[0] if isinstance(result, list) else result
            
            # Extract common properties
            label = props.get("label", "unknown")
            name = props.get("name", props.get("legalName", props.get("fullName", "Unknown")))
            
            return CommunityMember(
                vertex_id=vertex_id,
                label=label,
                name=str(name) if isinstance(name, list) else name,
                role="unknown",
                pagerank_score=0.0,
                triangle_count=0,
                degree=0,
                risk_score=0.0,
                properties=props
            )
        except Exception as e:
            logger.debug(f"Failed to get details for {vertex_id}: {e}")
            return None
    
    def _calculate_pagerank(self, members: List[CommunityMember]) -> None:
        """Calculate PageRank-style scores for members."""
        # Simplified PageRank based on degree
        total_edges = sum(m.degree for m in members)
        
        for member in members:
            # Get degree (edge count)
            degree_query = f"g.V('{member.vertex_id}').bothE().count()"
            try:
                degree = self.client.execute(degree_query)
                member.degree = int(degree[0]) if degree else 0
            except:
                member.degree = 0
            
            # PageRank approximation
            if total_edges > 0:
                member.pagerank_score = member.degree / total_edges
    
    def _count_triangles(self, members: List[CommunityMember]) -> None:
        """Count triangles (3-cycles) for collusion detection."""
        for member in members:
            # Count triangles: friends of friends who are also friends
            query = f"""
            g.V('{member.vertex_id}').both().aggregate('x').by(id()).
                both().where(within('x')).where(neq('{member.vertex_id}')).
                dedup().count()
            """
            try:
                count = self.client.execute(query)
                member.triangle_count = int(count[0]) if count else 0
            except:
                member.triangle_count = 0
    
    def _get_community_transactions(self, vertex_ids: List[str]) -> Tuple[int, float]:
        """Get transaction count and total value for community."""
        if not vertex_ids:
            return 0, 0.0
        
        query = f"""
        g.V({vertex_ids}).outE('transfers_to', 'receives_from').
            has('amount').
            group().
            by(constant('total')).
            by(project('count', 'sum').by(count()).by(values('amount').sum())).
            unfold().select(values)
        """
        
        try:
            result = self.client.execute(query)
            if result:
                count = result.get("count", 0)
                total = result.get("sum", 0.0)
                return int(count), float(total)
        except:
            pass
        
        return 0, 0.0
    
    def _calculate_community_risk(
        self,
        members: List[CommunityMember],
        total_transactions: int,
        total_value: float
    ) -> float:
        """Calculate overall risk score for community (0-1)."""
        score = 0.0
        
        # Orchestration risk
        orchestrator_count = sum(1 for m in members if m.role == "orchestrator")
        score += min(orchestrator_count * 0.1, 0.3)
        
        # Triangle risk (collusion)
        high_triangle_count = sum(1 for m in members if m.triangle_count >= self.TRIANGLE_COLLUSION_THRESHOLD)
        score += min(high_triangle_count * 0.05, 0.2)
        
        # Value risk
        if total_value > 1_000_000:
            score += 0.3
        elif total_value > 500_000:
            score += 0.2
        elif total_value > 100_000:
            score += 0.1
        
        # Velocity risk
        if total_transactions > 100:
            score += 0.2
        elif total_transactions > 50:
            score += 0.1
        
        return min(score, 1.0)
    
    def _generate_indicators(
        self,
        members: List[CommunityMember],
        total_value: float
    ) -> List[str]:
        """Generate fraud indicators for the community."""
        indicators = ["community_detected", "coordinated_activity"]
        
        # Orchestration indicators
        orchestrators = [m for m in members if m.role == "orchestrator"]
        if orchestrators:
            indicators.append("central_orchestrator_identified")
        
        # Collusion indicators
        high_triangles = [m for m in members if m.triangle_count >= self.TRIANGLE_COLLUSION_THRESHOLD]
        if high_triangles:
            indicators.append("collusion_pattern_detected")
        
        # Value indicators
        if total_value > 500_000:
            indicators.append("high_value_network")
        
        # Hub indicators
        hubs = [m for m in members if m.role == "hub"]
        if len(hubs) >= 3:
            indicators.append("multiple_hub_accounts")
        
        return indicators
    
    def _calculate_density(self, members: List[CommunityMember]) -> float:
        """Calculate subgraph density (ratio of actual to possible edges)."""
        n = len(members)
        if n < 2:
            return 0.0
        
        # Count actual edges
        total_edges = sum(m.degree for m in members) // 2  # Undirected
        
        # Possible edges in complete graph
        possible_edges = n * (n - 1) / 2
        
        return total_edges / possible_edges if possible_edges > 0 else 0.0
    
    def _get_graph_stats(self) -> Dict[str, Any]:
        """Get overall graph statistics."""
        stats = {}
        
        try:
            stats["total_vertices"] = self.client.execute("g.V().count()")[0]
            stats["total_edges"] = self.client.execute("g.E().count()")[0]
            stats["person_count"] = self.client.execute("g.V().hasLabel('person').count()")[0]
            stats["company_count"] = self.client.execute("g.V().hasLabel('company').count()")[0]
            stats["account_count"] = self.client.execute("g.V().hasLabel('account').count()")[0]
        except:
            pass
        
        return stats
    
    def get_orchestrator_traversal(self) -> str:
        """Return Gremlin traversal to find orchestrators (high PageRank)."""
        return """
        g.V().hasLabel('person', 'company').
            order().by(
                bothE().count(),
                desc
            ).
            limit(10).
            project('id', 'name', 'degree', 'label').
            by(id()).
            by(coalesce(values('name'), values('legalName'))).
            by(bothE().count()).
            by(label())
        """
    
    def get_collusion_triangles_traversal(self) -> str:
        """Return Gremlin traversal to find collusion triangles."""
        return """
        g.V().hasLabel('person', 'account').
            as('a').
            both().as('b').
            both().where(eq('a')).where(neq('b')).
            dedup().
            by(ordering).
            project('members', 'edge_count').
            by(dedup().fold()).
            by(path().count(local))
        """
    
    def export_for_visualization(
        self,
        community: FraudCommunity,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        Export community data for visualization (D3.js, Gephi, etc.).
        
        Args:
            community: FraudCommunity to export
            format: Output format ('json', 'gexf', 'graphml')
            
        Returns:
            Dict with nodes and edges for visualization
        """
        nodes = []
        for member in community.members:
            nodes.append({
                "id": member.vertex_id,
                "label": member.name,
                "type": member.label,
                "role": member.role,
                "risk_score": member.risk_score,
                "pagerank": member.pagerank_score,
                "triangles": member.triangle_count,
                "size": max(10, member.degree * 2)  # Node size for viz
            })
        
        # Get edges
        edges = []
        if community.members:
            vertex_ids = [m.vertex_id for m in community.members]
            edges_query = f"""
            g.V({vertex_ids}).outE().where(inV().within({vertex_ids})).
                project('source', 'target', 'type', 'properties').
                by(outV().id()).
                by(inV().id()).
                by(label()).
                by(valueMap())
            """
            try:
                edges = self.client.execute(edges_query)
            except:
                pass
        
        return {
            "community_id": community.community_id,
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "risk_level": community.risk_level.value,
                "risk_score": community.risk_score,
                "member_count": community.member_count,
                "total_value": community.total_value,
                "indicators": community.indicators
            }
        }


def create_community_detection_report(
    results: CommunityDetectionResult,
    output_format: str = "summary"
) -> str:
    """
    Create a compliance-ready community detection report.
    
    Args:
        results: Detection results from CommunityDetector
        output_format: 'summary', 'detailed', or 'sar_ready'
        
    Returns:
        Formatted report string
    """
    lines = [
        "=" * 70,
        "FRAUD COMMUNITY DETECTION REPORT",
        f"Generated: {results.analysis_timestamp.isoformat()}",
        "=" * 70,
        "",
        "EXECUTIVE SUMMARY",
        "-" * 40,
        f"Total Communities Detected: {results.total_communities}",
        f"High-Risk Communities: {results.high_risk_communities}",
        f"Total Fraud Actors: {results.total_fraud_actors}",
        f"Orchestrators Identified: {results.orchestrators_identified}",
        f"Mule Accounts Identified: {results.mule_accounts_identified}",
        "",
    ]
    
    if output_format == "summary":
        return "\n".join(lines)
    
    # Detailed community breakdown
    lines.extend([
        "DETECTED COMMUNITIES",
        "-" * 40,
    ])
    
    for i, community in enumerate(results.communities[:10], 1):  # Top 10
        lines.extend([
            f"\nCommunity {i}: {community.community_id}",
            f"  Members: {community.member_count}",
            f"  Risk Level: {community.risk_level.value.upper()}",
            f"  Risk Score: {community.risk_score:.2f}",
            f"  Total Value: ${community.total_value:,.2f}",
            f"  Transactions: {community.total_transactions}",
            f"  Orchestrators: {len(community.orchestrators)}",
            f"  Indicators: {', '.join(community.indicators[:5])}",
        ])
    
    if output_format == "sar_ready":
        lines.extend([
            "",
            "=" * 70,
            "SUSPICIOUS ACTIVITY REPORT (SAR) DATA",
            "-" * 40,
            "This section provides structured data for SAR filing:",
            "",
            "Subject Accounts:",
        ])
        
        for community in results.communities:
            if community.risk_level in [CommunityRiskLevel.CRITICAL, CommunityRiskLevel.HIGH]:
                for member in community.members:
                    if member.role in ["orchestrator", "hub"]:
                        lines.append(f"  - {member.name} ({member.label}) - Risk: {member.risk_score:.2f}")
    
    return "\n".join(lines)
