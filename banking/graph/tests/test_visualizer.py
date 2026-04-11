"""
Unit Tests for Graph Visualizer
================================

Tests for interactive network visualization including layouts,
styling, and export functionality.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.4 - Graph-Based Fraud Detection
"""

import pytest
import networkx as nx
from pathlib import Path
from typing import Dict, List, Set
import tempfile

from banking.graph.visualizer import (
    GraphVisualizer,
    VisualizationConfig,
    NodeStyle,
    EdgeStyle,
)


class TestVisualizationConfig:
    """Test VisualizationConfig dataclass."""
    
    def test_config_creation_defaults(self) -> None:
        """Test creating config with defaults."""
        config = VisualizationConfig()
        
        assert config.layout == "spring"
        assert config.node_size_range == (10, 50)
        assert config.show_labels is True
        assert config.width == 1200
        assert config.height == 800
    
    def test_config_custom_values(self) -> None:
        """Test creating config with custom values."""
        config = VisualizationConfig(
            layout="circular",
            node_size_range=(20, 60),
            width=1600,
            height=1000,
        )
        
        assert config.layout == "circular"
        assert config.node_size_range == (20, 60)
        assert config.width == 1600
        assert config.height == 1000
    
    def test_config_risk_colors_default(self) -> None:
        """Test default risk color scheme."""
        config = VisualizationConfig()
        
        assert "critical" in config.risk_colors
        assert "high" in config.risk_colors
        assert "medium" in config.risk_colors
        assert "low" in config.risk_colors
        assert config.risk_colors["critical"] == "#d32f2f"
    
    def test_config_custom_risk_colors(self) -> None:
        """Test custom risk color scheme."""
        custom_colors = {
            "critical": "#ff0000",
            "high": "#ff8800",
            "medium": "#ffff00",
            "low": "#00ff00",
            "unknown": "#888888",
        }
        config = VisualizationConfig(risk_colors=custom_colors)
        
        assert config.risk_colors == custom_colors


class TestNodeStyle:
    """Test NodeStyle dataclass."""
    
    def test_node_style_creation(self) -> None:
        """Test creating node style."""
        style = NodeStyle(
            node_id="node1",
            color="#ff0000",
            size=30.0,
            label="Node 1",
            hover_text="Risk: 85",
        )
        
        assert style.node_id == "node1"
        assert style.color == "#ff0000"
        assert style.size == 30.0
        assert style.shape == "circle"
    
    def test_node_style_custom_shape(self) -> None:
        """Test node style with custom shape."""
        style = NodeStyle(
            node_id="node1",
            color="#ff0000",
            size=30.0,
            label="Node 1",
            hover_text="Risk: 85",
            shape="diamond",
        )
        
        assert style.shape == "diamond"


class TestEdgeStyle:
    """Test EdgeStyle dataclass."""
    
    def test_edge_style_creation(self) -> None:
        """Test creating edge style."""
        style = EdgeStyle(
            source="node1",
            target="node2",
            color="#888888",
            width=2.0,
        )
        
        assert style.source == "node1"
        assert style.target == "node2"
        assert style.color == "#888888"
        assert style.width == 2.0
        assert style.style == "solid"
    
    def test_edge_style_with_label(self) -> None:
        """Test edge style with label."""
        style = EdgeStyle(
            source="node1",
            target="node2",
            color="#888888",
            width=2.0,
            label="transfer",
            hover_text="$50,000",
        )
        
        assert style.label == "transfer"
        assert style.hover_text == "$50,000"


