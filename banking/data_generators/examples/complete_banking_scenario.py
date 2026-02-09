"""
Complete Banking Scenario Example
==================================

Demonstrates the Master Orchestrator generating a complete banking ecosystem
with persons, companies, accounts, transactions, communications, and injected
financial crime patterns.

This example creates:
- 1,000 persons
- 200 companies
- 2,000 accounts
- 50,000 transactions
- 10,000 communications
- 1,000 trades
- 500 travel records
- 2,000 documents
- 10 injected patterns (2 of each type)

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from banking.data_generators.orchestration import GenerationConfig, MasterOrchestrator

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Generate complete banking scenario"""

    print("\n" + "=" * 80)
    print("COMPLETE BANKING SCENARIO GENERATOR")
    print("=" * 80)
    print("\nThis will generate a complete banking ecosystem with:")
    print("  - 1,000 persons")
    print("  - 200 companies")
    print("  - 2,000 accounts")
    print("  - 50,000 transactions")
    print("  - 10,000 communications")
    print("  - 1,000 trades")
    print("  - 500 travel records")
    print("  - 2,000 documents")
    print("  - 10 financial crime patterns (2 of each type)")
    print("\nEstimated time: 2-3 minutes")
    print("=" * 80)

    # Create configuration
    config = GenerationConfig(
        # Reproducibility
        seed=42,
        # Entity counts
        person_count=1000,
        company_count=200,
        account_count=2000,
        # Event counts
        transaction_count=50000,
        communication_count=10000,
        trade_count=1000,
        travel_count=500,
        document_count=2000,
        # Pattern counts (2 of each type)
        insider_trading_patterns=2,
        tbml_patterns=2,
        fraud_ring_patterns=2,
        structuring_patterns=2,
        cato_patterns=2,
        # Temporal settings
        duration_days=365,
        # Quality settings
        suspicious_transaction_rate=0.02,
        suspicious_communication_rate=0.01,
        # Output settings
        output_dir=Path("./output/complete_banking_scenario"),
        output_format="json",
        include_ground_truth=True,
        include_metadata=True,
        # Performance settings
        batch_size=1000,
        enable_parallel=False,
    )

    # Create orchestrator
    logger.info("Initializing Master Orchestrator...")
    orchestrator = MasterOrchestrator(config)

    # Generate all data
    logger.info("Starting data generation...")
    stats = orchestrator.generate_all()

    # Print summary
    print("\n" + "=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)
    print("\nEntities Generated:")
    print(f"  Persons:        {stats.persons_generated:>10,}")
    print(f"  Companies:      {stats.companies_generated:>10,}")
    print(f"  Accounts:       {stats.accounts_generated:>10,}")
    print("\nEvents Generated:")
    print(f"  Transactions:   {stats.transactions_generated:>10,}")
    print(f"  Communications: {stats.communications_generated:>10,}")
    print(f"  Trades:         {stats.trades_generated:>10,}")
    print(f"  Travel Records: {stats.travels_generated:>10,}")
    print(f"  Documents:      {stats.documents_generated:>10,}")
    print("\nPatterns Generated:")
    print(f"  Total Patterns: {stats.patterns_generated:>10,}")
    print("\nPerformance:")
    print(f"  Total Records:  {stats.total_records:>10,}")
    print(f"  Time:           {stats.generation_time_seconds:>10.2f}s")
    print(f"  Records/sec:    {stats.records_per_second:>10.2f}")
    print("\nOutput Location:")
    print(f"  {config.output_dir}")
    print("=" * 80)

    if stats.errors:
        print("\nERRORS:")
        for error in stats.errors:
            print(f"  - {error}")

    if stats.warnings:
        print("\nWARNINGS:")
        for warning in stats.warnings:
            print(f"  - {warning}")

    print("\n✓ Complete banking scenario generated successfully!")
    print("\nNext steps:")
    print("  1. Review generated data in output directory")
    print("  2. Load data into JanusGraph for analysis")
    print("  3. Run detection algorithms on patterns")
    print("  4. Validate detection accuracy")


if __name__ == "__main__":
    main()
