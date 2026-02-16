"""Tests for banking.data_generators.patterns.cato_pattern_generator module."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from banking.data_generators.patterns.cato_pattern_generator import CATOPatternGenerator
from banking.data_generators.utils.data_models import RiskLevel


@pytest.fixture
def gen():
    return CATOPatternGenerator(seed=42)


class TestInit:
    def test_init(self, gen):
        assert gen.person_gen is not None
        assert gen.account_gen is not None
        assert gen.transaction_gen is not None
        assert gen.communication_gen is not None

    def test_init_with_seed(self):
        g = CATOPatternGenerator(seed=123)
        assert g is not None


class TestGenerate:
    def test_credential_stuffing(self, gen):
        pattern = gen.generate(pattern_type="credential_stuffing", victim_count=3, attacker_count=1, duration_days=3)
        assert pattern.pattern_type == "account_takeover"
        assert pattern.detection_method == "coordinated_account_takeover_detection"
        assert len(pattern.indicators) > 0

    def test_session_hijacking(self, gen):
        pattern = gen.generate(pattern_type="session_hijacking", victim_count=2, attacker_count=1)
        assert pattern.detection_method == "session_hijacking_detection"
        assert len(pattern.indicators) > 0

    def test_sim_swap(self, gen):
        pattern = gen.generate(pattern_type="sim_swap", victim_count=2, attacker_count=1)
        assert pattern.detection_method == "sim_swap_detection"
        assert len(pattern.indicators) > 0

    def test_phishing_campaign(self, gen):
        pattern = gen.generate(pattern_type="phishing_campaign", victim_count=5, attacker_count=1)
        assert pattern.detection_method == "phishing_campaign_detection"
        assert len(pattern.indicators) > 0

    def test_malware_based(self, gen):
        pattern = gen.generate(pattern_type="malware_based", victim_count=3, attacker_count=1)
        assert pattern.detection_method == "malware_based_detection"
        assert len(pattern.indicators) > 0

    def test_unknown_type(self, gen):
        with pytest.raises(ValueError, match="Unknown CATO pattern type"):
            gen.generate(pattern_type="unknown")

    def test_with_start_date(self, gen):
        start = datetime(2026, 1, 1)
        pattern = gen.generate(start_date=start, victim_count=2, attacker_count=1)
        assert pattern.start_date == start

    def test_without_start_date(self, gen):
        pattern = gen.generate(victim_count=2, attacker_count=1)
        assert pattern.start_date is not None


class TestCredentialStuffing:
    def test_phases(self, gen):
        start = datetime(2026, 1, 1)
        end = start + timedelta(days=7)
        pattern = gen._generate_credential_stuffing(5, 2, start, end)
        assert "Phishing emails sent to all victims" in pattern.indicators
        assert pattern.metadata["attack_type"] == "credential_stuffing"
        assert pattern.metadata["victim_count"] == 5

    def test_high_failed_attempts(self, gen):
        start = datetime(2026, 1, 1)
        end = start + timedelta(days=7)
        pattern = gen._generate_credential_stuffing(15, 2, start, end)
        assert any("High volume" in f for f in pattern.red_flags)


class TestSessionHijacking:
    def test_session_hijacking(self, gen):
        start = datetime(2026, 1, 1)
        end = start + timedelta(days=7)
        pattern = gen._generate_session_hijacking(3, 1, start, end)
        assert pattern.metadata["attack_type"] == "session_hijacking"
        assert any("IP changed" in i or "session" in i.lower() for i in pattern.indicators)


class TestSimSwap:
    def test_sim_swap(self, gen):
        start = datetime(2026, 1, 1)
        end = start + timedelta(days=7)
        pattern = gen._generate_sim_swap(3, 2, start, end)
        assert pattern.metadata["attack_type"] == "sim_swap"
        assert any("SIM" in i for i in pattern.indicators)


class TestPhishingCampaign:
    def test_phishing(self, gen):
        start = datetime(2026, 1, 1)
        end = start + timedelta(days=7)
        pattern = gen._generate_phishing_campaign(10, 1, start, end)
        assert pattern.metadata["attack_type"] == "phishing_campaign"
        assert pattern.metadata["compromised_count"] >= 1


class TestMalwareBased:
    def test_malware(self, gen):
        start = datetime(2026, 1, 1)
        end = start + timedelta(days=7)
        pattern = gen._generate_malware_based(3, 1, start, end)
        assert pattern.metadata["attack_type"] == "malware_based"
        assert pattern.metadata["malware_type"] == "banking_trojan"


class TestConfidenceScore:
    def test_high_indicators(self, gen):
        score = gen._calculate_confidence_score(25, 12, 12, 150)
        assert score == 1.0

    def test_medium_indicators(self, gen):
        score = gen._calculate_confidence_score(15, 7, 7, 60)
        assert 0.5 < score < 1.0

    def test_low_indicators(self, gen):
        score = gen._calculate_confidence_score(3, 2, 2, 0)
        assert score < 0.5

    def test_no_failed_attempts(self, gen):
        score = gen._calculate_confidence_score(5, 3, 3, 0)
        assert score > 0

    def test_some_failed_attempts(self, gen):
        score = gen._calculate_confidence_score(5, 3, 3, 30)
        assert score > 0


class TestSeverityScore:
    def test_high_value(self, gen):
        score = gen._calculate_severity_score(0.8, Decimal("150000"), 12, 25)
        assert score >= 0.8

    def test_medium_value(self, gen):
        score = gen._calculate_severity_score(0.5, Decimal("60000"), 7, 10)
        assert 0.3 < score < 0.9

    def test_low_value(self, gen):
        score = gen._calculate_severity_score(0.3, Decimal("1000"), 2, 5)
        assert score < 0.5


class TestRiskLevel:
    def test_critical(self, gen):
        assert gen._determine_risk_level(0.9) == RiskLevel.CRITICAL

    def test_high(self, gen):
        assert gen._determine_risk_level(0.7) == RiskLevel.HIGH

    def test_medium(self, gen):
        assert gen._determine_risk_level(0.5) == RiskLevel.MEDIUM

    def test_low(self, gen):
        assert gen._determine_risk_level(0.2) == RiskLevel.LOW


class TestIPGeneration:
    def test_generates_valid_ip(self, gen):
        ip = gen._generate_ip_address()
        parts = ip.split(".")
        assert len(parts) == 4
        assert all(0 <= int(p) <= 255 for p in parts)

    def test_avoids_private(self, gen):
        for _ in range(100):
            ip = gen._generate_ip_address()
            parts = [int(p) for p in ip.split(".")]
            assert parts[0] != 10
            assert parts[0] != 127
            assert not (parts[0] == 172 and 16 <= parts[1] <= 31)
            assert not (parts[0] == 192 and parts[1] == 168)


class TestGenerateId:
    def test_id_format(self, gen):
        id_ = gen._generate_id()
        assert len(id_) == 6
        assert id_.isdigit()
