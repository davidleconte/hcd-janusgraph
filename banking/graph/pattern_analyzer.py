"""
Pattern Analyzer for Relationship Pattern Detection
===================================================

Implements pattern detection algorithms for identifying suspicious relationship
patterns in fraud networks, including shared attributes, circular references,
layering structures, and velocity patterns.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.4 - Graph-Based Fraud Detection

Key Features:
    - Shared attribute pattern detection (SSN, phone, address, email)
    - Circular reference detection (A → B → C → A)
    - Layering pattern detection (shell company networks)
    - Velocity pattern detection (rapid connection formation)
    - Relationship risk scoring
    - Pattern-based fraud indicators

Business Value:
    - Detect synthetic identity fraud patterns
    - Identify money laundering layering structures
    - Find rapid account takeover patterns
    - Support AML/KYC investigations
    - Generate compliance evidence
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import networkx as nx
import logging

logger = logging.getLogger(__name__)


@dataclass
class SharedAttributePattern:
    """Represents a shared attribute pattern between entities."""
    
    attribute_type: str  # ssn, phone, address, email
    attribute_value: str
    entities: Set[str]
    entity_count: int
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    
    def get_risk_score(self) -> float:
        """
        Calculate risk score for shared attribute pattern.
        
        More entities sharing an attribute = higher risk.
        
        Returns:
            Risk score (0-100, higher = more risky)
        """
        risk_score = 0.0
        
        # Entity count factor
        if self.entity_count >= 10:
            risk_score += 50
        elif self.entity_count >= 5:
            risk_score += 40
        elif self.entity_count >= 3:
            risk_score += 30
        else:
            risk_score += 20
        
        # Attribute type factor (SSN sharing is most suspicious)
        if self.attribute_type == "ssn":
            risk_score += 40
        elif self.attribute_type == "phone":
            risk_score += 30
        elif self.attribute_type == "address":
            risk_score += 20
        elif self.attribute_type == "email":
            risk_score += 10
        
        # Velocity factor (if timestamps available)
        if self.first_seen and self.last_seen:
            time_span = (self.last_seen - self.first_seen).days
            if time_span < 7:  # All connections within a week
                risk_score += 10
        
        return min(100.0, risk_score)
    
    def get_risk_level(self) -> str:
        """Get risk level classification."""
        risk_score = self.get_risk_score()
        if risk_score >= 80:
            return "critical"
        elif risk_score >= 60:
            return "high"
        elif risk_score >= 40:
            return "medium"
        else:
            return "low"


@dataclass
class CircularPattern:
    """Represents a circular reference pattern (cycle) in the network."""
    
    cycle: List[str]
    length: int
    edge_types: List[str] = field(default_factory=list)
    total_value: float = 0.0
    
    def get_risk_score(self) -> float:
        """
        Calculate risk score for circular pattern.
        
        Shorter cycles with high values are more suspicious.
        
        Returns:
            Risk score (0-100, higher = more risky)
        """
        risk_score = 0.0
        
        # Cycle length factor (shorter = more suspicious)
        if self.length == 3:
            risk_score += 50  # Triangle (most suspicious)
        elif self.length == 4:
            risk_score += 40
        elif self.length <= 6:
            risk_score += 30
        else:
            risk_score += 20
        
        # Value factor
        if self.total_value > 100000:
            risk_score += 40
        elif self.total_value > 50000:
            risk_score += 30
        elif self.total_value > 10000:
            risk_score += 20
        
        # Edge type diversity (multiple relationship types = more suspicious)
        unique_types = len(set(self.edge_types)) if self.edge_types else 0
        if unique_types >= 3:
            risk_score += 10
        
        return min(100.0, risk_score)
    
    def get_risk_level(self) -> str:
        """Get risk level classification."""
        risk_score = self.get_risk_score()
        if risk_score >= 80:
            return "critical"
        elif risk_score >= 60:
            return "high"
        elif risk_score >= 40:
            return "medium"
        else:
            return "low"


@dataclass
class LayeringPattern:
    """Represents a layering pattern (shell company network)."""
    
    layers: List[Set[str]]
    depth: int
    total_entities: int
    root_entity: str
    
    def get_risk_score(self) -> float:
        """
        Calculate risk score for layering pattern.
        
        Deeper layers with more entities = more suspicious.
        
        Returns:
            Risk score (0-100, higher = more risky)
        """
        risk_score = 0.0
        
        # Depth factor (deeper = more suspicious)
        if self.depth >= 5:
            risk_score += 50
        elif self.depth >= 4:
            risk_score += 40
        elif self.depth >= 3:
            risk_score += 30
        else:
            risk_score += 20
        
        # Entity count factor
        if self.total_entities >= 20:
            risk_score += 40
        elif self.total_entities >= 10:
            risk_score += 30
        elif self.total_entities >= 5:
            risk_score += 20
        
        # Layer distribution (balanced layers = more suspicious)
        layer_sizes = [len(layer) for layer in self.layers]
        if len(layer_sizes) > 1:
            avg_size = sum(layer_sizes) / len(layer_sizes)
            variance = sum((s - avg_size) ** 2 for s in layer_sizes) / len(layer_sizes)
            if variance < 2:  # Low variance = balanced = suspicious
                risk_score += 10
        
        return min(100.0, risk_score)
    
    def get_risk_level(self) -> str:
        """Get risk level classification."""
        risk_score = self.get_risk_score()
        if risk_score >= 80:
            return "critical"
        elif risk_score >= 60:
            return "high"
        elif risk_score >= 40:
            return "medium"
        else:
            return "low"


@dataclass
class VelocityPattern:
    """Represents a velocity pattern (rapid connection formation)."""
    
    entity_id: str
    connection_count: int
    time_window_days: int
    connection_rate: float  # connections per day
    connection_types: List[str] = field(default_factory=list)
    
    def get_risk_score(self) -> float:
        """
        Calculate risk score for velocity pattern.
        
        More connections in shorter time = more suspicious.
        
        Returns:
            Risk score (0-100, higher = more risky)
        """
        risk_score = 0.0
        
        # Connection rate factor
        if self.connection_rate >= 10:  # 10+ connections per day
            risk_score += 50
        elif self.connection_rate >= 5:
            risk_score += 40
        elif self.connection_rate >= 2:
            risk_score += 30
        else:
            risk_score += 20
        
        # Total connection count factor
        if self.connection_count >= 50:
            risk_score += 30
        elif self.connection_count >= 20:
            risk_score += 20
        elif self.connection_count >= 10:
            risk_score += 10
        
        # Time window factor (shorter = more suspicious)
        if self.time_window_days <= 7:
            risk_score += 20
        elif self.time_window_days <= 30:
            risk_score += 10
        
        return min(100.0, risk_score)
    
    def get_risk_level(self) -> str:
        """Get risk level classification."""
        risk_score = self.get_risk_score()
        if risk_score >= 80:
            return "critical"
        elif risk_score >= 60:
            return "high"
        elif risk_score >= 40:
            return "medium"
        else:
            return "low"


@dataclass
class PatternAnalysisResult:
    """Complete pattern analysis results."""
    
    shared_attribute_patterns: List[SharedAttributePattern]
    circular_patterns: List[CircularPattern]
    layering_patterns: List[LayeringPattern]
    velocity_patterns: List[VelocityPattern]
    
    def get_high_risk_patterns(self, min_risk: float = 60.0) -> Dict[str, List[Any]]:
        """
        Get all high-risk patterns across all categories.
        
        Args:
            min_risk: Minimum risk score threshold
            
        Returns:
            Dictionary of high-risk patterns by type
        """
        return {
            "shared_attributes": [
                p for p in self.shared_attribute_patterns
                if p.get_risk_score() >= min_risk
            ],
            "circular": [
                p for p in self.circular_patterns
                if p.get_risk_score() >= min_risk
            ],
            "layering": [
                p for p in self.layering_patterns
                if p.get_risk_score() >= min_risk
            ],
            "velocity": [
                p for p in self.velocity_patterns
                if p.get_risk_score() >= min_risk
            ],
        }
    
    def get_pattern_summary(self) -> Dict[str, int]:
        """Get summary counts of all patterns."""
        return {
            "shared_attribute_patterns": len(self.shared_attribute_patterns),
            "circular_patterns": len(self.circular_patterns),
            "layering_patterns": len(self.layering_patterns),
            "velocity_patterns": len(self.velocity_patterns),
            "total_patterns": (
                len(self.shared_attribute_patterns) +
                len(self.circular_patterns) +
                len(self.layering_patterns) +
                len(self.velocity_patterns)
            ),
        }


class PatternAnalyzer:
    """
    Analyzes relationship patterns in fraud networks.
    
    Detects various suspicious patterns including shared attributes,
    circular references, layering structures, and velocity patterns.
    """
    
    def __init__(self) -> None:
        """Initialize the pattern analyzer."""
        self.logger = logging.getLogger(__name__)
    
    def detect_shared_attributes(
        self,
        identities: List[Dict[str, Any]],
        attribute_types: Optional[List[str]] = None,
    ) -> List[SharedAttributePattern]:
        """
        Detect shared attribute patterns across identities.
        
        Args:
            identities: List of identity dictionaries
            attribute_types: Attribute types to check (default: ssn, phone, address, email)
            
        Returns:
            List of shared attribute patterns
        """
        if attribute_types is None:
            attribute_types = ["ssn", "phone", "address", "email"]
        
        # Build attribute index
        attribute_index: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
        
        for identity in identities:
            entity_id = identity.get("id", identity.get("identity_id", "unknown"))
            
            for attr_type in attribute_types:
                attr_value = identity.get(attr_type)
                if attr_value:
                    attribute_index[attr_type][attr_value].add(entity_id)
        
        # Find shared attributes
        patterns = []
        for attr_type, values in attribute_index.items():
            for attr_value, entities in values.items():
                if len(entities) >= 2:  # At least 2 entities share this attribute
                    pattern = SharedAttributePattern(
                        attribute_type=attr_type,
                        attribute_value=attr_value,
                        entities=entities,
                        entity_count=len(entities),
                    )
                    patterns.append(pattern)
        
        # Sort by risk score (highest first)
        patterns.sort(key=lambda p: p.get_risk_score(), reverse=True)
        
        self.logger.info(f"Detected {len(patterns)} shared attribute patterns")
        return patterns
    
    def detect_circular_patterns(
        self,
        graph: nx.Graph,
        max_cycle_length: int = 6,
    ) -> List[CircularPattern]:
        """
        Detect circular reference patterns (cycles) in the network.
        
        Args:
            graph: NetworkX graph
            max_cycle_length: Maximum cycle length to detect
            
        Returns:
            List of circular patterns
        """
        patterns = []
        
        # Find all simple cycles up to max_cycle_length
        try:
            # Use simple_cycles for directed graphs, or find cycles in undirected
            if graph.is_directed():
                cycles = list(nx.simple_cycles(graph))
            else:
                # For undirected graphs, find cycles using cycle basis
                cycles = nx.cycle_basis(graph)
            
            for cycle in cycles:
                if len(cycle) <= max_cycle_length:
                    # Get edge types and values if available
                    edge_types = []
                    total_value = 0.0
                    
                    for i in range(len(cycle)):
                        u = cycle[i]
                        v = cycle[(i + 1) % len(cycle)]
                        
                        if graph.has_edge(u, v):
                            edge_data = graph[u][v]
                            edge_types.append(edge_data.get("type", "unknown"))
                            total_value += edge_data.get("value", 0.0)
                    
                    pattern = CircularPattern(
                        cycle=cycle,
                        length=len(cycle),
                        edge_types=edge_types,
                        total_value=total_value,
                    )
                    patterns.append(pattern)
        
        except Exception as e:
            self.logger.warning(f"Error detecting cycles: {e}")
        
        # Sort by risk score (highest first)
        patterns.sort(key=lambda p: p.get_risk_score(), reverse=True)
        
        self.logger.info(f"Detected {len(patterns)} circular patterns")
        return patterns
    
    def detect_layering_patterns(
        self,
        graph: nx.DiGraph,
        min_depth: int = 3,
    ) -> List[LayeringPattern]:
        """
        Detect layering patterns (shell company networks).
        
        Args:
            graph: Directed NetworkX graph
            min_depth: Minimum depth to consider as layering
            
        Returns:
            List of layering patterns
        """
        patterns = []
        
        # Find nodes with no incoming edges (potential root entities)
        root_nodes = [n for n in graph.nodes() if graph.in_degree(n) == 0]
        
        for root in root_nodes:
            # Perform BFS to find layers
            layers: List[Set[str]] = []
            visited = {root}
            current_layer = {root}
            
            while current_layer:
                layers.append(current_layer.copy())
                next_layer = set()
                
                for node in current_layer:
                    for successor in graph.successors(node):
                        if successor not in visited:
                            next_layer.add(successor)
                            visited.add(successor)
                
                current_layer = next_layer
            
            # Check if this is a layering pattern
            # Depth is number of layers minus root layer
            depth = len(layers) - 1
            if depth >= min_depth:
                pattern = LayeringPattern(
                    layers=layers,
                    depth=depth,
                    total_entities=len(visited),
                    root_entity=root,
                )
                patterns.append(pattern)
        
        # Sort by risk score (highest first)
        patterns.sort(key=lambda p: p.get_risk_score(), reverse=True)
        
        self.logger.info(f"Detected {len(patterns)} layering patterns")
        return patterns
    
    def detect_velocity_patterns(
        self,
        graph: nx.Graph,
        time_window_days: int = 30,
        min_connections: int = 5,
    ) -> List[VelocityPattern]:
        """
        Detect velocity patterns (rapid connection formation).
        
        Args:
            graph: NetworkX graph with timestamp data
            time_window_days: Time window to analyze (days)
            min_connections: Minimum connections to flag
            
        Returns:
            List of velocity patterns
        """
        patterns = []
        
        for node in graph.nodes():
            # Get all edges for this node with timestamps
            edges_with_time = []
            
            for neighbor in graph.neighbors(node):
                edge_data = graph[node][neighbor]
                timestamp = edge_data.get("timestamp")
                if timestamp:
                    edges_with_time.append({
                        "neighbor": neighbor,
                        "timestamp": timestamp,
                        "type": edge_data.get("type", "unknown"),
                    })
            
            if not edges_with_time:
                continue
            
            # Sort by timestamp
            edges_with_time.sort(key=lambda e: e["timestamp"])
            
            # Find rapid connection windows
            for i in range(len(edges_with_time)):
                start_time = edges_with_time[i]["timestamp"]
                end_time = start_time + timedelta(days=time_window_days)
                
                # Count connections in this window
                connections_in_window = [
                    e for e in edges_with_time
                    if start_time <= e["timestamp"] <= end_time
                ]
                
                if len(connections_in_window) >= min_connections:
                    connection_rate = len(connections_in_window) / time_window_days
                    connection_types = [e["type"] for e in connections_in_window]
                    
                    pattern = VelocityPattern(
                        entity_id=node,
                        connection_count=len(connections_in_window),
                        time_window_days=time_window_days,
                        connection_rate=connection_rate,
                        connection_types=connection_types,
                    )
                    patterns.append(pattern)
                    break  # Only report once per node
        
        # Sort by risk score (highest first)
        patterns.sort(key=lambda p: p.get_risk_score(), reverse=True)
        
        self.logger.info(f"Detected {len(patterns)} velocity patterns")
        return patterns
    
    def analyze_patterns(
        self,
        graph: nx.Graph,
        identities: Optional[List[Dict[str, Any]]] = None,
        detect_shared: bool = True,
        detect_circular: bool = True,
        detect_layering: bool = True,
        detect_velocity: bool = True,
    ) -> PatternAnalysisResult:
        """
        Perform comprehensive pattern analysis.
        
        Args:
            graph: NetworkX graph
            identities: List of identity dictionaries (for shared attribute detection)
            detect_shared: Whether to detect shared attribute patterns
            detect_circular: Whether to detect circular patterns
            detect_layering: Whether to detect layering patterns
            detect_velocity: Whether to detect velocity patterns
            
        Returns:
            Complete pattern analysis results
        """
        shared_patterns = []
        circular_patterns = []
        layering_patterns = []
        velocity_patterns = []
        
        if detect_shared and identities:
            shared_patterns = self.detect_shared_attributes(identities)
        
        if detect_circular:
            circular_patterns = self.detect_circular_patterns(graph)
        
        if detect_layering and isinstance(graph, nx.DiGraph):
            layering_patterns = self.detect_layering_patterns(graph)
        
        if detect_velocity:
            velocity_patterns = self.detect_velocity_patterns(graph)
        
        result = PatternAnalysisResult(
            shared_attribute_patterns=shared_patterns,
            circular_patterns=circular_patterns,
            layering_patterns=layering_patterns,
            velocity_patterns=velocity_patterns,
        )
        
        summary = result.get_pattern_summary()
        self.logger.info(f"Pattern analysis complete: {summary['total_patterns']} total patterns")
        
        return result


# Made with Bob