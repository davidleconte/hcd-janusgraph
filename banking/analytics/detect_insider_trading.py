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

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-04
"""

import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from gremlin_python.driver import client, serializer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
            self.url,
            'g',
            message_serializer=serializer.GraphSONSerializersV3d0()
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
        self,
        corporate_events: Optional[List[CorporateEvent]] = None
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
         .by(coalesce(__.in('performed_trade').valueMap('first_name', 'last_name', 'is_pep'), constant({})))
        """
        
        try:
            trades = self._query(query)
            
            # Group trades by symbol
            trades_by_symbol = defaultdict(list)
            for trade in trades:
                trades_by_symbol[trade['symbol']].append(trade)
            
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
        self,
        symbol: str,
        trades: List[Dict]
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
                    total_value = sum(t.get('total_value', 0) for t in pre_trades)
                    
                    alert = InsiderTradingAlert(
                        alert_id=f"IT-TIMING-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                        alert_type='timing',
                        severity=self._calculate_severity(risk_score),
                        traders=list(set(t.get('trader_id', '') for t in pre_trades)),
                        trades=[t.get('trade_id', '') for t in pre_trades],
                        symbol=symbol,
                        total_value=total_value,
                        risk_score=risk_score,
                        indicators=[
                            f"{len(pre_trades)} trades in {self.PRE_ANNOUNCEMENT_WINDOW_DAYS} days before event",
                            f"Event: {event.event_type}",
                            f"Price impact: {event.price_change_percent:.1f}%",
                            f"Total pre-announcement trading: ${total_value:,.2f}"
                        ],
                        timestamp=datetime.now(timezone.utc),
                        details={
                            'event': event.__dict__ if hasattr(event, '__dict__') else str(event),
                            'trades': pre_trades
                        }
                    )
                    alerts.append(alert)
        
        return alerts
    
    def _find_pre_announcement_trades(
        self,
        trades: List[Dict],
        event: CorporateEvent
    ) -> List[Dict]:
        """Find trades made in the pre-announcement window."""
        pre_trades = []
        window_start = event.announcement_date - timedelta(days=self.PRE_ANNOUNCEMENT_WINDOW_DAYS)
        
        for trade in trades:
            trade_date_str = trade.get('trade_date', '')
            try:
                if isinstance(trade_date_str, datetime):
                    trade_date = trade_date_str
                else:
                    trade_date = datetime.fromisoformat(str(trade_date_str).replace('Z', '+00:00'))
                
                if window_start <= trade_date < event.announcement_date:
                    # Check if trade direction matches event impact
                    if (event.impact == 'positive' and trade.get('side') == 'buy') or \
                       (event.impact == 'negative' and trade.get('side') == 'sell'):
                        pre_trades.append(trade)
            except (ValueError, TypeError):
                continue
        
        return pre_trades
    
    def _detect_implicit_events(
        self,
        symbol: str,
        trades: List[Dict]
    ) -> List[CorporateEvent]:
        """Detect implicit corporate events from price/volume patterns."""
        events = []
        
        # Look for large volume clusters which might indicate pre-event trading
        clusters = self._find_trade_clusters(trades)
        
        for cluster in clusters:
            if cluster.total_volume > 1000:  # Significant volume
                # Create implicit event (in production, would verify against news/filings)
                event = CorporateEvent(
                    event_id=f"IMPL-{symbol}-{cluster.end_time.strftime('%Y%m%d')}",
                    company_id='',
                    symbol=symbol,
                    event_type='unknown',
                    announcement_date=cluster.end_time + timedelta(days=self.PRE_ANNOUNCEMENT_WINDOW_DAYS),
                    impact='positive' if sum(1 for t in cluster.trades if t.get('side') == 'buy') > len(cluster.trades) / 2 else 'negative',
                    price_change_percent=10.0  # Placeholder
                )
                events.append(event)
        
        return events
    
    def _calculate_timing_risk(
        self,
        pre_trades: List[Dict],
        event: CorporateEvent
    ) -> float:
        """Calculate risk score for timing pattern."""
        score = 0.3  # Base score for trades before event
        
        # More trades = higher risk
        if len(pre_trades) >= 10:
            score += 0.2
        elif len(pre_trades) >= 5:
            score += 0.1
        
        # Large total value = higher risk
        total_value = sum(t.get('total_value', 0) for t in pre_trades)
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
            trader_info = trade.get('trader_info', {})
            if isinstance(trader_info, dict) and trader_info.get('is_pep', [False])[0]:
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
                trades_by_symbol[trade['symbol']].append(trade)
            
            # Find coordinated patterns for each symbol
            for symbol, symbol_trades in trades_by_symbol.items():
                clusters = self._find_coordinated_clusters(symbol_trades)
                
                for cluster in clusters:
                    if len(cluster.unique_traders) >= 2:  # Multiple traders
                        risk_score = self._calculate_coordination_risk(cluster)
                        
                        if risk_score >= 0.6:
                            alert = InsiderTradingAlert(
                                alert_id=f"IT-COORD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                                alert_type='coordinated',
                                severity=self._calculate_severity(risk_score),
                                traders=list(cluster.unique_traders),
                                trades=[t.get('trade_id', '') for t in cluster.trades],
                                symbol=symbol,
                                total_value=cluster.total_value,
                                risk_score=risk_score,
                                indicators=[
                                    f"{len(cluster.unique_traders)} traders acting in {self.COORDINATION_TIME_WINDOW_HOURS}h window",
                                    f"Total volume: {cluster.total_volume:,} shares",
                                    f"Total value: ${cluster.total_value:,.2f}",
                                    f"Time window: {cluster.start_time} to {cluster.end_time}"
                                ],
                                timestamp=datetime.now(timezone.utc),
                                details={'cluster': {
                                    'trades': cluster.trades,
                                    'traders': list(cluster.unique_traders),
                                    'avg_price': cluster.avg_price
                                }}
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
        sorted_trades = sorted(trades, key=lambda t: t.get('trade_date', ''))
        
        if not sorted_trades:
            return clusters
        
        current_cluster_trades = [sorted_trades[0]]
        cluster_start = self._parse_date(sorted_trades[0].get('trade_date'))
        
        for trade in sorted_trades[1:]:
            trade_time = self._parse_date(trade.get('trade_date'))
            
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
        
        start_time = self._parse_date(trades[0].get('trade_date'))
        end_time = self._parse_date(trades[-1].get('trade_date'))
        
        if not start_time or not end_time:
            return None
        
        cluster = TradeCluster(
            trades=trades,
            symbol=trades[0].get('symbol', ''),
            start_time=start_time,
            end_time=end_time,
            total_volume=sum(t.get('quantity', 0) for t in trades),
            total_value=sum(t.get('total_value', 0) for t in trades),
            unique_traders=set(t.get('trader_id', '') for t in trades)
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
        sides = [t.get('side') for t in cluster.trades]
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
                trade_info = result.get('trade', {})
                comm_info = result.get('comm', {})
                trader_info = result.get('trader', {})
                
                # Check if communication contains suspicious content
                if self._is_suspicious_communication(comm_info, trade_info):
                    risk_score = self._calculate_communication_risk(comm_info, trade_info)
                    
                    if risk_score >= 0.6:
                        alert = InsiderTradingAlert(
                            alert_id=f"IT-COMM-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                            alert_type='communication',
                            severity=self._calculate_severity(risk_score),
                            traders=[trader_info.get('person_id', [''])[0]],
                            trades=[trade_info.get('trade_id', [''])[0]],
                            symbol=trade_info.get('symbol', [''])[0],
                            total_value=trade_info.get('total_value', [0])[0],
                            risk_score=risk_score,
                            indicators=[
                                "Suspicious communication preceding trade",
                                f"Communication type: {comm_info.get('communication_type', ['unknown'])[0]}",
                                f"Trade value: ${trade_info.get('total_value', [0])[0]:,.2f}",
                                "Potential MNPI sharing detected"
                            ],
                            timestamp=datetime.now(timezone.utc),
                            details={
                                'communication': comm_info,
                                'trade': trade_info,
                                'trader': trader_info
                            }
                        )
                        alerts.append(alert)
                        
        except Exception as e:
            logger.warning("Communication-based detection failed: %s", e)
        
        self.alerts.extend(alerts)
        logger.info("Found %s communication-based alerts", len(alerts))
        return alerts
    
    def _is_suspicious_communication(
        self,
        comm_info: Dict,
        trade_info: Dict
    ) -> bool:
        """Check if a communication is suspicious relative to a trade."""
        # Check if flagged as containing suspicious keywords
        if comm_info.get('contains_suspicious_keywords', [False])[0]:
            return True
        
        # Check content for MNPI keywords
        content = str(comm_info.get('content', '')).lower()
        mnpi_keywords = [
            'earnings', 'merger', 'acquisition', 'deal', 'announcement',
            'confidential', 'don\'t tell', 'keep quiet', 'between us',
            'inside', 'before it\'s public', 'non-public', 'material'
        ]
        
        for keyword in mnpi_keywords:
            if keyword in content:
                return True
        
        return False
    
    def _calculate_communication_risk(
        self,
        comm_info: Dict,
        trade_info: Dict
    ) -> float:
        """Calculate risk score for communication-trade relationship."""
        score = 0.4  # Base score for communication preceding trade
        
        # Flagged content = higher risk
        if comm_info.get('contains_suspicious_keywords', [False])[0]:
            score += 0.3
        
        # Large trade = higher risk
        trade_value = trade_info.get('total_value', [0])[0]
        if trade_value >= 200000:
            score += 0.2
        elif trade_value >= 100000:
            score += 0.1
        
        # Encrypted communication = potentially higher risk
        if comm_info.get('is_encrypted', [False])[0]:
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
                insider_id = result.get('insider', {}).get('person_id', [''])[0]
                contact_id = result.get('contact', {}).get('person_id', [''])[0]
                key = f"{insider_id}_{contact_id}"
                network_trades[key].append(result)
            
            # Analyze each network relationship
            for key, trades in network_trades.items():
                if len(trades) >= 2:  # Multiple trades through this relationship
                    risk_score = self._calculate_network_risk(trades)
                    
                    if risk_score >= 0.6:
                        total_value = sum(
                            t.get('trade', {}).get('total_value', [0])[0]
                            for t in trades
                        )
                        
                        insider_info = trades[0].get('insider', {})
                        contact_info = trades[0].get('contact', {})
                        
                        alert = InsiderTradingAlert(
                            alert_id=f"IT-NET-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                            alert_type='network',
                            severity=self._calculate_severity(risk_score),
                            traders=[contact_info.get('person_id', [''])[0]],
                            trades=[t.get('trade', {}).get('trade_id', [''])[0] for t in trades],
                            symbol=trades[0].get('trade', {}).get('symbol', [''])[0],
                            total_value=total_value,
                            risk_score=risk_score,
                            indicators=[
                                f"Trader connected to company insider",
                                f"Insider: {insider_info.get('full_name', ['Unknown'])[0]}",
                                f"Insider role: {insider_info.get('job_title', ['Unknown'])[0]}",
                                f"{len(trades)} trades through this connection"
                            ],
                            timestamp=datetime.now(timezone.utc),
                            details={
                                'insider': insider_info,
                                'contact': contact_info,
                                'trades': [t.get('trade', {}) for t in trades]
                            }
                        )
                        alerts.append(alert)
                        
        except Exception as e:
            logger.warning("Network-based detection failed: %s", e)
        
        self.alerts.extend(alerts)
        logger.info("Found %s network-based alerts", len(alerts))
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
        total_value = sum(t.get('trade', {}).get('total_value', [0])[0] for t in trades)
        if total_value >= 500000:
            score += 0.2
        elif total_value >= 200000:
            score += 0.1
        
        # Check if insider has high-level access
        insider_title = trades[0].get('insider', {}).get('job_title', [''])[0].lower()
        high_access_titles = ['ceo', 'cfo', 'cto', 'director', 'vp', 'executive']
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
                return datetime.fromisoformat(date_val.replace('Z', '+00:00'))
            except ValueError:
                pass
        return None
    
    def _find_trade_clusters(self, trades: List[Dict]) -> List[TradeCluster]:
        """Find clusters of trades based on time proximity."""
        return self._find_coordinated_clusters(trades)
    
    def _calculate_severity(self, risk_score: float) -> str:
        """Calculate alert severity from risk score."""
        if risk_score >= 0.85:
            return 'critical'
        elif risk_score >= 0.7:
            return 'high'
        elif risk_score >= 0.5:
            return 'medium'
        else:
            return 'low'
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive insider trading detection report."""
        return {
            'report_date': datetime.now(timezone.utc).isoformat(),
            'total_alerts': len(self.alerts),
            'alerts_by_type': {
                'timing': len([a for a in self.alerts if a.alert_type == 'timing']),
                'coordinated': len([a for a in self.alerts if a.alert_type == 'coordinated']),
                'communication': len([a for a in self.alerts if a.alert_type == 'communication']),
                'network': len([a for a in self.alerts if a.alert_type == 'network']),
                'volume': len([a for a in self.alerts if a.alert_type == 'volume']),
                'asymmetry': len([a for a in self.alerts if a.alert_type == 'asymmetry'])
            },
            'alerts_by_severity': {
                'critical': len([a for a in self.alerts if a.severity == 'critical']),
                'high': len([a for a in self.alerts if a.severity == 'high']),
                'medium': len([a for a in self.alerts if a.severity == 'medium']),
                'low': len([a for a in self.alerts if a.severity == 'low'])
            },
            'total_value_at_risk': sum(a.total_value for a in self.alerts),
            'unique_traders': len(set(t for a in self.alerts for t in a.traders)),
            'alerts': [
                {
                    'alert_id': a.alert_id,
                    'type': a.alert_type,
                    'severity': a.severity,
                    'risk_score': a.risk_score,
                    'traders': a.traders,
                    'symbol': a.symbol,
                    'total_value': a.total_value,
                    'indicators': a.indicators
                }
                for a in self.alerts
            ]
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
    print(f"\nAlerts by Type:")
    for alert_type, count in report['alerts_by_type'].items():
        print(f"  - {alert_type}: {count}")
    print(f"\nAlerts by Severity:")
    for severity, count in report['alerts_by_severity'].items():
        print(f"  - {severity}: {count}")
    print(f"\nTotal Value at Risk: ${report['total_value_at_risk']:,.2f}")
    print(f"Unique Traders Flagged: {report['unique_traders']}")
    print(f"{'='*80}\n")
    
    return report


if __name__ == "__main__":
    detect_insider_trading()
