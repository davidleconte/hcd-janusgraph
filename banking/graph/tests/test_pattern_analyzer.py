"""
Unit Tests for Pattern Analyzer
================================

Tests for relationship pattern detection including shared attributes,
circular references, layering structures, and velocity patterns.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.4 - Graph-Based Fraud Detection
"""

import pytest
import networkx as nx
from datetime import datetime, timedelta
from typing import List, Dict, Any

from banking.graph.pattern_analyzer import (
    PatternAnalyzer,
    SharedAttributePattern,
    CircularPattern,
    LayeringPattern,
    VelocityPattern,
    PatternAnalysisResult,
)


class TestSharedAttributePattern:
    """Test SharedAttributePattern dataclass."""
    
    def test_pattern_creation(self) -> None:
        """Test creating a shared attribute pattern."""
        pattern = SharedAttributePattern(
            attribute_type="ssn",
            attribute_value="123-45-6789",
            entities={"id1", "id2", "id3"},
            entity_count=3,
        )
        
        assert pattern.attribute_type == "ssn"
        assert pattern.attribute_value == "123-45-6789"
        assert len(pattern.entities) == 3
        assert pattern.entity_count == 3
    
    def test_risk_score_ssn_high_count(self) -> None:
        """Test risk score for SSN shared by many entities."""
        pattern = SharedAttributePattern(
            attribute_type="ssn",
            attribute_value="123-45-6789",
            entities={f"id{i}" for i in range(10)},
            entity_count=10,
        )
        
        risk_score = pattern.get_risk_score()
        assert risk_score >= 80  # High risk: SSN + 10 entities
    
    def test_risk_score_phone_medium_count(self) -> None:
        """Test risk score for phone shared by few entities."""
        pattern = SharedAttributePattern(
            attribute_type="phone",
            attribute_value="555-1234",
            entities={"id1", "id2", "id3"},
            entity_count=3,
        )
        
        risk_score = pattern.get_risk_score()
        assert 40 <= risk_score < 80  # Medium risk
    
    def test_risk_score_with_velocity(self) -> None:
        """Test risk score increases with rapid connections."""
        now = datetime.now()
        pattern = SharedAttributePattern(
            attribute_type="ssn",
            attribute_value="123-45-6789",
            entities={"id1", "id2", "id3"},
            entity_count=3,
            first_seen=now,
            last_seen=now + timedelta(days=3),  # 3 days
        )
        
        risk_score = pattern.get_risk_score()
        assert risk_score >= 60  # Velocity bonus applied
    
    def test_risk_levels(self) -> None:
        """Test risk level classification."""
        # Critical
        pattern_critical = SharedAttributePattern(
            attribute_type="ssn",
            attribute_value="123-45-6789",
            entities={f"id{i}" for i in range(10)},
            entity_count=10,
        )
        assert pattern_critical.get_risk_level() == "critical"
        
        # Low
        pattern_low = SharedAttributePattern(
            attribute_type="email",
            attribute_value="test@example.com",
            entities={"id1", "id2"},
            entity_count=2,
        )
        assert pattern_low.get_risk_level() == "low"


