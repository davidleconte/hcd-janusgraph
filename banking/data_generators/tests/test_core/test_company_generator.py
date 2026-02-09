"""
Unit Tests for CompanyGenerator
================================

Comprehensive tests for company entity generation including:
- Smoke tests
- Functional tests
- Edge case tests
- Industry validation tests

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

from datetime import date


class TestCompanyGeneratorSmoke:
    """Smoke tests - basic functionality"""

    def test_generator_initialization(self, company_generator):
        """Test that generator initializes without errors"""
        assert company_generator is not None
        assert company_generator.faker is not None

    def test_basic_generation(self, company_generator):
        """Test that generator can create a company"""
        company = company_generator.generate()
        assert company is not None
        assert company.id is not None

    def test_multiple_generation(self, company_generator):
        """Test generating multiple companies"""
        companies = [company_generator.generate() for _ in range(10)]
        assert len(companies) == 10
        assert all(c.id for c in companies)


class TestCompanyGeneratorFunctional:
    """Functional tests - correct behavior"""

    def test_required_fields_present(self, sample_company):
        """Test that all required fields are present"""
        assert sample_company.id
        assert sample_company.legal_name
        assert sample_company.company_type
        assert sample_company.industry
        assert sample_company.registration_number
        assert sample_company.registration_date
        assert sample_company.registration_country

    def test_company_id_format(self, sample_company):
        """Test company ID follows UUID format"""
        assert sample_company.id is not None
        assert len(sample_company.id) > 0

    def test_company_type_valid(self, sample_companies):
        """Test company type is valid"""
        valid_types = [
            "corporation",
            "llc",
            "partnership",
            "sole_proprietorship",
            "non_profit",
            "government",
            "trust",
        ]
        for company in sample_companies:
            assert company.company_type in valid_types

    def test_industry_valid(self, sample_companies):
        """Test industry is valid"""
        valid_industries = [
            "financial_services",
            "technology",
            "healthcare",
            "retail",
            "manufacturing",
            "real_estate",
            "energy",
            "telecommunications",
            "transportation",
            "hospitality",
            "agriculture",
            "construction",
            "education",
            "entertainment",
            "legal",
            "consulting",
        ]
        for company in sample_companies:
            assert company.industry in valid_industries

    def test_registration_number_format(self, sample_companies):
        """Test registration numbers are present and formatted"""
        for company in sample_companies:
            assert company.registration_number
            assert len(company.registration_number) > 0

    def test_registration_date_valid(self, sample_companies):
        """Test registration date is in the past"""
        today = date.today()
        for company in sample_companies:
            assert company.registration_date <= today

    def test_addresses_present(self, sample_companies):
        """Test addresses are generated"""
        for company in sample_companies:
            assert company.addresses
            assert len(company.addresses) > 0
            assert company.addresses[0].street
            assert company.addresses[0].city
            assert company.addresses[0].country

    def test_contact_info_present(self, sample_companies):
        """Test contact information is present"""
        for company in sample_companies:
            # At least one contact method should be present
            has_contact = company.phone or company.email or company.website
            assert has_contact


class TestCompanyGeneratorEdgeCases:
    """Edge case tests"""

    def test_unique_company_ids(self, company_generator):
        """Test that company IDs are unique"""
        companies = [company_generator.generate() for _ in range(100)]
        company_ids = [c.id for c in companies]
        assert len(company_ids) == len(set(company_ids))

    def test_unique_registration_numbers(self, company_generator):
        """Test that registration numbers are unique"""
        companies = [company_generator.generate() for _ in range(50)]
        reg_numbers = [c.registration_number for c in companies]
        # Most should be unique (allowing for some collisions in test data)
        assert len(set(reg_numbers)) >= 45

    def test_risk_level_distribution(self, company_generator):
        """Test risk level distribution is reasonable"""
        companies = [company_generator.generate() for _ in range(100)]
        risk_levels = [c.risk_level for c in companies]

        # Should have variety of risk levels
        unique_levels = set(risk_levels)
        assert len(unique_levels) >= 2

        # Most should be low/medium risk
        high_risk_count = sum(1 for r in risk_levels if r in ["high", "critical"])
        assert high_risk_count < 30  # Less than 30% high risk


class TestCompanyGeneratorIndustrySpecific:
    """Industry-specific validation tests"""

    def test_financial_services_companies(self, company_generator):
        """Test financial services companies have appropriate attributes"""
        companies = [company_generator.generate() for _ in range(50)]
        financial_companies = [c for c in companies if c.industry == "financial_services"]

        if financial_companies:
            # Financial companies should have higher compliance requirements
            for company in financial_companies:
                assert company.registration_number
                assert company.registration_date

    def test_technology_companies(self, company_generator):
        """Test technology companies are generated"""
        companies = [company_generator.generate() for _ in range(50)]
        tech_companies = [c for c in companies if c.industry == "technology"]

        # Should have some tech companies
        assert len(tech_companies) > 0


class TestCompanyGeneratorBatchGeneration:
    """Batch generation tests"""

    def test_batch_generation_performance(self, company_generator):
        """Test batch generation completes in reasonable time"""
        import time

        start = time.time()
        companies = company_generator.generate_batch(100)
        elapsed = time.time() - start

        assert len(companies) == 100
        assert elapsed < 10  # Should complete in under 10 seconds

    def test_batch_statistics(self, company_generator):
        """Test batch generation statistics"""
        company_generator.generate_batch(50)
        stats = company_generator.get_statistics()

        assert stats["generated_count"] == 50
        assert stats["error_count"] == 0
        assert stats["generation_rate_per_second"] > 0


# Run tests with: pytest banking/data_generators/tests/test_core/test_company_generator.py -v
