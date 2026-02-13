"""Tests for banking.data_generators.core modules."""
import pytest
import random
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from banking.data_generators.core.base_generator import BaseGenerator
from banking.data_generators.core.person_generator import PersonGenerator
from banking.data_generators.core.company_generator import CompanyGenerator
from banking.data_generators.core.account_generator import AccountGenerator
from banking.data_generators.utils.data_models import Person, Company, Account, Gender, RiskLevel


class ConcreteGenerator(BaseGenerator[str]):
    def generate(self) -> str:
        return self.faker.name()


class TestBaseGenerator:
    def test_init_defaults(self):
        gen = ConcreteGenerator()
        assert gen.seed is None
        assert gen.locale == "en_US"
        assert gen.config == {}
        assert gen.generated_count == 0
        assert gen.error_count == 0

    def test_init_with_seed(self):
        gen = ConcreteGenerator(seed=42)
        assert gen.seed == 42

    def test_init_with_config(self):
        gen = ConcreteGenerator(config={"key": "val"})
        assert gen.config["key"] == "val"

    def test_generate_batch(self):
        gen = ConcreteGenerator(seed=42)
        results = gen.generate_batch(10)
        assert len(results) == 10
        assert gen.generated_count == 10
        assert gen.error_count == 0

    def test_generate_batch_with_progress(self):
        gen = ConcreteGenerator(seed=42)
        results = gen.generate_batch(200, show_progress=True)
        assert len(results) == 200

    def test_generate_batch_error_handling(self):
        gen = ConcreteGenerator(seed=42)
        original_generate = gen.generate
        call_count = 0
        def failing_generate():
            nonlocal call_count
            call_count += 1
            if call_count == 3:
                raise ValueError("test error")
            return original_generate()
        gen.generate = failing_generate
        results = gen.generate_batch(5)
        assert len(results) == 4
        assert gen.error_count == 1

    def test_generate_batch_raise_on_error(self):
        gen = ConcreteGenerator(seed=42, config={"raise_on_error": True})
        original_generate = gen.generate
        call_count = 0
        def failing_generate():
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise ValueError("test error")
            return original_generate()
        gen.generate = failing_generate
        with pytest.raises(ValueError, match="test error"):
            gen.generate_batch(5)

    def test_get_statistics(self):
        gen = ConcreteGenerator(seed=42)
        gen.generate_batch(5)
        stats = gen.get_statistics()
        assert stats["generated_count"] == 5
        assert stats["error_count"] == 0
        assert stats["seed"] == 42
        assert stats["locale"] == "en_US"
        assert stats["elapsed_time_seconds"] is not None
        assert stats["generation_rate_per_second"] is not None

    def test_get_statistics_no_start(self):
        gen = ConcreteGenerator(seed=42)
        stats = gen.get_statistics()
        assert stats["elapsed_time_seconds"] is None
        assert stats["generation_rate_per_second"] is None

    def test_reset_statistics(self):
        gen = ConcreteGenerator(seed=42)
        gen.generate_batch(5)
        gen.reset_statistics()
        assert gen.generated_count == 0
        assert gen.error_count == 0
        assert gen.start_time is None

    def test_set_seed(self):
        gen = ConcreteGenerator()
        gen.set_seed(99)
        assert gen.seed == 99

    def test_update_config(self):
        gen = ConcreteGenerator(config={"a": 1})
        gen.update_config({"b": 2})
        assert gen.config == {"a": 1, "b": 2}


class TestPersonGenerator:
    def test_generate_person(self):
        gen = PersonGenerator(seed=42)
        person = gen.generate()
        assert isinstance(person, Person)
        assert person.first_name
        assert person.last_name
        assert person.date_of_birth
        assert person.nationality
        assert isinstance(person.gender, Gender)
        assert isinstance(person.risk_level, RiskLevel)

    def test_generate_batch(self):
        gen = PersonGenerator(seed=42)
        persons = gen.generate_batch(5)
        assert len(persons) == 5
        assert all(isinstance(p, Person) for p in persons)

    def test_reproducibility(self):
        gen1 = PersonGenerator(seed=42)
        p1 = gen1.generate()
        assert p1.first_name is not None
        assert p1.last_name is not None

    def test_config_options(self):
        gen = PersonGenerator(seed=42, config={
            "pep_probability": 1.0,
            "sanctioned_probability": 0.0,
            "min_age": 25,
            "max_age": 30,
        })
        person = gen.generate()
        assert person.is_pep is True
        age_days = (date.today() - person.date_of_birth).days
        assert 25 * 365 - 1 <= age_days <= 30 * 365 + 1

    def test_high_sanctioned_probability(self):
        gen = PersonGenerator(seed=42, config={"sanctioned_probability": 1.0})
        person = gen.generate()
        assert person.is_sanctioned is True

    def test_addresses_generated(self):
        gen = PersonGenerator(seed=42)
        person = gen.generate()
        assert len(person.addresses) > 0

    def test_phone_numbers_generated(self):
        gen = PersonGenerator(seed=42)
        person = gen.generate()
        assert len(person.phone_numbers) > 0

    def test_email_addresses_generated(self):
        gen = PersonGenerator(seed=42)
        person = gen.generate()
        assert len(person.email_addresses) > 0

    def test_identification_documents_generated(self):
        gen = PersonGenerator(seed=42)
        person = gen.generate()
        assert len(person.identification_documents) > 0


class TestCompanyGenerator:
    def test_generate_company(self):
        gen = CompanyGenerator(seed=42)
        company = gen.generate()
        assert isinstance(company, Company)
        assert company.legal_name
        assert company.registration_country
        assert isinstance(company.risk_level, RiskLevel)

    def test_generate_batch(self):
        gen = CompanyGenerator(seed=42)
        companies = gen.generate_batch(5)
        assert len(companies) == 5

    def test_config_options(self):
        gen = CompanyGenerator(seed=42, config={
            "public_company_probability": 1.0,
            "shell_company_probability": 0.0,
        })
        company = gen.generate()
        assert company.is_public is True

    def test_shell_company(self):
        gen = CompanyGenerator(seed=42, config={"shell_company_probability": 1.0})
        company = gen.generate()
        assert company.is_shell_company is True


class TestAccountGenerator:
    def test_generate_account(self):
        gen = AccountGenerator(seed=42)
        account = gen.generate()
        assert isinstance(account, Account)
        assert account.account_number
        assert account.currency
        assert isinstance(account.current_balance, Decimal)

    def test_generate_with_owner(self):
        gen = AccountGenerator(seed=42)
        account = gen.generate(owner_id="p-123", owner_type="person")
        assert account.owner_id == "p-123"

    def test_generate_batch(self):
        gen = AccountGenerator(seed=42)
        accounts = gen.generate_batch(5)
        assert len(accounts) == 5

    def test_config_options(self):
        gen = AccountGenerator(seed=42, config={
            "dormant_probability": 1.0,
            "min_balance": 100,
            "max_balance": 200,
        })
        account = gen.generate()
        assert account.is_dormant is True