class TestCircularPattern:
    """Test CircularPattern dataclass."""
    
    def test_pattern_creation(self) -> None:
        """Test creating a circular pattern."""
        pattern = CircularPattern(
            cycle=["A", "B", "C", "A"],
            length=3,
            edge_types=["transfer", "transfer", "transfer"],
            total_value=50000.0,
        )
        
        assert pattern.length == 3
        assert len(pattern.cycle) == 4  # Includes return to start
        assert pattern.total_value == 50000.0
    
    def test_risk_score_triangle_high_value(self) -> None:
        """Test risk score for triangle with high value."""
        pattern = CircularPattern(
            cycle=["A", "B", "C", "A"],
            length=3,
            edge_types=["transfer", "transfer", "transfer"],
            total_value=150000.0,
        )
        
        risk_score = pattern.get_risk_score()
        assert risk_score >= 80  # High risk: triangle + high value
    
    def test_risk_score_long_cycle(self) -> None:
        """Test risk score for longer cycle."""
        pattern = CircularPattern(
            cycle=["A", "B", "C", "D", "E", "F", "G", "A"],
            length=7,
            edge_types=["transfer"] * 7,
            total_value=10000.0,
        )
        
        risk_score = pattern.get_risk_score()
        assert risk_score < 60  # Lower risk: long cycle
    
    def test_risk_score_diverse_edge_types(self) -> None:
        """Test risk score with diverse edge types."""
        pattern = CircularPattern(
            cycle=["A", "B", "C", "A"],
            length=3,
            edge_types=["transfer", "loan", "payment"],
            total_value=50000.0,
        )
        
        risk_score = pattern.get_risk_score()
        assert risk_score >= 70  # Bonus for diverse types
    
    def test_risk_levels(self) -> None:
        """Test risk level classification."""
        # High
        pattern_high = CircularPattern(
            cycle=["A", "B", "C", "A"],
            length=3,
            total_value=100000.0,
        )
        assert pattern_high.get_risk_level() in ["high", "critical"]


class TestLayeringPattern:
    """Test LayeringPattern dataclass."""
    
    def test_pattern_creation(self) -> None:
        """Test creating a layering pattern."""
        pattern = LayeringPattern(
            layers=[{"root"}, {"A", "B"}, {"C", "D", "E"}],
            depth=3,
            total_entities=6,
            root_entity="root",
        )
        
        assert pattern.depth == 3
        assert pattern.total_entities == 6
        assert pattern.root_entity == "root"
    
    def test_risk_score_deep_layers(self) -> None:
        """Test risk score for deep layering."""
        pattern = LayeringPattern(
            layers=[{"root"}] + [{f"L{i}_{j}" for j in range(3)} for i in range(5)],
            depth=6,
            total_entities=16,
            root_entity="root",
        )
        
        risk_score = pattern.get_risk_score()
        assert risk_score >= 80  # High risk: deep + many entities
    
    def test_risk_score_balanced_layers(self) -> None:
        """Test risk score bonus for balanced layers."""
        pattern = LayeringPattern(
            layers=[{"root"}, {"A", "B", "C"}, {"D", "E", "F"}, {"G", "H", "I"}],
            depth=4,
            total_entities=10,
            root_entity="root",
        )
        
        risk_score = pattern.get_risk_score()
        assert risk_score >= 60  # Bonus for balanced structure
    
    def test_risk_levels(self) -> None:
        """Test risk level classification."""
        # Critical
        pattern_critical = LayeringPattern(
            layers=[{"root"}] + [{f"L{i}_{j}" for j in range(5)} for i in range(5)],
            depth=6,
            total_entities=26,
            root_entity="root",
        )
        assert pattern_critical.get_risk_level() == "critical"


class TestVelocityPattern:
    """Test VelocityPattern dataclass."""
    
    def test_pattern_creation(self) -> None:
        """Test creating a velocity pattern."""
        pattern = VelocityPattern(
            entity_id="entity1",
            connection_count=20,
            time_window_days=7,
            connection_rate=2.86,
            connection_types=["transfer"] * 20,
        )
        
        assert pattern.entity_id == "entity1"
        assert pattern.connection_count == 20
        assert pattern.time_window_days == 7
    
    def test_risk_score_high_velocity(self) -> None:
        """Test risk score for high connection velocity."""
        pattern = VelocityPattern(
            entity_id="entity1",
            connection_count=50,
            time_window_days=5,
            connection_rate=10.0,
        )
        
        risk_score = pattern.get_risk_score()
        assert risk_score >= 80  # High risk: 10 connections/day
    
    def test_risk_score_moderate_velocity(self) -> None:
        """Test risk score for moderate velocity."""
        pattern = VelocityPattern(
            entity_id="entity1",
            connection_count=15,
            time_window_days=30,
            connection_rate=0.5,
        )
        
        risk_score = pattern.get_risk_score()
        assert 30 <= risk_score < 60  # Moderate risk
    
    def test_risk_levels(self) -> None:
        """Test risk level classification."""
        # Critical
        pattern_critical = VelocityPattern(
            entity_id="entity1",
            connection_count=100,
            time_window_days=7,
            connection_rate=14.3,
        )
        assert pattern_critical.get_risk_level() == "critical"


