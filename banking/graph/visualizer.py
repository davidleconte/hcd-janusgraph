"""
Graph Visualizer for Interactive Network Visualization
======================================================

Implements interactive graph visualization for fraud network analysis,
including force-directed layouts, risk-based coloring, and fraud ring
highlighting.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.4 - Graph-Based Fraud Detection

Key Features:
    - Interactive network visualization with Plotly
    - Force-directed layout algorithms
    - Node coloring by risk level
    - Edge thickness by relationship strength
    - Fraud ring highlighting
    - Export to HTML and PNG
    - Customizable styling and layouts

Business Value:
    - Visual investigation support
    - Pattern recognition
    - Presentation-ready outputs
    - Compliance documentation
"""

from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Optional, Any, Union, TYPE_CHECKING
from pathlib import Path
import networkx as nx
import logging

# Visualization libraries
if TYPE_CHECKING:
    import plotly.graph_objects as go
    from pyvis.network import Network as PyvisNetwork

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    go = None  # type: ignore
    px = None  # type: ignore
    logging.warning("plotly not available, visualization features limited")

try:
    from pyvis.network import Network as PyvisNetwork
    PYVIS_AVAILABLE = True
except ImportError:
    PYVIS_AVAILABLE = False
    PyvisNetwork = None  # type: ignore
    logging.warning("pyvis not available, some visualization features unavailable")

logger = logging.getLogger(__name__)


@dataclass
class VisualizationConfig:
    """Configuration for graph visualization."""
    
    # Layout settings
    layout: str = "spring"  # spring, circular, kamada_kawai, spectral
    node_size_range: Tuple[int, int] = (10, 50)
    edge_width_range: Tuple[float, float] = (0.5, 5.0)
    
    # Color settings
    color_scheme: str = "risk"  # risk, community, centrality, custom
    risk_colors: Optional[Dict[str, str]] = None
    
    # Display settings
    show_labels: bool = True
    show_edge_labels: bool = False
    width: int = 1200
    height: int = 800
    
    # Interactive settings
    enable_hover: bool = True
    enable_zoom: bool = True
    enable_drag: bool = True
    
    def __post_init__(self) -> None:
        """Initialize default color schemes."""
        if self.risk_colors is None:
            self.risk_colors = {
                "critical": "#d32f2f",  # Red
                "high": "#f57c00",      # Orange
                "medium": "#fbc02d",    # Yellow
                "low": "#388e3c",       # Green
                "unknown": "#757575",   # Gray
            }


@dataclass
class NodeStyle:
    """Styling for a graph node."""
    
    node_id: str
    color: str
    size: float
    label: str
    hover_text: str
    shape: str = "circle"  # circle, square, triangle, diamond
    border_color: str = "#000000"
    border_width: float = 1.0


@dataclass
class EdgeStyle:
    """Styling for a graph edge."""
    
    source: str
    target: str
    color: str
    width: float
    label: str = ""
    hover_text: str = ""
    style: str = "solid"  # solid, dashed, dotted


