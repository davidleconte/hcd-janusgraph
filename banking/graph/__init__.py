"""
Graph-Based Fraud Detection Module
==================================

This module provides graph analysis capabilities for detecting fraud networks,
fraud rings, and complex relationship patterns in banking data.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.4 - Graph-Based Fraud Detection

Modules:
    network_analyzer: Network analysis algorithms (centrality, PageRank, etc.)
    community_detector: Community detection for fraud rings
    pattern_analyzer: Relationship pattern analysis (shared attributes, cycles, layering)
    visualizer: Interactive graph visualization (Plotly/PyVis)

Example:
    >>> from banking.graph import NetworkAnalyzer, CommunityDetector, PatternAnalyzer, GraphVisualizer
    >>> analyzer = NetworkAnalyzer()
    >>> network = analyzer.build_network(identities)
    >>> metrics = analyzer.calculate_centrality(network)
    >>> detector = CommunityDetector()
    >>> result = detector.detect_communities(network)
    >>> pattern_analyzer = PatternAnalyzer()
    >>> patterns = pattern_analyzer.analyze_patterns(network, identities)
    >>> visualizer = GraphVisualizer()
    >>> fig = visualizer.visualize(network, risk_scores=risk_scores)
"""

from banking.graph.network_analyzer import (
    NetworkAnalyzer,
    NetworkMetrics,
    CentralityMetrics,
)
from banking.graph.community_detector import (
    CommunityDetector,
    Community,
    CommunityDetectionResult,
)
from banking.graph.pattern_analyzer import (
    PatternAnalyzer,
    SharedAttributePattern,
    CircularPattern,
    LayeringPattern,
    VelocityPattern,
    PatternAnalysisResult,
)
from banking.graph.visualizer import (
    GraphVisualizer,
    VisualizationConfig,
    NodeStyle,
    EdgeStyle,
)

__all__ = [
    "NetworkAnalyzer",
    "NetworkMetrics",
    "CentralityMetrics",
    "CommunityDetector",
    "Community",
    "CommunityDetectionResult",
    "PatternAnalyzer",
    "SharedAttributePattern",
    "CircularPattern",
    "LayeringPattern",
    "VelocityPattern",
    "PatternAnalysisResult",
    "GraphVisualizer",
    "VisualizationConfig",
    "NodeStyle",
    "EdgeStyle",
]

__version__ = "1.0.0"

# Made with Bob
