"""
Transaction Generator
=====================

Generates realistic synthetic financial transaction entities with comprehensive
attributes including multi-currency support, geographic routing, risk scoring,
and structuring pattern detection.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..core.base_generator import BaseGenerator
from ..utils.constants import COUNTRIES, CURRENCIES
from ..utils.data_models import Transaction, TransactionType
from ..utils.helpers import (
    calculate_transaction_risk_score,
    is_just_below_threshold,
    is_round_amount,
    random_amount,
    random_business_hours_datetime,
    random_choice_weighted,
    random_datetime_between,
    random_just_below_threshold,
)


class TransactionGenerator(BaseGenerator[Transaction]):
    """
    Generator for realistic financial transaction entities.

    Features:
    - Multi-currency transactions
    - Various transaction types (wire, ACH, POS, etc.)
    - Geographic routing
    - Risk scoring
    - Structuring patterns
    - Round amount detection
    - Cross-border transactions
    """

    def __init__(
        self,
        seed: Optional[int] = None,
        locale: str = "en_US",
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize TransactionGenerator.

        Args:
            seed: Random seed for reproducibility
            locale: Faker locale
            config: Configuration options:
                - suspicious_probability: Probability of suspicious transaction (default: 0.02)
                - structuring_probability: Probability of structuring (default: 0.01)
                - round_amount_probability: Probability of round amount (default: 0.3)
                - cross_border_probability: Probability of cross-border (default: 0.15)
                - min_amount: Minimum transaction amount (default: 10)
                - max_amount: Maximum transaction amount (default: 1000000)
        """
        super().__init__(seed, locale, config)

        # Configuration defaults
        self.suspicious_probability = self.config.get("suspicious_probability", 0.02)
        self.structuring_probability = self.config.get("structuring_probability", 0.01)
        self.round_amount_probability = self.config.get("round_amount_probability", 0.3)
        self.cross_border_probability = self.config.get("cross_border_probability", 0.15)
        self.min_amount = self.config.get("min_amount", 10)
        self.max_amount = self.config.get("max_amount", 1000000)

    def generate(
        self,
        from_account_id: Optional[str] = None,
        to_account_id: Optional[str] = None,
        transaction_type: Optional[TransactionType] = None,
        force_structuring: bool = False,
    ) -> Transaction:
        """
        Generate a single transaction entity.

        Args:
            from_account_id: Source account ID
            to_account_id: Destination account ID
            transaction_type: Specific transaction type (optional)
            force_structuring: Force structuring pattern

        Returns:
            Transaction entity with all attributes
        """
        # Transaction identification
        transaction_id = f"TXN-{self.faker.uuid4()[:12].upper()}"
        reference_number = self.faker.bothify(text="REF-##########")

        # Transaction type
        if not transaction_type:
            transaction_type = self._generate_transaction_type()

        # Dates
        transaction_date = self._generate_transaction_date()
        posting_date = transaction_date + timedelta(days=random.randint(0, 2))
        value_date = posting_date.date()

        # Accounts
        if not from_account_id:
            from_account_id = f"ACC-{self.faker.uuid4()}"
        if not to_account_id:
            to_account_id = f"ACC-{self.faker.uuid4()}"

        # Entities (optional)
        from_entity_id = f"ENT-{self.faker.uuid4()}" if random.random() < 0.8 else None
        to_entity_id = f"ENT-{self.faker.uuid4()}" if random.random() < 0.8 else None

        # Currency and amount
        currency = self._generate_currency()

        # Determine if structuring
        is_structuring = force_structuring or (random.random() < self.structuring_probability)

        if is_structuring:
            amount = random_just_below_threshold(self._get_country_from_currency(currency))
        else:
            amount = random_amount(
                self.min_amount, self.max_amount, round_probability=self.round_amount_probability
            )

        # Exchange rate for cross-currency
        exchange_rate = None
        amount_local = None
        currency_local = None
        if random.random() < 0.1:  # 10% have local currency conversion
            currency_local = random.choice(list(CURRENCIES.keys()))
            exchange_rate = Decimal(str(random.uniform(0.5, 2.0)))
            amount_local = amount * exchange_rate

        # Fees
        fee_amount = self._calculate_fee(amount, transaction_type)
        fee_currency = currency

        # Geographic information
        originating_country = self._generate_country()

        is_cross_border = random.random() < self.cross_border_probability
        if is_cross_border:
            destination_country = self._generate_country(exclude=originating_country)
        else:
            destination_country = originating_country

        transaction_location = self.faker.city()
        ip_address = self.faker.ipv4()

        # Description
        description = self._generate_description(transaction_type)
        merchant_name = self._generate_merchant_name(transaction_type)
        merchant_category = self._generate_merchant_category(transaction_type)

        # Status
        status = self._generate_status()

        # Risk assessment
        is_round = is_round_amount(amount)
        is_below_threshold = is_just_below_threshold(amount, originating_country)

        risk_score = calculate_transaction_risk_score(
            amount=amount,
            currency=currency,
            from_country=originating_country,
            to_country=destination_country,
            is_round=is_round,
            is_below_threshold=is_below_threshold,
            involves_tax_haven=(
                originating_country in self._get_tax_havens()
                or destination_country in self._get_tax_havens()
            ),
        )

        is_suspicious = risk_score > 0.5 or random.random() < self.suspicious_probability

        alert_ids = []
        if is_suspicious:
            num_alerts = random.randint(1, 3)
            alert_ids = [f"ALERT-{self.faker.uuid4()[:8].upper()}" for _ in range(num_alerts)]

        # Pattern detection
        is_part_of_pattern = is_suspicious and random.random() < 0.3
        pattern_id = f"PTN-{self.faker.uuid4()[:8].upper()}" if is_part_of_pattern else None
        pattern_type = self._generate_pattern_type() if is_part_of_pattern else None

        # Create Transaction entity
        transaction = Transaction(
            transaction_id=transaction_id,
            reference_number=reference_number,
            transaction_type=transaction_type,
            transaction_date=transaction_date,
            posting_date=posting_date,
            value_date=value_date,
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            from_entity_id=from_entity_id,
            to_entity_id=to_entity_id,
            amount=amount,
            currency=currency,
            exchange_rate=exchange_rate,
            amount_local=amount_local,
            currency_local=currency_local,
            fee_amount=fee_amount,
            fee_currency=fee_currency,
            originating_country=originating_country,
            destination_country=destination_country,
            transaction_location=transaction_location,
            ip_address=ip_address,
            description=description,
            merchant_name=merchant_name,
            merchant_category=merchant_category,
            status=status,
            risk_score=risk_score,
            is_suspicious=is_suspicious,
            alert_ids=alert_ids,
            is_structuring=is_structuring,
            is_round_amount=is_round,
            is_part_of_pattern=is_part_of_pattern,
            pattern_id=pattern_id,
            pattern_type=pattern_type,
        )

        return transaction

    def generate_structuring_sequence(
        self, from_account_id: str, count: int = 5, time_window_hours: int = 24
    ) -> List[Transaction]:
        """
        Generate a sequence of structuring transactions.

        Args:
            from_account_id: Source account ID
            count: Number of transactions in sequence
            time_window_hours: Time window for transactions

        Returns:
            List of structuring transactions
        """
        transactions = []
        base_time = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30))

        for i in range(count):
            # Spread transactions across time window
            offset_hours = random.uniform(0, time_window_hours)
            txn_time = base_time + timedelta(hours=offset_hours)

            # Generate structuring transaction
            txn = self.generate(from_account_id=from_account_id, force_structuring=True)

            # Override transaction date
            txn.transaction_date = txn_time
            txn.posting_date = txn_time + timedelta(hours=random.randint(1, 48))

            transactions.append(txn)

        return transactions

    def _generate_transaction_type(self) -> TransactionType:
        """Generate transaction type with realistic distribution."""
        choices = [
            (TransactionType.TRANSFER, 0.30),
            (TransactionType.PAYMENT, 0.25),
            (TransactionType.DEPOSIT, 0.15),
            (TransactionType.WITHDRAWAL, 0.10),
            (TransactionType.WIRE, 0.08),
            (TransactionType.ACH, 0.05),
            (TransactionType.POS, 0.03),
            (TransactionType.ATM, 0.02),
            (TransactionType.ONLINE, 0.01),
            (TransactionType.CHECK, 0.01),
        ]
        return random_choice_weighted(choices)

    def _generate_transaction_date(self) -> datetime:
        """Generate transaction date."""
        # Transactions in last 90 days
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=90)

        # 70% during business hours
        if random.random() < 0.7:
            date_only = random_datetime_between(start_date, end_date).date()
            return random_business_hours_datetime(date_only)
        else:
            return random_datetime_between(start_date, end_date)

    def _generate_currency(self) -> str:
        """Generate currency with weighted distribution."""
        major_currencies = ["USD", "EUR", "GBP", "JPY", "CHF"]
        if random.random() < 0.85:
            return random.choice(major_currencies)
        return random.choice(list(CURRENCIES.keys()))

    def _get_country_from_currency(self, currency: str) -> str:
        """Get country code from currency."""
        currency_country_map = {
            "USD": "US",
            "EUR": "DE",
            "GBP": "GB",
            "JPY": "JP",
            "CHF": "CH",
            "CAD": "CA",
            "AUD": "AU",
        }
        return currency_country_map.get(currency, "US")

    def _calculate_fee(self, amount: Decimal, txn_type: TransactionType) -> Decimal:
        """Calculate transaction fee."""
        # Fee percentages by transaction type
        fee_rates = {
            TransactionType.WIRE: 0.01,  # 1%
            TransactionType.TRANSFER: 0.005,  # 0.5%
            TransactionType.PAYMENT: 0.003,  # 0.3%
            TransactionType.ACH: 0.002,  # 0.2%
            TransactionType.POS: 0.025,  # 2.5%
            TransactionType.ATM: 0.02,  # 2%
        }

        rate = Decimal(str(fee_rates.get(txn_type, 0.005)))
        fee = amount * rate

        # Minimum fee
        min_fee = Decimal("1.00")
        return max(fee, min_fee)

    def _generate_country(self, exclude: Optional[str] = None) -> str:
        """Generate country code."""
        countries = list(COUNTRIES.keys())
        if exclude:
            countries = [c for c in countries if c != exclude]

        # Weight major countries
        major_countries = ["US", "GB", "DE", "FR", "JP", "CA", "AU"]
        if random.random() < 0.7:
            available_major = [c for c in major_countries if c != exclude]
            if available_major:
                return random.choice(available_major)

        return random.choice(countries)

    def _get_tax_havens(self) -> List[str]:
        """Get list of tax haven countries."""
        from ..utils.constants import TAX_HAVENS

        return TAX_HAVENS

    def _generate_description(self, txn_type: TransactionType) -> str:
        """Generate transaction description."""
        descriptions = {
            TransactionType.TRANSFER: "Account transfer",
            TransactionType.PAYMENT: "Payment for services",
            TransactionType.DEPOSIT: "Deposit",
            TransactionType.WITHDRAWAL: "Cash withdrawal",
            TransactionType.WIRE: "Wire transfer",
            TransactionType.ACH: "ACH transfer",
            TransactionType.POS: "Point of sale purchase",
            TransactionType.ATM: "ATM withdrawal",
            TransactionType.ONLINE: "Online payment",
            TransactionType.CHECK: "Check payment",
        }
        return descriptions.get(txn_type, "Transaction")

    def _generate_merchant_name(self, txn_type: TransactionType) -> Optional[str]:
        """Generate merchant name for applicable transaction types."""
        if txn_type in [TransactionType.POS, TransactionType.ONLINE, TransactionType.PAYMENT]:
            return self.faker.company()
        return None

    def _generate_merchant_category(self, txn_type: TransactionType) -> Optional[str]:
        """Generate merchant category."""
        if txn_type in [TransactionType.POS, TransactionType.ONLINE, TransactionType.PAYMENT]:
            categories = [
                "retail",
                "grocery",
                "restaurant",
                "gas_station",
                "hotel",
                "airline",
                "entertainment",
                "healthcare",
                "utilities",
                "insurance",
            ]
            return random.choice(categories)
        return None

    def _generate_status(self) -> str:
        """Generate transaction status."""
        choices = [("completed", 0.92), ("pending", 0.05), ("failed", 0.02), ("reversed", 0.01)]
        return random_choice_weighted(choices)

    def _generate_pattern_type(self) -> str:
        """Generate pattern type for suspicious transactions."""
        patterns = [
            "structuring",
            "layering",
            "rapid_movement",
            "circular",
            "smurfing",
            "cuckoo_smurfing",
            "trade_based",
            "round_tripping",
        ]
        return random.choice(patterns)


__all__ = ["TransactionGenerator"]