class GraphVisualizer:
    """
    Visualizes fraud networks with interactive features.
    
    Supports multiple layout algorithms, risk-based coloring,
    and export to various formats.
    """
    
    def __init__(self, config: Optional[VisualizationConfig] = None) -> None:
        """
        Initialize the graph visualizer.
        
        Args:
            config: Visualization configuration
        """
        self.config = config or VisualizationConfig()
        self.logger = logging.getLogger(__name__)
        
        if not PLOTLY_AVAILABLE:
            self.logger.warning("Plotly not available, some features will be limited")
    
    def compute_layout(
        self,
        graph: nx.Graph,
        layout: Optional[str] = None,
    ) -> Dict[str, Tuple[float, float]]:
        """
        Compute node positions using specified layout algorithm.
        
        Args:
            graph: NetworkX graph
            layout: Layout algorithm (spring, circular, kamada_kawai, spectral)
            
        Returns:
            Dictionary mapping node IDs to (x, y) positions
        """
        layout = layout or self.config.layout
        
        try:
            if layout == "spring":
                pos = nx.spring_layout(graph, seed=42)
            elif layout == "circular":
                pos = nx.circular_layout(graph)
            elif layout == "kamada_kawai":
                pos = nx.kamada_kawai_layout(graph)
            elif layout == "spectral":
                pos = nx.spectral_layout(graph)
            else:
                self.logger.warning(f"Unknown layout '{layout}', using spring")
                pos = nx.spring_layout(graph, seed=42)
        except Exception as e:
            self.logger.error(f"Layout computation failed: {e}, using spring")
            pos = nx.spring_layout(graph, seed=42)
        
        return pos
    
    def style_nodes_by_risk(
        self,
        graph: nx.Graph,
        risk_scores: Dict[str, float],
    ) -> List[NodeStyle]:
        """
        Style nodes based on risk scores.
        
        Args:
            graph: NetworkX graph
            risk_scores: Dictionary mapping node IDs to risk scores (0-100)
            
        Returns:
            List of node styles
        """
        styles = []
        
        for node in graph.nodes():
            risk_score = risk_scores.get(node, 0.0)
            
            # Determine risk level
            if risk_score >= 80:
                risk_level = "critical"
            elif risk_score >= 60:
                risk_level = "high"
            elif risk_score >= 40:
                risk_level = "medium"
            elif risk_score > 0:
                risk_level = "low"
            else:
                risk_level = "unknown"
            
            # Get node attributes
            node_data = graph.nodes[node]
            label = node_data.get("label", str(node))
            
            # Compute size based on degree
            degree = graph.degree(node)
            min_size, max_size = self.config.node_size_range
            degrees = dict(graph.degree()).values()
            max_degree = max(degrees) if degrees and max(degrees) > 0 else 1
            size = min_size + (max_size - min_size) * (degree / max_degree)
            
            # Create hover text
            hover_text = f"Node: {node}<br>"
            hover_text += f"Risk Score: {risk_score:.1f}<br>"
            hover_text += f"Risk Level: {risk_level.upper()}<br>"
            hover_text += f"Degree: {degree}"
            
            style = NodeStyle(
                node_id=node,
                color=self.config.risk_colors[risk_level],
                size=size,
                label=label if self.config.show_labels else "",
                hover_text=hover_text,
            )
            styles.append(style)
        
        return styles
    
    def style_nodes_by_community(
        self,
        graph: nx.Graph,
        communities: Dict[str, int],
    ) -> List[NodeStyle]:
        """
        Style nodes based on community membership.
        
        Args:
            graph: NetworkX graph
            communities: Dictionary mapping node IDs to community IDs
            
        Returns:
            List of node styles
        """
        # Generate colors for communities
        unique_communities = set(communities.values())
        
        # Use plotly colors if available, otherwise use default palette
        if PLOTLY_AVAILABLE and px is not None:
            color_palette = px.colors.qualitative.Set3
        else:
            # Fallback color palette
            color_palette = [
                "#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3",
                "#fdb462", "#b3de69", "#fccde5", "#d9d9d9", "#bc80bd",
            ]
        
        community_colors = {
            comm: color_palette[i % len(color_palette)]
            for i, comm in enumerate(sorted(unique_communities))
        }
        
        styles = []
        
        for node in graph.nodes():
            community_id = communities.get(node, -1)
            color = community_colors.get(community_id, "#757575")
            
            # Get node attributes
            node_data = graph.nodes[node]
            label = node_data.get("label", str(node))
            
            # Compute size based on degree
            degree = graph.degree(node)
            min_size, max_size = self.config.node_size_range
            degrees = dict(graph.degree()).values()
            max_degree = max(degrees) if degrees and max(degrees) > 0 else 1
            size = min_size + (max_size - min_size) * (degree / max_degree)
            
            # Create hover text
            hover_text = f"Node: {node}<br>"
            hover_text += f"Community: {community_id}<br>"
            hover_text += f"Degree: {degree}"
            
            style = NodeStyle(
                node_id=node,
                color=color,
                size=size,
                label=label if self.config.show_labels else "",
                hover_text=hover_text,
            )
            styles.append(style)
        
        return styles
    
    def style_edges(
        self,
        graph: nx.Graph,
        edge_weights: Optional[Dict[Tuple[str, str], float]] = None,
    ) -> List[EdgeStyle]:
        """
        Style edges based on weights or attributes.
        
        Args:
            graph: NetworkX graph
            edge_weights: Optional dictionary of edge weights
            
        Returns:
            List of edge styles
        """
        styles = []
        
        # Get edge weight range for normalization
        if edge_weights:
            weights = list(edge_weights.values())
            min_weight = min(weights) if weights else 0
            max_weight = max(weights) if weights else 1
        else:
            min_weight, max_weight = 0, 1
        
        min_width, max_width = self.config.edge_width_range
        
        for u, v in graph.edges():
            edge_data = graph[u][v]
            
            # Get edge weight
            if edge_weights and (u, v) in edge_weights:
                weight = edge_weights[(u, v)]
            else:
                weight = edge_data.get("weight", 1.0)
            
            # Normalize width
            if max_weight > min_weight:
                normalized = (weight - min_weight) / (max_weight - min_weight)
                width = min_width + (max_width - min_width) * normalized
            else:
                width = min_width
            
            # Get edge type for styling
            edge_type = edge_data.get("type", "unknown")
            
            # Create hover text
            hover_text = f"Edge: {u} → {v}<br>"
            hover_text += f"Type: {edge_type}<br>"
            hover_text += f"Weight: {weight:.2f}"
            
            style = EdgeStyle(
                source=u,
                target=v,
                color="#888888",
                width=width,
                hover_text=hover_text,
            )
            styles.append(style)
        
        return styles
    
    def highlight_fraud_rings(
        self,
        graph: nx.Graph,
        fraud_rings: List[Set[str]],
        node_styles: List[NodeStyle],
    ) -> List[NodeStyle]:
        """
        Highlight nodes that are part of fraud rings.
        
        Args:
            graph: NetworkX graph
            fraud_rings: List of fraud ring node sets
            node_styles: Existing node styles to modify
            
        Returns:
            Updated node styles with fraud ring highlighting
        """
        # Create set of all fraud ring nodes
        fraud_nodes = set()
        for ring in fraud_rings:
            fraud_nodes.update(ring)
        
        # Update styles for fraud ring nodes
        for style in node_styles:
            if style.node_id in fraud_nodes:
                style.border_color = "#ff0000"  # Red border
                style.border_width = 3.0
                style.shape = "diamond"
                style.hover_text += "<br><b>⚠️ FRAUD RING MEMBER</b>"
        
        return node_styles
    
    def create_plotly_figure(
        self,
        graph: nx.Graph,
        node_styles: List[NodeStyle],
        edge_styles: List[EdgeStyle],
        pos: Dict[str, Tuple[float, float]],
        title: str = "Fraud Network Visualization",
    ) -> Any:
        """
        Create interactive Plotly figure.
        
        Args:
            graph: NetworkX graph
            node_styles: Node styling information
            edge_styles: Edge styling information
            pos: Node positions
            title: Figure title
            
        Returns:
            Plotly figure object
        """
        if not PLOTLY_AVAILABLE:
            raise ImportError("plotly is required for interactive visualization")
        
        # Create edge traces
        edge_traces = []
        for style in edge_styles:
            x0, y0 = pos[style.source]
            x1, y1 = pos[style.target]
            
            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode="lines",
                line=dict(width=style.width, color=style.color),
                hoverinfo="text",
                text=style.hover_text if self.config.enable_hover else None,
                showlegend=False,
            )
            edge_traces.append(edge_trace)
        
        # Create node trace
        node_x = []
        node_y = []
        node_colors = []
        node_sizes = []
        node_texts = []
        node_hovers = []
        
        for style in node_styles:
            x, y = pos[style.node_id]
            node_x.append(x)
            node_y.append(y)
            node_colors.append(style.color)
            node_sizes.append(style.size)
            node_texts.append(style.label)
            node_hovers.append(style.hover_text)
        
        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text" if self.config.show_labels else "markers",
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color="#000000"),
            ),
            text=node_texts,
            textposition="top center",
            hoverinfo="text",
            hovertext=node_hovers if self.config.enable_hover else None,
            showlegend=False,
        )
        
        # Create figure
        fig = go.Figure(data=edge_traces + [node_trace])
        
        # Update layout
        fig.update_layout(
            title=title,
            showlegend=False,
            hovermode="closest",
            width=self.config.width,
            height=self.config.height,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="white",
        )
        
        return fig
    
    def visualize(
        self,
        graph: nx.Graph,
        risk_scores: Optional[Dict[str, float]] = None,
        communities: Optional[Dict[str, int]] = None,
        fraud_rings: Optional[List[Set[str]]] = None,
        title: str = "Fraud Network Visualization",
        output_file: Optional[Path] = None,
    ) -> Any:
        """
        Create comprehensive network visualization.
        
        Args:
            graph: NetworkX graph
            risk_scores: Optional risk scores for nodes
            communities: Optional community assignments
            fraud_rings: Optional fraud ring node sets
            title: Figure title
            output_file: Optional path to save HTML file
            
        Returns:
            Plotly figure object
        """
        # Compute layout
        pos = self.compute_layout(graph)
        
        # Style nodes
        if risk_scores:
            node_styles = self.style_nodes_by_risk(graph, risk_scores)
        elif communities:
            node_styles = self.style_nodes_by_community(graph, communities)
        else:
            # Default styling
            node_styles = self.style_nodes_by_risk(graph, {})
        
        # Highlight fraud rings if provided
        if fraud_rings:
            node_styles = self.highlight_fraud_rings(graph, fraud_rings, node_styles)
        
        # Style edges
        edge_styles = self.style_edges(graph)
        
        # Create figure
        fig = self.create_plotly_figure(graph, node_styles, edge_styles, pos, title)
        
        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            fig.write_html(str(output_path))
            self.logger.info(f"Visualization saved to {output_path}")
        
        return fig
    
    def create_pyvis_network(
        self,
        graph: nx.Graph,
        risk_scores: Optional[Dict[str, float]] = None,
        output_file: Optional[Path] = None,
    ) -> Optional[Any]:
        """
        Create interactive PyVis network visualization.
        
        Args:
            graph: NetworkX graph
            risk_scores: Optional risk scores for nodes
            output_file: Path to save HTML file
            
        Returns:
            PyVis Network object or None if PyVis unavailable
        """
        if not PYVIS_AVAILABLE:
            self.logger.warning("PyVis not available, skipping PyVis visualization")
            return None
        
        # Create PyVis network
        net = PyvisNetwork(
            height=f"{self.config.height}px",
            width=f"{self.config.width}px",
            notebook=False,
        )
        
        # Add nodes
        for node in graph.nodes():
            risk_score = risk_scores.get(node, 0.0) if risk_scores else 0.0
            
            # Determine color
            if risk_score >= 80:
                color = self.config.risk_colors["critical"]
            elif risk_score >= 60:
                color = self.config.risk_colors["high"]
            elif risk_score >= 40:
                color = self.config.risk_colors["medium"]
            elif risk_score > 0:
                color = self.config.risk_colors["low"]
            else:
                color = self.config.risk_colors["unknown"]
            
            # Add node
            net.add_node(
                node,
                label=str(node),
                color=color,
                title=f"Risk: {risk_score:.1f}",
            )
        
        # Add edges
        for u, v in graph.edges():
            net.add_edge(u, v)
        
        # Configure physics
        net.set_options("""
        {
          "physics": {
            "enabled": true,
            "barnesHut": {
              "gravitationalConstant": -8000,
              "springLength": 250,
              "springConstant": 0.001
            }
          }
        }
        """)
        
        # Save to file
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            net.save_graph(str(output_path))
            self.logger.info(f"PyVis visualization saved to {output_path}")
        
        return net


# Made with Bob