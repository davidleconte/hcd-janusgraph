"""
Company Generator
=================

Generates realistic synthetic company entities with comprehensive attributes
including corporate structure, officers, financials, and risk indicators.

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

import random
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..utils.constants import (
    COUNTRIES,
    HIGH_RISK_COUNTRIES,
    SANCTIONS_LISTS,
    STOCK_EXCHANGES,
    TAX_HAVENS,
)
from ..utils.data_models import Company, CompanyAddress, CompanyType, IndustryType, RiskLevel
from ..utils.helpers import (
    calculate_entity_risk_score,
    generate_lei_code,
    generate_stock_ticker,
    random_choice_weighted,
    random_date_between,
)
from .base_generator import BaseGenerator


class CompanyGenerator(BaseGenerator[Company]):
    """
    Generator for realistic company entities.

    Features:
    - Multi-national company generation
    - Industry-specific attributes
    - Corporate structure (parent/subsidiary)
    - Officer and director generation
    - Financial metrics
    - Public/private designation
    - Shell company indicators
    - Risk assessment
    """

    def __init__(
        self,
        seed: Optional[int] = None,
        locale: str = "en_US",
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize CompanyGenerator.

        Args:
            seed: Random seed for reproducibility
            locale: Faker locale
            config: Configuration options:
                - public_company_probability: Probability of public company (default: 0.1)
                - shell_company_probability: Probability of shell company (default: 0.02)
                - sanctioned_probability: Probability of sanctioned (default: 0.001)
                - tax_haven_probability: Probability of tax haven presence (default: 0.15)
                - subsidiary_probability: Probability of having subsidiaries (default: 0.3)
        """
        super().__init__(seed, locale, config)

        # Configuration defaults
        self.public_company_probability = self.config.get("public_company_probability", 0.1)
        self.shell_company_probability = self.config.get("shell_company_probability", 0.02)
        self.sanctioned_probability = self.config.get("sanctioned_probability", 0.001)
        self.tax_haven_probability = self.config.get("tax_haven_probability", 0.15)
        self.subsidiary_probability = self.config.get("subsidiary_probability", 0.3)

    def generate(self) -> Company:
        """
        Generate a single company entity.

        Returns:
            Company entity with all attributes
        """
        # Basic information
        legal_name = self._generate_legal_name()
        trading_name = self._generate_trading_name(legal_name)
        company_type = self._generate_company_type()
        industry = self._generate_industry()

        # Registration
        registration_country = self._generate_registration_country()
        registration_date = self._generate_registration_date()
        registration_number = self._generate_registration_number(registration_country)
        tax_id = self._generate_tax_id(registration_country)
        lei_code = generate_lei_code() if random.random() < 0.3 else None

        # Addresses
        addresses = self._generate_addresses(registration_country)

        # Public/Private
        is_public = random.random() < self.public_company_probability
        stock_ticker = None
        stock_exchange = None
        if is_public:
            stock_ticker = generate_stock_ticker()
            stock_exchange = random.choice(list(STOCK_EXCHANGES.keys()))

        # Financial metrics
        employee_count = self._generate_employee_count(company_type, is_public)
        annual_revenue = self._generate_annual_revenue(employee_count, industry)
        market_cap = self._generate_market_cap(annual_revenue) if is_public else None

        # Corporate structure
        parent_company_id = None  # Will be set externally if needed
        subsidiary_ids = []  # Will be populated externally

        # Officers (will be populated with person IDs externally)
        officers = []  # Placeholder for now

        # Risk & Compliance
        is_shell_company = random.random() < self.shell_company_probability
        is_sanctioned = random.random() < self.sanctioned_probability
        sanction_lists = self._generate_sanction_lists() if is_sanctioned else []

        # Operating countries
        operating_countries = self._generate_operating_countries(registration_country)
        tax_havens = [c for c in operating_countries if c in TAX_HAVENS]

        # Calculate risk level
        risk_level = self._calculate_risk_level(
            is_sanctioned, is_shell_company, registration_country, tax_havens, industry
        )

        # Contact information
        website = f"https://www.{legal_name.lower().replace(' ', '').replace(',', '')}.com"
        phone = self.faker.phone_number()
        email = f"info@{legal_name.lower().replace(' ', '').replace(',', '')}.com"

        # Create Company entity
        company = Company(
            legal_name=legal_name,
            trading_name=trading_name,
            company_type=company_type,
            industry=industry,
            sub_industry=self._generate_sub_industry(industry),
            registration_number=registration_number,
            registration_country=registration_country,
            registration_date=registration_date,
            tax_id=tax_id,
            lei_code=lei_code,
            addresses=addresses,
            parent_company_id=parent_company_id,
            subsidiary_ids=subsidiary_ids,
            officers=officers,
            annual_revenue=annual_revenue,
            employee_count=employee_count,
            market_cap=market_cap,
            is_public=is_public,
            stock_ticker=stock_ticker,
            stock_exchange=stock_exchange,
            risk_level=risk_level,
            is_sanctioned=is_sanctioned,
            sanction_lists=sanction_lists,
            is_shell_company=is_shell_company,
            website=website,
            phone=phone,
            email=email,
            business_description=self._generate_business_description(industry),
            operating_countries=operating_countries,
            tax_havens=tax_havens,
        )

        return company

    def _generate_legal_name(self) -> str:
        """Generate legal company name."""
        base_name = self.faker.company()
        # Remove common suffixes that Faker adds
        for suffix in [" Inc", " LLC", " Ltd", " Corp", " Group"]:
            if base_name.endswith(suffix):
                base_name = base_name[: -len(suffix)]
        return base_name

    def _generate_trading_name(self, legal_name: str) -> Optional[str]:
        """Generate trading name (DBA)."""
        if random.random() < 0.3:
            # 30% chance of different trading name
            return self.faker.company()
        return None

    def _generate_company_type(self) -> CompanyType:
        """Generate company type with realistic distribution."""
        choices = [
            (CompanyType.CORPORATION, 0.40),
            (CompanyType.LLC, 0.30),
            (CompanyType.PARTNERSHIP, 0.15),
            (CompanyType.SOLE_PROPRIETORSHIP, 0.10),
            (CompanyType.NON_PROFIT, 0.03),
            (CompanyType.GOVERNMENT, 0.01),
            (CompanyType.TRUST, 0.01),
        ]
        return random_choice_weighted(choices)

    def _generate_industry(self) -> IndustryType:
        """Generate industry with weighted distribution."""
        # Weight common industries higher
        choices = [
            (IndustryType.TECHNOLOGY, 0.15),
            (IndustryType.FINANCIAL_SERVICES, 0.12),
            (IndustryType.HEALTHCARE, 0.10),
            (IndustryType.RETAIL, 0.10),
            (IndustryType.MANUFACTURING, 0.08),
            (IndustryType.REAL_ESTATE, 0.08),
            (IndustryType.CONSULTING, 0.07),
            (IndustryType.CONSTRUCTION, 0.06),
            (IndustryType.TRANSPORTATION, 0.05),
            (IndustryType.ENERGY, 0.04),
            (IndustryType.TELECOMMUNICATIONS, 0.04),
            (IndustryType.HOSPITALITY, 0.03),
            (IndustryType.EDUCATION, 0.03),
            (IndustryType.LEGAL, 0.02),
            (IndustryType.ENTERTAINMENT, 0.02),
            (IndustryType.AGRICULTURE, 0.01),
        ]
        return random_choice_weighted(choices)

    def _generate_sub_industry(self, industry: IndustryType) -> Optional[str]:
        """Generate sub-industry based on main industry."""
        sub_industries = {
            IndustryType.TECHNOLOGY: [
                "Software",
                "Hardware",
                "Cloud Services",
                "AI/ML",
                "Cybersecurity",
            ],
            IndustryType.FINANCIAL_SERVICES: [
                "Banking",
                "Insurance",
                "Investment",
                "Payments",
                "Fintech",
            ],
            IndustryType.HEALTHCARE: [
                "Pharmaceuticals",
                "Medical Devices",
                "Hospitals",
                "Biotech",
                "Telemedicine",
            ],
            IndustryType.RETAIL: [
                "E-commerce",
                "Department Stores",
                "Specialty Retail",
                "Grocery",
                "Luxury Goods",
            ],
            IndustryType.MANUFACTURING: [
                "Automotive",
                "Electronics",
                "Chemicals",
                "Machinery",
                "Textiles",
            ],
        }

        if industry in sub_industries:
            return random.choice(sub_industries[industry])
        return None

    def _generate_registration_country(self) -> str:
        """Generate registration country with weighted distribution."""
        # Weight major business jurisdictions
        major_jurisdictions = ["US", "GB", "DE", "FR", "SG", "HK", "CA", "AU"]
        if random.random() < 0.7:
            return random.choice(major_jurisdictions)
        return random.choice(list(COUNTRIES.keys()))

    def _generate_registration_date(self) -> date:
        """Generate company registration date."""
        # Companies registered between 1950 and today
        start_date = date(1950, 1, 1)
        end_date = date.today()
        return random_date_between(start_date, end_date)

    def _generate_registration_number(self, country: str) -> str:
        """Generate registration number."""
        if country == "US":
            # EIN format
            return f"{random.randint(10, 99)}-{random.randint(1000000, 9999999)}"
        elif country == "GB":
            # UK Company Number
            return f"{random.randint(10000000, 99999999)}"
        else:
            # Generic format
            return self.faker.bothify(text="??######")

    def _generate_tax_id(self, country: str) -> str:
        """Generate tax identification number."""
        if country == "US":
            return f"{random.randint(10, 99)}-{random.randint(1000000, 9999999)}"
        else:
            return self.faker.bothify(text="??#########")

    def _generate_addresses(self, registration_country: str) -> List[CompanyAddress]:
        """Generate company addresses."""
        addresses = []

        # Headquarters
        hq = CompanyAddress(
            street=self.faker.street_address(),
            city=self.faker.city(),
            state=self.faker.state() if registration_country == "US" else None,
            postal_code=self.faker.postcode(),
            country=COUNTRIES.get(registration_country, "United States"),
            country_code=registration_country,
            is_headquarters=True,
            is_registered_office=True,
            office_type="headquarters",
        )
        addresses.append(hq)

        # Additional offices (0-3)
        num_offices = random.choices([0, 1, 2, 3], weights=[0.5, 0.3, 0.15, 0.05])[0]
        for _ in range(num_offices):
            office_country = random.choice(list(COUNTRIES.keys()))
            office = CompanyAddress(
                street=self.faker.street_address(),
                city=self.faker.city(),
                state=self.faker.state() if office_country == "US" else None,
                postal_code=self.faker.postcode(),
                country=COUNTRIES.get(office_country, "United States"),
                country_code=office_country,
                is_headquarters=False,
                is_registered_office=False,
                office_type=random.choice(["branch", "subsidiary", "regional"]),
            )
            addresses.append(office)

        return addresses

    def _generate_employee_count(self, company_type: CompanyType, is_public: bool) -> Optional[int]:
        """Generate employee count based on company type."""
        if company_type == CompanyType.SOLE_PROPRIETORSHIP:
            return random.randint(1, 10)
        elif company_type == CompanyType.PARTNERSHIP:
            return random.randint(2, 50)
        elif company_type == CompanyType.LLC:
            return random.randint(5, 500)
        elif is_public:
            return random.randint(1000, 100000)
        else:
            return random.randint(10, 5000)

    def _generate_annual_revenue(
        self, employee_count: Optional[int], industry: IndustryType
    ) -> Optional[Decimal]:
        """Generate annual revenue."""
        if not employee_count:
            return None

        # Revenue per employee varies by industry
        revenue_per_employee = {
            IndustryType.TECHNOLOGY: Decimal("250000"),
            IndustryType.FINANCIAL_SERVICES: Decimal("300000"),
            IndustryType.HEALTHCARE: Decimal("200000"),
            IndustryType.RETAIL: Decimal("150000"),
            IndustryType.MANUFACTURING: Decimal("180000"),
        }

        base_revenue = revenue_per_employee.get(industry, Decimal("200000"))
        revenue = base_revenue * Decimal(str(employee_count))

        # Add randomness (+/- 50%)
        multiplier = Decimal(str(random.uniform(0.5, 1.5)))
        return revenue * multiplier

    def _generate_market_cap(self, annual_revenue: Optional[Decimal]) -> Optional[Decimal]:
        """Generate market capitalization for public companies."""
        if not annual_revenue:
            return None

        # Market cap typically 1-10x revenue
        multiplier = Decimal(str(random.uniform(1.0, 10.0)))
        return annual_revenue * multiplier

    def _generate_sanction_lists(self) -> List[str]:
        """Generate sanction list memberships."""
        num_lists = random.randint(1, 2)
        return random.sample(SANCTIONS_LISTS, min(num_lists, len(SANCTIONS_LISTS)))

    def _generate_operating_countries(self, registration_country: str) -> List[str]:
        """Generate list of operating countries."""
        countries = [registration_country]

        # Add additional countries (0-5)
        num_additional = random.choices(
            [0, 1, 2, 3, 4, 5], weights=[0.3, 0.3, 0.2, 0.1, 0.05, 0.05]
        )[0]

        if num_additional > 0:
            other_countries = [c for c in COUNTRIES.keys() if c != registration_country]
            countries.extend(
                random.sample(other_countries, min(num_additional, len(other_countries)))
            )

        return countries

    def _calculate_risk_level(
        self,
        is_sanctioned: bool,
        is_shell_company: bool,
        registration_country: str,
        tax_havens: List[str],
        industry: IndustryType,
    ) -> RiskLevel:
        """Calculate risk level."""
        from ..utils.constants import CASH_INTENSIVE_BUSINESSES

        score = calculate_entity_risk_score(
            is_pep=False,
            is_sanctioned=is_sanctioned,
            high_risk_country=(registration_country in HIGH_RISK_COUNTRIES),
            tax_haven_presence=(len(tax_havens) > 0),
            cash_intensive_business=(industry.value in CASH_INTENSIVE_BUSINESSES),
        )

        # Additional factors
        if is_shell_company:
            score += 0.3

        if score >= 0.7:
            return RiskLevel.CRITICAL
        elif score >= 0.5:
            return RiskLevel.HIGH
        elif score >= 0.3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _generate_business_description(self, industry: IndustryType) -> Optional[str]:
        """Generate business description."""
        descriptions = {
            IndustryType.TECHNOLOGY: "Provides innovative technology solutions and services",
            IndustryType.FINANCIAL_SERVICES: "Offers comprehensive financial services and products",
            IndustryType.HEALTHCARE: "Delivers healthcare services and medical solutions",
            IndustryType.RETAIL: "Operates retail stores and e-commerce platforms",
            IndustryType.MANUFACTURING: "Manufactures and distributes industrial products",
        }
        return descriptions.get(industry, "Provides professional services and solutions")


__all__ = ["CompanyGenerator"]
