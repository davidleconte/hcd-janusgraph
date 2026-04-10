"""
Crypto Streaming Integration Example
=====================================

This example demonstrates how to use the CryptoStreamingOrchestrator
to generate crypto wallet data, detect mixer patterns, screen for sanctions,
and publish events to Pulsar.

Author: AI Assistant
Date: 2026-04-10
Phase: 7.2 - Crypto Streaming Integration
"""

from banking.streaming import CryptoStreamingOrchestrator


def main():
    """Run crypto streaming orchestration example."""
    
    # Configuration
    config = {
        "seed": 42,  # For reproducible results
        "wallet_count": 100,
        "transaction_count": 200,
        "mixer_pattern_count": 5,
        "pulsar_url": "pulsar://localhost:6650",  # Change for production
    }
    
    print("=" * 70)
    print("Crypto Streaming Orchestration Example")
    print("=" * 70)
    print()
    print("Configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    print()
    
    # Create orchestrator (use_mock_producer=True for testing without Pulsar)
    orchestrator = CryptoStreamingOrchestrator(
        config,
        use_mock_producer=True  # Set to False to use real Pulsar
    )
    
    # Run complete workflow
    print("Running orchestration workflow...")
    print()
    stats = orchestrator.run()
    
    # Display results
    print()
    print("=" * 70)
    print("Orchestration Complete!")
    print("=" * 70)
    print()
    print("Statistics:")
    print(f"  Wallets Generated:       {stats['wallets_generated']}")
    print(f"  Transactions Generated:  {stats['transactions_generated']}")
    print(f"  Patterns Injected:       {stats['patterns_injected']}")
    print(f"  Mixer Detections:        {stats['mixer_detections']}")
    print(f"  Sanctions Screenings:    {stats['sanctions_screenings']}")
    print(f"  Events Published:        {stats['events_published']}")
    print(f"  Errors:                  {stats['errors']}")
    print()
    
    # If using mock producer, show event breakdown
    if hasattr(orchestrator.producer, 'get_events'):
        events = orchestrator.producer.get_events()
        event_types = {}
        for event in events:
            event_type = event.entity_type
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        print("Event Type Breakdown:")
        for event_type, count in sorted(event_types.items()):
            print(f"  {event_type}: {count}")
        print()
    
    print("=" * 70)
    print("Example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

# Made with Bob
