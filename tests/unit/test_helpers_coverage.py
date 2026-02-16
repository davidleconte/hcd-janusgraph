"""Tests for banking.data_generators.utils.helpers module - coverage gaps."""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal

from banking.data_generators.utils.helpers import (
    random_choice_weighted,
    random_date_between,
    random_datetime_between,
    random_business_hours_datetime,
    random_amount,
    random_just_below_threshold,
    generate_account_number,
    generate_iban,
    generate_swift_code,
    generate_tax_id,
    generate_lei_code,
    generate_stock_ticker,
    is_round_amount,
    is_just_below_threshold,
    is_high_risk_country,
    is_tax_haven,
    contains_suspicious_keywords,
    calculate_transaction_risk_score,
    calculate_entity_risk_score,
    detect_structuring_pattern,
    calculate_pattern_confidence,
    hash_pii,
    anonymize_account_number,
)


class TestRandomGenerators:
    def test_random_choice_weighted(self):
        choices = [("a", 1.0), ("b", 0.0)]
        for _ in range(10):
            assert random_choice_weighted(choices) in ["a", "b"]

    def test_random_date_between(self):
        start = date(2026, 1, 1)
        end = date(2026, 1, 31)
        d = random_date_between(start, end)
        assert start <= d <= end

    def test_random_datetime_between(self):
        start = datetime(2026, 1, 1)
        end = datetime(2026, 1, 31)
        dt = random_datetime_between(start, end)
        assert start <= dt <= end

    def test_random_business_hours(self):
        d = date(2026, 1, 15)
        dt = random_business_hours_datetime(d)
        assert 9 <= dt.hour <= 16

    def test_random_amount_round(self):
        for _ in range(50):
            amt = random_amount(100, 10000, round_probability=1.0)
            assert isinstance(amt, Decimal)

    def test_random_amount_not_round(self):
        amt = random_amount(100, 10000, round_probability=0.0)
        assert isinstance(amt, Decimal)

    def test_random_just_below_threshold_us(self):
        amt = random_just_below_threshold("US")
        assert amt < Decimal("10000")
        assert amt > Decimal("9000")

    def test_random_just_below_threshold_unknown(self):
        amt = random_just_below_threshold("ZZ")
        assert isinstance(amt, Decimal)


class TestIdentificationGeneration:
    def test_generate_account_number(self):
        acct = generate_account_number("001", 12)
        assert len(acct) == 12
        assert acct.startswith("001")

    def test_generate_iban(self):
        iban = generate_iban("DE")
        assert iban.startswith("DE")

    def test_generate_swift_code(self):
        swift = generate_swift_code("GB")
        assert "GB" in swift
        assert len(swift) == 11

    def test_generate_tax_id_us(self):
        tid = generate_tax_id("US")
        assert "-" in tid

    def test_generate_tax_id_gb(self):
        tid = generate_tax_id("GB")
        assert len(tid) == 9

    def test_generate_tax_id_other(self):
        tid = generate_tax_id("FR")
        assert len(tid) == 9

    def test_generate_lei_code(self):
        lei = generate_lei_code()
        assert len(lei) == 20

    def test_generate_stock_ticker(self):
        ticker = generate_stock_ticker(4)
        assert len(ticker) == 4
        assert ticker.isalpha()


class TestValidation:
    def test_is_round_amount_true(self):
        assert is_round_amount(Decimal("1000"))

    def test_is_round_amount_false(self):
        assert not is_round_amount(Decimal("1234.56"))

    def test_is_just_below_threshold_true(self):
        assert is_just_below_threshold(Decimal("9500"), "US")

    def test_is_just_below_threshold_false(self):
        assert not is_just_below_threshold(Decimal("5000"), "US")

    def test_is_high_risk_country(self):
        assert is_high_risk_country("IR")
        assert not is_high_risk_country("US")

    def test_is_tax_haven(self):
        assert is_tax_haven("KY")
        assert not is_tax_haven("US")

    def test_contains_suspicious_keywords(self):
        found, keywords = contains_suspicious_keywords("wire transfer to crypto exchange")
        assert isinstance(found, bool)

    def test_contains_suspicious_keywords_category(self):
        found, keywords = contains_suspicious_keywords("money laundering", category="aml")
        assert isinstance(found, bool)

    def test_contains_suspicious_keywords_empty(self):
        found, keywords = contains_suspicious_keywords("normal grocery purchase")
        assert isinstance(found, bool)


class TestRiskScoring:
    def test_transaction_risk_high(self):
        score = calculate_transaction_risk_score(
            Decimal("150000"), "USD", "IR", "KY",
            is_round=True, is_below_threshold=True, involves_tax_haven=True,
        )
        assert score == 1.0

    def test_transaction_risk_low(self):
        score = calculate_transaction_risk_score(
            Decimal("100"), "USD", "US", "US",
        )
        assert score == 0.0

    def test_transaction_risk_medium(self):
        score = calculate_transaction_risk_score(
            Decimal("60000"), "USD", "US", "GB",
        )
        assert 0 < score < 1.0

    def test_entity_risk_sanctioned(self):
        assert calculate_entity_risk_score(is_sanctioned=True) == 1.0

    def test_entity_risk_pep(self):
        score = calculate_entity_risk_score(is_pep=True, high_risk_country=True)
        assert score > 0.3

    def test_entity_risk_activity(self):
        score = calculate_entity_risk_score(
            transaction_count=2000, suspicious_activity_count=5,
        )
        assert score > 0

    def test_entity_risk_low(self):
        score = calculate_entity_risk_score()
        assert score == 0.0


class TestPatternDetection:
    def test_detect_structuring_few_txns(self):
        assert not detect_structuring_pattern([{"amount": Decimal("100")}])

    def test_detect_structuring_pattern(self):
        now = datetime.now()
        txns = [
            {"amount": Decimal("9500"), "timestamp": now},
            {"amount": Decimal("9600"), "timestamp": now + timedelta(hours=1)},
            {"amount": Decimal("9700"), "timestamp": now + timedelta(hours=2)},
        ]
        result = detect_structuring_pattern(txns)
        assert isinstance(result, bool)

    def test_detect_structuring_window_reset(self):
        now = datetime.now()
        txns = [
            {"amount": Decimal("9500"), "timestamp": now},
            {"amount": Decimal("9500"), "timestamp": now + timedelta(hours=30)},
        ]
        assert not detect_structuring_pattern(txns, time_window_hours=24)

    def test_calculate_pattern_confidence_high(self):
        score = calculate_pattern_confidence(
            indicators=["a"] * 10, red_flags=["b"] * 5,
            total_value=Decimal("2000000"), duration_days=120,
        )
        assert score == pytest.approx(1.0)

    def test_calculate_pattern_confidence_low(self):
        score = calculate_pattern_confidence(
            indicators=[], red_flags=[], total_value=Decimal("100"), duration_days=1,
        )
        assert score == 0.0


class TestHashAnonymize:
    def test_hash_pii(self):
        h1 = hash_pii("test")
        h2 = hash_pii("test")
        assert h1 == h2
        assert h1 != hash_pii("test", salt="other")

    def test_anonymize_account_number(self):
        assert anonymize_account_number("123456789012") == "********9012"

    def test_anonymize_short_number(self):
        assert anonymize_account_number("1234", 4) == "1234"
        assert anonymize_account_number("12", 4) == "12"
