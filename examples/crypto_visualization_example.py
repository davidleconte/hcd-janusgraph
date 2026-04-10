"""
Crypto Network Visualization Example
=====================================

This example demonstrates how to create interactive network visualizations
for crypto AML analysis using data from JanusGraph.

IMPORTANT: NetworkX is used ONLY for visualization (temporary in-memory graphs).
JanusGraph remains the authoritative source of truth for all graph data.

Author: AI Assistant
Date: 2026-04-10
Phase: 7.3 - Crypto Visualizations
"""

from banking.crypto import WalletGenerator, CryptoTransactionGenerator
from banking.crypto.visualizations.network_graphs import (
    create_mixer_network,
    create_transaction_flow,
    create_wallet_relationships
)


def main():
    """Run crypto visualization example."""
    
    print("=" * 70)
    print("Crypto Network Visualization Example")
    print("=" * 70)
    print()
    print("NOTE: In production, data would be queried from JanusGraph.")
    print("This example uses generated data for demonstration purposes.")
    print()
    
    # Generate sample data (in production, this would come from JanusGraph via Gremlin)
    print("Step 1: Generating sample crypto data...")
    wallet_gen = WalletGenerator(seed=42)
    wallets = [wallet_gen.generate() for _ in range(20)]  # Generate 20 wallets
    print(f"  ✅ Generated {len(wallets)} wallets")
    
    tx_gen = CryptoTransactionGenerator(wallets, seed=42)
    transactions = tx_gen.generate_batch(30)  # Generate 30 transactions
    print(f"  ✅ Generated {len(transactions)} transactions")
    print()
    
    # Create mixer network visualization
    print("Step 2: Creating mixer interaction network...")
    mixer_graph = create_mixer_network(
        wallets=wallets,
        transactions=transactions,
        mixer_results=[]  # Would come from MixerDetector in production
    )
    print(f"  ✅ Network created:")
    print(f"     - Nodes: {mixer_graph.graph.number_of_nodes()}")
    print(f"     - Edges: {mixer_graph.graph.number_of_edges()}")
    print(f"     - Mixer nodes: {len(mixer_graph.mixer_nodes)}")
    print(f"     - Suspicious edges: {len(mixer_graph.suspicious_edges)}")
    
    # Generate Plotly figure
    fig = mixer_graph.to_plotly()
    print(f"  ✅ Interactive visualization created")
    
    # Save to HTML
    output_file = "crypto_mixer_network.html"
    fig.write_html(output_file)
    print(f"  ✅ Saved to: {output_file}")
    print()
    
    # Create transaction flow visualization
    print("Step 3: Creating transaction flow network...")
    flow_graph = create_transaction_flow(
        transactions=transactions,
        threshold=0.5  # Transactions >= 0.5 BTC are "large"
    )
    print(f"  ✅ Flow network created:")
    print(f"     - Nodes: {flow_graph.graph.number_of_nodes()}")
    print(f"     - Edges: {flow_graph.graph.number_of_edges()}")
    print(f"     - Large transactions: {len(flow_graph.large_transactions)}")
    
    # Generate Plotly figure
    fig = flow_graph.to_plotly()
    print(f"  ✅ Interactive visualization created")
    
    # Save to HTML
    output_file = "crypto_transaction_flow.html"
    fig.write_html(output_file)
    print(f"  ✅ Saved to: {output_file}")
    print()
    
    # Create wallet relationship visualization
    print("Step 4: Creating wallet relationship network...")
    relationship_graph = create_wallet_relationships(
        wallets=wallets,
        transactions=transactions
    )
    print(f"  ✅ Relationship network created:")
    print(f"     - Nodes: {relationship_graph.graph.number_of_nodes()}")
    print(f"     - Edges: {relationship_graph.graph.number_of_edges()}")
    
    # Generate Plotly figure
    fig = relationship_graph.to_plotly()
    print(f"  ✅ Interactive visualization created")
    
    # Save to HTML
    output_file = "crypto_wallet_relationships.html"
    fig.write_html(output_file)
    print(f"  ✅ Saved to: {output_file}")
    print()
    
    print("=" * 70)
    print("Visualization Complete!")
    print("=" * 70)
    print()
    print("Generated Files:")
    print("  1. crypto_mixer_network.html - Mixer interaction network")
    print("  2. crypto_transaction_flow.html - Transaction flow visualization")
    print("  3. crypto_wallet_relationships.html - Wallet relationship network")
    print()
    print("Open these files in a web browser to view interactive visualizations.")
    print()
    print("Production Workflow:")
    print("  1. Query JanusGraph with Gremlin to get wallet/transaction data")
    print("  2. Pass data to visualization functions")
    print("  3. NetworkX creates temporary in-memory graph for layout")
    print("  4. Plotly generates interactive HTML/JavaScript visualization")
    print("  5. NetworkX graph is discarded (JanusGraph remains source of truth)")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()

# Made with Bob
