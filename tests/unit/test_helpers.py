"""Tests for banking.data_generators.utils.helpers module."""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal

from banking.data_generators.utils.helpers import (
    random_choice_weighted,
    random_date_between,
    random_datetime_between,
    random_business_hours_datetime,
    random_amount,
    generate_account_number,
    generate_iban,
    generate_swift_code,
    generate_tax_id,
    generate_lei_code,
    generate_stock_ticker,
    calculate_entity_risk_score,
)


class TestRandomChoiceWeighted:
    def test_single_option(self):
        result = random_choice_weighted([("a", 1.0)])
        assert result == "a"

    def test_weighted_selection(self):
        results = set()
        for _ in range(100):
            results.add(random_choice_weighted([("a", 0.99), ("b", 0.01)]))
        assert "a" in results

    def test_returns_value(self):
        result = random_choice_weighted([(42, 0.5), (99, 0.5)])
        assert result in (42, 99)


class TestRandomDateBetween:
    def test_returns_date_in_range(self):
        start = date(2020, 1, 1)
        end = date(2020, 12, 31)
        result = random_date_between(start, end)
        assert start <= result <= end

    def test_same_date(self):
        d = date(2020, 6, 15)
        result = random_date_between(d, d)
        assert result == d


class TestRandomDatetimeBetween:
    def test_returns_datetime_in_range(self):
        start = datetime(2020, 1, 1)
        end = datetime(2020, 12, 31)
        result = random_datetime_between(start, end)
        assert start <= result <= end


class TestRandomBusinessHoursDatetime:
    def test_returns_business_hours(self):
        d = date(2020, 6, 15)
        result = random_business_hours_datetime(d)
        assert 9 <= result.hour <= 16


class TestRandomAmount:
    def test_returns_decimal(self):
        result = random_amount(100.0, 1000.0)
        assert isinstance(result, Decimal)

    def test_in_range(self):
        for _ in range(50):
            result = random_amount(100.0, 200.0, round_probability=0.0)
            assert Decimal("100") <= result <= Decimal("200")

    def test_round_probability(self):
        results = [random_amount(100.0, 10000.0, round_probability=1.0) for _ in range(10)]
        assert len(results) == 10


class TestGenerateAccountNumber:
    def test_returns_string(self):
        result = generate_account_number()
        assert isinstance(result, str)
        assert len(result) > 0


class TestGenerateIban:
    def test_returns_string(self):
        result = generate_iban("US")
        assert isinstance(result, str)
        assert len(result) > 0


class TestGenerateSwiftCode:
    def test_returns_string(self):
        result = generate_swift_code("US")
        assert isinstance(result, str)
        assert len(result) > 0


class TestGenerateTaxId:
    def test_returns_string(self):
        result = generate_tax_id("US")
        assert isinstance(result, str)
        assert len(result) > 0


class TestGenerateLeiCode:
    def test_returns_string(self):
        result = generate_lei_code()
        assert isinstance(result, str)
        assert len(result) == 20


class TestGenerateStockTicker:
    def test_returns_string(self):
        result = generate_stock_ticker(4)
        assert isinstance(result, str)
        assert len(result) == 4


class TestCalculateEntityRiskScore:
    def test_returns_float(self):
        factors = {"pep": True, "sanctioned": False}
        result = calculate_entity_risk_score(factors)
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0