class TestGraphVisualizer:
    """Test GraphVisualizer class."""
    
    def test_visualizer_creation_default(self) -> None:
        """Test creating visualizer with defaults."""
        visualizer = GraphVisualizer()
        
        assert visualizer.config is not None
        assert visualizer.config.layout == "spring"
    
    def test_visualizer_creation_custom_config(self) -> None:
        """Test creating visualizer with custom config."""
        config = VisualizationConfig(layout="circular", width=1600)
        visualizer = GraphVisualizer(config)
        
        assert visualizer.config.layout == "circular"
        assert visualizer.config.width == 1600
    
    def test_compute_layout_spring(self) -> None:
        """Test spring layout computation."""
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])
        
        visualizer = GraphVisualizer()
        pos = visualizer.compute_layout(G, layout="spring")
        
        assert len(pos) == 3
        assert "A" in pos
        assert "B" in pos
        assert "C" in pos
        assert all(len(coords) == 2 for coords in pos.values())
    
    def test_compute_layout_circular(self) -> None:
        """Test circular layout computation."""
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("C", "D")])
        
        visualizer = GraphVisualizer()
        pos = visualizer.compute_layout(G, layout="circular")
        
        assert len(pos) == 4
        assert all(len(coords) == 2 for coords in pos.values())
    
    def test_compute_layout_deterministic(self) -> None:
        """Test that layout computation is deterministic."""
        import numpy as np
        
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])
        
        visualizer = GraphVisualizer()
        pos1 = visualizer.compute_layout(G, layout="spring")
        pos2 = visualizer.compute_layout(G, layout="spring")
        
        # Positions should be identical (seed=42)
        for node in G.nodes():
            np.testing.assert_array_almost_equal(pos1[node], pos2[node], decimal=10)
    
    def test_style_nodes_by_risk_critical(self) -> None:
        """Test styling nodes with critical risk."""
        G = nx.Graph()
        G.add_node("node1")
        
        risk_scores = {"node1": 85.0}
        
        visualizer = GraphVisualizer()
        styles = visualizer.style_nodes_by_risk(G, risk_scores)
        
        assert len(styles) == 1
        assert styles[0].node_id == "node1"
        assert styles[0].color == visualizer.config.risk_colors["critical"]
    
    def test_style_nodes_by_risk_levels(self) -> None:
        """Test styling nodes with different risk levels."""
        G = nx.Graph()
        G.add_nodes_from(["critical", "high", "medium", "low", "unknown"])
        
        risk_scores = {
            "critical": 85.0,
            "high": 65.0,
            "medium": 45.0,
            "low": 25.0,
            "unknown": 0.0,
        }
        
        visualizer = GraphVisualizer()
        styles = visualizer.style_nodes_by_risk(G, risk_scores)
        
        style_dict = {s.node_id: s for s in styles}
        
        assert style_dict["critical"].color == visualizer.config.risk_colors["critical"]
        assert style_dict["high"].color == visualizer.config.risk_colors["high"]
        assert style_dict["medium"].color == visualizer.config.risk_colors["medium"]
        assert style_dict["low"].color == visualizer.config.risk_colors["low"]
        assert style_dict["unknown"].color == visualizer.config.risk_colors["unknown"]
    
    def test_style_nodes_size_by_degree(self) -> None:
        """Test that node size scales with degree."""
        G = nx.Graph()
        G.add_edges_from([
            ("hub", "A"),
            ("hub", "B"),
            ("hub", "C"),
            ("A", "B"),
        ])
        
        risk_scores = {node: 50.0 for node in G.nodes()}
        
        visualizer = GraphVisualizer()
        styles = visualizer.style_nodes_by_risk(G, risk_scores)
        
        style_dict = {s.node_id: s for s in styles}
        
        # Hub should have larger size (degree=3)
        assert style_dict["hub"].size > style_dict["C"].size
    
    def test_style_nodes_by_community(self) -> None:
        """Test styling nodes by community."""
        G = nx.Graph()
        G.add_nodes_from(["A", "B", "C", "D"])
        
        communities = {"A": 0, "B": 0, "C": 1, "D": 1}
        
        visualizer = GraphVisualizer()
        styles = visualizer.style_nodes_by_community(G, communities)
        
        style_dict = {s.node_id: s for s in styles}
        
        # Nodes in same community should have same color
        assert style_dict["A"].color == style_dict["B"].color
        assert style_dict["C"].color == style_dict["D"].color
        assert style_dict["A"].color != style_dict["C"].color
    
    def test_style_edges_default(self) -> None:
        """Test default edge styling."""
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        
        visualizer = GraphVisualizer()
        styles = visualizer.style_edges(G)
        
        assert len(styles) == 2
        assert all(s.color == "#888888" for s in styles)
    
    def test_style_edges_with_weights(self) -> None:
        """Test edge styling with weights."""
        G = nx.Graph()
        G.add_edge("A", "B", weight=1.0)
        G.add_edge("B", "C", weight=5.0)
        
        edge_weights = {("A", "B"): 1.0, ("B", "C"): 5.0}
        
        visualizer = GraphVisualizer()
        styles = visualizer.style_edges(G, edge_weights)
        
        style_dict = {(s.source, s.target): s for s in styles}
        
        # Higher weight should have larger width
        bc_style = style_dict.get(("B", "C")) or style_dict.get(("C", "B"))
        ab_style = style_dict.get(("A", "B")) or style_dict.get(("B", "A"))
        
        assert bc_style.width > ab_style.width
    
    def test_highlight_fraud_rings(self) -> None:
        """Test fraud ring highlighting."""
        G = nx.Graph()
        G.add_nodes_from(["A", "B", "C", "D"])
        
        risk_scores = {node: 50.0 for node in G.nodes()}
        
        visualizer = GraphVisualizer()
        styles = visualizer.style_nodes_by_risk(G, risk_scores)
        
        fraud_rings = [{"A", "B"}]
        updated_styles = visualizer.highlight_fraud_rings(G, fraud_rings, styles)
        
        style_dict = {s.node_id: s for s in updated_styles}
        
        # Fraud ring members should have red border and diamond shape
        assert style_dict["A"].border_color == "#ff0000"
        assert style_dict["A"].shape == "diamond"
        assert style_dict["B"].border_color == "#ff0000"
        assert style_dict["B"].shape == "diamond"
        
        # Non-members should not
        assert style_dict["C"].border_color != "#ff0000"
        assert style_dict["D"].border_color != "#ff0000"
    
    def test_visualize_basic(self) -> None:
        """Test basic visualization creation."""
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])
        
        risk_scores = {"A": 80.0, "B": 60.0, "C": 40.0}
        
        visualizer = GraphVisualizer()
        
        # Test without plotly (should handle gracefully)
        try:
            fig = visualizer.visualize(G, risk_scores=risk_scores)
            # If plotly is available, fig should be created
            assert fig is not None
        except ImportError:
            # If plotly not available, should raise ImportError
            pass
    
    def test_visualize_with_communities(self) -> None:
        """Test visualization with community coloring."""
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("C", "D")])
        
        communities = {"A": 0, "B": 0, "C": 1, "D": 1}
        
        visualizer = GraphVisualizer()
        
        try:
            fig = visualizer.visualize(G, communities=communities)
            assert fig is not None
        except ImportError:
            pass
    
    def test_visualize_with_fraud_rings(self) -> None:
        """Test visualization with fraud ring highlighting."""
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])
        
        risk_scores = {node: 70.0 for node in G.nodes()}
        fraud_rings = [{"A", "B", "C"}]
        
        visualizer = GraphVisualizer()
        
        try:
            fig = visualizer.visualize(
                G,
                risk_scores=risk_scores,
                fraud_rings=fraud_rings,
            )
            assert fig is not None
        except ImportError:
            pass
    
    def test_visualize_save_to_file(self) -> None:
        """Test saving visualization to file."""
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        
        risk_scores = {node: 50.0 for node in G.nodes()}
        
        visualizer = GraphVisualizer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "test_viz.html"
            
            try:
                fig = visualizer.visualize(
                    G,
                    risk_scores=risk_scores,
                    output_file=output_file,
                )
                
                # Check if file was created
                if fig is not None:
                    assert output_file.exists()
            except ImportError:
                # Plotly not available, skip file check
                pass


