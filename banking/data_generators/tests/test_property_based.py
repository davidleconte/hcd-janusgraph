"""
Property-Based Tests for Data Generators
=========================================

Uses Hypothesis for property-based testing to verify invariants hold across
wide range of inputs. Tests verify that generators maintain consistency,
uniqueness, and validity constraints regardless of seed or configuration.

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-11
"""

import re
from datetime import datetime
from decimal import Decimal

from hypothesis import given, settings, strategies as st

from banking.data_generators.core import AccountGenerator, PersonGenerator
from banking.data_generators.events import TransactionGenerator


# ============================================================================
# Person Generator Property Tests (8 tests)
# ============================================================================


class TestPersonGeneratorProperties:
    """Property-based tests for PersonGenerator."""

    @given(seed=st.integers(min_value=0, max_value=1000000))
    @settings(max_examples=30)
    def test_person_generator_batch_consistency(self, seed: int) -> None:
        """Property: Batch generation produces consistent count and structure."""
        gen = PersonGenerator(seed=seed)
        batch_size = 10
        persons = gen.generate_batch(batch_size)
        
        # Verify batch size
        assert len(persons) == batch_size
        
        # Verify all persons have consistent structure
        for person in persons:
            assert person.first_name is not None
            assert person.last_name is not None
            assert len(person.email_addresses) > 0
            assert person.date_of_birth is not None

    @given(count=st.integers(min_value=1, max_value=100))
    @settings(max_examples=30)
    def test_person_generator_count(self, count: int) -> None:
        """Property: Generator produces exactly requested count."""
        gen = PersonGenerator(seed=42)
        persons = gen.generate_batch(count)
        assert len(persons) == count

    @given(seed=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=50)
    def test_person_ids_unique(self, seed: int) -> None:
        """Property: All person IDs are unique."""
        gen = PersonGenerator(seed=seed)
        persons = gen.generate_batch(100)
        ids = [p.person_id for p in persons]
        assert len(ids) == len(set(ids)), "Person IDs must be unique"

    @given(seed=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=50)
    def test_person_required_fields(self, seed: int) -> None:
        """Property: All persons have required fields."""
        gen = PersonGenerator(seed=seed)
        person = gen.generate()

        # Required fields must exist and not be None
        assert person.person_id is not None
        assert person.first_name is not None
        assert person.last_name is not None
        assert len(person.email_addresses) > 0
        assert len(person.phone_numbers) > 0
        assert person.date_of_birth is not None
        assert person.nationality is not None

    @given(seed=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=50)
    def test_person_email_format(self, seed: int) -> None:
        """Property: All emails are valid format."""
        gen = PersonGenerator(seed=seed)
        persons = gen.generate_batch(50)

        email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

        for person in persons:
            for email_obj in person.email_addresses:
                email = email_obj.email
                assert "@" in email, f"Email must contain @: {email}"
                assert "." in email.split("@")[1], f"Email domain must contain .: {email}"
                assert email_pattern.match(email), f"Email must match pattern: {email}"

    @given(seed=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=50)
    def test_person_risk_level_valid(self, seed: int) -> None:
        """Property: Risk levels are valid enum values."""
        gen = PersonGenerator(seed=seed)
        persons = gen.generate_batch(50)

        from banking.data_generators.utils.data_models import RiskLevel
        valid_levels = {RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL}

        for person in persons:
            assert person.risk_level in valid_levels, (
                f"Risk level must be valid: {person.risk_level}"
            )

    @given(seed=st.integers(min_value=0, max_value=10000), count=st.integers(min_value=10, max_value=100))
    @settings(max_examples=30)
    def test_person_generator_no_exceptions(self, seed: int, count: int) -> None:
        """Property: Generator never raises exceptions for valid inputs."""
        gen = PersonGenerator(seed=seed)
        persons = gen.generate_batch(count)
        assert len(persons) == count

    @given(seed=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=50)
    def test_person_data_types(self, seed: int) -> None:
        """Property: All fields have correct data types."""
        from datetime import date as date_type
        
        gen = PersonGenerator(seed=seed)
        person = gen.generate()

        assert isinstance(person.person_id, str)
        assert isinstance(person.first_name, str)
        assert isinstance(person.last_name, str)
        assert isinstance(person.date_of_birth, date_type)
        assert isinstance(person.nationality, str)
        assert isinstance(person.age, int)


# ============================================================================
# Account Generator Property Tests (6 tests)
# ============================================================================


