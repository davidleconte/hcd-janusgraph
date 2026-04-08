"""
Insider Trading Detection Module
=================================

Advanced detection of insider trading patterns including:
1. Timing Correlation Analysis (trades before corporate announcements)
2. Coordinated Trading Detection (multiple traders acting together)
3. Communication-Based Detection (suspicious comms before trades)
4. Network Analysis (trader relationship mapping)
5. Abnormal Volume/Price Detection
6. Information Asymmetry Detection

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-04
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

from gremlin_python.driver import client, serializer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class InsiderTradingAlert:
    """Insider Trading Detection Alert"""

    alert_id: str
    alert_type: str  # 'timing', 'coordinated', 'communication', 'network', 'volume', 'asymmetry'
    severity: str  # 'critical', 'high', 'medium', 'low'
    traders: List[str]  # Person IDs involved
    trades: List[str]  # Trade IDs involved
    symbol: str
    total_value: float
    risk_score: float
    indicators: List[str]
    timestamp: datetime
    details: Dict[str, Any]


@dataclass
class TradeCluster:
    """Cluster of related trades"""

    trades: List[Dict]
    symbol: str
    start_time: datetime
    end_time: datetime
    total_volume: int
    total_value: float
    unique_traders: Set[str] = field(default_factory=set)
    avg_price: float = 0.0


@dataclass
class CorporateEvent:
    """Corporate event/announcement"""

    event_id: str
    company_id: str
    symbol: str
    event_type: str  # 'earnings', 'merger', 'acquisition', 'product_launch', 'management_change'
    announcement_date: datetime
    impact: str  # 'positive', 'negative', 'neutral'
    price_change_percent: float


class InsiderTradingDetector:
    """
    Advanced Insider Trading Detection System.

    Detects various insider trading patterns:
    - Timing correlation with corporate events
    - Coordinated trading among connected individuals
    - Suspicious communications preceding trades
    - Network-based relationship analysis
    - Abnormal volume and price patterns
    """

    # Detection thresholds
    PRE_ANNOUNCEMENT_WINDOW_DAYS = 14  # Days before announcement to analyze
    POST_ANNOUNCEMENT_WINDOW_DAYS = 3  # Days after to confirm price movement
    VOLUME_SPIKE_THRESHOLD = 2.5  # 2.5x average volume
    PRICE_MOVEMENT_THRESHOLD = 0.05  # 5% price movement
    COORDINATION_TIME_WINDOW_HOURS = 4  # Hours for trades to be considered coordinated
    MIN_SUSPICIOUS_TRADES = 3  # Minimum trades to flag pattern
    COMMUNICATION_WINDOW_HOURS = 48  # Hours before trade to check communications
    ALERT_TYPE_ORDER = ("timing", "coordinated", "communication", "network", "volume", "asymmetry")
    ALERT_SEVERITY_ORDER = ("critical", "high", "medium", "low")

    def __init__(self, url: str = "ws://localhost:18182/gremlin"):
        """Initialize insider trading detector with JanusGraph connection."""
        self.url = url
        self.client = None
        self.alerts: List[InsiderTradingAlert] = []
        self.corporate_events: Dict[str, List[CorporateEvent]] = {}

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
    # TIMING CORRELATION ANALYSIS
    # =========================================================================

    def detect_timing_patterns(
        self, corporate_events: Optional[List[CorporateEvent]] = None
    ) -> List[InsiderTradingAlert]:
        """
        Detect trades suspiciously timed before corporate announcements.

        Looks for:
        - Significant trades in days before major announcements
        - Trades that profit from subsequent price movements
        - Unusual trading by insiders or connected parties

        Args:
            corporate_events: List of corporate events to analyze against

        Returns:
            List of timing-related insider trading alerts
        """
        logger.info("Detecting timing-based insider trading patterns...")
        alerts = []

        # Load corporate events if provided
        if corporate_events:
            for event in corporate_events:
                if event.symbol not in self.corporate_events:
                    self.corporate_events[event.symbol] = []
                self.corporate_events[event.symbol].append(event)

        # Query for high-value trades
        query = """
        g.V().hasLabel('trade')
         .order().by('total_value', desc)
         .limit(200)
         .project('trade_id', 'trader_id', 'symbol', 'side', 'quantity', 'price',
                  'total_value', 'trade_date', 'trader_info')
         .by('trade_id')
         .by('trader_id')
         .by('symbol')
         .by('side')
         .by('quantity')
         .by('price')
         .by('total_value')
         .by(coalesce(values('trade_date'), constant('2026-01-01')))
         .by(coalesce(__.in('performed_trade').valueMap('first_name', 'is_pep'), constant({})))
        """

        try:
            trades = self._query(query)

            # Group trades by symbol
            trades_by_symbol = defaultdict(list)
            for trade in trades:
                trades_by_symbol[trade["symbol"]].append(trade)

            # Analyze each symbol for timing patterns
            for symbol, symbol_trades in trades_by_symbol.items():
                timing_alerts = self._analyze_timing_for_symbol(symbol, symbol_trades)
                alerts.extend(timing_alerts)

        except Exception as e:
            logger.warning("Timing pattern detection failed: %s", e)

        self.alerts.extend(alerts)
        logger.info("Found %s timing-based alerts", len(alerts))
        return alerts

    def _analyze_timing_for_symbol(
        self, symbol: str, trades: List[Dict]
    ) -> List[InsiderTradingAlert]:
        """Analyze trades for a specific symbol for timing patterns."""
        alerts = []

        # Check if we have corporate events for this symbol
        events = self.corporate_events.get(symbol, [])

        if not events:
            # Simulate event detection based on large price movements
            # In production, this would come from event database
            events = self._detect_implicit_events(symbol, trades)

        for event in events:
            # Find trades in pre-announcement window
            pre_trades = self._find_pre_announcement_trades(trades, event)

            if len(pre_trades) >= self.MIN_SUSPICIOUS_TRADES:
                # Calculate suspicion score
                risk_score = self._calculate_timing_risk(pre_trades, event)

                if risk_score >= 0.6:
                    total_value = sum(t.get("total_value", 0) for t in pre_trades)

                    alert = InsiderTradingAlert(
                        alert_id=f"IT-TIMING-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                        alert_type="timing",
                        severity=self._calculate_severity(risk_score),
                        traders=list(set(t.get("trader_id", "") for t in pre_trades)),
                        trades=[t.get("trade_id", "") for t in pre_trades],
                        symbol=symbol,
                        total_value=total_value,
                        risk_score=risk_score,
                        indicators=[
                            f"{len(pre_trades)} trades in {self.PRE_ANNOUNCEMENT_WINDOW_DAYS} days before event",
                            f"Event: {event.event_type}",
                            f"Price impact: {event.price_change_percent:.1f}%",
                            f"Total pre-announcement trading: ${total_value:,.2f}",
                        ],
                        timestamp=datetime.now(timezone.utc),
                        details={
                            "event": event.__dict__ if hasattr(event, "__dict__") else str(event),
                            "trades": pre_trades,
                        },
                    )
                    alerts.append(alert)

        return alerts

    def _find_pre_announcement_trades(
        self, trades: List[Dict], event: CorporateEvent
    ) -> List[Dict]:
        """Find trades made in the pre-announcement window."""
        pre_trades = []
        window_start = event.announcement_date - timedelta(days=self.PRE_ANNOUNCEMENT_WINDOW_DAYS)

        for trade in trades:
            trade_date_str = trade.get("trade_date", "")
            try:
                if isinstance(trade_date_str, datetime):
                    trade_date = trade_date_str
                else:
                    trade_date = datetime.fromisoformat(str(trade_date_str).replace("Z", "+00:00"))

                if window_start <= trade_date < event.announcement_date:
                    # Check if trade direction matches event impact
                    if (event.impact == "positive" and trade.get("side") == "buy") or (
                        event.impact == "negative" and trade.get("side") == "sell"
                    ):
                        pre_trades.append(trade)
            except (ValueError, TypeError):
                continue

        return pre_trades

    def _detect_implicit_events(self, symbol: str, trades: List[Dict]) -> List[CorporateEvent]:
        """Detect implicit corporate events from price/volume patterns."""
        events = []

        # Look for large volume clusters which might indicate pre-event trading
        clusters = self._find_trade_clusters(trades)

        for cluster in clusters:
            if cluster.total_volume > 1000:  # Significant volume
                # Create implicit event (in production, would verify against news/filings)
                event = CorporateEvent(
                    event_id=f"IMPL-{symbol}-{cluster.end_time.strftime('%Y%m%d')}",
                    company_id="",
                    symbol=symbol,
                    event_type="unknown",
                    announcement_date=cluster.end_time
                    + timedelta(days=self.PRE_ANNOUNCEMENT_WINDOW_DAYS),
                    impact=(
                        "positive"
                        if sum(1 for t in cluster.trades if t.get("side") == "buy")
                        > len(cluster.trades) / 2
                        else "negative"
                    ),
                    price_change_percent=10.0,  # Placeholder
                )
                events.append(event)

        return events

    def _calculate_timing_risk(self, pre_trades: List[Dict], event: CorporateEvent) -> float:
        """Calculate risk score for timing pattern."""
        score = 0.3  # Base score for trades before event

        # More trades = higher risk
        if len(pre_trades) >= 10:
            score += 0.2
        elif len(pre_trades) >= 5:
            score += 0.1

        # Large total value = higher risk
        total_value = sum(t.get("total_value", 0) for t in pre_trades)
        if total_value >= 500000:
            score += 0.2
        elif total_value >= 100000:
            score += 0.1

        # Significant price impact = higher risk
        if abs(event.price_change_percent) >= 20:
            score += 0.2
        elif abs(event.price_change_percent) >= 10:
            score += 0.1

        # Check for PEP (Politically Exposed Persons) involvement
        for trade in pre_trades:
            trader_info = trade.get("trader_info", {})
            if isinstance(trader_info, dict) and trader_info.get("is_pep", [False])[0]:
                score += 0.2
                break

        return min(score, 1.0)

    # =========================================================================
    # COORDINATED TRADING DETECTION
    # =========================================================================

    def detect_coordinated_trading(self) -> List[InsiderTradingAlert]:
        """
        Detect coordinated trading among multiple traders.

        Looks for:
        - Multiple traders making similar trades in short time window
        - Traders with known relationships acting together
        - Pattern of trades that individually appear normal but collectively are suspicious
        """
        logger.info("Detecting coordinated trading patterns...")
        alerts = []

        # Query for trades grouped by symbol and time
        query = """
        g.V().hasLabel('trade')
         .project('trade_id', 'trader_id', 'symbol', 'side', 'quantity', 'price',
                  'total_value', 'trade_date', 'trader_name')
         .by('trade_id')
         .by('trader_id')
         .by('symbol')
         .by('side')
         .by('quantity')
         .by('price')
         .by('total_value')
         .by(coalesce(values('trade_date'), constant('2026-01-01')))
         .by(coalesce(__.in('performed_trade').values('full_name'), constant('Unknown')))
         .limit(500)
        """

        try:
            trades = self._query(query)

            # Group trades by symbol
            trades_by_symbol = defaultdict(list)
            for trade in trades:
                trades_by_symbol[trade["symbol"]].append(trade)

            # Find coordinated patterns for each symbol
            for symbol, symbol_trades in trades_by_symbol.items():
                clusters = self._find_coordinated_clusters(symbol_trades)

                for cluster in clusters:
                    if len(cluster.unique_traders) >= 2:  # Multiple traders
                        risk_score = self._calculate_coordination_risk(cluster)

                        if risk_score >= 0.6:
                            alert = InsiderTradingAlert(
                                alert_id=f"IT-COORD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                                alert_type="coordinated",
                                severity=self._calculate_severity(risk_score),
                                traders=list(cluster.unique_traders),
                                trades=[t.get("trade_id", "") for t in cluster.trades],
                                symbol=symbol,
                                total_value=cluster.total_value,
                                risk_score=risk_score,
                                indicators=[
                                    f"{len(cluster.unique_traders)} traders acting in {self.COORDINATION_TIME_WINDOW_HOURS}h window",
                                    f"Total volume: {cluster.total_volume:,} shares",
                                    f"Total value: ${cluster.total_value:,.2f}",
                                    f"Time window: {cluster.start_time} to {cluster.end_time}",
                                ],
                                timestamp=datetime.now(timezone.utc),
                                details={
                                    "cluster": {
                                        "trades": cluster.trades,
                                        "traders": list(cluster.unique_traders),
                                        "avg_price": cluster.avg_price,
                                    }
                                },
                            )
                            alerts.append(alert)

        except Exception as e:
            logger.warning("Coordinated trading detection failed: %s", e)

        self.alerts.extend(alerts)
        logger.info("Found %s coordinated trading alerts", len(alerts))
        return alerts

    def _find_coordinated_clusters(self, trades: List[Dict]) -> List[TradeCluster]:
        """Find clusters of potentially coordinated trades."""
        clusters = []

        # Sort trades by time
        sorted_trades = sorted(trades, key=lambda t: t.get("trade_date", ""))

        if not sorted_trades:
            return clusters

        current_cluster_trades = [sorted_trades[0]]
        cluster_start = self._parse_date(sorted_trades[0].get("trade_date"))

        for trade in sorted_trades[1:]:
            trade_time = self._parse_date(trade.get("trade_date"))

            if trade_time and cluster_start:
                time_diff = (trade_time - cluster_start).total_seconds() / 3600

                if time_diff <= self.COORDINATION_TIME_WINDOW_HOURS:
                    current_cluster_trades.append(trade)
                else:
                    # Close current cluster and start new one
                    if len(current_cluster_trades) >= 2:
                        cluster = self._create_cluster(current_cluster_trades)
                        if cluster:
                            clusters.append(cluster)

                    current_cluster_trades = [trade]
                    cluster_start = trade_time

        # Don't forget the last cluster
        if len(current_cluster_trades) >= 2:
            cluster = self._create_cluster(current_cluster_trades)
            if cluster:
                clusters.append(cluster)

        return clusters

    def _create_cluster(self, trades: List[Dict]) -> Optional[TradeCluster]:
        """Create a trade cluster from a list of trades."""
        if not trades:
            return None

        start_time = self._parse_date(trades[0].get("trade_date"))
        end_time = self._parse_date(trades[-1].get("trade_date"))

        if not start_time or not end_time:
            return None

        cluster = TradeCluster(
            trades=trades,
            symbol=trades[0].get("symbol", ""),
            start_time=start_time,
            end_time=end_time,
            total_volume=sum(t.get("quantity", 0) for t in trades),
            total_value=sum(t.get("total_value", 0) for t in trades),
            unique_traders=set(t.get("trader_id", "") for t in trades),
        )

        if cluster.total_volume > 0:
            cluster.avg_price = cluster.total_value / cluster.total_volume

        return cluster

    def _calculate_coordination_risk(self, cluster: TradeCluster) -> float:
        """Calculate risk score for coordinated trading pattern."""
        score = 0.3  # Base score for multiple traders

        # More traders = higher coordination risk
        num_traders = len(cluster.unique_traders)
        if num_traders >= 5:
            score += 0.3
        elif num_traders >= 3:
            score += 0.2

        # Large total value = higher risk
        if cluster.total_value >= 500000:
            score += 0.2
        elif cluster.total_value >= 100000:
            score += 0.1

        # Same side trades (all buys or all sells) = higher risk
        sides = [t.get("side") for t in cluster.trades]
        if len(set(sides)) == 1:  # All same side
            score += 0.2

        return min(score, 1.0)

    # =========================================================================
    # COMMUNICATION-BASED DETECTION
    # =========================================================================

    def detect_suspicious_communications(self) -> List[InsiderTradingAlert]:
        """
        Detect suspicious communications preceding trades.

        Looks for:
        - Communications between insiders and traders before significant trades
        - Keywords indicating MNPI (Material Non-Public Information)
        - Unusual communication patterns before trading activity
        """
        logger.info("Detecting suspicious communication patterns...")
        alerts = []

        # Query for communications that might indicate insider information sharing
        query = """
        g.V().hasLabel('trade')
         .has('total_value', gt(50000))
         .as('trade')
         .in('performed_trade').as('trader')
         .in('sent_to', 'sent_from')
         .hasLabel('communication')
         .as('comm')
         .select('trade', 'trader', 'comm')
         .by(valueMap('trade_id', 'symbol', 'total_value', 'side', 'trade_date'))
         .by(valueMap('person_id', 'full_name'))
         .by(valueMap('communication_id', 'communication_type', 'content', 'timestamp', 'contains_suspicious_keywords'))
         .limit(100)
        """

        try:
            results = self._query(query)

            # Analyze communication-trade relationships
            for result in results:
                trade_info = result.get("trade", {})
                comm_info = result.get("comm", {})
                trader_info = result.get("trader", {})

                # Check if communication contains suspicious content
                if self._is_suspicious_communication(comm_info, trade_info):
                    risk_score = self._calculate_communication_risk(comm_info, trade_info)

                    if risk_score >= 0.6:
                        alert = InsiderTradingAlert(
                            alert_id=f"IT-COMM-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                            alert_type="communication",
                            severity=self._calculate_severity(risk_score),
                            traders=[trader_info.get("person_id", [""])[0]],
                            trades=[trade_info.get("trade_id", [""])[0]],
                            symbol=trade_info.get("symbol", [""])[0],
                            total_value=trade_info.get("total_value", [0])[0],
                            risk_score=risk_score,
                            indicators=[
                                "Suspicious communication preceding trade",
                                f"Communication type: {comm_info.get('communication_type', ['unknown'])[0]}",
                                f"Trade value: ${trade_info.get('total_value', [0])[0]:,.2f}",
                                "Potential MNPI sharing detected",
                            ],
                            timestamp=datetime.now(timezone.utc),
                            details={
                                "communication": comm_info,
                                "trade": trade_info,
                                "trader": trader_info,
                            },
                        )
                        alerts.append(alert)

        except Exception as e:
            logger.warning("Communication-based detection failed: %s", e)

        self.alerts.extend(alerts)
        logger.info("Found %s communication-based alerts", len(alerts))
        return alerts

    def _is_suspicious_communication(self, comm_info: Dict, trade_info: Dict) -> bool:
        """Check if a communication is suspicious relative to a trade."""
        # Check if flagged as containing suspicious keywords
        if comm_info.get("contains_suspicious_keywords", [False])[0]:
            return True

        # Check content for MNPI keywords
        content = str(comm_info.get("content", "")).lower()
        mnpi_keywords = [
            "earnings",
            "merger",
            "acquisition",
            "deal",
            "announcement",
            "confidential",
            "don't tell",
            "keep quiet",
            "between us",
            "inside",
            "before it's public",
            "non-public",
            "material",
        ]

        for keyword in mnpi_keywords:
            if keyword in content:
                return True

        return False

    def _calculate_communication_risk(self, comm_info: Dict, trade_info: Dict) -> float:
        """Calculate risk score for communication-trade relationship."""
        score = 0.4  # Base score for communication preceding trade

        # Flagged content = higher risk
        if comm_info.get("contains_suspicious_keywords", [False])[0]:
            score += 0.3

        # Large trade = higher risk
        trade_value = trade_info.get("total_value", [0])[0]
        if trade_value >= 200000:
            score += 0.2
        elif trade_value >= 100000:
            score += 0.1

        # Encrypted communication = potentially higher risk
        if comm_info.get("is_encrypted", [False])[0]:
            score += 0.1

        return min(score, 1.0)

    # =========================================================================
    # NETWORK ANALYSIS
    # =========================================================================

    def detect_network_patterns(self) -> List[InsiderTradingAlert]:
        """
        Detect insider trading through network relationship analysis.

        Looks for:
        - Trading by individuals connected to company insiders
        - Trading patterns among social/professional networks
        - Family/business relationships with material information access
        """
        logger.info("Detecting network-based insider trading patterns...")
        alerts = []

        # Query for traders connected to company insiders
        query = """
        g.V().hasLabel('company').as('company')
         .in('works_for', 'director_of', 'officer_of').as('insider')
         .out('knows', 'related_to', 'colleague_of').as('contact')
         .out('performed_trade').as('trade')
         .select('company', 'insider', 'contact', 'trade')
         .by(valueMap('name', 'stock_ticker'))
         .by(valueMap('person_id', 'full_name', 'job_title'))
         .by(valueMap('person_id', 'full_name'))
         .by(valueMap('trade_id', 'symbol', 'total_value', 'side', 'trade_date'))
         .limit(100)
        """

        try:
            results = self._query(query)

            # Group by insider-contact pairs
            network_trades = defaultdict(list)
            for result in results:
                insider_id = result.get("insider", {}).get("person_id", [""])[0]
                contact_id = result.get("contact", {}).get("person_id", [""])[0]
                key = f"{insider_id}_{contact_id}"
                network_trades[key].append(result)

            # Analyze each network relationship
            for key, trades in network_trades.items():
                if len(trades) >= 2:  # Multiple trades through this relationship
                    risk_score = self._calculate_network_risk(trades)

                    if risk_score >= 0.6:
                        total_value = sum(
                            t.get("trade", {}).get("total_value", [0])[0] for t in trades
                        )

                        insider_info = trades[0].get("insider", {})
                        contact_info = trades[0].get("contact", {})

                        alert = InsiderTradingAlert(
                            alert_id=f"IT-NET-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                            alert_type="network",
                            severity=self._calculate_severity(risk_score),
                            traders=[contact_info.get("person_id", [""])[0]],
                            trades=[t.get("trade", {}).get("trade_id", [""])[0] for t in trades],
                            symbol=trades[0].get("trade", {}).get("symbol", [""])[0],
                            total_value=total_value,
                            risk_score=risk_score,
                            indicators=[
                                "Trader connected to company insider",
                                f"Insider: {insider_info.get('full_name', ['Unknown'])[0]}",
                                f"Insider role: {insider_info.get('job_title', ['Unknown'])[0]}",
                                f"{len(trades)} trades through this connection",
                            ],
                            timestamp=datetime.now(timezone.utc),
                            details={
                                "insider": insider_info,
                                "contact": contact_info,
                                "trades": [t.get("trade", {}) for t in trades],
                            },
                        )
                        alerts.append(alert)

        except Exception as e:
            logger.warning("Network-based detection failed: %s", e)

        self.alerts.extend(alerts)
        logger.info("Found %s network-based alerts", len(alerts))
    # =========================================================================
    # MULTI-HOP TIPPING DETECTION
    # =========================================================================

    def detect_multi_hop_tipping(
        self, 
        max_hops: int = 5,
        time_window_days: int = 30
    ) -> List[InsiderTradingAlert]:
        """
        Detect multi-hop insider tipping chains.
        
        Identifies information flow from insiders through intermediaries
        to traders, detecting up to N-hop tipping chains.
        
        This method uses graph traversals to find paths from company insiders
        (CEO, CFO, etc.) through social/professional networks to traders who
        executed suspicious trades before corporate events.
        
        Args:
            max_hops: Maximum relationship hops to traverse (default: 5)
            time_window_days: Days before event to analyze (default: 30)
        
        Returns:
            List of multi-hop tipping alerts
            
        Example:
            >>> detector = InsiderTradingDetector()
            >>> detector.connect()
            >>> alerts = detector.detect_multi_hop_tipping(max_hops=5)
            >>> for alert in alerts:
            ...     print(f"Found {alert.details['hop_count']}-hop chain")
        """
        logger.info(f"Detecting multi-hop tipping chains (max {max_hops} hops)...")
        alerts = []
        
        # Query for multi-hop tipping chains
        # This traversal finds paths from insiders to traders through intermediaries
        query = f"""
        g.V().hasLabel('person')
         .has('job_title', within('CEO', 'CFO', 'Director', 'VP', 'President'))
         .as('insider')
         .repeat(
           out('knows', 'related_to', 'colleague_of', 'family_of')
           .simplePath()
         )
         .times({max_hops})
         .as('contact')
         .where(
           out('performed_trade')
           .has('total_value', gt(50000))
         )
         .path()
         .by(valueMap('person_id', 'full_name', 'job_title'))
         .limit(100)
        """
        
        try:
            results = self._query(query)
            
            for path in results:
                if len(path) < 3:  # Need at least insider -> intermediary -> trader
                    continue
                    
                # Extract path details
                insider = path[0]
                intermediaries = path[1:-1]
                trader = path[-1]
                
                # Get trader's trades
                trader_id = trader.get('person_id', [''])[0]
                trades_query = f"""
                g.V().has('person', 'person_id', '{trader_id}')
                 .out('performed_trade')
                 .has('total_value', gt(50000))
                 .valueMap('trade_id', 'symbol', 'total_value', 'side', 'trade_date')
                 .limit(20)
                """
                trader_trades = self._query(trades_query)
                
                if not trader_trades:
                    continue
                
                # Calculate risk based on path length and roles
                risk_score = self._calculate_multi_hop_risk(
                    insider, intermediaries, trader, trader_trades
                )
                
                if risk_score >= 0.7:
                    total_value = sum(t.get('total_value', [0])[0] for t in trader_trades)
                    symbols = list(set(t.get('symbol', [''])[0] for t in trader_trades))
                    
                    alert = InsiderTradingAlert(
                        alert_id=f"IT-MULTIHOP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                        alert_type="multi_hop_tipping",
                        severity=self._calculate_severity(risk_score),
                        traders=[trader_id],
                        trades=[t.get('trade_id', [''])[0] for t in trader_trades],
                        symbol=symbols[0] if symbols else "",
                        total_value=total_value,
                        risk_score=risk_score,
                        indicators=[
                            f"{len(path)}-hop tipping chain detected",
                            f"Insider: {insider.get('full_name', ['Unknown'])[0]}",
                            f"Role: {insider.get('job_title', ['Unknown'])[0]}",
                            f"Intermediaries: {len(intermediaries)}",
                            f"Final trader: {trader.get('full_name', ['Unknown'])[0]}",
                            f"Total trades: {len(trader_trades)}",
                            f"Total value: ${total_value:,.2f}",
                            "Sophisticated tipping network detected"
                        ],
                        timestamp=datetime.now(timezone.utc),
                        details={
                            'path': path,
                            'hop_count': len(path),
                            'insider': insider,
                            'intermediaries': intermediaries,
                            'trader': trader,
                            'trades': trader_trades,
                            'symbols': symbols
                        }
                    )
                    alerts.append(alert)
        
        except Exception as e:
            logger.warning(f"Multi-hop detection failed: {e}")
        
        self.alerts.extend(alerts)
        logger.info(f"Found {len(alerts)} multi-hop tipping alerts")
        return alerts

    def _calculate_multi_hop_risk(
        self,
        insider: Dict,
        intermediaries: List[Dict],
        trader: Dict,
        trades: List[Dict]
    ) -> float:
        """
        Calculate risk score for multi-hop tipping chain.
        
        Risk factors:
        - Path length (longer = more sophisticated)
        - Insider seniority (C-level = higher risk)
        - Number of intermediaries
        - Trade volume and value
        
        Args:
            insider: Insider person dict
            intermediaries: List of intermediary person dicts
            trader: Trader person dict
            trades: List of trade dicts
            
        Returns:
            Risk score between 0.0 and 1.0
        """
        score = 0.5  # Base score for multi-hop chain
        
        # Longer chains = higher sophistication = higher risk
        hop_count = len(intermediaries) + 2
        if hop_count >= 5:
            score += 0.2
        elif hop_count >= 3:
            score += 0.1
        
        # C-level insider = higher risk
        insider_title = insider.get('job_title', [''])[0].lower()
        if any(title in insider_title for title in ['ceo', 'cfo', 'president']):
            score += 0.2
        elif any(title in insider_title for title in ['director', 'vp']):
            score += 0.1
        
        # Multiple intermediaries = more sophisticated = higher risk
        if len(intermediaries) >= 2:
            score += 0.1
        
        # High trade volume = higher risk
        if len(trades) >= 5:
            score += 0.1
        
        # High trade value = higher risk
        total_value = sum(t.get('total_value', [0])[0] for t in trades)
        if total_value >= 500000:
            score += 0.1
        
        return min(score, 1.0)

        return alerts

    def _calculate_network_risk(self, trades: List[Dict]) -> float:
        """Calculate risk score for network-based pattern."""
        score = 0.4  # Base score for insider connection

        # More trades = higher risk
        if len(trades) >= 5:
            score += 0.2
        elif len(trades) >= 3:
            score += 0.1

        # Large total value = higher risk
        total_value = sum(t.get("trade", {}).get("total_value", [0])[0] for t in trades)
        if total_value >= 500000:
            score += 0.2
        elif total_value >= 200000:
            score += 0.1

        # Check if insider has high-level access
        insider_title = trades[0].get("insider", {}).get("job_title", [""])[0].lower()
        high_access_titles = ["ceo", "cfo", "cto", "director", "vp", "executive"]
        if any(title in insider_title for title in high_access_titles):
            score += 0.2

        return min(score, 1.0)

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def _parse_date(self, date_val: Any) -> Optional[datetime]:
        """Parse date from various formats."""
        if isinstance(date_val, datetime):
            return date_val
        if isinstance(date_val, str):
            try:
                return datetime.fromisoformat(date_val.replace("Z", "+00:00"))
            except ValueError:
                pass
        return None

    def _find_trade_clusters(self, trades: List[Dict]) -> List[TradeCluster]:
        """Find clusters of trades based on time proximity."""
        return self._find_coordinated_clusters(trades)

    def _calculate_severity(self, risk_score: float) -> str:
        """Calculate alert severity from risk score."""
        if risk_score >= 0.85:
            return "critical"
        elif risk_score >= 0.7:
            return "high"
        elif risk_score >= 0.5:
            return "medium"
        else:
            return "low"

    def _count_alerts_by_type(self) -> Dict[str, int]:
        """Count alerts grouped by alert_type using deterministic key order."""

    # =========================================================================
    # BIDIRECTIONAL COMMUNICATION ANALYSIS
    # =========================================================================

    def detect_conversation_patterns(
        self,
        time_window_hours: int = 48
    ) -> List[InsiderTradingAlert]:
        """
        Detect suspicious conversation patterns before trades.
        
        Analyzes bidirectional communication sequences (request-response)
        that may indicate MNPI sharing. Unlike unidirectional analysis,
        this method detects back-and-forth conversations that show
        information exchange patterns.
        
        Key Patterns Detected:
        - Insider initiates communication with suspicious keywords
        - Contact responds (bidirectional flow)
        - Subsequent trading activity by contact
        - Temporal correlation between conversation and trades
        
        Args:
            time_window_hours: Hours before trade to analyze communications (default: 48)
        
        Returns:
            List of conversation pattern alerts
            
        Example:
            >>> detector = InsiderTradingDetector()
            >>> detector.connect()
            >>> alerts = detector.detect_conversation_patterns(time_window_hours=48)
            >>> for alert in alerts:
            ...     print(f"Conversation between {alert.details['insider']['full_name']}")
            ...     print(f"and {alert.details['contact']['full_name']}")
        """
        logger.info("Detecting suspicious conversation patterns...")
        alerts = []
        
        # Query for bidirectional communication sequences
        # This finds conversations where:
        # 1. Insider sends message with suspicious keywords
        # 2. Contact responds (bidirectional)
        # 3. Contact has trading activity
        query = """
        g.V().hasLabel('person')
         .has('job_title', within('CEO', 'CFO', 'Director', 'VP', 'President'))
         .as('insider')
         .both('sent_to', 'sent_from')
         .hasLabel('communication')
         .has('contains_suspicious_keywords', true)
         .as('comm1')
         .both('sent_to', 'sent_from')
         .where(neq('insider'))
         .as('contact')
         .both('sent_to', 'sent_from')
         .hasLabel('communication')
         .as('comm2')
         .where(
           select('comm2').values('timestamp')
         )
         .select('insider', 'comm1', 'contact', 'comm2')
         .by(valueMap('person_id', 'full_name', 'job_title'))
         .by(valueMap('communication_id', 'timestamp', 'communication_type', 'content', 'contains_suspicious_keywords'))
         .by(valueMap('person_id', 'full_name'))
         .by(valueMap('communication_id', 'timestamp', 'communication_type', 'content', 'contains_suspicious_keywords'))
         .limit(50)
        """
        
        try:
            results = self._query(query)
            
            for result in results:
                insider = result.get('insider', {})
                comm1 = result.get('comm1', {})
                contact = result.get('contact', {})
                comm2 = result.get('comm2', {})
                
                # Check if this is a suspicious conversation
                if self._is_suspicious_conversation(comm1, comm2):
                    # Get contact's trades
                    contact_id = contact.get('person_id', [''])[0]
                    trades_query = f"""
                    g.V().has('person', 'person_id', '{contact_id}')
                     .out('performed_trade')
                     .has('total_value', gt(50000))
                     .valueMap('trade_id', 'symbol', 'total_value', 'side', 'trade_date')
                     .limit(20)
                    """
                    contact_trades = self._query(trades_query)
                    
                    # Calculate risk score
                    risk_score = self._calculate_conversation_risk(
                        insider, comm1, contact, comm2, contact_trades
                    )
                    
                    if risk_score >= 0.6:
                        total_value = sum(t.get('total_value', [0])[0] for t in contact_trades) if contact_trades else 0
                        
                        alert = InsiderTradingAlert(
                            alert_id=f"IT-CONV-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                            alert_type="conversation_pattern",
                            severity=self._calculate_severity(risk_score),
                            traders=[contact_id],
                            trades=[t.get('trade_id', [''])[0] for t in contact_trades] if contact_trades else [],
                            symbol=contact_trades[0].get('symbol', [''])[0] if contact_trades else "",
                            total_value=total_value,
                            risk_score=risk_score,
                            indicators=[
                                "Bidirectional communication pattern detected",
                                f"Insider: {insider.get('full_name', ['Unknown'])[0]} ({insider.get('job_title', ['Unknown'])[0]})",
                                f"Contact: {contact.get('full_name', ['Unknown'])[0]}",
                                "MNPI keywords in conversation",
                                "Request-response sequence identified",
                                f"Communication types: {comm1.get('communication_type', ['unknown'])[0]} → {comm2.get('communication_type', ['unknown'])[0]}",
                                f"Subsequent trades: {len(contact_trades) if contact_trades else 0}"
                            ],
                            timestamp=datetime.now(timezone.utc),
                            details={
                                'insider': insider,
                                'initial_communication': comm1,
                                'contact': contact,
                                'response_communication': comm2,
                                'conversation_type': 'bidirectional',
                                'trades': contact_trades if contact_trades else [],
                                'time_between_comms': self._calculate_time_diff(comm1, comm2)
                            }
                        )
                        alerts.append(alert)
        
        except Exception as e:
            logger.warning(f"Conversation pattern detection failed: {e}")
        
        self.alerts.extend(alerts)
        logger.info(f"Found {len(alerts)} conversation pattern alerts")
        return alerts

    def _is_suspicious_conversation(
        self,
        comm1: Dict,
        comm2: Dict
    ) -> bool:
        """
        Check if conversation pattern is suspicious.
        
        Criteria:
        - Time proximity (within 24 hours)
        - MNPI keywords in at least one message
        - Different communication types (e.g., email → phone)
        
        Args:
            comm1: First communication dict
            comm2: Second communication dict
            
        Returns:
            True if conversation is suspicious
        """
        # Check time proximity (within 24 hours)
        time1 = self._parse_date(comm1.get('timestamp', [''])[0])
        time2 = self._parse_date(comm2.get('timestamp', [''])[0])
        
        if time1 and time2:
            time_diff = abs((time2 - time1).total_seconds() / 3600)
            if time_diff > 24:
                return False
        else:
            return False
        
        # Check for MNPI keywords in either communication
        has_mnpi_1 = comm1.get('contains_suspicious_keywords', [False])[0]
        has_mnpi_2 = comm2.get('contains_suspicious_keywords', [False])[0]
        
        if not (has_mnpi_1 or has_mnpi_2):
            # Also check content directly for MNPI keywords
            content1 = str(comm1.get('content', '')).lower()
            content2 = str(comm2.get('content', '')).lower()
            
            mnpi_keywords = [
                'merger', 'acquisition', 'earnings', 'announcement',
                'confidential', 'material', 'non-public', 'deal',
                'between us', 'don\'t tell', 'keep quiet', 'inside'
            ]
            
            has_mnpi_1 = any(kw in content1 for kw in mnpi_keywords)
            has_mnpi_2 = any(kw in content2 for kw in mnpi_keywords)
        
        return has_mnpi_1 or has_mnpi_2

    def _calculate_conversation_risk(
        self,
        insider: Dict,
        comm1: Dict,
        contact: Dict,
        comm2: Dict,
        trades: Optional[List[Dict]] = None
    ) -> float:
        """
        Calculate risk score for conversation pattern.
        
        Risk Factors:
        - Insider seniority (C-level = higher risk)
        - MNPI keywords in both messages
        - Quick response time (<1 hour)
        - Communication type changes (email → phone)
        - Subsequent trading activity
        
        Args:
            insider: Insider person dict
            comm1: First communication dict
            contact: Contact person dict
            comm2: Second communication dict
            trades: Optional list of subsequent trades
            
        Returns:
            Risk score between 0.0 and 1.0
        """
        score = 0.4  # Base score for bidirectional communication
        
        # C-level insider = higher risk
        insider_title = insider.get('job_title', [''])[0].lower()
        if any(title in insider_title for title in ['ceo', 'cfo', 'president']):
            score += 0.2
        elif any(title in insider_title for title in ['director', 'vp']):
            score += 0.1
        
        # MNPI keywords in both messages = higher risk
        if comm1.get('contains_suspicious_keywords', [False])[0] and \
           comm2.get('contains_suspicious_keywords', [False])[0]:
            score += 0.2
        elif comm1.get('contains_suspicious_keywords', [False])[0] or \
             comm2.get('contains_suspicious_keywords', [False])[0]:
            score += 0.1
        
        # Quick response time (<1 hour) = higher urgency = higher risk
        time1 = self._parse_date(comm1.get('timestamp', [''])[0])
        time2 = self._parse_date(comm2.get('timestamp', [''])[0])
        if time1 and time2:
            time_diff = abs((time2 - time1).total_seconds() / 3600)
            if time_diff < 1:
                score += 0.15
            elif time_diff < 4:
                score += 0.1
        
        # Communication type change (email → phone) = higher risk
        type1 = comm1.get('communication_type', [''])[0]
        type2 = comm2.get('communication_type', [''])[0]
        if type1 != type2 and 'phone' in [type1.lower(), type2.lower()]:
            score += 0.1
        
        # Subsequent trading activity = higher risk
        if trades and len(trades) > 0:
            score += 0.1
            if len(trades) >= 3:
                score += 0.05
        
        return min(score, 1.0)

    def _calculate_time_diff(self, comm1: Dict, comm2: Dict) -> Optional[float]:
        """
        Calculate time difference between two communications in hours.
        
        Args:
            comm1: First communication dict
            comm2: Second communication dict
            
        Returns:
            Time difference in hours, or None if timestamps invalid
        """
        time1 = self._parse_date(comm1.get('timestamp', [''])[0])
        time2 = self._parse_date(comm2.get('timestamp', [''])[0])
        
        if time1 and time2:
            return abs((time2 - time1).total_seconds() / 3600)
        return None

        return {
            alert_type: len([alert for alert in self.alerts if alert.alert_type == alert_type])
            for alert_type in self.ALERT_TYPE_ORDER
        }

    def _count_alerts_by_severity(self) -> Dict[str, int]:
        """Count alerts grouped by severity using deterministic key order."""
        return {
            severity: len([alert for alert in self.alerts if alert.severity == severity])
            for severity in self.ALERT_SEVERITY_ORDER
        }

    def _total_value_at_risk(self) -> float:
        """Compute total value exposed by all alerts."""
        return sum(alert.total_value for alert in self.alerts)

    def _unique_trader_count(self) -> int:
        """Compute number of unique traders across alerts."""
        return len({trader for alert in self.alerts for trader in alert.traders})

    # ============================================================================
    # VECTOR SEARCH METHODS (Sprint 1.4 - Added 2026-04-07)
    # ============================================================================

    def detect_semantic_mnpi_sharing(
        self,
        insider_id: str,
        mnpi_threshold: float = 0.8,
        similarity_threshold: float = 0.7,
        time_window_days: int = 30
    ) -> Optional[InsiderTradingAlert]:
        """
        Detect MNPI sharing using semantic vector similarity (OpenSearch k-NN).
        
        This method uses OpenSearch vector search to detect Material Non-Public
        Information (MNPI) sharing based on semantic similarity of communications,
        rather than exact keyword matching.
        
        Detection Logic:
        1. Find communications from insider with high MNPI similarity (>0.8)
        2. Cluster semantically similar communications (coordinated messaging)
        3. Identify recipients who traded after receiving MNPI
        4. Calculate risk score based on network size and trading patterns
        
        Args:
            insider_id: Person ID of the insider
            mnpi_threshold: Minimum MNPI similarity score (0.0 to 1.0)
            similarity_threshold: Minimum semantic similarity for clustering
            time_window_days: Time window for trade correlation (days)
            
        Returns:
            InsiderTradingAlert if MNPI sharing detected, None otherwise
            
        Example:
            >>> detector = InsiderTradingDetector(client)
            >>> alert = detector.detect_semantic_mnpi_sharing("insider-123")
            >>> if alert:
            >>>     print(f"MNPI sharing detected: {alert.risk_score}")
        """
        try:
            from banking.analytics.vector_search import get_vector_search_client
        except ImportError:
            logger.warning("Vector search not available - install sentence-transformers and opensearch-py")
            return None
        
        logger.info(f"Detecting semantic MNPI sharing for insider: {insider_id}")
        
        # Initialize vector search client
        vector_client = get_vector_search_client()
        
        # Detect MNPI sharing network using vector similarity
        network_results = vector_client.detect_mnpi_sharing_network(
            insider_id=insider_id,
            mnpi_threshold=mnpi_threshold,
            similarity_threshold=similarity_threshold
        )
        
        if network_results['mnpi_communications_count'] == 0:
            logger.info(f"No MNPI communications found for insider: {insider_id}")
            return None
        
        # Get communication IDs from clusters
        communication_ids = []
        for cluster in network_results['similar_clusters']:
            communication_ids.extend(cluster['communications'])
        
        if not communication_ids:
            logger.info(f"No clustered MNPI communications for insider: {insider_id}")
            return None
        
        # Query JanusGraph for trades correlated with these communications
        query = """
        g.V().has('person', 'person_id', insider_id)
             .out('sent_communication')
             .has('communication_id', within(comm_ids))
             .as('comm')
             .out('sent_to')
             .as('recipient')
             .out('performed_trade')
             .has('timestamp', gte(start_time))
             .as('trade')
             .select('comm', 'recipient', 'trade')
             .by(valueMap(true))
        """
        
        # Calculate time window
        start_time = (datetime.now(timezone.utc) - timedelta(days=time_window_days)).isoformat()
        
        bindings = {
            'insider_id': insider_id,
            'comm_ids': communication_ids,
            'start_time': start_time
        }
        
        try:
            results = self.client.submit(query, bindings).all().result()
        except Exception as e:
            logger.error(f"Graph query failed: {e}")
            return None
        
        if not results:
            logger.info(f"No correlated trades found for MNPI communications")
            return None
        
        # Process results
        traders = set()
        trades = []
        total_value = 0.0
        recipients = set()
        
        for result in results:
            recipient_id = result['recipient']['person_id'][0]
            trade_id = result['trade']['trade_id'][0]
            trade_value = float(result['trade']['total_value'][0])
            
            traders.add(recipient_id)
            recipients.add(recipient_id)
            trades.append(trade_id)
            total_value += trade_value
        
        # Calculate risk score
        risk_score = self._calculate_semantic_mnpi_risk(
            network_results=network_results,
            trader_count=len(traders),
            trade_count=len(trades),
            total_value=total_value
        )
        
        # Determine severity
        severity = self._determine_severity(risk_score)
        
        # Create alert
        alert = InsiderTradingAlert(
            alert_id=f"semantic_mnpi_{insider_id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            alert_type="semantic_mnpi",
            severity=severity,
            traders=[insider_id] + list(traders),
            trades=trades,
            symbol="MULTIPLE",
            total_value=total_value,
            risk_score=risk_score,
            indicators=[
                f"MNPI communications: {network_results['mnpi_communications_count']}",
                f"Semantic clusters: {len(network_results['similar_clusters'])}",
                f"Recipients who traded: {len(recipients)}",
                f"Network risk score: {network_results['risk_score']:.3f}",
                f"Top MNPI keywords: {', '.join([kw[0] for kw in network_results['top_mnpi_keywords'][:5]])}",
            ],
            timestamp=datetime.now(timezone.utc),
            details={
                "insider_id": insider_id,
                "mnpi_communications_count": network_results['mnpi_communications_count'],
                "semantic_clusters": network_results['similar_clusters'],
                "network_risk_score": network_results['risk_score'],
                "alert_level": network_results['alert_level'],
                "top_mnpi_keywords": network_results['top_mnpi_keywords'],
                "recipients": list(recipients),
                "time_window_days": time_window_days,
                "detection_method": "vector_similarity"
            }
        )
        
        self.alerts.append(alert)
        logger.info(f"Semantic MNPI sharing alert created: {alert.alert_id} (risk={risk_score:.3f})")
        
        return alert
    
    def _calculate_semantic_mnpi_risk(
        self,
        network_results: Dict[str, Any],
        trader_count: int,
        trade_count: int,
        total_value: float
    ) -> float:
        """
        Calculate risk score for semantic MNPI sharing detection.
        
        Risk factors:
        1. Network risk score from vector analysis (40%)
        2. Number of traders who acted on information (30%)
        3. Number of trades executed (15%)
        4. Total value of trades (15%)
        
        Args:
            network_results: Results from vector search network detection
            trader_count: Number of traders who traded after receiving MNPI
            trade_count: Number of trades executed
            total_value: Total value of trades
            
        Returns:
            Risk score (0.0 to 1.0)
        """
        # Network risk score (from vector analysis)
        network_score = network_results['risk_score']
        
        # Trader count score (normalize to 0-1, max at 10 traders)
        trader_score = min(trader_count / 10.0, 1.0)
        
        # Trade count score (normalize to 0-1, max at 20 trades)
        trade_score = min(trade_count / 20.0, 1.0)
        
        # Value score (normalize to 0-1, max at $10M)
        value_score = min(total_value / 10_000_000, 1.0)
        
        # Weighted average
        risk_score = (
            network_score * 0.40 +
            trader_score * 0.30 +
            trade_score * 0.15 +
            value_score * 0.15
        )
        
        return round(risk_score, 3)
    
    def detect_coordinated_mnpi_network(
        self,
        min_participants: int = 3,
        mnpi_threshold: float = 0.8,
        similarity_threshold: float = 0.75,
        time_window_hours: int = 48
    ) -> List[InsiderTradingAlert]:
        """
        Detect coordinated MNPI sharing networks using vector similarity.
        
        Identifies groups of people sharing semantically similar MNPI content
        and trading in coordination. Uses OpenSearch k-NN to find clusters of
        similar communications across multiple senders.
        
        Detection Logic:
        1. Find all communications with high MNPI similarity across all senders
        2. Cluster communications by semantic similarity (coordinated messaging)
        3. Identify clusters with multiple senders (network coordination)
        4. Check if cluster participants traded within time window
        5. Generate alerts for coordinated networks
        
        Args:
            min_participants: Minimum number of people in network
            mnpi_threshold: Minimum MNPI similarity score
            similarity_threshold: Minimum semantic similarity for clustering
            time_window_hours: Time window for coordinated trading
            
        Returns:
            List of alerts for detected coordinated networks
            
        Example:
            >>> detector = InsiderTradingDetector(client)
            >>> alerts = detector.detect_coordinated_mnpi_network(min_participants=3)
            >>> print(f"Found {len(alerts)} coordinated networks")
        """
        try:
            from banking.analytics.vector_search import get_vector_search_client
        except ImportError:
            logger.warning("Vector search not available")
            return []
        
        logger.info("Detecting coordinated MNPI networks using vector similarity")
        
        # Initialize vector search client
        vector_client = get_vector_search_client()
        
        # Search for all high-MNPI communications
        search_body = {
            "size": 1000,
            "query": {
                "range": {
                    "mnpi_similarity": {"gte": mnpi_threshold}
                }
            },
            "sort": [
                {"mnpi_similarity": {"order": "desc"}},
                {"timestamp": {"order": "desc"}}
            ]
        }
        
        try:
            response = vector_client.client.search(
                index="communications-vector",
                body=search_body
            )
        except Exception as e:
            logger.error(f"OpenSearch query failed: {e}")
            return []
        
        if not response['hits']['hits']:
            logger.info("No high-MNPI communications found")
            return []
        
        # Extract communications
        communications = []
        for hit in response['hits']['hits']:
            comm = hit['_source']
            comm['embedding'] = comm.get('content_vector', [])
            communications.append(comm)
        
        # Cluster by semantic similarity
        clusters = self._cluster_communications_by_similarity(
            communications,
            similarity_threshold
        )
        
        # Filter clusters by minimum participants
        coordinated_clusters = [
            cluster for cluster in clusters
            if len(cluster['senders']) >= min_participants
        ]
        
        if not coordinated_clusters:
            logger.info(f"No coordinated networks found (min_participants={min_participants})")
            return []
        
        # Generate alerts for each coordinated network
        alerts = []
        for cluster in coordinated_clusters:
            alert = self._create_coordinated_network_alert(
                cluster,
                time_window_hours
            )
            if alert:
                alerts.append(alert)
                self.alerts.append(alert)
        
        logger.info(f"Detected {len(alerts)} coordinated MNPI networks")
        return alerts
    
    def _cluster_communications_by_similarity(
        self,
        communications: List[Dict[str, Any]],
        threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Cluster communications by semantic similarity.
        
        Uses cosine similarity between embeddings to group
        semantically similar communications.
        
        Args:
            communications: List of communications with embeddings
            threshold: Similarity threshold for clustering
            
        Returns:
            List of clusters with metadata
        """
        import numpy as np
        
        if len(communications) < 2:
            return []
        
        # Extract embeddings
        embeddings = []
        for comm in communications:
            embedding = np.array(comm.get('embedding', []))
            if embedding.size == 0:
                # Skip communications without embeddings
                continue
            embeddings.append(embedding)
        
        if len(embeddings) < 2:
            return []
        
        # Simple clustering: find groups with high pairwise similarity
        clusters = []
        processed = set()
        
        for i, comm1 in enumerate(communications):
            if i in processed or not comm1.get('embedding'):
                continue
            
            cluster = {
                "cluster_id": f"cluster_{len(clusters)}",
                "communications": [comm1['communication_id']],
                "senders": {comm1['sender_id']},
                "receivers": {comm1.get('receiver_id', 'unknown')},
                "avg_mnpi_similarity": comm1['mnpi_similarity'],
                "timestamps": [comm1['timestamp']],
                "matching_keywords": set(comm1.get('matching_keywords', []))
            }
            
            embedding1 = embeddings[i]
            
            for j, comm2 in enumerate(communications[i+1:], start=i+1):
                if j in processed or not comm2.get('embedding'):
                    continue
                
                embedding2 = embeddings[j]
                
                # Calculate cosine similarity
                similarity = np.dot(embedding1, embedding2) / (
                    np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
                )
                
                if similarity >= threshold:
                    cluster['communications'].append(comm2['communication_id'])
                    cluster['senders'].add(comm2['sender_id'])
                    cluster['receivers'].add(comm2.get('receiver_id', 'unknown'))
                    cluster['timestamps'].append(comm2['timestamp'])
                    cluster['matching_keywords'].update(comm2.get('matching_keywords', []))
                    processed.add(j)
            
            if len(cluster['communications']) > 1:
                # Convert sets to lists for JSON serialization
                cluster['senders'] = list(cluster['senders'])
                cluster['receivers'] = list(cluster['receivers'])
                cluster['matching_keywords'] = list(cluster['matching_keywords'])
                clusters.append(cluster)
                processed.add(i)
        
        return clusters
    
    def _create_coordinated_network_alert(
        self,
        cluster: Dict[str, Any],
        time_window_hours: int
    ) -> Optional[InsiderTradingAlert]:
        """
        Create alert for coordinated MNPI network.
        
        Args:
            cluster: Cluster of coordinated communications
            time_window_hours: Time window for trade correlation
            
        Returns:
            InsiderTradingAlert if trades detected, None otherwise
        """
        senders = cluster['senders']
        
        # Query for trades by cluster participants
        query = """
        g.V().has('person', 'person_id', within(sender_ids))
             .out('performed_trade')
             .has('timestamp', gte(start_time))
             .valueMap(true)
        """
        
        # Calculate time window
        start_time = (datetime.now(timezone.utc) - timedelta(hours=time_window_hours)).isoformat()
        
        bindings = {
            'sender_ids': senders,
            'start_time': start_time
        }
        
        try:
            results = self.client.submit(query, bindings).all().result()
        except Exception as e:
            logger.error(f"Graph query failed: {e}")
            return None
        
        if not results:
            return None
        
        # Process trades
        trades = []
        total_value = 0.0
        
        for result in results:
            trade_id = result['trade_id'][0]
            trade_value = float(result['total_value'][0])
            trades.append(trade_id)
            total_value += trade_value
        
        # Calculate risk score
        risk_score = self._calculate_coordinated_network_risk(
            cluster=cluster,
            trade_count=len(trades),
            total_value=total_value
        )
        
        # Determine severity
        severity = self._determine_severity(risk_score)
        
        # Create alert
        alert = InsiderTradingAlert(
            alert_id=f"coordinated_network_{cluster['cluster_id']}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            alert_type="coordinated_network",
            severity=severity,
            traders=senders,
            trades=trades,
            symbol="MULTIPLE",
            total_value=total_value,
            risk_score=risk_score,
            indicators=[
                f"Network participants: {len(senders)}",
                f"Coordinated communications: {len(cluster['communications'])}",
                f"Trades executed: {len(trades)}",
                f"Avg MNPI similarity: {cluster['avg_mnpi_similarity']:.3f}",
                f"Top keywords: {', '.join(list(cluster['matching_keywords'])[:5])}",
            ],
            timestamp=datetime.now(timezone.utc),
            details={
                "cluster_id": cluster['cluster_id'],
                "participants": senders,
                "communication_count": len(cluster['communications']),
                "avg_mnpi_similarity": cluster['avg_mnpi_similarity'],
                "matching_keywords": cluster['matching_keywords'],
                "time_window_hours": time_window_hours,
                "detection_method": "coordinated_vector_clustering"
            }
        )
        
        return alert
    
    def _calculate_coordinated_network_risk(
        self,
        cluster: Dict[str, Any],
        trade_count: int,
        total_value: float
    ) -> float:
        """
        Calculate risk score for coordinated network.
        
        Risk factors:
        1. Number of participants (30%)
        2. MNPI similarity (30%)
        3. Number of trades (20%)
        4. Total value (20%)
        
        Args:
            cluster: Cluster metadata
            trade_count: Number of trades
            total_value: Total trade value
            
        Returns:
            Risk score (0.0 to 1.0)
        """
        # Participant score (normalize to 0-1, max at 10 participants)
        participant_score = min(len(cluster['senders']) / 10.0, 1.0)
        
        # MNPI similarity score
        mnpi_score = cluster['avg_mnpi_similarity']
        
        # Trade count score (normalize to 0-1, max at 20 trades)
        trade_score = min(trade_count / 20.0, 1.0)
        
        # Value score (normalize to 0-1, max at $10M)
        value_score = min(total_value / 10_000_000, 1.0)
        
        # Weighted average
        risk_score = (
            participant_score * 0.30 +
            mnpi_score * 0.30 +
            trade_score * 0.20 +
            value_score * 0.20
        )
        
        return round(risk_score, 3)


    @staticmethod
    def _serialize_alert(alert: InsiderTradingAlert) -> Dict[str, Any]:
        """Serialize one alert in report summary format."""
        return {
            "alert_id": alert.alert_id,
            "type": alert.alert_type,
            "severity": alert.severity,
            "risk_score": alert.risk_score,
            "traders": alert.traders,
            "symbol": alert.symbol,
            "total_value": alert.total_value,
            "indicators": alert.indicators,
        }

    def _serialize_alerts(self) -> List[Dict[str, Any]]:
        """Serialize all alerts in deterministic insertion order."""
        return [self._serialize_alert(alert) for alert in self.alerts]

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive insider trading detection report."""
        return {
            "report_date": datetime.now(timezone.utc).isoformat(),
            "total_alerts": len(self.alerts),
            "alerts_by_type": self._count_alerts_by_type(),
            "alerts_by_severity": self._count_alerts_by_severity(),
            "total_value_at_risk": self._total_value_at_risk(),
            "unique_traders": self._unique_trader_count(),
            "alerts": self._serialize_alerts(),
        }

    def run_full_scan(self) -> Dict[str, Any]:
        """Run all insider trading detection methods."""
        logger.info("Starting full insider trading scan...")

        self.connect()

        try:
            # Run all detection methods
            self.detect_timing_patterns()
            self.detect_coordinated_trading()
            self.detect_suspicious_communications()
            self.detect_network_patterns()

            # Generate report
            report = self.generate_report()

            logger.info("Insider trading scan complete. Found %s alerts.", len(self.alerts))
            return report

        finally:
            self.close()


def detect_insider_trading():
    """Legacy function for backward compatibility."""
    detector = InsiderTradingDetector()
    report = detector.run_full_scan()

    print(f"\n{'='*80}")
    print("INSIDER TRADING DETECTION REPORT")
    print(f"{'='*80}")
    print(f"Total Alerts: {report['total_alerts']}")
    print("\nAlerts by Type:")
    for alert_type, count in report["alerts_by_type"].items():
        print(f"  - {alert_type}: {count}")
    print("\nAlerts by Severity:")
    for severity, count in report["alerts_by_severity"].items():
        print(f"  - {severity}: {count}")
    print(f"\nTotal Value at Risk: ${report['total_value_at_risk']:,.2f}")
    print(f"Unique Traders Flagged: {report['unique_traders']}")
    print(f"{'='*80}\n")

    return report
