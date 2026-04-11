"""
Synthetic Identity Generator
=============================

Generates deterministic synthetic identities for fraud detection testing.

Synthetic identity fraud involves creating fake identities by combining real and
fabricated information (e.g., real SSN with fake name). This is one of the fastest
growing financial crimes, costing US banks $6B annually.

Features:
- 100% deterministic with seed
- Multiple identity types (Frankenstein, manipulated, fabricated)
- Shared attribute patterns (SSN, phone, address, email)
- Credit profile generation
- Risk scoring
- Bust-out scheme indicators

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-04-11
Phase: 7.2 - Synthetic Identity Fraud Detection
"""

import logging
from datetime import timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from banking.data_generators.core.base_generator import BaseGenerator
from banking.data_generators.utils.deterministic import REFERENCE_TIMESTAMP, seeded_uuid_hex

logger = logging.getLogger(__name__)


class IdentityType(str, Enum):
    """Types of synthetic identities."""
    FRANKENSTEIN = "frankenstein"  # Mix of real and fake data (most common)
    MANIPULATED = "manipulated"    # Slightly altered real identity
    FABRICATED = "fabricated"      # Completely fake identity
    LEGITIMATE = "legitimate"      # Real identity (for comparison)


class CreditTier(str, Enum):
    """Credit score tiers."""
    EXCELLENT = "excellent"  # 750-850
    GOOD = "good"           # 700-749
    FAIR = "fair"           # 650-699
    POOR = "poor"           # 600-649
    BAD = "bad"             # 300-599