class TestAccountGeneratorProperties:
    """Property-based tests for AccountGenerator."""

    @given(seed=st.integers(min_value=0, max_value=1000000))
    @settings(max_examples=30)
    def test_account_generator_batch_consistency(self, seed: int) -> None:
        """Property: Batch generation produces consistent count and structure."""
        gen = AccountGenerator(seed=seed)
        batch_size = 10
        accounts = gen.generate_batch(batch_size)
        
        # Verify batch size
        assert len(accounts) == batch_size
        
        # Verify all accounts have consistent structure
        for account in accounts:
            assert account.account_number is not None
            assert account.account_type is not None
            assert account.currency is not None

    @given(seed=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=50)
    def test_account_balance_non_negative(self, seed: int) -> None:
        """Property: Account balances are non-negative."""
        gen = AccountGenerator(seed=seed)
        accounts = gen.generate_batch(50)

        for account in accounts:
            assert account.current_balance >= 0, (
                f"Balance must be non-negative: {account.current_balance}"
            )

    @given(seed=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=50)
    def test_account_ids_unique(self, seed: int) -> None:
        """Property: All account IDs are unique."""
        gen = AccountGenerator(seed=seed)
        accounts = gen.generate_batch(100)
        ids = [a.id for a in accounts]
        assert len(ids) == len(set(ids)), "Account IDs must be unique"

    @given(seed=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=50)
    def test_account_required_fields(self, seed: int) -> None:
        """Property: All accounts have required fields."""
        gen = AccountGenerator(seed=seed)
        account = gen.generate()

        # Required fields must exist and not be None
        assert account.id is not None
        assert account.account_number is not None
        assert account.account_type is not None
        assert account.currency is not None
        assert account.current_balance is not None
        assert account.opened_date is not None

    @given(seed=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=50)
    def test_account_types_valid(self, seed: int) -> None:
        """Property: Account types are from valid set."""
        gen = AccountGenerator(seed=seed)
        accounts = gen.generate_batch(50)

        from banking.data_generators.utils.data_models import AccountType
        valid_types = {
            AccountType.CHECKING,
            AccountType.SAVINGS,
            AccountType.INVESTMENT,
            AccountType.BUSINESS,
            AccountType.CREDIT_CARD,
            AccountType.LOAN,
            AccountType.MORTGAGE,
        }

        for account in accounts:
            assert account.account_type in valid_types, (
                f"Account type must be valid: {account.account_type}"
            )

    @given(seed=st.integers(min_value=0, max_value=10000), count=st.integers(min_value=1, max_value=100))
    @settings(max_examples=30)
    def test_account_generator_no_exceptions(self, seed: int, count: int) -> None:
        """Property: Generator never raises exceptions."""
        gen = AccountGenerator(seed=seed)
        accounts = gen.generate_batch(count)
        assert len(accounts) == count


# ============================================================================
# Transaction Generator Property Tests (6 tests)
# ============================================================================


class TestTransactionGeneratorProperties:
    """Property-based tests for TransactionGenerator."""

    @given(seed=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=50)
    def test_transaction_amount_positive(self, seed: int) -> None:
        """Property: Transaction amounts are positive."""
        gen = TransactionGenerator(seed=seed)
        transactions = gen.generate_batch(50)

        for txn in transactions:
            assert txn.amount > 0, f"Transaction amount must be positive: {txn.amount}"

    @given(seed=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=50)
    def test_transaction_timestamps_valid(self, seed: int) -> None:
        """Property: Transactions have valid timestamps."""
        gen = TransactionGenerator(seed=seed)
        transactions = gen.generate_batch(50)

        for txn in transactions:
            assert txn.transaction_date is not None
            assert isinstance(txn.transaction_date, datetime)
            # Transaction date should be a valid datetime (can be past or future for testing)
            assert txn.transaction_date.year >= 2000
            assert txn.transaction_date.year <= 2030

    @given(seed=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=50)
    def test_transaction_ids_unique(self, seed: int) -> None:
        """Property: All transaction IDs are unique."""
        gen = TransactionGenerator(seed=seed)
        transactions = gen.generate_batch(100)
        ids = [t.transaction_id for t in transactions]
        assert len(ids) == len(set(ids)), "Transaction IDs must be unique"

    @given(seed=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=50)
    def test_transaction_required_fields(self, seed: int) -> None:
        """Property: All transactions have required fields."""
        gen = TransactionGenerator(seed=seed)
        transaction = gen.generate()

        required_fields = [
            "transaction_id",
            "from_account_id",
            "to_account_id",
            "amount",
            "currency",
            "transaction_date",
            "transaction_type",
        ]

        for field in required_fields:
            assert hasattr(transaction, field), f"Transaction must have field: {field}"
            assert getattr(transaction, field) is not None, f"Field must not be None: {field}"

    @given(seed=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=50)
    def test_transaction_accounts_different(self, seed: int) -> None:
        """Property: From and to accounts are different."""
        gen = TransactionGenerator(seed=seed)
        transactions = gen.generate_batch(50)

        for txn in transactions:
            assert txn.from_account_id != txn.to_account_id, (
                f"From and to accounts must be different: "
                f"{txn.from_account_id} vs {txn.to_account_id}"
            )

    @given(seed=st.integers(min_value=0, max_value=10000), count=st.integers(min_value=1, max_value=100))
    @settings(max_examples=30)
    def test_transaction_generator_no_exceptions(self, seed: int, count: int) -> None:
        """Property: Generator never raises exceptions."""
        gen = TransactionGenerator(seed=seed)
        transactions = gen.generate_batch(count)
        assert len(transactions) == count


