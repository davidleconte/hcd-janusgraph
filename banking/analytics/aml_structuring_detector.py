"""
AML Structuring Pattern Detector
=================================

Analyzes JanusGraph transaction data for potential money laundering
structuring patterns (transactions just under $10K reporting threshold).

Features:
- Detect transactions near CTR threshold ($10,000)
- Identify accounts with multiple small transactions
- Find rapid succession deposits
- Calculate risk scores for accounts
- Generate compliance-ready reports

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-03
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
from gremlin_python.driver import client, serializer

logger = logging.getLogger(__name__)

# AML Constants
CTR_THRESHOLD = 10000.0  # Currency Transaction Report threshold
STRUCTURING_THRESHOLD = 9500.0  # Likely structuring if repeatedly near this
SUSPICIOUS_TX_COUNT = 3  # Multiple transactions below threshold is suspicious


class AMLStructuringDetector:
    """
    Detects money laundering structuring patterns in transaction data.
    
    Structuring (also known as "smurfing") involves breaking up large
    transactions into smaller ones to avoid Currency Transaction Reports (CTRs).
    """
    
    def __init__(self, url: str = "ws://localhost:18182/gremlin"):
        self.url = url
        self.client = None
        self.findings = {
            "high_risk_accounts": [],
            "suspicious_transactions": [],
            "structuring_patterns": [],
            "summary_stats": {}
        }
        
    def connect(self):
        """Establish connection to JanusGraph."""
        logger.info(f"Connecting to JanusGraph at {self.url}...")
        self.client = client.Client(
            self.url,
            'g',
            message_serializer=serializer.GraphSONSerializersV3d0()
        )
        result = self.client.submit("g.V().count()").all().result()
        logger.info(f"Connected. Current vertex count: {result[0]}")
        
    def close(self):
        """Close connection."""
        if self.client:
            self.client.close()
            
    def _query(self, gremlin: str) -> List[Any]:
        """Execute a Gremlin query."""
        return self.client.submit(gremlin).all().result()
        
    def analyze_transaction_amounts(self) -> Dict[str, Any]:
        """
        Analyze transaction amounts to detect structuring patterns.
        
        Returns distribution and suspicious patterns.
        """
        print("\n📊 Analyzing Transaction Amounts...")
        print("=" * 60)
        
        # Get all transaction amounts
        amounts = self._query("g.V().hasLabel('transaction').values('amount')")
        
        if not amounts:
            print("⚠️  No transactions found in graph")
            return {}
            
        # Calculate statistics
        total_count = len(amounts)
        total_amount = sum(amounts)
        avg_amount = total_amount / total_count if total_count > 0 else 0
        min_amount = min(amounts)
        max_amount = max(amounts)
        
        # Count transactions by range
        under_1k = sum(1 for a in amounts if a < 1000)
        between_1k_5k = sum(1 for a in amounts if 1000 <= a < 5000)
        between_5k_9k = sum(1 for a in amounts if 5000 <= a < 9000)
        between_9k_10k = sum(1 for a in amounts if 9000 <= a < 10000)  # SUSPICIOUS
        above_10k = sum(1 for a in amounts if a >= 10000)
        
        # Transactions just under threshold (potential structuring)
        near_threshold = [a for a in amounts if STRUCTURING_THRESHOLD <= a < CTR_THRESHOLD]
        
        stats = {
            "total_transactions": total_count,
            "total_amount": total_amount,
            "average_amount": avg_amount,
            "min_amount": min_amount,
            "max_amount": max_amount,
            "distribution": {
                "under_1k": under_1k,
                "1k_to_5k": between_1k_5k,
                "5k_to_9k": between_5k_9k,
                "9k_to_10k (SUSPICIOUS)": between_9k_10k,
                "above_10k": above_10k
            },
            "near_threshold_count": len(near_threshold),
            "near_threshold_total": sum(near_threshold) if near_threshold else 0
        }
        
        print(f"\nTransaction Statistics:")
        print(f"  Total Transactions: {total_count:,}")
        print(f"  Total Amount: ${total_amount:,.2f}")
        print(f"  Average Amount: ${avg_amount:,.2f}")
        print(f"  Min/Max: ${min_amount:,.2f} / ${max_amount:,.2f}")
        
        print(f"\nAmount Distribution:")
        print(f"  Under $1K: {under_1k} ({under_1k/total_count*100:.1f}%)")
        print(f"  $1K - $5K: {between_1k_5k} ({between_1k_5k/total_count*100:.1f}%)")
        print(f"  $5K - $9K: {between_5k_9k} ({between_5k_9k/total_count*100:.1f}%)")
        print(f"  $9K - $10K: {between_9k_10k} ({between_9k_10k/total_count*100:.1f}%) ⚠️  SUSPICIOUS RANGE")
        print(f"  Above $10K: {above_10k} ({above_10k/total_count*100:.1f}%)")
        
        if between_9k_10k > 0:
            print(f"\n🚨 ALERT: {between_9k_10k} transactions in suspicious range ($9K-$10K)")
            print(f"   These may indicate structuring to avoid CTR reporting!")
            
        self.findings["summary_stats"] = stats
        return stats
        
    def identify_high_volume_accounts(self) -> List[Dict[str, Any]]:
        """
        Find accounts with many transactions (potential mule accounts).
        """
        print("\n🔍 Identifying High-Volume Accounts...")
        print("=" * 60)
        
        # Get accounts with transaction counts (outgoing)
        query = """
        g.V().hasLabel('account').as('acc')
            .out('sent_transaction').count().as('sent_count')
            .select('acc', 'sent_count')
            .by('account_id')
            .by()
            .order().by(select('sent_count'), desc)
            .limit(20)
        """
        
        try:
            results = self._query(query)
        except Exception as e:
            # Fallback to simpler query
            query = """
            g.V().hasLabel('account')
                .project('account_id', 'sent', 'received')
                .by('account_id')
                .by(out('sent_transaction').count())
                .by(in('received_by').count())
                .order().by(select('sent'), desc)
                .limit(20)
            """
            results = self._query(query)
            
        high_volume = []
        print("\nTop Accounts by Transaction Volume:")
        print("-" * 60)
        
        for r in results[:10]:
            if isinstance(r, dict):
                account_id = r.get('account_id', 'Unknown')
                sent = r.get('sent', 0)
                received = r.get('received', 0)
            else:
                continue
                
            total = sent + received
            if total > 5:  # Significant activity
                high_volume.append({
                    "account_id": account_id,
                    "sent_count": sent,
                    "received_count": received,
                    "total_transactions": total,
                    "risk_level": "HIGH" if total > 20 else "MEDIUM"
                })
                print(f"  {account_id[:20]}... | Sent: {sent} | Received: {received} | Total: {total}")
                
        self.findings["high_risk_accounts"] = high_volume
        return high_volume
        
    def detect_structuring_patterns(self) -> List[Dict[str, Any]]:
        """
        Detect accounts with multiple transactions just under CTR threshold.
        
        Pattern: Multiple transactions in $9,000-$9,999 range from same account.
        """
        print("\n🚨 Detecting Structuring Patterns...")
        print("=" * 60)
        
        # Find accounts sending transactions near threshold
        query = """
        g.V().hasLabel('account').as('acc')
            .out('sent_transaction')
            .has('amount', between(9000.0, 10000.0))
            .group()
            .by(select('acc').by('account_id'))
            .by(count())
            .unfold()
            .where(select(values).is(gte(2)))
        """
        
        patterns = []
        
        try:
            results = self._query(query)
            
            for r in results:
                if isinstance(r, dict):
                    for account_id, count in r.items():
                        patterns.append({
                            "account_id": account_id,
                            "suspicious_tx_count": count,
                            "pattern": "STRUCTURING",
                            "risk_level": "HIGH",
                            "recommendation": "File SAR (Suspicious Activity Report)"
                        })
        except Exception as e:
            logger.debug(f"Complex query failed, using fallback: {e}")
            
            # Fallback: analyze all accounts individually
            accounts = self._query("g.V().hasLabel('account').values('account_id')")
            
            for account_id in accounts[:50]:  # Limit for performance
                try:
                    count_query = f"""
                    g.V().has('account', 'account_id', '{account_id}')
                        .out('sent_transaction')
                        .has('amount', gte(9000.0))
                        .has('amount', lt(10000.0))
                        .count()
                    """
                    count = self._query(count_query)[0]
                    
                    if count >= 2:
                        patterns.append({
                            "account_id": account_id,
                            "suspicious_tx_count": count,
                            "pattern": "STRUCTURING",
                            "risk_level": "HIGH",
                            "recommendation": "File SAR"
                        })
                except:
                    continue
                    
        if patterns:
            print(f"\n🚨 FOUND {len(patterns)} POTENTIAL STRUCTURING PATTERNS!")
            print("-" * 60)
            for p in patterns[:10]:
                print(f"  Account: {p['account_id'][:30]}...")
                print(f"    Suspicious Transactions: {p['suspicious_tx_count']}")
                print(f"    Risk Level: {p['risk_level']}")
                print(f"    Action: {p['recommendation']}")
                print()
        else:
            print("\n✅ No obvious structuring patterns detected")
            print("   (This is good - or criminals are being more sophisticated)")
            
        self.findings["structuring_patterns"] = patterns
        return patterns
        
    def analyze_transaction_chains(self) -> List[Dict[str, Any]]:
        """
        Find transaction chains that might indicate layering.
        
        Pattern: A -> B -> C -> D (money moving through multiple accounts quickly)
        """
        print("\n🔗 Analyzing Transaction Chains (Layering Detection)...")
        print("=" * 60)
        
        # Find 2-hop transaction chains
        query = """
        g.V().hasLabel('account').as('start')
            .out('sent_transaction').as('tx1')
            .out('received_by').as('middle')
            .out('sent_transaction').as('tx2')
            .out('received_by').as('end')
            .select('start', 'middle', 'end')
            .by('account_id')
            .by('account_id')
            .by('account_id')
            .limit(20)
        """
        
        chains = []
        
        try:
            results = self._query(query)
            
            print(f"\nFound {len(results)} 2-hop transaction chains")
            print("-" * 60)
            
            for r in results[:10]:
                if isinstance(r, dict):
                    chain = {
                        "source": r.get('start', 'Unknown'),
                        "intermediate": r.get('middle', 'Unknown'),
                        "destination": r.get('end', 'Unknown'),
                        "hops": 2
                    }
                    chains.append(chain)
                    print(f"  {chain['source'][:15]}... -> {chain['intermediate'][:15]}... -> {chain['destination'][:15]}...")
                    
        except Exception as e:
            print(f"⚠️  Chain analysis limited: {e}")
            
        self.findings["transaction_chains"] = chains
        return chains
        
    def generate_report(self) -> str:
        """
        Generate a compliance-ready AML report.
        """
        print("\n" + "=" * 60)
        print("📋 AML STRUCTURING DETECTION REPORT")
        print("=" * 60)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        stats = self.findings.get("summary_stats", {})
        patterns = self.findings.get("structuring_patterns", [])
        high_risk = self.findings.get("high_risk_accounts", [])
        
        report = []
        report.append(f"\n1. EXECUTIVE SUMMARY")
        report.append(f"   Total Transactions Analyzed: {stats.get('total_transactions', 0):,}")
        report.append(f"   Total Amount: ${stats.get('total_amount', 0):,.2f}")
        report.append(f"   Structuring Patterns Found: {len(patterns)}")
        report.append(f"   High-Risk Accounts: {len(high_risk)}")
        
        report.append(f"\n2. SUSPICIOUS TRANSACTION RANGE ($9K-$10K)")
        dist = stats.get("distribution", {})
        suspicious_count = dist.get("9k_to_10k (SUSPICIOUS)", 0)
        report.append(f"   Transactions in Range: {suspicious_count}")
        report.append(f"   Total Near-Threshold: ${stats.get('near_threshold_total', 0):,.2f}")
        
        if patterns:
            report.append(f"\n3. STRUCTURING ALERTS (SAR RECOMMENDED)")
            for p in patterns[:5]:
                report.append(f"   - Account: {p['account_id'][:30]}...")
                report.append(f"     Suspicious Tx Count: {p['suspicious_tx_count']}")
                report.append(f"     Recommendation: {p['recommendation']}")
                
        report.append(f"\n4. RECOMMENDATIONS")
        if len(patterns) > 0:
            report.append("   ⚠️  File Suspicious Activity Reports for flagged accounts")
            report.append("   ⚠️  Enhanced monitoring for high-volume accounts")
        else:
            report.append("   ✅ No immediate SAR filings required")
            report.append("   ✅ Continue routine monitoring")
            
        report.append("\n" + "=" * 60)
        
        report_text = "\n".join(report)
        print(report_text)
        
        return report_text
        
    def run_full_analysis(self) -> Dict[str, Any]:
        """
        Run complete AML structuring analysis.
        """
        print("\n" + "=" * 60)
        print("🏦 AML STRUCTURING PATTERN DETECTION")
        print("=" * 60)
        print(f"Analysis started: {datetime.now()}")
        
        try:
            self.connect()
            
            # Run all detection algorithms
            self.analyze_transaction_amounts()
            self.identify_high_volume_accounts()
            self.detect_structuring_patterns()
            self.analyze_transaction_chains()
            
            # Generate report
            self.generate_report()
            
            print("\n✅ AML Analysis Complete!")
            
        finally:
            self.close()
            
        return self.findings


def main():
    """Run AML analysis."""
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="AML Structuring Pattern Detection")
    parser.add_argument("--url", default="ws://localhost:18182/gremlin", help="JanusGraph URL")
    args = parser.parse_args()
    
    detector = AMLStructuringDetector(url=args.url)
    findings = detector.run_full_analysis()
    
    # Print final summary
    print("\n" + "=" * 60)
    print("FINDINGS SUMMARY")
    print("=" * 60)
    print(f"Structuring Patterns: {len(findings['structuring_patterns'])}")
    print(f"High-Risk Accounts: {len(findings['high_risk_accounts'])}")
    print("=" * 60)


if __name__ == "__main__":
    main()