class SyntheticIdentityGenerator(BaseGenerator[Dict[str, Any]]):
    """
    Generate deterministic synthetic identities for fraud detection.
    
    Synthetic identities are created by combining real and fake information:
    - Real SSN + Fake name/DOB (Frankenstein - 80% of cases)
    - Real identity with minor changes (Manipulated - 15%)
    - Completely fabricated (Fabricated - 5%)
    
    Key fraud indicators:
    - Shared SSN across multiple identities
    - Shared phone/address/email
    - Recent credit file creation
    - Rapid credit building (authorized user piggybacking)
    - Bust-out pattern (max credit then disappear)
    
    Example:
        >>> gen = SyntheticIdentityGenerator(seed=42)
        >>> identity = gen.generate()
        >>> print(identity["identity_type"])  # 'frankenstein'
        >>> print(identity["ssn"])  # Real SSN format
        >>> print(identity["is_synthetic"])  # True
    """
    
    # SSN format: XXX-XX-XXXX (avoid real SSNs)
    # Use test SSN ranges: 987-65-XXXX (IRS test range)
    SSN_TEST_PREFIX = "987-65"
    
    # Identity type distribution (realistic fraud patterns)
    IDENTITY_TYPE_WEIGHTS = {
        IdentityType.FRANKENSTEIN: 0.80,  # Most common
        IdentityType.MANIPULATED: 0.15,
        IdentityType.FABRICATED: 0.05,
    }
    
    # Credit tier distribution for synthetic identities
    CREDIT_TIER_WEIGHTS = {
        CreditTier.EXCELLENT: 0.05,  # Rare for synthetics
        CreditTier.GOOD: 0.15,
        CreditTier.FAIR: 0.30,
        CreditTier.POOR: 0.35,
        CreditTier.BAD: 0.15,
    }
    
    def __init__(
        self,
        seed: Optional[int] = None,
        locale: str = "en_US",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize synthetic identity generator.
        
        Args:
            seed: Random seed for reproducibility (42, 123, or 999)
            locale: Faker locale (default: en_US)
            config: Additional configuration:
                - synthetic_probability: Probability of synthetic (default: 0.10)
                - shared_ssn_probability: Probability of shared SSN (default: 0.30)
                - shared_phone_probability: Probability of shared phone (default: 0.25)
                - shared_address_probability: Probability of shared address (default: 0.20)
                - bust_out_probability: Probability of bust-out pattern (default: 0.15)
        """
        super().__init__(seed=seed, locale=locale, config=config)
        
        # Configuration
        self.synthetic_probability = config.get("synthetic_probability", 0.10) if config else 0.10
        self.shared_ssn_probability = config.get("shared_ssn_probability", 0.30) if config else 0.30
        self.shared_phone_probability = config.get("shared_phone_probability", 0.25) if config else 0.25
        self.shared_address_probability = config.get("shared_address_probability", 0.20) if config else 0.20
        self.bust_out_probability = config.get("bust_out_probability", 0.15) if config else 0.15
        
        # Shared attribute pools (for creating connections)
        self._shared_ssns: List[str] = []
        self._shared_phones: List[str] = []
        self._shared_addresses: List[Dict[str, str]] = []
        self._shared_emails: List[str] = []
        
        logger.info(
            f"SyntheticIdentityGenerator initialized with seed={seed}, "
            f"synthetic_prob={self.synthetic_probability}, "
            f"shared_ssn_prob={self.shared_ssn_probability}"
        )
    
    def generate(self) -> Dict[str, Any]:
        """
        Generate a single identity (synthetic or legitimate).
        
        Returns:
            Dictionary with identity data:
            - identity_id: Unique deterministic ID
            - identity_type: Type of identity (frankenstein, manipulated, etc.)
            - is_synthetic: Boolean flag
            - ssn: Social Security Number
            - first_name: First name
            - middle_name: Middle name (optional)
            - last_name: Last name
            - date_of_birth: Date of birth
            - phone: Phone number
            - email: Email address
            - address: Physical address
            - credit_score: Credit score (300-850)
            - credit_tier: Credit tier category
            - credit_file_age_months: Age of credit file
            - num_credit_accounts: Number of credit accounts
            - total_credit_limit: Total credit limit
            - credit_utilization: Credit utilization ratio
            - has_authorized_user_history: Piggybacking indicator
            - bust_out_risk_score: Risk score for bust-out (0-100)
            - shared_attributes: List of shared attributes
            - created_at: Creation timestamp (REFERENCE_TIMESTAMP)
            - risk_indicators: List of fraud risk indicators
        """
        # Determine if synthetic
        is_synthetic = self.faker.random.random() < self.synthetic_probability
        
        if is_synthetic:
            identity_type = self._weighted_choice(self.IDENTITY_TYPE_WEIGHTS)
        else:
            identity_type = IdentityType.LEGITIMATE
        
        # Generate identity components
        identity_id = f"identity-{seeded_uuid_hex()[:12]}"
        ssn = self._generate_ssn(is_synthetic)
        first_name = self.faker.first_name()
        middle_name = self.faker.first_name() if self.faker.random.random() < 0.5 else None
        last_name = self.faker.last_name()
        date_of_birth = self._generate_dob(identity_type)
        phone = self._generate_phone(is_synthetic)
        email = self._generate_email(first_name, last_name, is_synthetic)
        address = self._generate_address(is_synthetic)
        
        # Generate credit profile
        credit_profile = self._generate_credit_profile(is_synthetic, identity_type)
        
        # Identify shared attributes
        shared_attributes = self._identify_shared_attributes(ssn, phone, email, address)
        
        # Calculate bust-out risk
        bust_out_risk_score = self._calculate_bust_out_risk(
            is_synthetic, credit_profile, shared_attributes
        )
        
        # Identify risk indicators
        risk_indicators = self._identify_risk_indicators(
            is_synthetic, identity_type, credit_profile, shared_attributes, bust_out_risk_score
        )
        
        return {
            "identity_id": identity_id,
            "identity_type": identity_type.value,
            "is_synthetic": is_synthetic,
            "ssn": ssn,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "date_of_birth": date_of_birth.isoformat(),
            "phone": phone,
            "email": email,
            "address": address,
            "credit_score": credit_profile["credit_score"],
            "credit_tier": credit_profile["credit_tier"],
            "credit_file_age_months": credit_profile["credit_file_age_months"],
            "num_credit_accounts": credit_profile["num_credit_accounts"],
            "total_credit_limit": credit_profile["total_credit_limit"],
            "credit_utilization": credit_profile["credit_utilization"],
            "has_authorized_user_history": credit_profile["has_authorized_user_history"],
            "bust_out_risk_score": bust_out_risk_score,
            "shared_attributes": shared_attributes,
            "created_at": REFERENCE_TIMESTAMP.isoformat(),
            "risk_indicators": risk_indicators,
        }
    
    def _generate_ssn(self, is_synthetic: bool) -> str:
        """Generate SSN (test range for synthetics)."""
        if is_synthetic and self.faker.random.random() < self.shared_ssn_probability:
            # Use shared SSN
            if not self._shared_ssns:
                # Create new shared SSN
                ssn = f"{self.SSN_TEST_PREFIX}-{self.faker.random.randint(1000, 9999)}"
                self._shared_ssns.append(ssn)
            else:
                # Reuse existing shared SSN
                ssn = self.faker.random.choice(self._shared_ssns)
        else:
            # Generate unique SSN
            ssn = f"{self.SSN_TEST_PREFIX}-{self.faker.random.randint(1000, 9999)}"
        
        return ssn
    
    def _generate_dob(self, identity_type: IdentityType) -> Any:
        """Generate date of birth."""
        if identity_type == IdentityType.FRANKENSTEIN:
            # Synthetic identities often use fake DOB (younger to build credit)
            age_years = self.faker.random.randint(18, 35)
        elif identity_type == IdentityType.MANIPULATED:
            # Slightly altered real DOB
            age_years = self.faker.random.randint(25, 65)
        else:
            # Normal distribution
            age_years = self.faker.random.randint(18, 85)
        
        dob = REFERENCE_TIMESTAMP.date() - timedelta(days=age_years * 365)
        return dob
    
    def _generate_phone(self, is_synthetic: bool) -> str:
        """Generate phone number."""
        if is_synthetic and self.faker.random.random() < self.shared_phone_probability:
            # Use shared phone
            if not self._shared_phones:
                phone = self.faker.phone_number()
                self._shared_phones.append(phone)
            else:
                phone = self.faker.random.choice(self._shared_phones)
        else:
            phone = self.faker.phone_number()
        
        return phone
    
    def _generate_email(self, first_name: str, last_name: str, is_synthetic: bool) -> str:
        """Generate email address."""
        if is_synthetic and self.faker.random.random() < 0.15:
            # Use shared email domain
            if not self._shared_emails:
                email = f"{first_name.lower()}.{last_name.lower()}@{self.faker.free_email_domain()}"
                self._shared_emails.append(email)
            else:
                # Reuse domain
                base_email = self.faker.random.choice(self._shared_emails)
                domain = base_email.split('@')[1]
                email = f"{first_name.lower()}.{last_name.lower()}@{domain}"
        else:
            email = f"{first_name.lower()}.{last_name.lower()}@{self.faker.free_email_domain()}"
        
        return email
    
    def _generate_address(self, is_synthetic: bool) -> Dict[str, str]:
        """Generate physical address."""
        if is_synthetic and self.faker.random.random() < self.shared_address_probability:
            # Use shared address
            if not self._shared_addresses:
                address = {
                    "street": self.faker.street_address(),
                    "city": self.faker.city(),
                    "state": self.faker.state_abbr(),
                    "zip_code": self.faker.zipcode(),
                }
                self._shared_addresses.append(address)
            else:
                address = self.faker.random.choice(self._shared_addresses)
        else:
            address = {
                "street": self.faker.street_address(),
                "city": self.faker.city(),
                "state": self.faker.state_abbr(),
                "zip_code": self.faker.zipcode(),
            }
        
        return address
    
    def _generate_credit_profile(
        self, is_synthetic: bool, identity_type: IdentityType
    ) -> Dict[str, Any]:
        """Generate credit profile."""
        if is_synthetic:
            # Synthetic identities have specific credit patterns
            credit_tier = self._weighted_choice(self.CREDIT_TIER_WEIGHTS)
            
            # Credit file age (synthetics are typically newer)
            if identity_type == IdentityType.FRANKENSTEIN:
                credit_file_age_months = self.faker.random.randint(6, 36)  # 6 months to 3 years
            else:
                credit_file_age_months = self.faker.random.randint(12, 60)
            
            # Authorized user history (piggybacking is common)
            has_authorized_user_history = self.faker.random.random() < 0.40
            
            # Number of accounts (synthetics build credit quickly)
            if has_authorized_user_history:
                num_credit_accounts = self.faker.random.randint(3, 8)
            else:
                num_credit_accounts = self.faker.random.randint(1, 4)
        else:
            # Legitimate identities have normal credit patterns
            credit_tier = self._weighted_choice({
                CreditTier.EXCELLENT: 0.20,
                CreditTier.GOOD: 0.30,
                CreditTier.FAIR: 0.25,
                CreditTier.POOR: 0.15,
                CreditTier.BAD: 0.10,
            })
            credit_file_age_months = self.faker.random.randint(24, 240)  # 2-20 years
            has_authorized_user_history = self.faker.random.random() < 0.15
            num_credit_accounts = self.faker.random.randint(2, 12)
        
        # Credit score based on tier
        credit_score = self._credit_score_from_tier(credit_tier)
        
        # Credit limit and utilization
        total_credit_limit = self._calculate_credit_limit(credit_score, num_credit_accounts)
        credit_utilization = self._calculate_credit_utilization(is_synthetic, credit_tier)
        
        return {
            "credit_score": credit_score,
            "credit_tier": credit_tier.value,
            "credit_file_age_months": credit_file_age_months,
            "num_credit_accounts": num_credit_accounts,
            "total_credit_limit": float(total_credit_limit),
            "credit_utilization": credit_utilization,
            "has_authorized_user_history": has_authorized_user_history,
        }
    
    def _credit_score_from_tier(self, tier: CreditTier) -> int:
        """Generate credit score within tier range."""
        ranges = {
            CreditTier.EXCELLENT: (750, 850),
            CreditTier.GOOD: (700, 749),
            CreditTier.FAIR: (650, 699),
            CreditTier.POOR: (600, 649),
            CreditTier.BAD: (300, 599),
        }
        min_score, max_score = ranges[tier]
        return self.faker.random.randint(min_score, max_score)
    
    def _calculate_credit_limit(self, credit_score: int, num_accounts: int) -> Decimal:
        """Calculate total credit limit based on score and accounts."""
        # Base limit per account
        if credit_score >= 750:
            base_limit = Decimal(self.faker.random.randint(5000, 15000))
        elif credit_score >= 700:
            base_limit = Decimal(self.faker.random.randint(3000, 8000))
        elif credit_score >= 650:
            base_limit = Decimal(self.faker.random.randint(2000, 5000))
        else:
            base_limit = Decimal(self.faker.random.randint(500, 2000))
        
        return base_limit * num_accounts
    
    def _calculate_credit_utilization(self, is_synthetic: bool, tier: CreditTier) -> float:
        """Calculate credit utilization ratio."""
        if is_synthetic:
            # Synthetics often max out credit (bust-out pattern)
            if self.faker.random.random() < self.bust_out_probability:
                return round(self.faker.random.uniform(0.85, 1.0), 2)
            else:
                return round(self.faker.random.uniform(0.30, 0.70), 2)
        else:
            # Legitimate users have lower utilization
            if tier in [CreditTier.EXCELLENT, CreditTier.GOOD]:
                return round(self.faker.random.uniform(0.05, 0.30), 2)
            else:
                return round(self.faker.random.uniform(0.30, 0.60), 2)
    
    def _identify_shared_attributes(
        self, ssn: str, phone: str, email: str, address: Dict[str, str]
    ) -> List[str]:
        """Identify which attributes are shared."""
        shared = []
        
        if ssn in self._shared_ssns:
            shared.append("ssn")
        if phone in self._shared_phones:
            shared.append("phone")
        if any(addr == address for addr in self._shared_addresses):
            shared.append("address")
        
        return shared
    
    def _calculate_bust_out_risk(
        self,
        is_synthetic: bool,
        credit_profile: Dict[str, Any],
        shared_attributes: List[str]
    ) -> int:
        """Calculate bust-out risk score (0-100)."""
        if not is_synthetic:
            return 0
        
        risk_score = 0
        
        # High credit utilization
        if credit_profile["credit_utilization"] > 0.80:
            risk_score += 40
        elif credit_profile["credit_utilization"] > 0.60:
            risk_score += 20
        
        # Recent credit file
        if credit_profile["credit_file_age_months"] < 12:
            risk_score += 25
        elif credit_profile["credit_file_age_months"] < 24:
            risk_score += 15
        
        # Shared attributes
        risk_score += len(shared_attributes) * 10
        
        # Authorized user history (piggybacking)
        if credit_profile["has_authorized_user_history"]:
            risk_score += 15
        
        return min(risk_score, 100)
    
    def _identify_risk_indicators(
        self,
        is_synthetic: bool,
        identity_type: IdentityType,
        credit_profile: Dict[str, Any],
        shared_attributes: List[str],
        bust_out_risk_score: int
    ) -> List[str]:
        """Identify fraud risk indicators."""
        indicators = []
        
        if is_synthetic:
            indicators.append(f"synthetic_identity_{identity_type.value}")
        
        if shared_attributes:
            indicators.append(f"shared_attributes_{','.join(shared_attributes)}")
        
        if credit_profile["credit_file_age_months"] < 12:
            indicators.append("recent_credit_file")
        
        if credit_profile["has_authorized_user_history"]:
            indicators.append("authorized_user_piggybacking")
        
        if credit_profile["credit_utilization"] > 0.80:
            indicators.append("high_credit_utilization")
        
        if bust_out_risk_score >= 70:
            indicators.append("high_bust_out_risk")
        elif bust_out_risk_score >= 50:
            indicators.append("medium_bust_out_risk")
        
        return indicators
    
    def _weighted_choice(self, weights: Dict[Any, float]) -> Any:
        """Make a weighted random choice."""
        items = list(weights.keys())
        probabilities = list(weights.values())
        return self.faker.random.choices(items, weights=probabilities, k=1)[0]
    
    def get_shared_attribute_stats(self) -> Dict[str, int]:
        """Get statistics on shared attributes."""
        return {
            "shared_ssns": len(self._shared_ssns),
            "shared_phones": len(self._shared_phones),
            "shared_addresses": len(self._shared_addresses),
            "shared_emails": len(self._shared_emails),
        }


__all__ = ["SyntheticIdentityGenerator", "IdentityType", "CreditTier"]

# Made with Bob