class TestPatternAnalysisResult:
    """Test PatternAnalysisResult dataclass."""
    
    def test_result_creation(self) -> None:
        """Test creating analysis result."""
        result = PatternAnalysisResult(
            shared_attribute_patterns=[],
            circular_patterns=[],
            layering_patterns=[],
            velocity_patterns=[],
        )
        
        assert isinstance(result.shared_attribute_patterns, list)
        assert isinstance(result.circular_patterns, list)
    
    def test_get_high_risk_patterns(self) -> None:
        """Test filtering high-risk patterns."""
        shared = SharedAttributePattern(
            attribute_type="ssn",
            attribute_value="123-45-6789",
            entities={f"id{i}" for i in range(10)},
            entity_count=10,
        )
        
        circular = CircularPattern(
            cycle=["A", "B", "C", "A"],
            length=3,
            total_value=150000.0,
        )
        
        result = PatternAnalysisResult(
            shared_attribute_patterns=[shared],
            circular_patterns=[circular],
            layering_patterns=[],
            velocity_patterns=[],
        )
        
        high_risk = result.get_high_risk_patterns(min_risk=60.0)
        assert len(high_risk["shared_attributes"]) >= 1
        assert len(high_risk["circular"]) >= 1
    
    def test_get_pattern_summary(self) -> None:
        """Test pattern summary generation."""
        result = PatternAnalysisResult(
            shared_attribute_patterns=[
                SharedAttributePattern("ssn", "123", {"a", "b"}, 2),
                SharedAttributePattern("phone", "555", {"c", "d"}, 2),
            ],
            circular_patterns=[
                CircularPattern(["A", "B", "A"], 2),
            ],
            layering_patterns=[],
            velocity_patterns=[],
        )
        
        summary = result.get_pattern_summary()
        assert summary["shared_attribute_patterns"] == 2
        assert summary["circular_patterns"] == 1
        assert summary["total_patterns"] == 3


