#!/usr/bin/env python3
"""
Test Crypto AML Notebook
========================

Simple test script to verify the crypto AML notebook workflow works correctly.
This tests the core functionality without requiring Jupyter execution.

Author: AI Assistant
Date: 2026-04-10
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from banking.crypto import (
    WalletGenerator,
    CryptoTransactionGenerator,
    MixerDetector,
    SanctionsScreener,
)
from banking.data_generators.patterns import CryptoMixerPatternGenerator


def test_crypto_workflow():
    """Test the complete crypto AML workflow."""
    print("=" * 80)
    print("CRYPTO AML NOTEBOOK WORKFLOW TEST")
    print("=" * 80)
    
    # Configuration
    SEED = 42
    WALLET_COUNT = 20
    TRANSACTION_COUNT = 50
    MIXER_PATTERN_COUNT = 3
    
    print(f"\n📋 Configuration:")
    print(f"   Seed: {SEED}")
    print(f"   Wallets: {WALLET_COUNT}")
    print(f"   Transactions: {TRANSACTION_COUNT}")
    print(f"   Mixer Patterns: {MIXER_PATTERN_COUNT}")
    
    # Step 1: Generate wallets
    print(f"\n{'Step 1: Generate Wallets':-^80}")
    wallet_gen = WalletGenerator(seed=SEED)
    wallets = wallet_gen.generate_batch(WALLET_COUNT)
    print(f"✅ Generated {len(wallets)} wallets")
    
    # Step 2: Generate transactions
    print(f"\n{'Step 2: Generate Transactions':-^80}")
    tx_gen = CryptoTransactionGenerator(wallets, seed=SEED)
    transactions = tx_gen.generate_batch(TRANSACTION_COUNT)
    print(f"✅ Generated {len(transactions)} transactions")
    
    # Step 3: Inject mixer patterns
    print(f"\n{'Step 3: Inject Mixer Patterns':-^80}")
    pattern_gen = CryptoMixerPatternGenerator(seed=SEED)
    pattern_result = pattern_gen.inject_pattern(
        wallets=wallets,
        transactions=transactions,
        pattern_count=MIXER_PATTERN_COUNT,
        pattern_type=None
    )
    print(f"✅ Injected {len(pattern_result['patterns'])} mixer patterns")
    print(f"   Affected Transactions: {len(pattern_result['affected_transactions'])}")
    print(f"   Total Amount Mixed: ${pattern_result['total_amount_mixed']:,.2f}")
    
    # Step 4: Mixer detection
    print(f"\n{'Step 4: Mixer Detection':-^80}")
    mixer_detector = MixerDetector()
    wallet_data_map = {}
    for wallet in wallets:
        wallet_data_map[wallet["wallet_id"]] = {
            "is_mixer": wallet["is_mixer"],
            "mixer_paths": []
        }
    
    mixer_results = mixer_detector.batch_detect(
        wallet_ids=[w["wallet_id"] for w in wallets],
        wallet_data_map=wallet_data_map
    )
    mixer_stats = mixer_detector.get_mixer_statistics(mixer_results)
    
    print(f"✅ Mixer detection complete")
    print(f"   Total Wallets: {mixer_stats['total_wallets']}")
    print(f"   Mixer Wallets: {mixer_stats['mixer_wallets']}")
    print(f"   Wallets with Interaction: {mixer_stats['wallets_with_interaction']}")
    print(f"   Average Risk Score: {mixer_stats['average_risk_score']:.3f}")
    print(f"   Recommendations:")
    for rec, count in mixer_stats['recommendations'].items():
        print(f"      {rec.capitalize()}: {count}")
    
    # Step 5: Sanctions screening
    print(f"\n{'Step 5: Sanctions Screening':-^80}")
    sanctions_screener = SanctionsScreener()
    sanctions_wallet_data_map = {}
    
    # Generate random jurisdictions for testing
    import random
    random.seed(SEED)
    jurisdictions = ["US", "GB", "FR", "DE", "JP", "CN", "IR", "KP", "SY", "RU"]
    
    for wallet in wallets:
        sanctions_wallet_data_map[wallet["wallet_id"]] = {
            "jurisdiction": random.choice(jurisdictions),
            "is_mixer": wallet["is_mixer"],
            "high_value_transactions": False,
            "rapid_movement": False,
        }
    
    sanctions_results = sanctions_screener.batch_screen(
        wallet_ids=[w["wallet_id"] for w in wallets],
        wallet_data_map=sanctions_wallet_data_map
    )
    sanctions_stats = sanctions_screener.get_screening_statistics(sanctions_results)
    
    print(f"✅ Sanctions screening complete")
    print(f"   Total Wallets: {sanctions_stats['total_wallets']}")
    print(f"   Sanctioned Wallets: {sanctions_stats['sanctioned_wallets']}")
    print(f"   High-Risk Jurisdiction: {sanctions_stats['high_risk_jurisdiction_wallets']}")
    print(f"   Total Matches: {sanctions_stats['total_matches']}")
    print(f"   Average Risk Score: {sanctions_stats['average_risk_score']:.3f}")
    print(f"   Recommendations:")
    for rec, count in sanctions_stats['recommendations'].items():
        print(f"      {rec.capitalize()}: {count}")
    
    # Summary
    print(f"\n{'SUMMARY':-^80}")
    print(f"✅ All workflow steps completed successfully")
    print(f"✅ Notebook is ready for execution")
    print(f"\n{'='*80}")
    
    return True


if __name__ == "__main__":
    try:
        success = test_crypto_workflow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Made with Bob
