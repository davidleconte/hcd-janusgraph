"""
Trade Generator for Banking Compliance Use Cases

Generates realistic stock, options, and futures trades with insider trading indicators,
market manipulation patterns, and timing analysis for compliance monitoring.

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..core.base_generator import BaseGenerator
from ..utils.constants import STOCK_EXCHANGES
from ..utils.data_models import Trade
from ..utils.helpers import generate_stock_ticker, random_choice_weighted, random_datetime_between


class TradeGenerator(BaseGenerator[Trade]):
    """
    Generates realistic trades with insider trading and market manipulation indicators.

    Features:
    - Multiple asset types: stocks, options, futures, bonds
    - Multi-exchange support (16 major exchanges)
    - Insider trading indicators (timing, volume, price movement)
    - Market manipulation patterns (pump-and-dump, spoofing, layering)
    - Pre-announcement trading detection
    - Unusual volume/price movement analysis
    - Beneficial ownership tracking

    Use Cases:
    - Insider trading detection
    - Market manipulation surveillance
    - Trade surveillance and monitoring
    - Regulatory compliance (SEC, FINRA, MiFID II)
    """

    def __init__(
        self,
        seed: Optional[int] = None,
        locale: str = "en_US",
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize TradeGenerator.

        Args:
            seed: Random seed for reproducibility
            locale: Faker locale
            config: Additional configuration options
        """
        super().__init__(seed, locale, config)

        # Asset type distribution
        self.asset_type_weights = {
            "stock": 0.60,  # 60% - most common
            "option": 0.20,  # 20% - derivatives
            "future": 0.10,  # 10% - commodities/indices
            "bond": 0.05,  # 5% - fixed income
            "etf": 0.05,  # 5% - exchange-traded funds
        }

        # Trade side distribution
        self.side_weights = {"buy": 0.50, "sell": 0.50}

        # Order type distribution
        self.order_type_weights = {"market": 0.40, "limit": 0.45, "stop": 0.10, "stop_limit": 0.05}

        # Insider trading probability (configurable)
        self.insider_probability = config.get("insider_probability", 0.02) if config else 0.02

    def generate(
        self,
        trader_id: Optional[str] = None,
        account_id: Optional[str] = None,
        asset_type: Optional[str] = None,
        exchange: Optional[str] = None,
        force_insider: bool = False,
    ) -> Trade:
        """
        Generate a single trade.

        Args:
            trader_id: ID of trader (person)
            account_id: ID of trading account
            asset_type: Type of asset (if None, randomly selected)
            exchange: Exchange code (if None, randomly selected)
            force_insider: Force insider trading indicators

        Returns:
            Trade object with all attributes
        """
        # Generate IDs if not provided
        if trader_id is None:
            trader_id = f"PER-{self.faker.uuid4()[:8]}"
        if account_id is None:
            account_id = f"ACC-{self.faker.uuid4()[:8]}"

        # Select asset type (ensure not None)
        if asset_type is None:
            asset_type = random_choice_weighted(list(self.asset_type_weights.items()))

        # Select exchange (ensure not None)
        if exchange is None:
            exchange = random.choice(list(STOCK_EXCHANGES.keys()))

        # Generate symbol based on asset type
        symbol = self._generate_symbol(asset_type, exchange)

        # Generate trade details
        side = random_choice_weighted(list(self.side_weights.items()))
        order_type = random_choice_weighted(list(self.order_type_weights.items()))

        # Generate quantity (realistic ranges by asset type)
        quantity = self._generate_quantity(asset_type)

        # Generate price
        price = self._generate_price(asset_type)

        # Calculate total value
        total_value = Decimal(str(quantity)) * price

        # Generate timestamp (within last 90 days)
        trade_date = random_datetime_between(
            datetime.now(timezone.utc) - timedelta(days=90), datetime.now(timezone.utc)
        )

        # Determine if insider trade
        is_insider = force_insider or random.random() < self.insider_probability

        # Generate insider trading indicators
        insider_indicators = []
        if is_insider:
            insider_indicators = self._generate_insider_indicators()

        # Calculate risk score
        risk_score = self._calculate_risk_score(
            asset_type, quantity, total_value, insider_indicators, trade_date
        )

        # Generate metadata
        metadata = self._generate_metadata(asset_type, exchange, order_type, is_insider)

        # Determine if flagged
        flagged_for_review = risk_score > 0.6 or len(insider_indicators) > 2

        return Trade(
            id=f"TRADE-{self.faker.uuid4()[:12]}",
            trader_id=trader_id,
            account_id=account_id,
            symbol=symbol,
            asset_type=asset_type,
            exchange=exchange,
            side=side,
            quantity=quantity,
            price=price,
            total_value=total_value,
            order_type=order_type,
            trade_date=trade_date,
            settlement_date=trade_date + timedelta(days=2),  # T+2 settlement
            currency=self._get_exchange_currency(exchange),
            insider_indicators=insider_indicators,
            risk_score=risk_score,
            flagged_for_review=flagged_for_review,
            metadata=metadata,
        )

    def _generate_symbol(self, asset_type: str, exchange: str) -> str:
        """Generate realistic symbol based on asset type."""
        if asset_type == "stock":
            return generate_stock_ticker()
        elif asset_type == "option":
            base = generate_stock_ticker()
            expiry = (datetime.now() + timedelta(days=random.randint(30, 365))).strftime("%y%m%d")
            strike = random.randint(50, 500)
            call_put = random.choice(["C", "P"])
            return f"{base}{expiry}{call_put}{strike:05d}"
        elif asset_type == "future":
            commodity = random.choice(["CL", "GC", "SI", "ES", "NQ", "ZB"])
            month = random.choice(["H", "M", "U", "Z"])  # Mar, Jun, Sep, Dec
            year = datetime.now().year % 100
            return f"{commodity}{month}{year}"
        elif asset_type == "bond":
            return f"US{random.randint(1, 30)}Y"
        else:  # ETF
            return random.choice(["SPY", "QQQ", "IWM", "DIA", "EEM", "GLD", "TLT"])

    def _generate_quantity(self, asset_type: str) -> int:
        """Generate realistic quantity based on asset type."""
        if asset_type == "stock":
            # Stocks: 1 to 100,000 shares
            return random.choice(
                [
                    random.randint(1, 100),  # Small retail: 70%
                    random.randint(100, 1000),  # Medium retail: 20%
                    random.randint(1000, 10000),  # Institutional: 8%
                    random.randint(10000, 100000),  # Large institutional: 2%
                ]
            )
        elif asset_type == "option":
            # Options: 1 to 1000 contracts
            return random.randint(1, 1000)
        elif asset_type == "future":
            # Futures: 1 to 500 contracts
            return random.randint(1, 500)
        elif asset_type == "bond":
            # Bonds: face value in thousands
            return random.randint(1, 10000) * 1000
        else:  # ETF
            return random.randint(1, 10000)

    def _generate_price(self, asset_type: str) -> Decimal:
        """Generate realistic price based on asset type."""
        if asset_type == "stock":
            price = random.uniform(1.0, 500.0)
        elif asset_type == "option":
            price = random.uniform(0.10, 50.0)
        elif asset_type == "future":
            price = random.uniform(10.0, 5000.0)
        elif asset_type == "bond":
            price = random.uniform(90.0, 110.0)  # Percentage of par
        else:  # ETF
            price = random.uniform(10.0, 500.0)

        return Decimal(str(round(price, 2)))

    def _generate_insider_indicators(self) -> List[str]:
        """Generate insider trading indicators."""
        indicators = []

        # Possible indicators
        all_indicators = [
            "pre_announcement_trading",
            "unusual_volume",
            "unusual_price_movement",
            "timing_suspicious",
            "beneficial_owner_trade",
            "executive_trade",
            "large_position_change",
            "coordinated_trading",
            "information_asymmetry",
            "pattern_recognition",
        ]

        # Select 1-4 indicators
        num_indicators = random.randint(1, 4)
        indicators = random.sample(all_indicators, num_indicators)

        return indicators

    def _calculate_risk_score(
        self,
        asset_type: str,
        quantity: int,
        total_value: Decimal,
        insider_indicators: List[str],
        trade_date: datetime,
    ) -> float:
        """Calculate trade risk score (0-1)."""
        score = 0.0

        # Insider indicators (major factor)
        if len(insider_indicators) > 0:
            score += 0.3
        if len(insider_indicators) > 2:
            score += 0.2

        # Large trade value
        if total_value > 1000000:
            score += 0.15
        if total_value > 10000000:
            score += 0.15

        # Options trading (higher risk)
        if asset_type == "option":
            score += 0.1

        # Off-hours trading
        hour = trade_date.hour
        if hour < 9 or hour > 16:  # Outside market hours
            score += 0.1

        return min(score, 1.0)

    def _generate_metadata(
        self, asset_type: str, exchange: str, order_type: str, is_insider: bool
    ) -> Dict[str, Any]:
        """Generate trade metadata."""
        metadata: Dict[str, Any] = {
            "exchange_name": STOCK_EXCHANGES.get(exchange, "Unknown"),
            "order_type": order_type,
            "execution_venue": random.choice(["exchange", "dark_pool", "otc"]),
            "broker_id": f"BRK-{self.faker.uuid4()[:8]}",
            "commission": round(random.uniform(0.0, 50.0), 2),
        }

        if is_insider:
            metadata["insider_relationship"] = random.choice(
                ["executive", "director", "beneficial_owner", "family_member"]
            )
            metadata["days_before_announcement"] = random.randint(1, 30)

        return metadata

    def _get_exchange_currency(self, exchange: str) -> str:
        """Get currency for exchange."""
        exchange_currencies = {
            "NYSE": "USD",
            "NASDAQ": "USD",
            "LSE": "GBP",
            "TSE": "JPY",
            "HKEX": "HKD",
            "SSE": "CNY",
            "SZSE": "CNY",
            "Euronext": "EUR",
            "TSX": "CAD",
            "ASX": "AUD",
            "BSE": "INR",
            "NSE": "INR",
            "BMV": "MXN",
            "B3": "BRL",
            "JSE": "ZAR",
            "KRX": "KRW",
        }
        return exchange_currencies.get(exchange, "USD")

    def generate_insider_trading_sequence(
        self,
        trader_id: str,
        account_id: str,
        symbol: str,
        trade_count: int = 5,
        days_before_announcement: int = 30,
    ) -> List[Trade]:
        """
        Generate a sequence of trades indicating insider trading pattern.

        Args:
            trader_id: ID of trader
            account_id: ID of account
            symbol: Stock symbol
            trade_count: Number of trades in sequence
            days_before_announcement: Days before public announcement

        Returns:
            List of Trade objects forming insider pattern
        """
        trades = []
        announcement_date = datetime.now(timezone.utc)

        for i in range(trade_count):
            # Trades get closer to announcement date
            days_before = days_before_announcement - (i * (days_before_announcement // trade_count))
            trade_date = announcement_date - timedelta(days=days_before)

            # Generate trade with insider indicators
            trade = self.generate(
                trader_id=trader_id, account_id=account_id, asset_type="stock", force_insider=True
            )

            # Override symbol and date
            trade.symbol = symbol
            trade.trade_date = trade_date
            trade.settlement_date = trade_date + timedelta(days=2)

            # Add specific insider metadata
            trade.metadata["days_before_announcement"] = days_before
            trade.metadata["sequence_position"] = i + 1
            trade.metadata["total_sequence_trades"] = trade_count

            trades.append(trade)

        return trades