class TestPatternAnalyzer:
    """Test PatternAnalyzer class."""
    
    def test_analyzer_creation(self) -> None:
        """Test creating pattern analyzer."""
        analyzer = PatternAnalyzer()
        assert analyzer is not None
    
    def test_detect_shared_attributes_ssn(self) -> None:
        """Test detecting shared SSN patterns."""
        identities = [
            {"id": "id1", "ssn": "123-45-6789", "name": "John Doe"},
            {"id": "id2", "ssn": "123-45-6789", "name": "Jane Smith"},
            {"id": "id3", "ssn": "987-65-4321", "name": "Bob Johnson"},
        ]
        
        analyzer = PatternAnalyzer()
        patterns = analyzer.detect_shared_attributes(identities, ["ssn"])
        
        assert len(patterns) == 1
        assert patterns[0].attribute_type == "ssn"
        assert patterns[0].entity_count == 2
    
    def test_detect_shared_attributes_multiple_types(self) -> None:
        """Test detecting multiple shared attribute types."""
        identities = [
            {"id": "id1", "ssn": "123-45-6789", "phone": "555-1234"},
            {"id": "id2", "ssn": "123-45-6789", "phone": "555-5678"},
            {"id": "id3", "ssn": "987-65-4321", "phone": "555-1234"},
        ]
        
        analyzer = PatternAnalyzer()
        patterns = analyzer.detect_shared_attributes(identities, ["ssn", "phone"])
        
        assert len(patterns) == 2  # One SSN, one phone
        types = {p.attribute_type for p in patterns}
        assert "ssn" in types
        assert "phone" in types
    
    def test_detect_shared_attributes_no_sharing(self) -> None:
        """Test when no attributes are shared."""
        identities = [
            {"id": "id1", "ssn": "111-11-1111"},
            {"id": "id2", "ssn": "222-22-2222"},
            {"id": "id3", "ssn": "333-33-3333"},
        ]
        
        analyzer = PatternAnalyzer()
        patterns = analyzer.detect_shared_attributes(identities, ["ssn"])
        
        assert len(patterns) == 0
    
    def test_detect_circular_patterns_triangle(self) -> None:
        """Test detecting triangle (3-cycle) patterns."""
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])
        
        analyzer = PatternAnalyzer()
        patterns = analyzer.detect_circular_patterns(G, max_cycle_length=6)
        
        assert len(patterns) >= 1
        assert any(p.length == 3 for p in patterns)
    
    def test_detect_circular_patterns_with_values(self) -> None:
        """Test detecting cycles with edge values."""
        G = nx.Graph()
        G.add_edge("A", "B", type="transfer", value=10000.0)
        G.add_edge("B", "C", type="transfer", value=20000.0)
        G.add_edge("C", "A", type="transfer", value=30000.0)
        
        analyzer = PatternAnalyzer()
        patterns = analyzer.detect_circular_patterns(G)
        
        assert len(patterns) >= 1
        if patterns:
            assert patterns[0].total_value == 60000.0
    
    def test_detect_circular_patterns_no_cycles(self) -> None:
        """Test when no cycles exist."""
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("C", "D")])  # Tree
        
        analyzer = PatternAnalyzer()
        patterns = analyzer.detect_circular_patterns(G)
        
        assert len(patterns) == 0
    
    def test_detect_layering_patterns_simple(self) -> None:
        """Test detecting simple layering pattern."""
        G = nx.DiGraph()
        G.add_edges_from([
            ("root", "L1_A"),
            ("root", "L1_B"),
            ("L1_A", "L2_A"),
            ("L1_B", "L2_B"),
            ("L2_A", "L3_A"),
        ])
        
        analyzer = PatternAnalyzer()
        patterns = analyzer.detect_layering_patterns(G, min_depth=3)
        
        assert len(patterns) >= 1
        assert patterns[0].depth >= 3
        assert patterns[0].root_entity == "root"
    
    def test_detect_layering_patterns_multiple_roots(self) -> None:
        """Test detecting patterns with multiple root nodes."""
        G = nx.DiGraph()
        # Root 1
        G.add_edges_from([
            ("root1", "L1_A"),
            ("L1_A", "L2_A"),
            ("L2_A", "L3_A"),
        ])
        # Root 2
        G.add_edges_from([
            ("root2", "L1_B"),
            ("L1_B", "L2_B"),
            ("L2_B", "L3_B"),
        ])
        
        analyzer = PatternAnalyzer()
        patterns = analyzer.detect_layering_patterns(G, min_depth=3)
        
        assert len(patterns) == 2
        roots = {p.root_entity for p in patterns}
        assert "root1" in roots
        assert "root2" in roots
    
    def test_detect_layering_patterns_shallow(self) -> None:
        """Test that shallow structures are not flagged."""
        G = nx.DiGraph()
        G.add_edges_from([("root", "L1_A"), ("L1_A", "L2_A")])
        
        analyzer = PatternAnalyzer()
        patterns = analyzer.detect_layering_patterns(G, min_depth=3)
        
        assert len(patterns) == 0
    
    def test_detect_velocity_patterns_rapid(self) -> None:
        """Test detecting rapid connection formation."""
        G = nx.Graph()
        now = datetime.now()
        
        # Add rapid connections
        for i in range(10):
            G.add_edge(
                "entity1",
                f"target{i}",
                timestamp=now + timedelta(days=i),
                type="transfer",
            )
        
        analyzer = PatternAnalyzer()
        patterns = analyzer.detect_velocity_patterns(
            G, time_window_days=30, min_connections=5
        )
        
        assert len(patterns) >= 1
        assert patterns[0].entity_id == "entity1"
        assert patterns[0].connection_count >= 5
    
    def test_detect_velocity_patterns_slow(self) -> None:
        """Test that slow connections are not flagged."""
        G = nx.Graph()
        now = datetime.now()
        
        # Add slow connections
        for i in range(3):
            G.add_edge(
                "entity1",
                f"target{i}",
                timestamp=now + timedelta(days=i * 30),
                type="transfer",
            )
        
        analyzer = PatternAnalyzer()
        patterns = analyzer.detect_velocity_patterns(
            G, time_window_days=30, min_connections=5
        )
        
        assert len(patterns) == 0
    
    def test_detect_velocity_patterns_no_timestamps(self) -> None:
        """Test when edges have no timestamps."""
        G = nx.Graph()
        G.add_edges_from([("entity1", f"target{i}") for i in range(10)])
        
        analyzer = PatternAnalyzer()
        patterns = analyzer.detect_velocity_patterns(G)
        
        assert len(patterns) == 0
    
    def test_analyze_patterns_comprehensive(self) -> None:
        """Test comprehensive pattern analysis."""
        # Create graph with multiple pattern types
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])  # Triangle
        
        identities = [
            {"id": "A", "ssn": "123-45-6789"},
            {"id": "B", "ssn": "123-45-6789"},
            {"id": "C", "ssn": "987-65-4321"},
        ]
        
        analyzer = PatternAnalyzer()
        result = analyzer.analyze_patterns(G, identities)
        
        assert isinstance(result, PatternAnalysisResult)
        assert len(result.shared_attribute_patterns) >= 1
        assert len(result.circular_patterns) >= 1
    
    def test_analyze_patterns_selective(self) -> None:
        """Test selective pattern detection."""
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        
        analyzer = PatternAnalyzer()
        result = analyzer.analyze_patterns(
            G,
            detect_shared=False,
            detect_circular=True,
            detect_layering=False,
            detect_velocity=False,
        )
        
        assert len(result.shared_attribute_patterns) == 0
        assert len(result.layering_patterns) == 0
        assert len(result.velocity_patterns) == 0


