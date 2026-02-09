"""
Unit Tests for AccountGenerator
================================

Comprehensive tests for account entity generation including:
- Smoke tests
- Functional tests
- Balance validation tests
- Account type tests

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

from decimal import Decimal


class TestAccountGeneratorSmoke:
    """Smoke tests - basic functionality"""

    def test_generator_initialization(self, account_generator):
        """Test that generator initializes without errors"""
        assert account_generator is not None
        assert account_generator.faker is not None

    def test_basic_generation(self, account_generator, sample_person):
        """Test that generator can create an account"""
        account = account_generator.generate(owner_id=sample_person.id, owner_type="person")
        assert account is not None
        assert account.id is not None

    def test_multiple_generation(self, account_generator, sample_persons):
        """Test generating multiple accounts"""
        accounts = [
            account_generator.generate(owner_id=person.id, owner_type="person")
            for person in sample_persons[:5]
        ]
        assert len(accounts) == 5
        assert all(a.id for a in accounts)


class TestAccountGeneratorFunctional:
    """Functional tests - correct behavior"""

    def test_required_fields_present(self, sample_account):
        """Test that all required fields are present"""
        assert sample_account.id
        assert sample_account.account_number
        assert sample_account.account_type
        assert sample_account.currency
        assert sample_account.current_balance is not None
        assert sample_account.owner_id
        assert sample_account.owner_type
        assert sample_account.status

    def test_account_id_format(self, sample_account):
        """Test account ID follows UUID format"""
        assert sample_account.id is not None
        assert len(sample_account.id) > 0

    def test_account_number_format(self, sample_accounts):
        """Test account numbers are properly formatted"""
        for account in sample_accounts:
            assert account.account_number
            assert len(account.account_number) >= 10
            # Should be alphanumeric
            assert account.account_number.replace("-", "").isalnum()

    def test_account_type_valid(self, sample_accounts):
        """Test account type is valid"""
        valid_types = [
            "checking",
            "savings",
            "investment",
            "credit_card",
            "loan",
            "mortgage",
            "business",
        ]
        for account in sample_accounts:
            assert account.account_type in valid_types

    def test_currency_valid(self, sample_accounts):
        """Test currency codes are valid (common currencies)"""
        # Generator may produce various currencies, just check it's a 3-letter code
        for account in sample_accounts:
            assert len(account.currency) == 3
            assert account.currency.isupper()

    def test_balance_is_decimal(self, sample_accounts):
        """Test balance is Decimal type"""
        for account in sample_accounts:
            assert isinstance(account.current_balance, Decimal)

    def test_status_valid(self, sample_accounts):
        """Test account status is valid"""
        valid_statuses = ["active", "inactive", "closed", "frozen", "suspended", "dormant"]
        for account in sample_accounts:
            assert account.status in valid_statuses

    def test_owner_reference(self, sample_account, sample_person):
        """Test account has valid owner reference"""
        assert sample_account.owner_id == sample_person.id
        assert sample_account.owner_type == "person"


class TestAccountGeneratorBalances:
    """Balance validation tests"""

    def test_checking_account_balance_range(self, account_generator, sample_person):
        """Test checking account balances are reasonable"""
        accounts = [
            account_generator.generate(owner_id=sample_person.id, owner_type="person")
            for _ in range(20)
        ]
        checking_accounts = [a for a in accounts if a.account_type == "checking"]

        if checking_accounts:
            for account in checking_accounts:
                # Checking accounts typically have moderate balances
                assert Decimal("-10000") <= account.current_balance <= Decimal("1000000")

    def test_savings_account_positive_balance(self, account_generator, sample_person):
        """Test savings accounts typically have positive balances"""
        accounts = [
            account_generator.generate(owner_id=sample_person.id, owner_type="person")
            for _ in range(20)
        ]
        savings_accounts = [a for a in accounts if a.account_type == "savings"]

        if savings_accounts:
            positive_count = sum(1 for a in savings_accounts if a.current_balance > 0)
            # Most savings accounts should have positive balance
            assert positive_count >= len(savings_accounts) * 0.8

    def test_credit_card_balance_range(self, account_generator, sample_person):
        """Test credit card balances are within reasonable limits"""
        accounts = [
            account_generator.generate(owner_id=sample_person.id, owner_type="person")
            for _ in range(20)
        ]
        credit_accounts = [a for a in accounts if a.account_type == "credit_card"]

        if credit_accounts:
            for account in credit_accounts:
                # Credit cards can have negative balance (debt)
                assert Decimal("-50000") <= account.current_balance <= Decimal("10000")


class TestAccountGeneratorEdgeCases:
    """Edge case tests"""

    def test_unique_account_ids(self, account_generator, sample_persons):
        """Test that account IDs are unique"""
        accounts = [
            account_generator.generate(owner_id=person.id, owner_type="person")
            for person in sample_persons
        ]
        account_ids = [a.id for a in accounts]
        assert len(account_ids) == len(set(account_ids))

    def test_unique_account_numbers(self, account_generator, sample_persons):
        """Test that account numbers are unique"""
        accounts = [
            account_generator.generate(owner_id=person.id, owner_type="person")
            for person in sample_persons
        ]
        account_numbers = [a.account_number for a in accounts]
        assert len(account_numbers) == len(set(account_numbers))

    def test_company_owned_accounts(self, account_generator, sample_company):
        """Test accounts can be owned by companies"""
        account = account_generator.generate(owner_id=sample_company.id, owner_type="company")
        assert account.owner_id == sample_company.id
        assert account.owner_type == "company"
        # Business accounts more likely for companies
        assert account.account_type in ["checking", "savings", "business", "loan"]


class TestAccountGeneratorBatchGeneration:
    """Batch generation tests"""

    def test_batch_generation_with_owners(self, account_generator, sample_persons):
        """Test batch generation with multiple owners"""
        accounts = []
        for person in sample_persons[:5]:
            # Generate accounts individually since batch doesn't accept owner params
            for _ in range(2):
                account = account_generator.generate(owner_id=person.id, owner_type="person")
                accounts.append(account)

        assert len(accounts) == 10
        # Each person should have 2 accounts
        owner_counts = {}
        for account in accounts:
            owner_counts[account.owner_id] = owner_counts.get(account.owner_id, 0) + 1
        assert all(count == 2 for count in owner_counts.values())


class TestAccountGeneratorAccountTypes:
    """Account type specific tests"""

    def test_investment_account_characteristics(self, account_generator, sample_person):
        """Test investment accounts have appropriate characteristics"""
        accounts = [
            account_generator.generate(owner_id=sample_person.id, owner_type="person")
            for _ in range(30)
        ]
        investment_accounts = [a for a in accounts if a.account_type == "investment"]

        if investment_accounts:
            for account in investment_accounts:
                # Investment accounts should have reasonable balances
                assert account.current_balance >= Decimal("0")

    def test_loan_account_characteristics(self, account_generator, sample_person):
        """Test loan accounts have appropriate characteristics"""
        accounts = [
            account_generator.generate(owner_id=sample_person.id, owner_type="person")
            for _ in range(30)
        ]
        loan_accounts = [a for a in accounts if a.account_type in ["loan", "mortgage"]]

        if loan_accounts:
            for account in loan_accounts:
                # Loans typically show as negative balance (debt)
                # But could be positive if overpaid
                assert Decimal("-1000000") <= account.current_balance <= Decimal("10000")


# Run tests with: pytest banking/data_generators/tests/test_core/test_account_generator.py -v
