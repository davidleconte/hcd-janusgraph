"""
Account Generator
=================

Generates realistic synthetic bank account entities with comprehensive attributes
including multi-currency support, ownership structures, and risk indicators.

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

import random
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any

from .base_generator import BaseGenerator
from ..utils.data_models import (
    Account, AccountType, RiskLevel
)
from ..utils.constants import (
    CURRENCIES, COUNTRIES
)
from ..utils.helpers import (
    random_choice_weighted, random_date_between,
    generate_account_number, generate_iban, generate_swift_code,
    random_amount, calculate_entity_risk_score
)


class AccountGenerator(BaseGenerator[Account]):
    """
    Generator for realistic bank account entities.
    
    Features:
    - Multi-currency accounts
    - Various account types
    - Ownership structures (single, joint, beneficial)
    - Realistic balances and transaction metrics
    - Risk assessment
    - Dormant account detection
    """
    
    def __init__(
        self,
        seed: Optional[int] = None,
        locale: str = "en_US",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize AccountGenerator.
        
        Args:
            seed: Random seed for reproducibility
            locale: Faker locale
            config: Configuration options:
                - dormant_probability: Probability of dormant account (default: 0.05)
                - monitored_probability: Probability of monitored account (default: 0.02)
                - joint_account_probability: Probability of joint account (default: 0.15)
                - min_balance: Minimum balance (default: 0)
                - max_balance: Maximum balance (default: 1000000)
        """
        super().__init__(seed, locale, config)
        
        # Configuration defaults
        self.dormant_probability = self.config.get('dormant_probability', 0.05)
        self.monitored_probability = self.config.get('monitored_probability', 0.02)
        self.joint_account_probability = self.config.get('joint_account_probability', 0.15)
        self.min_balance = Decimal(str(self.config.get('min_balance', 0)))
        self.max_balance = Decimal(str(self.config.get('max_balance', 1000000)))
    
    def generate(self, owner_id: Optional[str] = None, 
                owner_type: str = "person") -> Account:
        """
        Generate a single account entity.
        
        Args:
            owner_id: ID of the account owner (person or company)
            owner_type: Type of owner ("person" or "company")
            
        Returns:
            Account entity with all attributes
        """
        # Account identification
        account_number = generate_account_number()
        account_type = self._generate_account_type(owner_type)
        currency = self._generate_currency()
        
        # Bank information
        bank_name = self.faker.company() + " Bank"
        branch_name = self.faker.city() + " Branch"
        branch_code = self.faker.bothify(text="###")
        
        # International identifiers
        iban = generate_iban(self._get_country_from_currency(currency))
        swift_code = generate_swift_code(self._get_country_from_currency(currency))
        routing_number = self.faker.bothify(text="#########") if currency == "USD" else None
        
        # Ownership
        if not owner_id:
            owner_id = f"OWNER-{self.faker.uuid4()}"
        
        joint_owners = []
        if random.random() < self.joint_account_probability:
            num_joint = random.randint(1, 2)
            joint_owners = [f"JOINT-{self.faker.uuid4()}" for _ in range(num_joint)]
        
        beneficial_owners = []
        if owner_type == "company" and random.random() < 0.3:
            num_beneficial = random.randint(1, 3)
            beneficial_owners = [f"BENEFICIAL-{self.faker.uuid4()}" for _ in range(num_beneficial)]
        
        # Status
        opened_date = self._generate_opened_date()
        status = self._generate_status()
        closed_date = None
        if status == "closed":
            closed_date = opened_date + timedelta(days=random.randint(365, 3650))
        
        # Balances
        current_balance = self._generate_balance(account_type, status)
        available_balance = current_balance - random_amount(0, float(current_balance) * 0.1)
        credit_limit = self._generate_credit_limit(account_type)
        
        # Activity metrics
        transaction_count = self._generate_transaction_count(opened_date, status)
        total_deposits, total_withdrawals = self._generate_transaction_totals(
            transaction_count, current_balance
        )
        average_balance = self._calculate_average_balance(
            current_balance, total_deposits, total_withdrawals
        )
        
        # Risk & Compliance
        is_dormant = (status == "dormant") or (random.random() < self.dormant_probability)
        is_monitored = random.random() < self.monitored_probability
        monitoring_reason = self._generate_monitoring_reason() if is_monitored else None
        has_suspicious_activity = is_monitored and random.random() < 0.5
        
        risk_level = self._calculate_risk_level(
            is_monitored, has_suspicious_activity, is_dormant,
            current_balance, transaction_count
        )
        
        # KYC/AML verification
        kyc_verified = status != "frozen" and random.random() < 0.95
        aml_verified = status != "frozen" and random.random() < 0.90
        
        # Create Account entity
        account = Account(
            account_number=account_number,
            iban=iban,
            swift_code=swift_code,
            routing_number=routing_number,
            account_type=account_type,
            currency=currency,
            bank_name=bank_name,
            branch_name=branch_name,
            branch_code=branch_code,
            owner_id=owner_id,
            owner_type=owner_type,
            joint_owners=joint_owners,
            beneficial_owners=beneficial_owners,
            status=status,
            opened_date=opened_date,
            closed_date=closed_date,
            current_balance=current_balance,
            available_balance=available_balance,
            credit_limit=credit_limit,
            risk_level=risk_level,
            is_monitored=is_monitored,
            monitoring_reason=monitoring_reason,
            transaction_count=transaction_count,
            total_deposits=total_deposits,
            total_withdrawals=total_withdrawals,
            average_balance=average_balance,
            is_dormant=is_dormant,
            has_suspicious_activity=has_suspicious_activity,
            kyc_verified=kyc_verified,
            aml_verified=aml_verified
        )
        
        return account
    
    def _generate_account_type(self, owner_type: str) -> AccountType:
        """Generate account type based on owner type."""
        if owner_type == "company":
            choices = [
                (AccountType.BUSINESS, 0.70),
                (AccountType.CHECKING, 0.20),
                (AccountType.SAVINGS, 0.05),
                (AccountType.INVESTMENT, 0.05)
            ]
        else:
            choices = [
                (AccountType.CHECKING, 0.40),
                (AccountType.SAVINGS, 0.30),
                (AccountType.CREDIT_CARD, 0.15),
                (AccountType.INVESTMENT, 0.10),
                (AccountType.LOAN, 0.03),
                (AccountType.MORTGAGE, 0.02)
            ]
        return random_choice_weighted(choices)
    
    def _generate_currency(self) -> str:
        """Generate currency with weighted distribution."""
        major_currencies = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD"]
        if random.random() < 0.85:
            return random.choice(major_currencies)
        return random.choice(list(CURRENCIES.keys()))
    
    def _get_country_from_currency(self, currency: str) -> str:
        """Get country code from currency."""
        currency_country_map = {
            "USD": "US", "EUR": "DE", "GBP": "GB", "JPY": "JP",
            "CHF": "CH", "CAD": "CA", "AUD": "AU", "CNY": "CN",
            "INR": "IN", "SGD": "SG", "HKD": "HK"
        }
        return currency_country_map.get(currency, "US")
    
    def _generate_opened_date(self) -> date:
        """Generate account opening date."""
        # Accounts opened between 1990 and today
        start_date = date(1990, 1, 1)
        end_date = date.today()
        return random_date_between(start_date, end_date)
    
    def _generate_status(self) -> str:
        """Generate account status."""
        choices = [
            ("active", 0.85),
            ("dormant", 0.08),
            ("frozen", 0.02),
            ("closed", 0.05)
        ]
        return random_choice_weighted(choices)
    
    def _generate_balance(self, account_type: AccountType, status: str) -> Decimal:
        """Generate account balance based on type and status."""
        if status == "closed":
            return Decimal("0.00")
        
        if status == "dormant":
            # Dormant accounts typically have low balances
            return random_amount(0, 1000)
        
        # Balance ranges by account type
        balance_ranges = {
            AccountType.CHECKING: (100, 50000),
            AccountType.SAVINGS: (1000, 100000),
            AccountType.INVESTMENT: (5000, 500000),
            AccountType.BUSINESS: (10000, 1000000),
            AccountType.CREDIT_CARD: (0, 0),  # Credit cards show balance owed
            AccountType.LOAN: (0, 0),  # Loans show amount owed
            AccountType.MORTGAGE: (0, 0)  # Mortgages show amount owed
        }
        
        min_bal, max_bal = balance_ranges.get(account_type, (0, 10000))
        return random_amount(min_bal, max_bal)
    
    def _generate_credit_limit(self, account_type: AccountType) -> Optional[Decimal]:
        """Generate credit limit for applicable account types."""
        if account_type == AccountType.CREDIT_CARD:
            return random_amount(1000, 50000)
        elif account_type in [AccountType.LOAN, AccountType.MORTGAGE]:
            return random_amount(10000, 500000)
        return None
    
    def _generate_transaction_count(self, opened_date: date, status: str) -> int:
        """Generate transaction count based on account age and status."""
        if status == "closed":
            return 0
        
        days_open = (date.today() - opened_date).days
        
        if status == "dormant":
            # Dormant accounts have few transactions
            return random.randint(0, 10)
        
        # Average 2-10 transactions per month
        monthly_txns = random.randint(2, 10)
        months_open = max(1, days_open // 30)
        return monthly_txns * months_open
    
    def _generate_transaction_totals(self, transaction_count: int,
                                     current_balance: Decimal) -> tuple:
        """Generate total deposits and withdrawals."""
        if transaction_count == 0:
            return Decimal("0.00"), Decimal("0.00")
        
        # Estimate total deposits (should be > current balance)
        total_deposits = current_balance + random_amount(
            float(current_balance) * 0.5,
            float(current_balance) * 5.0
        )
        
        # Total withdrawals = deposits - current balance
        total_withdrawals = total_deposits - current_balance
        
        return total_deposits, total_withdrawals
    
    def _calculate_average_balance(self, current_balance: Decimal,
                                   total_deposits: Decimal,
                                   total_withdrawals: Decimal) -> Decimal:
        """Calculate average balance."""
        # Simple estimation: average of current and half of total deposits
        if total_deposits > Decimal("0"):
            return (current_balance + (total_deposits / Decimal("2"))) / Decimal("2")
        return current_balance
    
    def _generate_monitoring_reason(self) -> str:
        """Generate reason for account monitoring."""
        reasons = [
            "high_value_transactions",
            "unusual_activity_pattern",
            "multiple_currency_transactions",
            "high_risk_jurisdiction",
            "structuring_suspicion",
            "pep_related",
            "sanctions_screening",
            "fraud_alert"
        ]
        return random.choice(reasons)
    
    def _calculate_risk_level(self, is_monitored: bool, has_suspicious_activity: bool,
                             is_dormant: bool, current_balance: Decimal,
                             transaction_count: int) -> RiskLevel:
        """Calculate risk level."""
        score = 0.0
        
        if has_suspicious_activity:
            score += 0.4
        
        if is_monitored:
            score += 0.3
        
        if is_dormant:
            score += 0.1
        
        # High balance accounts
        if current_balance > Decimal("500000"):
            score += 0.2
        elif current_balance > Decimal("100000"):
            score += 0.1
        
        # High transaction volume
        if transaction_count > 1000:
            score += 0.1
        
        if score >= 0.7:
            return RiskLevel.CRITICAL
        elif score >= 0.5:
            return RiskLevel.HIGH
        elif score >= 0.3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW


__all__ = ['AccountGenerator']

