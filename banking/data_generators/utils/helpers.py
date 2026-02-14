"""
Helper Functions for Synthetic Data Generation
===============================================

Common utility functions for data generation, validation, and manipulation.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

import hashlib
import random
import string
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from .constants import (
    HIGH_RISK_COUNTRIES,
    ROUND_AMOUNTS,
    STRUCTURING_THRESHOLDS,
    SUSPICIOUS_KEYWORDS,
    TAX_HAVENS,
)

# ============================================================================
# RANDOM GENERATION HELPERS
# ============================================================================


def random_choice_weighted(choices: List[Tuple[Any, float]]) -> Any:
    """
    Select a random choice from weighted options.

    Args:
        choices: List of (value, weight) tuples

    Returns:
        Selected value
    """
    values, weights = zip(*choices)
    return random.choices(values, weights=weights, k=1)[0]


def random_date_between(start_date: date, end_date: date) -> date:
    """
    Generate a random date between two dates.

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        Random date
    """
    days_between = (end_date - start_date).days
    random_days = random.randint(0, days_between)
    return start_date + timedelta(days=random_days)


def random_datetime_between(start_dt: datetime, end_dt: datetime) -> datetime:
    """
    Generate a random datetime between two datetimes.

    Args:
        start_dt: Start datetime
        end_dt: End datetime

    Returns:
        Random datetime
    """
    delta = end_dt - start_dt
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start_dt + timedelta(seconds=random_seconds)


def random_business_hours_datetime(base_date: date, timezone: str = "America/New_York") -> datetime:
    """
    Generate a random datetime during business hours (9 AM - 5 PM).

    Args:
        base_date: Base date
        timezone: Timezone name

    Returns:
        Random datetime during business hours
    """
    hour = random.randint(9, 16)  # 9 AM to 4 PM
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return datetime.combine(base_date, datetime.min.time()).replace(
        hour=hour, minute=minute, second=second
    )


def random_amount(min_amount: float, max_amount: float, round_probability: float = 0.3) -> Decimal:
    """
    Generate a random amount with optional rounding to suspicious amounts.

    Args:
        min_amount: Minimum amount
        max_amount: Maximum amount
        round_probability: Probability of generating a round amount

    Returns:
        Random amount as Decimal
    """
    if random.random() < round_probability:
        # Generate a round amount
        valid_rounds = [r for r in ROUND_AMOUNTS if min_amount <= r <= max_amount]
        if valid_rounds:
            return Decimal(str(random.choice(valid_rounds)))

    # Generate a random amount
    amount = random.uniform(min_amount, max_amount)
    return Decimal(str(round(amount, 2)))


def random_just_below_threshold(country_code: str = "US", margin_percent: float = 0.05) -> Decimal:
    """
    Generate an amount just below the structuring threshold.

    Args:
        country_code: Country code for threshold lookup
        margin_percent: Percentage below threshold (0.05 = 5%)

    Returns:
        Amount just below threshold
    """
    threshold = STRUCTURING_THRESHOLDS.get(country_code, STRUCTURING_THRESHOLDS["US"])
    margin = threshold * margin_percent
    amount = threshold - random.uniform(0, margin)
    return Decimal(str(round(amount, 2)))


# ============================================================================
# IDENTIFICATION GENERATION
# ============================================================================


def generate_account_number(bank_code: str = "001", length: int = 12) -> str:
    """
    Generate a realistic account number.

    Args:
        bank_code: Bank identifier code
        length: Total length of account number

    Returns:
        Account number
    """
    remaining_length = length - len(bank_code)
    random_digits = "".join(random.choices(string.digits, k=remaining_length))
    return f"{bank_code}{random_digits}"


def generate_iban(country_code: str = "US") -> str:
    """
    Generate a realistic IBAN (International Bank Account Number).

    Args:
        country_code: ISO 3166-1 alpha-2 country code

    Returns:
        IBAN string
    """
    # Simplified IBAN generation
    check_digits = random.randint(10, 99)
    bank_code = "".join(random.choices(string.digits, k=4))
    account_number = "".join(random.choices(string.digits, k=10))
    return f"{country_code}{check_digits}{bank_code}{account_number}"


def generate_swift_code(country_code: str = "US") -> str:
    """
    Generate a realistic SWIFT/BIC code.

    Args:
        country_code: ISO 3166-1 alpha-2 country code

    Returns:
        SWIFT code
    """
    bank_code = "".join(random.choices(string.ascii_uppercase, k=4))
    location_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=2))
    branch_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
    return f"{bank_code}{country_code}{location_code}{branch_code}"


def generate_tax_id(country_code: str = "US") -> str:
    """
    Generate a realistic tax identification number.

    Args:
        country_code: ISO 3166-1 alpha-2 country code

    Returns:
        Tax ID
    """
    if country_code == "US":
        # SSN format: XXX-XX-XXXX
        return f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"
    elif country_code == "GB":
        # UK National Insurance Number
        prefix = "".join(random.choices(string.ascii_uppercase, k=2))
        digits = "".join(random.choices(string.digits, k=6))
        suffix = random.choice(string.ascii_uppercase)
        return f"{prefix}{digits}{suffix}"
    else:
        # Generic format
        return "".join(random.choices(string.digits, k=9))


def generate_lei_code() -> str:
    """
    Generate a realistic Legal Entity Identifier (LEI).

    Returns:
        20-character LEI code
    """
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=20))


def generate_stock_ticker(length: int = 4) -> str:
    """
    Generate a realistic stock ticker symbol.

    Args:
        length: Length of ticker (3-5 characters typical)

    Returns:
        Stock ticker
    """
    return "".join(random.choices(string.ascii_uppercase, k=length))


# ============================================================================
# VALIDATION HELPERS
# ============================================================================


def is_round_amount(amount: Decimal, tolerance: Decimal = Decimal("0.01")) -> bool:
    """
    Check if an amount is a round number.

    Args:
        amount: Amount to check
        tolerance: Tolerance for rounding

    Returns:
        True if round amount
    """
    for round_amt in ROUND_AMOUNTS:
        if abs(amount - Decimal(str(round_amt))) <= tolerance:
            return True
    return False


def is_just_below_threshold(
    amount: Decimal, country_code: str = "US", margin_percent: float = 0.1
) -> bool:
    """
    Check if amount is just below structuring threshold.

    Args:
        amount: Amount to check
        country_code: Country code for threshold
        margin_percent: Margin percentage (0.1 = 10%)

    Returns:
        True if just below threshold
    """
    threshold = STRUCTURING_THRESHOLDS.get(country_code, STRUCTURING_THRESHOLDS["US"])
    margin = Decimal(str(threshold * margin_percent))
    return Decimal(str(threshold)) - margin <= amount < Decimal(str(threshold))


def is_high_risk_country(country_code: str) -> bool:
    """
    Check if country is high-risk for AML/CFT.

    Args:
        country_code: ISO 3166-1 alpha-2 country code

    Returns:
        True if high-risk
    """
    return country_code in HIGH_RISK_COUNTRIES


def is_tax_haven(country_code: str) -> bool:
    """
    Check if country is a tax haven.

    Args:
        country_code: ISO 3166-1 alpha-2 country code

    Returns:
        True if tax haven
    """
    return country_code in TAX_HAVENS


def contains_suspicious_keywords(
    text: str, category: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """
    Check if text contains suspicious keywords.

    Args:
        text: Text to analyze
        category: Specific category to check (optional)

    Returns:
        Tuple of (has_keywords, list_of_found_keywords)
    """
    text_lower = text.lower()
    found_keywords = []

    categories_to_check = [category] if category else SUSPICIOUS_KEYWORDS.keys()

    for cat in categories_to_check:
        if cat in SUSPICIOUS_KEYWORDS:
            for keyword in SUSPICIOUS_KEYWORDS[cat]:
                if keyword.lower() in text_lower:
                    found_keywords.append(keyword)

    return len(found_keywords) > 0, found_keywords


# ============================================================================
# RISK SCORING HELPERS
# ============================================================================


def calculate_transaction_risk_score(
    amount: Decimal,
    currency: str,
    from_country: str,
    to_country: str,
    is_round: bool = False,
    is_below_threshold: bool = False,
    involves_tax_haven: bool = False,
) -> float:
    """
    Calculate risk score for a transaction (0-1 scale).

    Args:
        amount: Transaction amount
        currency: Currency code
        from_country: Originating country
        to_country: Destination country
        is_round: Whether amount is round
        is_below_threshold: Whether just below threshold
        involves_tax_haven: Whether involves tax haven

    Returns:
        Risk score (0-1)
    """
    score = 0.0

    # Base score from amount
    if amount > Decimal("100000"):
        score += 0.2
    elif amount > Decimal("50000"):
        score += 0.1

    # Round amount
    if is_round:
        score += 0.15

    # Just below threshold
    if is_below_threshold:
        score += 0.25

    # High-risk countries
    if is_high_risk_country(from_country):
        score += 0.2
    if is_high_risk_country(to_country):
        score += 0.2

    # Tax havens
    if involves_tax_haven:
        score += 0.15

    # Cross-border
    if from_country != to_country:
        score += 0.1

    return min(score, 1.0)


def calculate_entity_risk_score(
    is_pep: bool = False,
    is_sanctioned: bool = False,
    high_risk_country: bool = False,
    tax_haven_presence: bool = False,
    cash_intensive_business: bool = False,
    transaction_count: int = 0,
    suspicious_activity_count: int = 0,
) -> float:
    """
    Calculate risk score for an entity (0-1 scale).

    Args:
        is_pep: Politically Exposed Person
        is_sanctioned: On sanctions list
        high_risk_country: From high-risk country
        tax_haven_presence: Presence in tax havens
        cash_intensive_business: Cash-intensive business
        transaction_count: Number of transactions
        suspicious_activity_count: Number of suspicious activities

    Returns:
        Risk score (0-1)
    """
    score = 0.0

    # Critical factors
    if is_sanctioned:
        return 1.0  # Maximum risk

    if is_pep:
        score += 0.3

    # Geographic risk
    if high_risk_country:
        score += 0.2
    if tax_haven_presence:
        score += 0.15

    # Business risk
    if cash_intensive_business:
        score += 0.15

    # Activity-based risk
    if transaction_count > 1000:
        score += 0.1

    if suspicious_activity_count > 0:
        score += min(suspicious_activity_count * 0.1, 0.3)

    return min(score, 1.0)


# ============================================================================
# PATTERN DETECTION HELPERS
# ============================================================================


def detect_structuring_pattern(
    transactions: List[Dict[str, Any]], time_window_hours: int = 24
) -> bool:
    """
    Detect potential structuring pattern in transactions.

    Args:
        transactions: List of transaction dictionaries
        time_window_hours: Time window for pattern detection

    Returns:
        True if structuring pattern detected
    """
    if len(transactions) < 2:
        return False

    # Sort by timestamp
    sorted_txns = sorted(transactions, key=lambda x: x.get("timestamp", datetime.now()))

    # Check for multiple transactions just below threshold within time window
    suspicious_count = 0
    window_start = sorted_txns[0].get("timestamp", datetime.now())

    for txn in sorted_txns:
        txn_time = txn.get("timestamp", datetime.now())
        amount = txn.get("amount", Decimal("0"))

        # Reset window if beyond time limit
        if (txn_time - window_start).total_seconds() > time_window_hours * 3600:
            window_start = txn_time
            suspicious_count = 0

        # Check if just below threshold
        if is_just_below_threshold(amount):
            suspicious_count += 1

        # Pattern detected if 3+ suspicious transactions in window
        if suspicious_count >= 3:
            return True

    return False


def calculate_pattern_confidence(
    indicators: List[str], red_flags: List[str], total_value: Decimal, duration_days: int
) -> float:
    """
    Calculate confidence score for a detected pattern.

    Args:
        indicators: List of indicators present
        red_flags: List of red flags present
        total_value: Total value involved
        duration_days: Duration of pattern

    Returns:
        Confidence score (0-1)
    """
    score = 0.0

    # Indicator count
    score += min(len(indicators) * 0.1, 0.4)

    # Red flag count
    score += min(len(red_flags) * 0.15, 0.3)

    # Value-based
    if total_value > Decimal("1000000"):
        score += 0.2
    elif total_value > Decimal("100000"):
        score += 0.1

    # Duration-based
    if duration_days > 90:
        score += 0.1

    return min(score, 1.0)


# ============================================================================
# HASHING & ANONYMIZATION
# ============================================================================


def hash_pii(value: str, salt: str = "default_salt") -> str:
    """
    Hash personally identifiable information.

    Args:
        value: Value to hash
        salt: Salt for hashing

    Returns:
        Hashed value
    """
    salted = f"{salt}{value}".encode("utf-8")
    return hashlib.sha256(salted).hexdigest()


def anonymize_account_number(account_number: str, visible_digits: int = 4) -> str:
    """
    Anonymize account number showing only last N digits.

    Args:
        account_number: Full account number
        visible_digits: Number of digits to show

    Returns:
        Anonymized account number
    """
    if len(account_number) <= visible_digits:
        return account_number

    masked_length = len(account_number) - visible_digits
    return "*" * masked_length + account_number[-visible_digits:]


# ============================================================================
# EXPORT ALL HELPERS
# ============================================================================

__all__ = [
    "random_choice_weighted",
    "random_date_between",
    "random_datetime_between",
    "random_business_hours_datetime",
    "random_amount",
    "random_just_below_threshold",
    "generate_account_number",
    "generate_iban",
    "generate_swift_code",
    "generate_tax_id",
    "generate_lei_code",
    "generate_stock_ticker",
    "is_round_amount",
    "is_just_below_threshold",
    "is_high_risk_country",
    "is_tax_haven",
    "contains_suspicious_keywords",
    "calculate_transaction_risk_score",
    "calculate_entity_risk_score",
    "detect_structuring_pattern",
    "calculate_pattern_confidence",
    "hash_pii",
    "anonymize_account_number",
]
