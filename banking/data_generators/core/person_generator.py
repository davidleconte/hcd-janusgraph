"""
Person Generator
================

Generates realistic synthetic person entities with comprehensive attributes
including demographics, contact information, employment, identification,
and risk indicators.

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

import random
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any

from faker import Faker
import phonenumbers

from .base_generator import BaseGenerator
from ..utils.data_models import (
    Person, Address, PhoneNumber, EmailAddress,
    IdentificationDocument, Employment, Gender, RiskLevel
)
from ..utils.constants import (
    COUNTRIES, LANGUAGES, HIGH_RISK_COUNTRIES,
    TAX_HAVENS, PEP_CATEGORIES, SANCTIONS_LISTS
)
from ..utils.helpers import (
    random_choice_weighted, random_date_between,
    generate_tax_id, calculate_entity_risk_score
)


class PersonGenerator(BaseGenerator[Person]):
    """
    Generator for realistic person entities.
    
    Features:
    - Multi-national person generation
    - Realistic demographics distribution
    - Employment history
    - Multiple addresses, phones, emails
    - Identification documents
    - PEP designation
    - Sanctions checking
    - Risk level assignment
    """
    
    def __init__(
        self,
        seed: Optional[int] = None,
        locale: str = "en_US",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize PersonGenerator.
        
        Args:
            seed: Random seed for reproducibility
            locale: Faker locale
            config: Configuration options:
                - pep_probability: Probability of PEP (default: 0.01)
                - sanctioned_probability: Probability of sanctioned (default: 0.001)
                - high_risk_probability: Probability of high risk (default: 0.05)
                - multi_citizenship_probability: Probability of dual citizenship (default: 0.1)
                - min_age: Minimum age (default: 18)
                - max_age: Maximum age (default: 85)
        """
        super().__init__(seed, locale, config)
        
        # Configuration defaults
        self.pep_probability = self.config.get('pep_probability', 0.01)
        self.sanctioned_probability = self.config.get('sanctioned_probability', 0.001)
        self.high_risk_probability = self.config.get('high_risk_probability', 0.05)
        self.multi_citizenship_probability = self.config.get('multi_citizenship_probability', 0.1)
        self.min_age = self.config.get('min_age', 18)
        self.max_age = self.config.get('max_age', 85)
    
    def generate(self) -> Person:
        """
        Generate a single person entity.
        
        Returns:
            Person entity with all attributes
        """
        # Basic demographics
        gender = self._generate_gender()
        first_name, middle_name, last_name = self._generate_names(gender)
        date_of_birth = self._generate_date_of_birth()
        nationality = self._generate_nationality()
        
        # Contact information
        addresses = self._generate_addresses(nationality)
        phone_numbers = self._generate_phone_numbers(nationality)
        email_addresses = self._generate_email_addresses(first_name, last_name)
        
        # Identification
        identification_documents = self._generate_identification_documents(
            nationality, date_of_birth
        )
        tax_id = generate_tax_id(nationality)
        
        # Employment & Financial
        employment_history = self._generate_employment_history(date_of_birth)
        annual_income = self._calculate_annual_income(employment_history)
        net_worth = self._calculate_net_worth(annual_income, date_of_birth)
        
        # Risk & Compliance
        is_pep = random.random() < self.pep_probability
        pep_details = self._generate_pep_details() if is_pep else None
        
        is_sanctioned = random.random() < self.sanctioned_probability
        sanction_lists = self._generate_sanction_lists() if is_sanctioned else []
        
        # Calculate risk level
        risk_level = self._calculate_risk_level(
            is_pep, is_sanctioned, nationality, annual_income
        )
        
        # Additional attributes
        citizenship = self._generate_citizenship(nationality)
        languages = self._generate_languages(nationality)
        education_level = self._generate_education_level()
        marital_status = self._generate_marital_status()
        dependents = self._generate_dependents(marital_status)
        social_media_profiles = self._generate_social_media_profiles(first_name, last_name)
        
        # Create Person entity
        person = Person(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            full_name=f"{first_name} {middle_name or ''} {last_name}".strip(),
            date_of_birth=date_of_birth,
            age=0,  # Will be calculated by validator
            gender=gender,
            nationality=nationality,
            citizenship=citizenship,
            addresses=addresses,
            phone_numbers=phone_numbers,
            email_addresses=email_addresses,
            identification_documents=identification_documents,
            tax_id=tax_id,
            employment_history=employment_history,
            net_worth=net_worth,
            annual_income=annual_income,
            risk_level=risk_level,
            is_pep=is_pep,
            pep_details=pep_details,
            is_sanctioned=is_sanctioned,
            sanction_lists=sanction_lists,
            languages=languages,
            education_level=education_level,
            marital_status=marital_status,
            dependents=dependents,
            social_media_profiles=social_media_profiles,
            online_activity_score=random.uniform(0.1, 0.9)
        )
        
        return person
    
    def _generate_gender(self) -> Gender:
        """Generate gender with realistic distribution."""
        choices = [
            (Gender.MALE, 0.49),
            (Gender.FEMALE, 0.49),
            (Gender.NON_BINARY, 0.01),
            (Gender.PREFER_NOT_TO_SAY, 0.01)
        ]
        return random_choice_weighted(choices)
    
    def _generate_names(self, gender: Gender) -> tuple:
        """Generate first, middle, and last names."""
        if gender == Gender.MALE:
            first_name = self.faker.first_name_male()
        elif gender == Gender.FEMALE:
            first_name = self.faker.first_name_female()
        else:
            first_name = self.faker.first_name()
        
        middle_name = self.faker.first_name() if random.random() < 0.7 else None
        last_name = self.faker.last_name()
        
        return first_name, middle_name, last_name
    
    def _generate_date_of_birth(self) -> date:
        """Generate date of birth based on age range."""
        today = date.today()
        min_date = today - timedelta(days=self.max_age * 365)
        max_date = today - timedelta(days=self.min_age * 365)
        return random_date_between(min_date, max_date)
    
    def _generate_nationality(self) -> str:
        """Generate nationality with weighted distribution."""
        # Weight major countries higher
        major_countries = ["US", "GB", "DE", "FR", "JP", "CA", "AU", "IT", "ES", "NL"]
        if random.random() < 0.7:
            return random.choice(major_countries)
        return random.choice(list(COUNTRIES.keys()))
    
    def _generate_addresses(self, nationality: str, count: Optional[int] = None) -> List[Address]:
        """Generate addresses."""
        if count is None:
            count = random.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]
        
        addresses = []
        for i in range(count):
            address = Address(
                street=self.faker.street_address(),
                city=self.faker.city(),
                state=self.faker.state() if nationality == "US" else None,
                postal_code=self.faker.postcode(),
                country=COUNTRIES.get(nationality, "United States"),
                country_code=nationality,
                latitude=float(self.faker.latitude()),
                longitude=float(self.faker.longitude()),
                is_primary=(i == 0),
                address_type=random.choice(["residential", "business", "mailing"])
            )
            addresses.append(address)
        
        return addresses
    
    def _generate_phone_numbers(self, nationality: str, count: Optional[int] = None) -> List[PhoneNumber]:
        """Generate phone numbers."""
        if count is None:
            count = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
        
        phones = []
        for i in range(count):
            phone = PhoneNumber(
                number=self.faker.phone_number(),
                country_code=nationality,
                phone_type=random.choice(["mobile", "home", "work"]),
                is_primary=(i == 0),
                is_verified=random.random() < 0.8
            )
            phones.append(phone)
        
        return phones
    
    def _generate_email_addresses(self, first_name: str, last_name: str, 
                                  count: Optional[int] = None) -> List[EmailAddress]:
        """Generate email addresses."""
        if count is None:
            count = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
        
        emails = []
        domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com"]
        
        for i in range(count):
            # Generate realistic email
            username = f"{first_name.lower()}.{last_name.lower()}"
            if i > 0:
                username += str(random.randint(1, 999))
            
            email = EmailAddress(
                email=f"{username}@{random.choice(domains)}",
                email_type="personal" if i == 0 else "work",
                is_primary=(i == 0),
                is_verified=random.random() < 0.9
            )
            emails.append(email)
        
        return emails
    
    def _generate_identification_documents(self, nationality: str, 
                                          dob: date) -> List[IdentificationDocument]:
        """Generate identification documents."""
        docs = []
        
        # Passport
        if random.random() < 0.7:
            issue_date = random_date_between(dob + timedelta(days=6570), date.today())  # After 18
            docs.append(IdentificationDocument(
                doc_type="passport",
                doc_number=self.faker.bothify(text="??######"),
                issuing_country=nationality,
                issuing_authority="Passport Office",
                issue_date=issue_date,
                expiry_date=issue_date + timedelta(days=3650),  # 10 years
                is_verified=random.random() < 0.95
            ))
        
        # Driver's License
        if random.random() < 0.8:
            issue_date = random_date_between(dob + timedelta(days=5840), date.today())  # After 16
            docs.append(IdentificationDocument(
                doc_type="drivers_license",
                doc_number=self.faker.bothify(text="??#######"),
                issuing_country=nationality,
                issue_date=issue_date,
                expiry_date=issue_date + timedelta(days=1825),  # 5 years
                is_verified=random.random() < 0.9
            ))
        
        return docs
    
    def _generate_employment_history(self, dob: date) -> List[Employment]:
        """Generate employment history."""
        from ..utils.data_models import IndustryType
        
        employment = []
        work_start_age = 18 + random.randint(0, 8)  # 18-26
        work_start_date = dob + timedelta(days=work_start_age * 365)
        
        if work_start_date > date.today():
            return employment
        
        # Generate 1-3 jobs
        num_jobs = random.choices([1, 2, 3], weights=[0.5, 0.35, 0.15])[0]
        
        current_date = work_start_date
        for i in range(num_jobs):
            is_current = (i == num_jobs - 1)
            
            # Job duration: 1-10 years
            duration_years = random.randint(1, 10)
            end_date = None if is_current else current_date + timedelta(days=duration_years * 365)
            
            if end_date and end_date > date.today():
                end_date = None
                is_current = True
            
            job = Employment(
                employer_name=self.faker.company(),
                job_title=self.faker.job(),
                industry=random.choice(list(IndustryType)),
                start_date=current_date,
                end_date=end_date,
                annual_income=Decimal(str(random.randint(30000, 500000))),
                currency="USD",
                is_current=is_current
            )
            employment.append(job)
            
            if not is_current and end_date:
                current_date = end_date + timedelta(days=random.randint(30, 365))
        
        return employment
    
    def _calculate_annual_income(self, employment_history: List[Employment]) -> Optional[Decimal]:
        """Calculate current annual income."""
        current_jobs = [e for e in employment_history if e.is_current]
        if current_jobs:
            total = sum(e.annual_income for e in current_jobs)
            return Decimal(str(total)) if total else None
        return None
    
    def _calculate_net_worth(self, annual_income: Optional[Decimal], dob: date) -> Optional[Decimal]:
        """Calculate estimated net worth."""
        if not annual_income:
            return None
        
        age = (date.today() - dob).days // 365
        years_working = max(0, age - 22)
        
        # Simple net worth estimation
        multiplier = Decimal(str(random.uniform(0.5, 5.0)))
        net_worth = annual_income * multiplier * Decimal(str(years_working / 10))
        
        return net_worth
    
    def _generate_pep_details(self) -> Dict[str, Any]:
        """Generate PEP details."""
        return {
            "category": random.choice(PEP_CATEGORIES),
            "position": self.faker.job(),
            "country": random.choice(list(COUNTRIES.keys())),
            "start_date": str(random_date_between(date(2000, 1, 1), date.today())),
            "is_active": random.random() < 0.7
        }
    
    def _generate_sanction_lists(self) -> List[str]:
        """Generate sanction list memberships."""
        num_lists = random.randint(1, 3)
        return random.sample(SANCTIONS_LISTS, min(num_lists, len(SANCTIONS_LISTS)))
    
    def _calculate_risk_level(self, is_pep: bool, is_sanctioned: bool,
                             nationality: str, annual_income: Optional[Decimal]) -> RiskLevel:
        """Calculate risk level."""
        score = calculate_entity_risk_score(
            is_pep=is_pep,
            is_sanctioned=is_sanctioned,
            high_risk_country=(nationality in HIGH_RISK_COUNTRIES),
            tax_haven_presence=False,
            cash_intensive_business=False
        )
        
        if score >= 0.7:
            return RiskLevel.CRITICAL
        elif score >= 0.5:
            return RiskLevel.HIGH
        elif score >= 0.3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_citizenship(self, nationality: str) -> List[str]:
        """Generate citizenship list."""
        citizenships = [nationality]
        
        if random.random() < self.multi_citizenship_probability:
            # Add second citizenship
            other_country = random.choice([c for c in COUNTRIES.keys() if c != nationality])
            citizenships.append(other_country)
        
        return citizenships
    
    def _generate_languages(self, nationality: str) -> List[str]:
        """Generate language proficiency."""
        # Primary language based on nationality
        language_map = {
            "US": "en", "GB": "en", "CA": "en", "AU": "en",
            "FR": "fr", "DE": "de", "ES": "es", "IT": "it",
            "JP": "ja", "CN": "zh", "RU": "ru", "BR": "pt"
        }
        
        primary = language_map.get(nationality, "en")
        languages = [primary]
        
        # Add additional languages
        num_additional = random.choices([0, 1, 2], weights=[0.5, 0.35, 0.15])[0]
        if num_additional > 0:
            other_langs = [l for l in ["en", "es", "fr", "de", "zh"] if l != primary]
            languages.extend(random.sample(other_langs, min(num_additional, len(other_langs))))
        
        return languages
    
    def _generate_education_level(self) -> str:
        """Generate education level."""
        levels = [
            "high_school", "associate", "bachelor", "master", "doctorate", "professional"
        ]
        weights = [0.25, 0.15, 0.35, 0.15, 0.05, 0.05]
        return random.choices(levels, weights=weights)[0]
    
    def _generate_marital_status(self) -> str:
        """Generate marital status."""
        statuses = ["single", "married", "divorced", "widowed", "separated"]
        weights = [0.35, 0.45, 0.12, 0.05, 0.03]
        return random.choices(statuses, weights=weights)[0]
    
    def _generate_dependents(self, marital_status: str) -> int:
        """Generate number of dependents."""
        if marital_status == "single":
            return random.choices([0, 1, 2], weights=[0.8, 0.15, 0.05])[0]
        elif marital_status == "married":
            return random.choices([0, 1, 2, 3, 4], weights=[0.2, 0.25, 0.3, 0.15, 0.1])[0]
        else:
            return random.choices([0, 1, 2], weights=[0.5, 0.3, 0.2])[0]
    
    def _generate_social_media_profiles(self, first_name: str, last_name: str) -> Dict[str, str]:
        """Generate social media profiles."""
        profiles = {}
        username = f"{first_name.lower()}{last_name.lower()}{random.randint(1, 999)}"
        
        platforms = ["twitter", "linkedin", "facebook", "instagram"]
        num_platforms = random.choices([0, 1, 2, 3], weights=[0.2, 0.3, 0.3, 0.2])[0]
        
        for platform in random.sample(platforms, num_platforms):
            profiles[platform] = f"https://{platform}.com/{username}"
        
        return profiles


__all__ = ['PersonGenerator']