class TestDeterminism:
    """Test deterministic behavior."""
    
    def test_layout_deterministic(self) -> None:
        """Test that layout is deterministic."""
        import numpy as np
        
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")])
        
        visualizer = GraphVisualizer()
        
        pos1 = visualizer.compute_layout(G, layout="spring")
        pos2 = visualizer.compute_layout(G, layout="spring")
        
        for node in G.nodes():
            np.testing.assert_array_almost_equal(pos1[node], pos2[node], decimal=10)
    
    def test_styling_deterministic(self) -> None:
        """Test that styling is deterministic."""
        G = nx.Graph()
        G.add_nodes_from(["A", "B", "C"])
        
        risk_scores = {"A": 80.0, "B": 60.0, "C": 40.0}
        
        visualizer = GraphVisualizer()
        
        styles1 = visualizer.style_nodes_by_risk(G, risk_scores)
        styles2 = visualizer.style_nodes_by_risk(G, risk_scores)
        
        for s1, s2 in zip(styles1, styles2):
            assert s1.node_id == s2.node_id
            assert s1.color == s2.color
            assert s1.size == s2.size


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_graph(self) -> None:
        """Test with empty graph."""
        G = nx.Graph()
        
        visualizer = GraphVisualizer()
        pos = visualizer.compute_layout(G)
        
        assert len(pos) == 0
    
    def test_single_node_graph(self) -> None:
        """Test with single node."""
        G = nx.Graph()
        G.add_node("A")
        
        visualizer = GraphVisualizer()
        pos = visualizer.compute_layout(G)
        
        assert len(pos) == 1
        assert "A" in pos
    
    def test_disconnected_graph(self) -> None:
        """Test with disconnected components."""
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("C", "D")])
        
        visualizer = GraphVisualizer()
        pos = visualizer.compute_layout(G)
        
        assert len(pos) == 4
    
    def test_missing_risk_scores(self) -> None:
        """Test styling with missing risk scores."""
        G = nx.Graph()
        G.add_nodes_from(["A", "B", "C"])
        
        risk_scores = {"A": 80.0}  # Missing B and C
        
        visualizer = GraphVisualizer()
        styles = visualizer.style_nodes_by_risk(G, risk_scores)
        
        assert len(styles) == 3
        # Missing scores should default to 0 (unknown)
        style_dict = {s.node_id: s for s in styles}
        assert style_dict["B"].color == visualizer.config.risk_colors["unknown"]
    
    def test_invalid_layout_fallback(self) -> None:
        """Test fallback for invalid layout."""
        G = nx.Graph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        
        visualizer = GraphVisualizer()
        pos = visualizer.compute_layout(G, layout="invalid_layout")
        
        # Should fallback to spring layout
        assert len(pos) == 3
    
    def test_empty_fraud_rings(self) -> None:
        """Test with empty fraud rings list."""
        G = nx.Graph()
        G.add_nodes_from(["A", "B"])
        
        risk_scores = {node: 50.0 for node in G.nodes()}
        
        visualizer = GraphVisualizer()
        styles = visualizer.style_nodes_by_risk(G, risk_scores)
        
        fraud_rings: List[Set[str]] = []
        updated_styles = visualizer.highlight_fraud_rings(G, fraud_rings, styles)
        
        # Should not modify styles
        assert len(updated_styles) == 2


# Made with Bob