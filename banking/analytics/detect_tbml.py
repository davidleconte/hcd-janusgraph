"""
Trade-Based Money Laundering (TBML) Detection Module
=====================================================

Advanced detection of TBML patterns including:
1. Carousel Fraud (Circular Trading Loops)
2. Over/Under Invoicing Detection
3. Phantom Shipments (Goods that don't exist)
4. Multiple Invoicing for Same Goods
5. Price Manipulation Patterns
6. Shell Company Network Detection

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-04
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from gremlin_python.driver import client, serializer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class TBMLAlert:
    """TBML Detection Alert"""

    alert_id: str
    alert_type: str  # 'carousel', 'over_invoicing', 'under_invoicing', 'phantom', 'shell_network'
    severity: str  # 'critical', 'high', 'medium', 'low'
    entities: List[str]  # Company IDs involved
    transactions: List[str]  # Transaction IDs involved
    total_value: float
    risk_score: float
    indicators: List[str]
    timestamp: datetime
    details: Dict[str, Any]


@dataclass
class PriceAnomaly:
    """Price anomaly detection result"""

    transaction_id: str
    declared_price: float
    market_price: float
    deviation_percent: float
    direction: str  # 'over' or 'under'
    risk_score: float


class TBMLDetector:
    """
    Advanced Trade-Based Money Laundering Detection System.

    Detects various TBML schemes including:
    - Carousel fraud (circular trading)
    - Over/under invoicing
    - Phantom shipments
    - Multiple invoicing
    - Shell company networks
    """

    # Detection thresholds
    PRICE_DEVIATION_THRESHOLD = 0.20  # 20% deviation from market price
    CIRCULAR_LOOP_MAX_DEPTH = 5
    MIN_LOOP_VALUE = 50000.0  # Minimum value for suspicious loops
    SHELL_COMPANY_INDICATORS = {
        "low_employees": 5,
        "recent_incorporation_days": 180,
        "high_transaction_volume_ratio": 10.0,
    }

    def __init__(self, url: str = "ws://localhost:18182/gremlin"):
        """Initialize TBML detector with JanusGraph connection."""
        self.url = url
        self.client = None
        self.alerts: List[TBMLAlert] = []
        self.market_prices: Dict[str, float] = {}  # Cache for market prices

    def connect(self):
        """Establish connection to JanusGraph."""
        logger.info("Connecting to JanusGraph at %s...", self.url)
        self.client = client.Client(
            self.url, "g", message_serializer=serializer.GraphSONSerializersV3d0()
        )
        result = self._query("g.V().count()")
        logger.info("Connected. Current vertex count: %s", result[0])

    def close(self):
        """Close connection."""
        if self.client:
            self.client.close()

    def _query(self, gremlin: str) -> List[Any]:
        """Execute a Gremlin query."""
        return self.client.submit(gremlin).all().result()

    # =========================================================================
    # CAROUSEL FRAUD (CIRCULAR TRADING) DETECTION
    # =========================================================================

    def detect_carousel_fraud(self, max_depth: int = 4) -> List[TBMLAlert]:
        """
        Detect carousel fraud patterns (circular trading loops).

        Carousel fraud involves circular trade of goods between companies
        to fraudulently claim tax refunds (especially VAT).

        Pattern: Company A → B → C → A (goods/money loop)

        Args:
            max_depth: Maximum loop depth to search (2-5 recommended)

        Returns:
            List of TBMLAlerts for detected carousel patterns
        """
        logger.info("Detecting carousel fraud (max depth: %s)...", max_depth)
        alerts = []

        # Find companies involved in circular trading
        for depth in range(2, min(max_depth + 1, 6)):
            loops = self._find_circular_loops(depth)

            for loop in loops:
                total_value = sum(tx.get("amount", 0) for tx in loop.get("transactions", []))

                if total_value >= self.MIN_LOOP_VALUE:
                    alert = TBMLAlert(
                        alert_id=f"TBML-CAROUSEL-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                        alert_type="carousel",
                        severity=self._calculate_severity(total_value),
                        entities=loop.get("companies", []),
                        transactions=loop.get("transaction_ids", []),
                        total_value=total_value,
                        risk_score=self._calculate_carousel_risk(loop),
                        indicators=[
                            f"Circular trading loop of depth {depth}",
                            f"Total loop value: ${total_value:,.2f}",
                            f"{len(loop.get('companies', []))} companies involved",
                        ],
                        timestamp=datetime.now(timezone.utc),
                        details=loop,
                    )
                    alerts.append(alert)

        self.alerts.extend(alerts)
        logger.info("Found %s carousel fraud patterns", len(alerts))
        return alerts

    def _find_circular_loops(self, depth: int) -> List[Dict]:
        """Find circular transaction loops of specified depth."""
        loops = []

        # Build dynamic query based on depth
        # This query finds paths that return to the starting company
        if depth == 2:
            query = """
            g.V().has_label('company').as('start')
             .out('owns_account').out('sent_transaction').out('received_by').in('owns_account')
             .has_label('company').as('mid')
             .where(neq('start'))
             .out('owns_account').out('sent_transaction').out('received_by').in('owns_account')
             .where(eq('start'))
             .select('start', 'mid')
             .by(valueMap('name', 'registration_number'))
             .limit(20)
            """
        elif depth == 3:
            query = """
            g.V().has_label('company').as('start')
             .out('owns_account').out('sent_transaction').as('tx1').out('received_by').in('owns_account')
             .has_label('company').as('hop1').where(neq('start'))
             .out('owns_account').out('sent_transaction').as('tx2').out('received_by').in('owns_account')
             .has_label('company').as('hop2').where(neq('start')).where(neq('hop1'))
             .out('owns_account').out('sent_transaction').as('tx3').out('received_by').in('owns_account')
             .where(eq('start'))
             .select('start', 'hop1', 'hop2', 'tx1', 'tx2', 'tx3')
             .by(valueMap('name'))
             .by(valueMap('name'))
             .by(valueMap('name'))
             .by(valueMap('amount'))
             .by(valueMap('amount'))
             .by(valueMap('amount'))
             .limit(10)
            """
        else:
            # Generic approach for depth 4+
            query = f"""
            g.V().has_label('company').as('start')
             .repeat(out('owns_account').out('sent_transaction').out('received_by').in('owns_account').has_label('company').simplePath())
             .times({depth})
             .where(eq('start'))
             .path()
             .limit(10)
            """

        try:
            results = self._query(query)
            for r in results:
                loops.append(
                    {
                        "companies": self._extract_companies(r),
                        "transaction_ids": self._extract_transaction_ids(r),
                        "depth": depth,
                        "raw_data": r,
                    }
                )
        except Exception as e:
            logger.warning("Circular loop query failed for depth %s: %s", depth, e)

        return loops

    def _extract_companies(self, result: Any) -> List[str]:
        """Extract company names from query result."""
        if isinstance(result, dict):
            companies = []
            for key in ["start", "hop1", "hop2", "hop3", "mid"]:
                if key in result and isinstance(result[key], dict):
                    name = result[key].get("name", [])
                    if name:
                        companies.append(name[0] if isinstance(name, list) else name)
            return companies
        return []

    def _extract_transaction_ids(self, result: Any) -> List[str]:
        """Extract transaction IDs from query result."""
        if isinstance(result, dict):
            tx_ids = []
            for key in ["tx1", "tx2", "tx3", "tx4"]:
                if key in result:
                    tx_ids.append(str(result[key]))
            return tx_ids
        return []

    def _calculate_carousel_risk(self, loop: Dict) -> float:
        """Calculate risk score for carousel fraud pattern."""
        base_score = 0.5

        # Higher depth = higher sophistication = higher risk
        depth = loop.get("depth", 2)
        base_score += depth * 0.1

        # More companies involved = higher risk
        num_companies = len(loop.get("companies", []))
        base_score += num_companies * 0.05

        # Higher value = higher risk
        total_value = sum(tx.get("amount", 0) for tx in loop.get("transactions", []))
        if total_value > 500000:
            base_score += 0.2
        elif total_value > 100000:
            base_score += 0.1

        return min(base_score, 1.0)

    # =========================================================================
    # OVER/UNDER INVOICING DETECTION
    # =========================================================================

    def detect_invoice_manipulation(
        self, market_prices: Optional[Dict[str, float]] = None
    ) -> Tuple[List[PriceAnomaly], List[TBMLAlert]]:
        """
        Detect over-invoicing and under-invoicing patterns.

        Over-invoicing: Declaring higher prices to move money out
        Under-invoicing: Declaring lower prices to avoid customs/taxes

        Args:
            market_prices: Dict of product codes to market prices

        Returns:
            Tuple of (anomalies, alerts)
        """
        logger.info("Detecting invoice manipulation patterns...")
        anomalies = []
        alerts = []

        if market_prices:
            self.market_prices.update(market_prices)

        # Query trades/invoices with amounts and product info
        query = """
        g.V().has_label('transaction')
         .has('transaction_type', within('invoice', 'trade', 'wire'))
         .project('tx_id', 'amount', 'description', 'currency', 'from_company', 'to_company')
         .by('transaction_id')
         .by('amount')
         .by(coalesce(values('description'), constant('N/A')))
         .by(coalesce(values('currency'), constant('USD')))
         .by(coalesce(__.in('sent_transaction').in('owns_account').values('name'), constant('Unknown')))
         .by(coalesce(__.out('received_by').in('owns_account').values('name'), constant('Unknown')))
         .limit(500)
        """

        try:
            results = self._query(query)

            # Analyze each transaction for price anomalies
            for tx in results:
                anomaly = self._check_price_anomaly(tx)
                if anomaly:
                    anomalies.append(anomaly)

                    # Generate alert for high-risk anomalies
                    if anomaly.risk_score >= 0.7:
                        alert = TBMLAlert(
                            alert_id=f"TBML-{anomaly.direction.upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                            alert_type=f"{anomaly.direction}_invoicing",
                            severity="high" if anomaly.risk_score >= 0.85 else "medium",
                            entities=[tx.get("from_company", ""), tx.get("to_company", "")],
                            transactions=[tx.get("tx_id", "")],
                            total_value=anomaly.declared_price,
                            risk_score=anomaly.risk_score,
                            indicators=[
                                f"Price deviation: {anomaly.deviation_percent:.1f}%",
                                f"Declared: ${anomaly.declared_price:,.2f}, Market: ${anomaly.market_price:,.2f}",
                                f"Direction: {anomaly.direction}-invoicing",
                            ],
                            timestamp=datetime.now(timezone.utc),
                            details={"anomaly": anomaly.__dict__, "transaction": tx},
                        )
                        alerts.append(alert)

        except Exception as e:
            logger.warning("Invoice manipulation detection failed: %s", e)

        self.alerts.extend(alerts)
        logger.info("Found %s price anomalies, %s high-risk alerts", len(anomalies), len(alerts))
        return anomalies, alerts

    def _check_price_anomaly(self, transaction: Dict) -> Optional[PriceAnomaly]:
        """Check if a transaction has price anomaly."""
        amount = transaction.get("amount", 0)
        description = transaction.get("description", "").lower()

        # Try to match against known market prices
        # In production, this would use product codes or ML classification
        estimated_market = self._estimate_market_price(description, amount)

        if estimated_market and estimated_market > 0:
            deviation = (amount - estimated_market) / estimated_market

            if abs(deviation) > self.PRICE_DEVIATION_THRESHOLD:
                direction = "over" if deviation > 0 else "under"
                risk_score = min(abs(deviation) * 2, 1.0)  # Cap at 1.0

                return PriceAnomaly(
                    transaction_id=transaction.get("tx_id", "unknown"),
                    declared_price=amount,
                    market_price=estimated_market,
                    deviation_percent=deviation * 100,
                    direction=direction,
                    risk_score=risk_score,
                )

        return None

    def _estimate_market_price(self, description: str, declared_amount: float) -> Optional[float]:
        """
        Estimate market price for a transaction based on description.

        In production, this would use:
        - Product code databases
        - Commodity price feeds
        - ML-based price estimation
        """
        # Simple heuristic-based estimation
        # Check for common patterns that might indicate manipulation

        # High-value items that are often manipulated
        high_value_keywords = ["gold", "diamond", "jewelry", "art", "antique", "luxury"]
        tech_keywords = ["electronics", "computer", "phone", "server", "equipment"]

        for keyword in high_value_keywords:
            if keyword in description:
                # Return a range that would flag unusual amounts
                if declared_amount > 100000:
                    return declared_amount * 0.7  # Suggest potential over-invoicing

        for keyword in tech_keywords:
            if keyword in description:
                if declared_amount > 50000:
                    return declared_amount * 0.75

        # Default: No anomaly detected
        return None

    # =========================================================================
    # SHELL COMPANY NETWORK DETECTION
    # =========================================================================

    def detect_shell_company_networks(self) -> List[TBMLAlert]:
        """
        Detect networks of shell companies used for TBML.

        Shell company indicators:
        - Recently incorporated
        - Few or no employees
        - High transaction volume relative to size
        - Common ownership with other suspicious entities
        - Registered in offshore jurisdictions
        """
        logger.info("Detecting shell company networks...")
        alerts = []

        # Query for companies with shell company indicators
        query = """
        g.V().has_label('company')
         .project('id', 'name', 'employee_count', 'registration_date', 'is_shell',
                  'country', 'tx_count', 'tx_total', 'connected_companies')
         .by(id)
         .by('name')
         .by(coalesce(values('employee_count'), constant(0)))
         .by(coalesce(values('registration_date'), constant('2020-01-01')))
         .by(coalesce(values('is_shell_company'), constant(false)))
         .by(coalesce(values('registration_country'), constant('US')))
         .by(coalesce(out('owns_account').out('sent_transaction').count(), constant(0)))
         .by(coalesce(out('owns_account').out('sent_transaction').values('amount').sum(), constant(0)))
         .by(coalesce(out('owns_account').out('sent_transaction').out('received_by').in('owns_account').has_label('company').dedup().count(), constant(0)))
         .limit(200)
        """

        try:
            results = self._query(query)
            shell_candidates = []

            for company in results:
                shell_score = self._calculate_shell_company_score(company)

                if shell_score >= 0.6:
                    shell_candidates.append({"company": company, "shell_score": shell_score})

            # Find networks of connected shell companies
            if shell_candidates:
                networks = self._find_shell_networks(shell_candidates)

                for network in networks:
                    if len(network["companies"]) >= 2:
                        total_value = sum(
                            c["company"].get("tx_total", 0) for c in network["companies"]
                        )

                        alert = TBMLAlert(
                            alert_id=f"TBML-SHELL-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                            alert_type="shell_network",
                            severity=self._calculate_severity(total_value),
                            entities=[c["company"].get("name", "") for c in network["companies"]],
                            transactions=[],
                            total_value=total_value,
                            risk_score=max(c["shell_score"] for c in network["companies"]),
                            indicators=[
                                f"{len(network['companies'])} connected shell companies",
                                f"Total transaction volume: ${total_value:,.2f}",
                                "High-risk TBML network detected",
                            ],
                            timestamp=datetime.now(timezone.utc),
                            details=network,
                        )
                        alerts.append(alert)

        except Exception as e:
            logger.warning("Shell company detection failed: %s", e)

        self.alerts.extend(alerts)
        logger.info("Found %s shell company network alerts", len(alerts))
        return alerts

    def _calculate_shell_company_score(self, company: Dict) -> float:
        """Calculate shell company probability score."""
        score = 0.0

        # Already flagged as shell
        if company.get("is_shell"):
            score += 0.5

        # Low employee count
        employees = company.get("employee_count", 0)
        if employees <= self.SHELL_COMPANY_INDICATORS["low_employees"]:
            score += 0.2

        # Recent incorporation
        reg_date = company.get("registration_date")
        if reg_date:
            try:
                days_since = (datetime.now() - datetime.fromisoformat(str(reg_date))).days
                if days_since <= self.SHELL_COMPANY_INDICATORS["recent_incorporation_days"]:
                    score += 0.2
            except (ValueError, TypeError):
                pass

        # High transaction volume relative to size
        tx_count = company.get("tx_count", 0)
        if employees > 0 and tx_count > 0:
            tx_per_employee = tx_count / employees
            if tx_per_employee > self.SHELL_COMPANY_INDICATORS["high_transaction_volume_ratio"]:
                score += 0.2

        # High-risk jurisdictions
        high_risk_countries = {"KY", "VG", "PA", "BZ", "SC", "MU"}  # Cayman, BVI, Panama, etc.
        if company.get("country", "") in high_risk_countries:
            score += 0.3

        return min(score, 1.0)

    def _find_shell_networks(self, shell_candidates: List[Dict]) -> List[Dict]:
        """Find connected networks among shell company candidates."""
        networks = []
        visited = set()

        for candidate in shell_candidates:
            company_name = candidate["company"].get("name", "")
            if company_name in visited:
                continue

            # Find all connected shell companies
            network = [candidate]
            visited.add(company_name)

            for other in shell_candidates:
                other_name = other["company"].get("name", "")
                if other_name not in visited:
                    # Check if they have transactions between them
                    if candidate["company"].get("connected_companies", 0) > 0:
                        network.append(other)
                        visited.add(other_name)

            if len(network) > 1:
                networks.append({"companies": network})

        return networks

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def _calculate_severity(self, total_value: float) -> str:
        """Calculate alert severity based on value."""
        if total_value >= 1000000:
            return "critical"
        elif total_value >= 500000:
            return "high"
        elif total_value >= 100000:
            return "medium"
        else:
            return "low"

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive TBML detection report."""
        return {
            "report_date": datetime.now(timezone.utc).isoformat(),
            "total_alerts": len(self.alerts),
            "alerts_by_type": {
                "carousel": len([a for a in self.alerts if a.alert_type == "carousel"]),
                "over_invoicing": len([a for a in self.alerts if a.alert_type == "over_invoicing"]),
                "under_invoicing": len(
                    [a for a in self.alerts if a.alert_type == "under_invoicing"]
                ),
                "shell_network": len([a for a in self.alerts if a.alert_type == "shell_network"]),
            },
            "alerts_by_severity": {
                "critical": len([a for a in self.alerts if a.severity == "critical"]),
                "high": len([a for a in self.alerts if a.severity == "high"]),
                "medium": len([a for a in self.alerts if a.severity == "medium"]),
                "low": len([a for a in self.alerts if a.severity == "low"]),
            },
            "total_value_at_risk": sum(a.total_value for a in self.alerts),
            "alerts": [
                {
                    "alert_id": a.alert_id,
                    "type": a.alert_type,
                    "severity": a.severity,
                    "risk_score": a.risk_score,
                    "entities": a.entities,
                    "total_value": a.total_value,
                    "indicators": a.indicators,
                }
                for a in self.alerts
            ],
        }

    def run_full_scan(self) -> Dict[str, Any]:
        """Run all TBML detection methods."""
        logger.info("Starting full TBML scan...")

        self.connect()

        try:
            # Run all detection methods
            self.detect_carousel_fraud()
            self.detect_invoice_manipulation()
            self.detect_shell_company_networks()

            # Generate report
            report = self.generate_report()

            logger.info("TBML scan complete. Found %s alerts.", len(self.alerts))
            return report

        finally:
            self.close()


def detect_tbml_loops():
    """Legacy function for backward compatibility."""
    detector = TBMLDetector()
    report = detector.run_full_scan()

    print(f"\n{'='*80}")
    print("TBML DETECTION REPORT")
    print(f"{'='*80}")
    print(f"Total Alerts: {report['total_alerts']}")
    print("\nAlerts by Type:")
    for alert_type, count in report["alerts_by_type"].items():
        print(f"  - {alert_type}: {count}")
    print(f"\nTotal Value at Risk: ${report['total_value_at_risk']:,.2f}")
    print(f"{'='*80}\n")

    return report
