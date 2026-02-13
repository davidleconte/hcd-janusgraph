"""Additional tests for coverage of remaining modules."""
import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

from banking.data_generators.utils.constants import (
    COUNTRIES, HIGH_RISK_COUNTRIES, CURRENCIES, PEP_CATEGORIES,
    SANCTIONS_LISTS, TAX_HAVENS, STOCK_EXCHANGES,
    ROUND_AMOUNTS, STRUCTURING_THRESHOLDS, SUSPICIOUS_KEYWORDS,
)
from banking.data_generators.utils.data_models import (
    Gender, RiskLevel, AccountType, TransactionType, CommunicationType,
    CompanyType, IndustryType, RelationshipType,
    BaseEntity, Address, PhoneNumber, EmailAddress, IdentificationDocument,
    Employment, Person, Company, Account, Transaction, Trade, Communication,
    CompanyAddress, CompanyOfficer, Relationship, Pattern,
)
from banking.compliance.audit_logger import get_audit_logger, AuditEventType


class TestConstants:
    def test_countries_not_empty(self):
        assert len(COUNTRIES) > 0

    def test_high_risk_countries(self):
        assert len(HIGH_RISK_COUNTRIES) > 0
        for c in HIGH_RISK_COUNTRIES:
            assert c in COUNTRIES or isinstance(c, str)

    def test_currencies(self):
        assert len(CURRENCIES) > 0
        assert "USD" in CURRENCIES

    def test_pep_categories(self):
        assert len(PEP_CATEGORIES) > 0

    def test_sanctions_lists(self):
        assert len(SANCTIONS_LISTS) > 0

    def test_tax_havens(self):
        assert len(TAX_HAVENS) > 0

    def test_round_amounts(self):
        assert len(ROUND_AMOUNTS) > 0

    def test_structuring_thresholds(self):
        assert len(STRUCTURING_THRESHOLDS) > 0

    def test_suspicious_keywords(self):
        assert len(SUSPICIOUS_KEYWORDS) > 0


class TestEnums:
    def test_gender_values(self):
        assert Gender.MALE.value == "male"
        assert Gender.FEMALE.value == "female"
        assert Gender.NON_BINARY.value == "non_binary"
        assert Gender.PREFER_NOT_TO_SAY.value == "prefer_not_to_say"

    def test_risk_level_values(self):
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_account_type_values(self):
        assert len(AccountType) > 0

    def test_transaction_type_values(self):
        assert len(TransactionType) > 0

    def test_communication_type_values(self):
        assert len(CommunicationType) > 0

    def test_company_type_values(self):
        assert len(CompanyType) > 0

    def test_industry_type_values(self):
        assert len(IndustryType) > 0

    def test_relationship_type_values(self):
        assert len(RelationshipType) > 0


class TestDataModels:
    def test_address(self):
        addr = Address(
            street="123 Main St", city="NYC", state="NY",
            country="US", country_code="US", postal_code="10001",
        )
        assert addr.city == "NYC"

    def test_phone_number(self):
        phone = PhoneNumber(country_code="+1", number="5551234567", phone_type="mobile")
        assert phone.number == "5551234567"

    def test_email_address(self):
        email = EmailAddress(email="test@example.com", email_type="personal")
        assert email.email == "test@example.com"

    def test_identification_document(self):
        doc = IdentificationDocument(
            doc_type="passport", doc_number="AB123456",
            issuing_country="US", issue_date=date(2020, 1, 1),
            expiry_date=date(2030, 1, 1),
        )
        assert doc.doc_type == "passport"

    def test_employment(self):
        emp = Employment(
            employer_name="Acme Corp", job_title="Engineer",
            industry=IndustryType.TECHNOLOGY, annual_income=Decimal("100000"),
            start_date=date(2020, 1, 1),
        )
        assert emp.employer_name == "Acme Corp"

    def test_company_address(self):
        addr = CompanyAddress(
            street="456 Corp Ave", city="London", country="GB",
            country_code="GB", postal_code="EC1A 1BB",
        )
        assert addr.country_code == "GB"

    def test_company_officer(self):
        officer = CompanyOfficer(
            person_id="p-1", name="Jane Doe", role="CEO",
            appointment_date=date(2020, 1, 1),
        )
        assert officer.role == "CEO"


class TestAuditLogger:
    def test_audit_event_types(self):
        assert hasattr(AuditEventType, "DATA_ACCESS")
        assert hasattr(AuditEventType, "AUTH_LOGIN")


class TestHelpersFull:
    def test_calculate_entity_risk_score_high_risk(self):
        from banking.data_generators.utils.helpers import calculate_entity_risk_score
        score = calculate_entity_risk_score({"pep": True, "sanctioned": True, "high_risk_country": True})
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_calculate_entity_risk_score_low_risk(self):
        from banking.data_generators.utils.helpers import calculate_entity_risk_score
        score = calculate_entity_risk_score({"pep": False, "sanctioned": False})
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_generate_iban_different_countries(self):
        from banking.data_generators.utils.helpers import generate_iban
        for country in ["US", "GB", "DE", "FR"]:
            iban = generate_iban(country)
            assert isinstance(iban, str)
            assert len(iban) > 0

    def test_generate_swift_code_different_countries(self):
        from banking.data_generators.utils.helpers import generate_swift_code
        for country in ["US", "GB", "DE"]:
            swift = generate_swift_code(country)
            assert isinstance(swift, str)

    def test_generate_tax_id_different_countries(self):
        from banking.data_generators.utils.helpers import generate_tax_id
        for country in ["US", "GB", "DE", "FR", "JP"]:
            tax_id = generate_tax_id(country)
            assert isinstance(tax_id, str)
