"""
Advanced Scenario Examples
==========================

Demonstrates complex data generation scenarios including:
- Multi-pattern injection
- Large-scale generation
- Custom configurations
- Pattern coordination

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

from pathlib import Path

from banking.data_generators.orchestration import GenerationConfig, MasterOrchestrator


def scenario_1_comprehensive_financial_crime():
    """
    Scenario 1: Comprehensive Financial Crime Ecosystem

    Generates a complete financial ecosystem with multiple
    coordinated patterns representing various financial crimes.

    Use Case: Testing comprehensive AML/fraud detection systems
    """
    print("=" * 60)
    print("Scenario 1: Comprehensive Financial Crime Ecosystem")
    print("=" * 60)

    config = GenerationConfig(
        seed=42,
        # Large entity base
        person_count=5000,
        company_count=2000,
        account_count=10000,
        # High transaction volume
        transaction_count=100000,
        communication_count=50000,
        trade_count=30000,
        travel_count=10000,
        document_count=20000,
        # Multiple pattern types
        insider_trading_patterns=5,
        tbml_patterns=3,
        fraud_ring_patterns=4,
        structuring_patterns=6,
        cato_patterns=2,
        output_dir=Path("./output/scenario1"),
    )

    print("\nConfiguration:")
    print(f"  Entities: {config.person_count + config.company_count + config.account_count:,}")
    print(
        f"  Events: {config.transaction_count + config.communication_count + config.trade_count:,}"
    )
    print(
        f"  Patterns: {config.insider_trading_patterns + config.tbml_patterns + config.fraud_ring_patterns + config.structuring_patterns + config.cato_patterns}"
    )

    orchestrator = MasterOrchestrator(config)

    print("\nGenerating data...")
    stats = orchestrator.generate_all()

    print("\nGeneration Complete!")
    print(f"  Persons: {stats.persons_generated:,}")
    print(f"  Companies: {stats.companies_generated:,}")
    print(f"  Accounts: {stats.accounts_generated:,}")
    print(f"  Transactions: {stats.transactions_generated:,}")
    print(f"  Communications: {stats.communications_generated:,}")
    print(f"  Trades: {stats.trades_generated:,}")
    print(f"  Patterns Injected: {stats.patterns_injected}")
    print(f"  Duration: {stats.duration_seconds:.2f}s")
    print(
        f"  Throughput: {(stats.persons_generated + stats.companies_generated + stats.accounts_generated) / stats.duration_seconds:.0f} entities/sec"
    )

    # Export data
    output_file = config.output_dir / "comprehensive_data.json"
    orchestrator.export_to_json(output_file)
    print(f"\nData exported to: {output_file}")

    return stats


def scenario_2_insider_trading_focus():
    """
    Scenario 2: Insider Trading Focus

    Generates data specifically focused on insider trading patterns
    with high-frequency trading and communications.

    Use Case: Testing insider trading detection algorithms
    """
    print("\n" + "=" * 60)
    print("Scenario 2: Insider Trading Focus")
    print("=" * 60)

    config = GenerationConfig(
        seed=123,
        # Moderate entity base
        person_count=1000,
        company_count=500,
        account_count=2000,
        # High trade and communication volume
        transaction_count=20000,
        communication_count=30000,  # High communication volume
        trade_count=50000,  # Very high trade volume
        travel_count=5000,
        document_count=10000,
        # Focus on insider trading
        insider_trading_patterns=10,  # Multiple insider trading patterns
        tbml_patterns=0,
        fraud_ring_patterns=0,
        structuring_patterns=0,
        cato_patterns=0,
        output_dir=Path("./output/scenario2"),
    )

    print("\nConfiguration:")
    print("  Focus: Insider Trading Detection")
    print(f"  Trades: {config.trade_count:,}")
    print(f"  Communications: {config.communication_count:,}")
    print(f"  Insider Trading Patterns: {config.insider_trading_patterns}")

    orchestrator = MasterOrchestrator(config)

    print("\nGenerating data...")
    stats = orchestrator.generate_all()

    print("\nGeneration Complete!")
    print(
        f"  Total Entities: {stats.persons_generated + stats.companies_generated + stats.accounts_generated:,}"
    )
    print(f"  Trades: {stats.trades_generated:,}")
    print(f"  Communications: {stats.communications_generated:,}")
    print(f"  Insider Trading Patterns: {stats.patterns_injected}")
    print(f"  Duration: {stats.duration_seconds:.2f}s")

    output_file = config.output_dir / "insider_trading_data.json"
    orchestrator.export_to_json(output_file)
    print(f"\nData exported to: {output_file}")

    return stats


def scenario_3_money_laundering_network():
    """
    Scenario 3: Money Laundering Network

    Generates a complex network focused on money laundering patterns
    including TBML, structuring, and fraud rings.

    Use Case: Testing AML transaction monitoring systems
    """
    print("\n" + "=" * 60)
    print("Scenario 3: Money Laundering Network")
    print("=" * 60)

    config = GenerationConfig(
        seed=456,
        # Large network
        person_count=3000,
        company_count=1500,
        account_count=6000,
        # Very high transaction volume
        transaction_count=150000,  # High transaction volume
        communication_count=20000,
        trade_count=10000,
        travel_count=15000,  # High travel for TBML
        document_count=30000,  # High document volume for TBML
        # Focus on money laundering patterns
        insider_trading_patterns=0,
        tbml_patterns=8,  # Trade-Based Money Laundering
        fraud_ring_patterns=6,  # Fraud rings
        structuring_patterns=12,  # Structuring/smurfing
        cato_patterns=0,
        output_dir=Path("./output/scenario3"),
    )

    print("\nConfiguration:")
    print("  Focus: Money Laundering Detection")
    print(f"  Transactions: {config.transaction_count:,}")
    print(f"  TBML Patterns: {config.tbml_patterns}")
    print(f"  Fraud Ring Patterns: {config.fraud_ring_patterns}")
    print(f"  Structuring Patterns: {config.structuring_patterns}")

    orchestrator = MasterOrchestrator(config)

    print("\nGenerating data...")
    stats = orchestrator.generate_all()

    print("\nGeneration Complete!")
    print(f"  Transactions: {stats.transactions_generated:,}")
    print(f"  Travel Events: {stats.travels_generated:,}")
    print(f"  Documents: {stats.documents_generated:,}")
    print(f"  Money Laundering Patterns: {stats.patterns_injected}")
    print(f"  Duration: {stats.duration_seconds:.2f}s")

    output_file = config.output_dir / "money_laundering_data.json"
    orchestrator.export_to_json(output_file)
    print(f"\nData exported to: {output_file}")

    return stats


def scenario_4_fraud_detection_testing():
    """
    Scenario 4: Fraud Detection Testing

    Generates data focused on various fraud patterns including
    fraud rings and coordinated account takeovers.

    Use Case: Testing fraud detection and prevention systems
    """
    print("\n" + "=" * 60)
    print("Scenario 4: Fraud Detection Testing")
    print("=" * 60)

    config = GenerationConfig(
        seed=789,
        # Moderate entity base
        person_count=2000,
        company_count=800,
        account_count=4000,
        # High transaction volume
        transaction_count=80000,
        communication_count=15000,
        trade_count=5000,
        travel_count=3000,
        document_count=8000,
        # Focus on fraud patterns
        insider_trading_patterns=0,
        tbml_patterns=0,
        fraud_ring_patterns=10,  # Multiple fraud rings
        structuring_patterns=0,
        cato_patterns=8,  # Coordinated account takeovers
        output_dir=Path("./output/scenario4"),
    )

    print("\nConfiguration:")
    print("  Focus: Fraud Detection")
    print(f"  Accounts: {config.account_count:,}")
    print(f"  Transactions: {config.transaction_count:,}")
    print(f"  Fraud Ring Patterns: {config.fraud_ring_patterns}")
    print(f"  CATO Patterns: {config.cato_patterns}")

    orchestrator = MasterOrchestrator(config)

    print("\nGenerating data...")
    stats = orchestrator.generate_all()

    print("\nGeneration Complete!")
    print(f"  Accounts: {stats.accounts_generated:,}")
    print(f"  Transactions: {stats.transactions_generated:,}")
    print(f"  Fraud Patterns: {stats.patterns_injected}")
    print(f"  Duration: {stats.duration_seconds:.2f}s")

    output_file = config.output_dir / "fraud_detection_data.json"
    orchestrator.export_to_json(output_file)
    print(f"\nData exported to: {output_file}")

    return stats


def scenario_5_performance_benchmark():
    """
    Scenario 5: Performance Benchmark

    Generates a very large dataset for performance testing
    and scalability validation.

    Use Case: Performance testing and capacity planning
    """
    print("\n" + "=" * 60)
    print("Scenario 5: Performance Benchmark")
    print("=" * 60)

    config = GenerationConfig(
        seed=999,
        # Very large scale
        person_count=10000,
        company_count=5000,
        account_count=20000,
        # Massive event volume
        transaction_count=500000,
        communication_count=100000,
        trade_count=50000,
        travel_count=20000,
        document_count=40000,
        # Moderate patterns
        insider_trading_patterns=5,
        tbml_patterns=5,
        fraud_ring_patterns=5,
        structuring_patterns=5,
        cato_patterns=5,
        output_dir=Path("./output/scenario5"),
    )

    print("\nConfiguration:")
    print("  Focus: Performance Benchmark")
    print(
        f"  Total Entities: {config.person_count + config.company_count + config.account_count:,}"
    )
    print(
        f"  Total Events: {config.transaction_count + config.communication_count + config.trade_count + config.travel_count + config.document_count:,}"
    )
    print(
        f"  Total Patterns: {config.insider_trading_patterns + config.tbml_patterns + config.fraud_ring_patterns + config.structuring_patterns + config.cato_patterns}"
    )

    orchestrator = MasterOrchestrator(config)

    print("\nGenerating data...")
    import time

    start = time.time()

    stats = orchestrator.generate_all()

    duration = time.time() - start

    print("\nGeneration Complete!")
    print(
        f"  Total Entities: {stats.persons_generated + stats.companies_generated + stats.accounts_generated:,}"
    )
    print(
        f"  Total Events: {stats.transactions_generated + stats.communications_generated + stats.trades_generated + stats.travels_generated + stats.documents_generated:,}"
    )
    print(f"  Total Patterns: {stats.patterns_injected}")
    print(f"  Duration: {duration:.2f}s")
    print("\nPerformance Metrics:")
    print(
        f"  Entity Throughput: {(stats.persons_generated + stats.companies_generated + stats.accounts_generated) / duration:.0f} entities/sec"
    )
    print(
        f"  Event Throughput: {(stats.transactions_generated + stats.communications_generated + stats.trades_generated) / duration:.0f} events/sec"
    )
    print(
        f"  Overall Throughput: {(stats.persons_generated + stats.companies_generated + stats.accounts_generated + stats.transactions_generated) / duration:.0f} items/sec"
    )

    output_file = config.output_dir / "benchmark_data.json"
    orchestrator.export_to_json(output_file)
    print(f"\nData exported to: {output_file}")

    return stats


def main():
    """Run all advanced scenarios"""
    print("\n" + "=" * 60)
    print("ADVANCED SCENARIO EXAMPLES")
    print("=" * 60)
    print("\nThis script demonstrates advanced data generation scenarios")
    print("for testing comprehensive financial crime detection systems.")
    print("\nNote: Large scenarios may take several minutes to complete.")

    # Run scenarios
    scenarios = [
        ("Comprehensive Financial Crime", scenario_1_comprehensive_financial_crime),
        ("Insider Trading Focus", scenario_2_insider_trading_focus),
        ("Money Laundering Network", scenario_3_money_laundering_network),
        ("Fraud Detection Testing", scenario_4_fraud_detection_testing),
        ("Performance Benchmark", scenario_5_performance_benchmark),
    ]

    results = {}

    for name, scenario_func in scenarios:
        try:
            stats = scenario_func()
            results[name] = stats
        except Exception as e:
            print(f"\nError in {name}: {e}")
            results[name] = None

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for name, stats in results.items():
        if stats:
            total_items = (
                stats.persons_generated
                + stats.companies_generated
                + stats.accounts_generated
                + stats.transactions_generated
                + stats.communications_generated
                + stats.trades_generated
                + stats.travels_generated
                + stats.documents_generated
            )
            print(f"\n{name}:")
            print(f"  Total Items: {total_items:,}")
            print(f"  Patterns: {stats.patterns_injected}")
            print(f"  Duration: {stats.duration_seconds:.2f}s")
            print(f"  Throughput: {total_items / stats.duration_seconds:.0f} items/sec")
        else:
            print(f"\n{name}: FAILED")

    print("\n" + "=" * 60)
    print("All scenarios complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
