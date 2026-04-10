"""
Crypto Network Graph Visualizations
====================================

This module provides network graph visualizations for crypto AML analysis:
- Mixer interaction networks
- Transaction flow graphs
- Wallet relationship graphs

IMPORTANT ARCHITECTURE NOTE:
----------------------------
NetworkX is used ONLY for visualization (temporary in-memory graphs for rendering).
JanusGraph remains the authoritative source of truth for all graph data.

Workflow:
1. Data is stored permanently in HCD-JanusGraph
2. Gremlin queries extract data from JanusGraph
3. NetworkX creates temporary in-memory graphs for visualization layout calculation
4. Plotly generates interactive HTML/JavaScript visualizations
5. NetworkX graphs are discarded after visualization

NetworkX is analogous to matplotlib/seaborn - it's a visualization tool, NOT a database.

Author: AI Assistant
Date: 2026-04-10
Phase: 7.3 - Crypto Visualizations
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx
import plotly.graph_objects as go

logger = logging.getLogger(__name__)


@dataclass
class MixerNetworkGraph:
    """
    Mixer interaction network graph.
    
    Shows relationships between wallets and mixers, highlighting
    suspicious patterns and high-risk connections.
    """
    
    graph: nx.DiGraph
    layout: Dict[str, Tuple[float, float]]
    mixer_nodes: List[str]
    suspicious_edges: List[Tuple[str, str]]
    
    def to_plotly(self) -> go.Figure:
        """Convert to Plotly figure for interactive visualization."""
        # Create edge traces
        edge_traces = []
        
        # Regular edges
        regular_edges = [e for e in self.graph.edges() if e not in self.suspicious_edges]
        if regular_edges:
            edge_x, edge_y = [], []
            for edge in regular_edges:
                x0, y0 = self.layout[edge[0]]
                x1, y1 = self.layout[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
            
            edge_traces.append(go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=1, color='#888'),
                hoverinfo='none',
                mode='lines',
                name='Regular Transaction'
            ))
        
        # Suspicious edges (highlighted)
        if self.suspicious_edges:
            sus_edge_x, sus_edge_y = [], []
            for edge in self.suspicious_edges:
                x0, y0 = self.layout[edge[0]]
                x1, y1 = self.layout[edge[1]]
                sus_edge_x.extend([x0, x1, None])
                sus_edge_y.extend([y0, y1, None])
            
            edge_traces.append(go.Scatter(
                x=sus_edge_x, y=sus_edge_y,
                line=dict(width=2, color='red'),
                hoverinfo='none',
                mode='lines',
                name='Suspicious Transaction'
            ))
        
        # Create node traces
        node_traces = []
        
        # Mixer nodes (highlighted)
        mixer_x, mixer_y, mixer_text = [], [], []
        for node in self.mixer_nodes:
            x, y = self.layout[node]
            mixer_x.append(x)
            mixer_y.append(y)
            mixer_text.append(f"Mixer: {node}")
        
        if mixer_x:
            node_traces.append(go.Scatter(
                x=mixer_x, y=mixer_y,
                mode='markers+text',
                hoverinfo='text',
                text=mixer_text,
                marker=dict(
                    size=20,
                    color='red',
                    symbol='diamond',
                    line=dict(width=2, color='darkred')
                ),
                name='Mixer Wallet'
            ))
        
        # Regular nodes
        regular_nodes = [n for n in self.graph.nodes() if n not in self.mixer_nodes]
        if regular_nodes:
            node_x, node_y, node_text = [], [], []
            for node in regular_nodes:
                x, y = self.layout[node]
                node_x.append(x)
                node_y.append(y)
                node_text.append(f"Wallet: {node}")
            
            node_traces.append(go.Scatter(
                x=node_x, y=node_y,
                mode='markers',
                hoverinfo='text',
                text=node_text,
                marker=dict(
                    size=10,
                    color='lightblue',
                    line=dict(width=1, color='blue')
                ),
                name='Regular Wallet'
            ))
        
        # Create figure
        fig = go.Figure(
            data=edge_traces + node_traces,
            layout=go.Layout(
                title='Mixer Interaction Network',
                showlegend=True,
                hovermode='closest',
                margin=dict(b=0, l=0, r=0, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor='white'
            )
        )
        
        return fig


@dataclass
class TransactionFlowGraph:
    """
    Transaction flow graph showing money movement.
    
    Visualizes the flow of funds between wallets, highlighting
    large transactions and suspicious patterns.
    """
    
    graph: nx.DiGraph
    layout: Dict[str, Tuple[float, float]]
    large_transactions: List[Tuple[str, str, float]]
    
    def to_plotly(self) -> go.Figure:
        """Convert to Plotly figure for interactive visualization."""
        # Create edge traces with varying widths based on amount
        edge_traces = []
        
        for edge in self.graph.edges(data=True):
            source, target, data = edge
            amount = data.get('amount', 0)
            
            x0, y0 = self.layout[source]
            x1, y1 = self.layout[target]
            
            # Determine if large transaction
            is_large = any(
                s == source and t == target 
                for s, t, _ in self.large_transactions
            )
            
            edge_traces.append(go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                line=dict(
                    width=3 if is_large else 1,
                    color='red' if is_large else '#888'
                ),
                hoverinfo='text',
                text=f"{source} → {target}<br>Amount: {amount:.2f}",
                mode='lines',
                showlegend=False
            ))
        
        # Create node trace
        node_x, node_y, node_text = [], [], []
        for node in self.graph.nodes():
            x, y = self.layout[node]
            node_x.append(x)
            node_y.append(y)
            
            # Calculate total in/out
            total_in = sum(
                data.get('amount', 0) 
                for _, _, data in self.graph.in_edges(node, data=True)
            )
            total_out = sum(
                data.get('amount', 0) 
                for _, _, data in self.graph.out_edges(node, data=True)
            )
            
            node_text.append(
                f"Wallet: {node}<br>"
                f"Total In: {total_in:.2f}<br>"
                f"Total Out: {total_out:.2f}"
            )
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            hoverinfo='text',
            text=node_text,
            marker=dict(
                size=15,
                color='lightgreen',
                line=dict(width=1, color='green')
            ),
            name='Wallet'
        )
        
        # Create figure
        fig = go.Figure(
            data=edge_traces + [node_trace],
            layout=go.Layout(
                title='Transaction Flow Network',
                showlegend=True,
                hovermode='closest',
                margin=dict(b=0, l=0, r=0, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor='white'
            )
        )
        
        return fig


@dataclass
class WalletRelationshipGraph:
    """
    Wallet relationship graph showing connections.
    
    Visualizes relationships between wallets based on transaction
    patterns, shared addresses, and risk indicators.
    """
    
    graph: nx.Graph
    layout: Dict[str, Tuple[float, float]]
    risk_scores: Dict[str, float]
    
    def to_plotly(self) -> go.Figure:
        """Convert to Plotly figure for interactive visualization."""
        # Create edge trace
        edge_x, edge_y = [], []
        for edge in self.graph.edges():
            x0, y0 = self.layout[edge[0]]
            x1, y1 = self.layout[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='#888'),
            hoverinfo='none',
            mode='lines',
            name='Connection'
        )
        
        # Create node trace with color based on risk score
        node_x, node_y, node_text, node_color = [], [], [], []
        for node in self.graph.nodes():
            x, y = self.layout[node]
            node_x.append(x)
            node_y.append(y)
            
            risk_score = self.risk_scores.get(node, 0.0)
            node_color.append(risk_score)
            
            node_text.append(
                f"Wallet: {node}<br>"
                f"Risk Score: {risk_score:.2f}<br>"
                f"Connections: {self.graph.degree(node)}"
            )
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            hoverinfo='text',
            text=node_text,
            marker=dict(
                size=15,
                color=node_color,
                colorscale='YlOrRd',
                showscale=True,
                colorbar=dict(
                    title="Risk Score",
                    thickness=15,
                    len=0.7
                ),
                line=dict(width=1, color='black')
            ),
            name='Wallet'
        )
        
        # Create figure
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title='Wallet Relationship Network',
                showlegend=True,
                hovermode='closest',
                margin=dict(b=0, l=0, r=0, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor='white'
            )
        )
        
        return fig


def create_mixer_network(
    wallets: List[Dict[str, Any]],
    transactions: List[Dict[str, Any]],
    mixer_results: List[Any]
) -> MixerNetworkGraph:
    """
    Create mixer interaction network graph.
    
    Args:
        wallets: List of wallet dictionaries
        transactions: List of transaction dictionaries
        mixer_results: List of mixer detection results
        
    Returns:
        MixerNetworkGraph instance
    """
    # Create directed graph
    G = nx.DiGraph()
    
    # Add nodes
    for wallet in wallets:
        G.add_node(wallet['wallet_id'])
    
    # Add edges from transactions
    suspicious_edges = []
    for tx in transactions:
        source = tx.get('from_wallet')
        target = tx.get('to_wallet')
        if source and target:
            G.add_edge(source, target, amount=tx.get('amount', 0))
            if tx.get('is_suspicious', False):
                suspicious_edges.append((source, target))
    
    # Identify mixer nodes
    mixer_nodes = [
        wallet['wallet_id'] 
        for wallet in wallets 
        if wallet.get('is_mixer', False)
    ]
    
    # Create layout
    layout = nx.spring_layout(G, k=0.5, iterations=50)
    
    return MixerNetworkGraph(
        graph=G,
        layout=layout,
        mixer_nodes=mixer_nodes,
        suspicious_edges=suspicious_edges
    )


def create_transaction_flow(
    transactions: List[Dict[str, Any]],
    threshold: float = 1.0
) -> TransactionFlowGraph:
    """
    Create transaction flow graph.
    
    Args:
        transactions: List of transaction dictionaries
        threshold: Amount threshold for "large" transactions
        
    Returns:
        TransactionFlowGraph instance
    """
    # Create directed graph
    G = nx.DiGraph()
    
    # Add edges with amounts
    large_transactions = []
    for tx in transactions:
        source = tx.get('from_wallet')
        target = tx.get('to_wallet')
        amount = tx.get('amount', 0)
        
        if source and target:
            G.add_edge(source, target, amount=amount)
            if amount >= threshold:
                large_transactions.append((source, target, amount))
    
    # Create layout
    layout = nx.spring_layout(G, k=0.5, iterations=50)
    
    return TransactionFlowGraph(
        graph=G,
        layout=layout,
        large_transactions=large_transactions
    )


def create_wallet_relationships(
    wallets: List[Dict[str, Any]],
    transactions: List[Dict[str, Any]]
) -> WalletRelationshipGraph:
    """
    Create wallet relationship graph.
    
    Args:
        wallets: List of wallet dictionaries
        transactions: List of transaction dictionaries
        
    Returns:
        WalletRelationshipGraph instance
    """
    # Create undirected graph
    G = nx.Graph()
    
    # Add nodes
    for wallet in wallets:
        G.add_node(wallet['wallet_id'])
    
    # Add edges (undirected connections)
    for tx in transactions:
        source = tx.get('from_wallet')
        target = tx.get('to_wallet')
        if source and target:
            if G.has_edge(source, target):
                G[source][target]['weight'] += 1
            else:
                G.add_edge(source, target, weight=1)
    
    # Extract risk scores
    risk_scores = {
        wallet['wallet_id']: wallet.get('risk_score', 0.0)
        for wallet in wallets
    }
    
    # Create layout
    layout = nx.spring_layout(G, k=0.5, iterations=50)
    
    return WalletRelationshipGraph(
        graph=G,
        layout=layout,
        risk_scores=risk_scores
    )

# Made with Bob