# ============================================================================
# Cross-Generator Property Tests (3 tests)
# ============================================================================


class TestCrossGeneratorProperties:
    """Property-based tests across multiple generators."""

    @given(seed=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=20)
    def test_generators_produce_valid_entities(self, seed: int) -> None:
        """Property: All generators produce valid entities with required fields."""
        # Person generator
        person_gen = PersonGenerator(seed=seed)
        person = person_gen.generate()
        assert person.first_name is not None
        assert person.last_name is not None
        assert len(person.email_addresses) > 0

        # Account generator
        account_gen = AccountGenerator(seed=seed)
        account = account_gen.generate()
        assert account.account_number is not None
        assert account.account_type is not None

        # Transaction generator
        txn_gen = TransactionGenerator(seed=seed)
        txn = txn_gen.generate()
        assert txn.amount > 0
        assert txn.currency is not None

    @given(
        seed=st.integers(min_value=0, max_value=10000),
        person_count=st.integers(min_value=10, max_value=50),
        account_count=st.integers(min_value=10, max_value=50),
    )
    @settings(max_examples=20)
    def test_generators_produce_consistent_counts(
        self, seed: int, person_count: int, account_count: int
    ) -> None:
        """Property: Generators produce exactly requested counts."""
        person_gen = PersonGenerator(seed=seed)
        persons = person_gen.generate_batch(person_count)
        assert len(persons) == person_count

        account_gen = AccountGenerator(seed=seed)
        accounts = account_gen.generate_batch(account_count)
        assert len(accounts) == account_count

    @given(seed=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=30)
    def test_generators_maintain_data_integrity(self, seed: int) -> None:
        """Property: Generated data maintains referential integrity."""
        person_gen = PersonGenerator(seed=seed)
        person = person_gen.generate()

        # Person should have valid contact info
        assert len(person.email_addresses) > 0
        assert len(person.phone_numbers) > 0
        assert len(person.addresses) > 0

        # Account linked to person should be valid
        account_gen = AccountGenerator(seed=seed)
        account = account_gen.generate(owner_id=person.person_id)
        assert account.owner_id == person.person_id

        # Transaction between accounts should be valid
        account2 = account_gen.generate()
        txn_gen = TransactionGenerator(seed=seed)
        txn = txn_gen.generate(
            from_account_id=account.id, to_account_id=account2.id
        )
        assert txn.from_account_id == account.id
        assert txn.to_account_id == account2.id


# ============================================================================
# Configuration Property Tests (2 tests)
# ============================================================================


class TestConfigurationProperties:
    """Property-based tests for generator configuration."""

    @given(seed=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=30)
    def test_account_has_valid_balance_range(self, seed: int) -> None:
        """Property: Account balances are within reasonable range."""
        gen = AccountGenerator(seed=seed)
        accounts = gen.generate_batch(50)

        for account in accounts:
            # Balances should be reasonable (not negative, not absurdly large)
            assert account.current_balance >= 0
            assert account.current_balance <= Decimal("10000000")  # 10 million max
            assert account.available_balance >= 0
            assert account.available_balance <= account.current_balance

    @given(seed=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=30)
    def test_transaction_has_valid_amount_range(self, seed: int) -> None:
        """Property: Transaction amounts are within reasonable range."""
        gen = TransactionGenerator(seed=seed)
        transactions = gen.generate_batch(50)

        for txn in transactions:
            # Amounts should be reasonable (positive, not absurdly large)
            assert txn.amount > 0
            assert txn.amount <= Decimal("10000000")  # 10 million max
            assert txn.fee_amount >= 0
            assert txn.fee_amount < txn.amount  # Fee should be less than amount

# Made with Bob