class TestDeterminism:
    """Test deterministic behavior."""
    
    def test_shared_attribute_detection_deterministic(self) -> None:
        """Test that shared attribute detection is deterministic."""
        identities = [
            {"id": f"id{i}", "ssn": "123-45-6789"} for i in range(5)
        ]
        
        analyzer = PatternAnalyzer()
        
        patterns1 = analyzer.detect_shared_attributes(identities)
        patterns2 = analyzer.detect_shared_attributes(identities)
        
        assert len(patterns1) == len(patterns2)
        assert patterns1[0].entity_count == patterns2[0].entity_count
    
    def test_circular_detection_deterministic(self) -> None:
        """Test that circular detection is deterministic."""
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])
        
        analyzer = PatternAnalyzer()
        
        patterns1 = analyzer.detect_circular_patterns(G)
        patterns2 = analyzer.detect_circular_patterns(G)
        
        assert len(patterns1) == len(patterns2)


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_identities(self) -> None:
        """Test with empty identity list."""
        analyzer = PatternAnalyzer()
        patterns = analyzer.detect_shared_attributes([])
        assert len(patterns) == 0
    
    def test_empty_graph(self) -> None:
        """Test with empty graph."""
        G = nx.Graph()
        analyzer = PatternAnalyzer()
        
        circular = analyzer.detect_circular_patterns(G)
        assert len(circular) == 0
    
    def test_single_node_graph(self) -> None:
        """Test with single node graph."""
        G = nx.Graph()
        G.add_node("A")
        
        analyzer = PatternAnalyzer()
        patterns = analyzer.detect_circular_patterns(G)
        
        assert len(patterns) == 0
    
    def test_missing_attributes(self) -> None:
        """Test with identities missing attributes."""
        identities = [
            {"id": "id1", "ssn": "123-45-6789"},
            {"id": "id2"},  # Missing SSN
            {"id": "id3", "ssn": "123-45-6789"},
        ]
        
        analyzer = PatternAnalyzer()
        patterns = analyzer.detect_shared_attributes(identities, ["ssn"])
        
        assert len(patterns) == 1
        assert patterns[0].entity_count == 2


# Made with Bob