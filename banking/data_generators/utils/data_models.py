"""
Data Models for Synthetic Data Generation
==========================================

Pydantic models for all entity types used in synthetic data generation.
These models ensure type safety, validation, and consistent data structures.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from pydantic.functional_serializers import PlainSerializer
from typing_extensions import Annotated

from banking.data_generators.utils.deterministic import (
    reference_now,
    seeded_uuid_hex,
)

# Custom serializers for Pydantic V2
DatetimeSerializer = Annotated[datetime, PlainSerializer(lambda v: v.isoformat(), return_type=str)]
DateSerializer = Annotated[date, PlainSerializer(lambda v: v.isoformat(), return_type=str)]
DecimalSerializer = Annotated[Decimal, PlainSerializer(lambda v: str(v), return_type=str)]


# ============================================================================
# ENUMERATIONS
# ============================================================================


class Gender(str, Enum):
    """Gender enumeration"""

    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class RiskLevel(str, Enum):
    """Risk level classification"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AccountType(str, Enum):
    """Bank account types"""

    CHECKING = "checking"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    CREDIT_CARD = "credit_card"
    LOAN = "loan"
    MORTGAGE = "mortgage"
    BUSINESS = "business"


class TransactionType(str, Enum):
    """Transaction types"""

    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    WIRE = "wire"
    ACH = "ach"
    CHECK = "check"
    ATM = "atm"
    POS = "pos"
    ONLINE = "online"


class CommunicationType(str, Enum):
    """Communication channel types"""

    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    CHAT = "chat"
    VIDEO = "video"
    SOCIAL_MEDIA = "social_media"
    MEETING = "meeting"


class CompanyType(str, Enum):
    """Company types"""

    CORPORATION = "corporation"
    LLC = "llc"
    PARTNERSHIP = "partnership"
    SOLE_PROPRIETORSHIP = "sole_proprietorship"
    NON_PROFIT = "non_profit"
    GOVERNMENT = "government"
    TRUST = "trust"


class IndustryType(str, Enum):
    """Industry classifications"""

    FINANCIAL_SERVICES = "financial_services"
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    REAL_ESTATE = "real_estate"
    ENERGY = "energy"
    TELECOMMUNICATIONS = "telecommunications"
    TRANSPORTATION = "transportation"
    HOSPITALITY = "hospitality"
    AGRICULTURE = "agriculture"
    CONSTRUCTION = "construction"
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    LEGAL = "legal"
    CONSULTING = "consulting"


class RelationshipType(str, Enum):
    """Relationship types between entities"""

    FAMILY = "family"
    SPOUSE = "spouse"
    PARENT = "parent"
    CHILD = "child"
    SIBLING = "sibling"
    COLLEAGUE = "colleague"
    BUSINESS_PARTNER = "business_partner"
    FRIEND = "friend"
    ACQUAINTANCE = "acquaintance"
    EMPLOYEE = "employee"
    EMPLOYER = "employer"
    SHAREHOLDER = "shareholder"
    DIRECTOR = "director"
    BENEFICIAL_OWNER = "beneficial_owner"


# ============================================================================
# BASE MODELS
# ============================================================================


class BaseEntity(BaseModel):
    """Base entity with common fields"""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        ser_json_timedelta="iso8601",
        ser_json_bytes="utf8",
    )

    id: str = Field(default_factory=lambda: seeded_uuid_hex())
    created_at: datetime = Field(default_factory=reference_now)
    updated_at: datetime = Field(default_factory=reference_now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# PERSON MODELS
# ============================================================================


class Address(BaseModel):
    """Physical address"""

    street: str
    city: str
    state: Optional[str] = None
    postal_code: str
    country: str
    country_code: str  # ISO 3166-1 alpha-2
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_primary: bool = True
    address_type: str = "residential"  # residential, business, mailing


class PhoneNumber(BaseModel):
    """Phone number with metadata"""

    number: str
    country_code: str
    phone_type: str = "mobile"  # mobile, home, work, fax
    is_primary: bool = True
    is_verified: bool = False


class EmailAddress(BaseModel):
    """Email address with metadata"""

    email: EmailStr
    email_type: str = "personal"  # personal, work
    is_primary: bool = True
    is_verified: bool = False


class IdentificationDocument(BaseModel):
    """Identification document"""

    doc_type: str  # passport, drivers_license, national_id, ssn
    doc_number: str
    issuing_country: str
    issuing_authority: Optional[str] = None
    issue_date: date
    expiry_date: Optional[date] = None
    is_verified: bool = False


class Employment(BaseModel):
    """Employment information"""

    employer_id: Optional[str] = None
    employer_name: str
    job_title: str
    industry: IndustryType
    start_date: date
    end_date: Optional[date] = None
    annual_income: Decimal
    currency: str = "USD"
    is_current: bool = True


class Person(BaseEntity):
    """Person entity with comprehensive attributes"""

    @property
    def person_id(self) -> str:
        """Alias for id field - provides semantic clarity when referring to a person's identifier"""
        return self.id

    # Basic Information
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    full_name: str
    maiden_name: Optional[str] = None
    preferred_name: Optional[str] = None

    # Demographics
    date_of_birth: date
    age: int
    gender: Gender
    nationality: str
    citizenship: List[str] = Field(default_factory=list)

    # Contact Information
    addresses: List[Address] = Field(default_factory=list)
    phone_numbers: List[PhoneNumber] = Field(default_factory=list)
    email_addresses: List[EmailAddress] = Field(default_factory=list)

    # Identification
    identification_documents: List[IdentificationDocument] = Field(default_factory=list)
    tax_id: Optional[str] = None

    # Employment & Financial
    employment_history: List[Employment] = Field(default_factory=list)
    net_worth: Optional[Decimal] = None
    annual_income: Optional[Decimal] = None

    # Risk & Compliance
    risk_level: RiskLevel = RiskLevel.LOW
    is_pep: bool = False  # Politically Exposed Person
    pep_details: Optional[Dict[str, Any]] = None
    is_sanctioned: bool = False
    sanction_lists: List[str] = Field(default_factory=list)

    # Behavioral Attributes
    languages: List[str] = Field(default_factory=list)
    education_level: Optional[str] = None
    marital_status: Optional[str] = None
    dependents: int = 0

    # Digital Footprint
    social_media_profiles: Dict[str, str] = Field(default_factory=dict)
    online_activity_score: float = 0.5  # 0-1 scale

    @field_validator("age", mode="before")
    @classmethod
    def calculate_age(cls, v, info):
        """Calculate age from date of birth"""
        if hasattr(info, "data") and "date_of_birth" in info.data:
            dob = info.data["date_of_birth"]
            today = date.today()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return v


# ============================================================================
# COMPANY MODELS
# ============================================================================


class CompanyAddress(BaseModel):
    """Company address with business-specific fields"""

    street: str
    city: str
    state: Optional[str] = None
    postal_code: str
    country: str
    country_code: str
    is_headquarters: bool = False
    is_registered_office: bool = False
    office_type: str = "branch"  # headquarters, branch, subsidiary, registered


class CompanyOfficer(BaseModel):
    """Company officer/director"""

    person_id: str
    role: str  # CEO, CFO, Director, Secretary
    appointment_date: date
    resignation_date: Optional[date] = None
    is_active: bool = True
    ownership_percentage: Optional[float] = None


class Company(BaseEntity):
    """Company entity with comprehensive attributes"""

    # Basic Information
    legal_name: str
    trading_name: Optional[str] = None
    company_type: CompanyType
    industry: IndustryType
    sub_industry: Optional[str] = None

    # Registration
    registration_number: str
    registration_country: str
    registration_date: date
    tax_id: str
    lei_code: Optional[str] = None  # Legal Entity Identifier

    # Addresses
    addresses: List[CompanyAddress] = Field(default_factory=list)

    # Structure
    parent_company_id: Optional[str] = None
    subsidiary_ids: List[str] = Field(default_factory=list)
    officers: List[CompanyOfficer] = Field(default_factory=list)

    # Financial
    annual_revenue: Optional[Decimal] = None
    employee_count: Optional[int] = None
    market_cap: Optional[Decimal] = None
    is_public: bool = False
    stock_ticker: Optional[str] = None
    stock_exchange: Optional[str] = None

    # Risk & Compliance
    risk_level: RiskLevel = RiskLevel.LOW
    is_sanctioned: bool = False
    sanction_lists: List[str] = Field(default_factory=list)
    is_shell_company: bool = False

    # Operational
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    business_description: Optional[str] = None

    # Jurisdictions
    operating_countries: List[str] = Field(default_factory=list)
    tax_havens: List[str] = Field(default_factory=list)


# ============================================================================
# ACCOUNT MODELS
# ============================================================================


class Account(BaseEntity):
    """Bank account entity"""

    # Account Identification
    account_number: str
    iban: Optional[str] = None
    swift_code: Optional[str] = None
    routing_number: Optional[str] = None

    # Account Details
    account_type: AccountType
    currency: str = "USD"
    bank_name: str
    bank_id: Optional[str] = None
    branch_name: Optional[str] = None
    branch_code: Optional[str] = None

    # Ownership
    owner_id: str  # Person or Company ID
    owner_type: str  # person, company
    joint_owners: List[str] = Field(default_factory=list)
    beneficial_owners: List[str] = Field(default_factory=list)

    # Status
    status: str = "active"  # active, dormant, frozen, closed
    opened_date: date
    closed_date: Optional[date] = None

    # Balances
    current_balance: Decimal = Decimal("0.00")
    available_balance: Decimal = Decimal("0.00")
    credit_limit: Optional[Decimal] = None

    # Risk & Compliance
    risk_level: RiskLevel = RiskLevel.LOW
    is_monitored: bool = False
    monitoring_reason: Optional[str] = None

    # Activity Metrics
    transaction_count: int = 0
    total_deposits: Decimal = Decimal("0.00")
    total_withdrawals: Decimal = Decimal("0.00")
    average_balance: Decimal = Decimal("0.00")

    # Flags
    is_dormant: bool = False
    has_suspicious_activity: bool = False
    kyc_verified: bool = True
    aml_verified: bool = True


# ============================================================================
# TRANSACTION MODELS
# ============================================================================


class Transaction(BaseEntity):
    """Financial transaction entity"""

    # Transaction Identification
    transaction_id: str = Field(default_factory=lambda: f"TXN-{seeded_uuid_hex()}")
    reference_number: Optional[str] = None

    # Transaction Details
    transaction_type: TransactionType
    transaction_date: datetime
    posting_date: Optional[datetime] = None
    value_date: Optional[date] = None

    # Parties
    from_account_id: Optional[str] = None
    to_account_id: Optional[str] = None
    from_entity_id: Optional[str] = None
    to_entity_id: Optional[str] = None

    # Amounts
    amount: Decimal
    currency: str = "USD"
    exchange_rate: Optional[Decimal] = None
    amount_local: Optional[Decimal] = None
    currency_local: Optional[str] = None

    # Fees
    fee_amount: Decimal = Decimal("0.00")
    fee_currency: str = "USD"

    # Location
    originating_country: Optional[str] = None
    destination_country: Optional[str] = None
    transaction_location: Optional[str] = None
    ip_address: Optional[str] = None

    # Description
    description: Optional[str] = None
    merchant_name: Optional[str] = None
    merchant_category: Optional[str] = None

    # Status
    status: str = "completed"  # pending, completed, failed, reversed

    # Risk & Compliance
    risk_score: float = 0.0  # 0-1 scale
    is_suspicious: bool = False
    alert_ids: List[str] = Field(default_factory=list)
    is_structuring: bool = False
    is_round_amount: bool = False

    # Pattern Detection
    is_part_of_pattern: bool = False
    pattern_id: Optional[str] = None
    pattern_type: Optional[str] = None


# ============================================================================
# TRADE MODELS
# ============================================================================


class Trade(BaseEntity):
    """Trade/Securities transaction entity"""

    # Trade Identification
    trade_id: str = Field(default_factory=lambda: f"TRADE-{seeded_uuid_hex()}")

    # Trader & Account
    trader_id: str
    account_id: str

    # Security Details
    symbol: str
    asset_type: str  # stock, option, future, bond, etf
    exchange: str

    # Trade Details
    side: str  # buy, sell
    quantity: int
    price: Decimal
    total_value: Decimal
    order_type: str  # market, limit, stop, stop_limit

    # Dates
    trade_date: datetime
    settlement_date: datetime

    # Currency
    currency: str = "USD"

    # Insider Trading Indicators
    insider_indicators: List[str] = Field(default_factory=list)

    # Risk & Compliance
    risk_score: float = 0.0  # 0-1 scale
    flagged_for_review: bool = False

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# COMMUNICATION MODELS
# ============================================================================


class Communication(BaseEntity):
    """Communication event entity"""

    # Communication Identification
    communication_id: str = Field(default_factory=lambda: f"COMM-{seeded_uuid_hex()}")

    # Communication Details
    communication_type: CommunicationType
    timestamp: datetime
    duration_seconds: Optional[int] = None  # For calls/meetings

    # Parties
    sender_id: str
    sender_type: str  # person, company
    recipient_ids: List[str] = Field(default_factory=list)
    recipient_types: List[str] = Field(default_factory=list)

    # Content
    subject: Optional[str] = None
    content: Optional[str] = None
    language: str = "en"
    is_encrypted: bool = False

    # Metadata
    platform: Optional[str] = None  # Gmail, WhatsApp, Zoom, etc.
    device_type: Optional[str] = None
    location: Optional[str] = None
    ip_address: Optional[str] = None

    # Attachments
    has_attachments: bool = False
    attachment_count: int = 0
    attachment_types: List[str] = Field(default_factory=list)

    # Sentiment & Analysis
    sentiment_score: Optional[float] = None  # -1 to 1
    contains_financial_terms: bool = False
    contains_suspicious_keywords: bool = False
    suspicious_keywords: List[str] = Field(default_factory=list)

    # Risk & Compliance
    risk_score: float = 0.0
    is_flagged: bool = False
    flag_reason: Optional[str] = None


# ============================================================================
# RELATIONSHIP MODELS
# ============================================================================


class Relationship(BaseEntity):
    """Relationship between entities"""

    # Relationship Identification
    relationship_id: str = Field(default_factory=lambda: f"REL-{seeded_uuid_hex()}")

    # Entities
    from_entity_id: str
    from_entity_type: str  # person, company
    to_entity_id: str
    to_entity_type: str

    # Relationship Details
    relationship_type: RelationshipType
    relationship_strength: float = 0.5  # 0-1 scale

    # Temporal
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool = True

    # Context
    context: Optional[str] = None
    description: Optional[str] = None

    # Metrics
    interaction_count: int = 0
    last_interaction_date: Optional[datetime] = None
    transaction_count: int = 0
    total_transaction_value: Decimal = Decimal("0.00")

    # Risk
    is_suspicious: bool = False
    risk_factors: List[str] = Field(default_factory=list)


# ============================================================================
# PATTERN MODELS
# ============================================================================


class Pattern(BaseEntity):
    """Detected pattern entity"""

    # Pattern Identification
    pattern_id: str = Field(default_factory=lambda: f"PTN-{seeded_uuid_hex()}")
    pattern_type: str  # insider_trading, tbml, fraud_ring, structuring, cato

    # Detection
    detection_date: datetime = Field(default_factory=reference_now)
    detection_method: str
    confidence_score: float  # 0-1 scale

    # Entities Involved
    entity_ids: List[str] = Field(default_factory=list)
    entity_types: List[str] = Field(default_factory=list)
    transaction_ids: List[str] = Field(default_factory=list)
    communication_ids: List[str] = Field(default_factory=list)

    # Pattern Characteristics
    start_date: datetime
    end_date: Optional[datetime] = None
    duration_days: Optional[int] = None
    total_value: Decimal = Decimal("0.00")
    transaction_count: int = 0

    # Risk Assessment
    risk_level: RiskLevel
    severity_score: float  # 0-1 scale

    # Indicators
    indicators: List[str] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)

    # Investigation
    is_investigated: bool = False
    investigation_status: Optional[str] = None
    investigator_id: Optional[str] = None
    investigation_notes: Optional[str] = None

    # Outcome
    is_confirmed: Optional[bool] = None
    outcome: Optional[str] = None
    action_taken: Optional[str] = None


# ============================================================================
# EXPORT ALL MODELS
# ============================================================================

__all__ = [
    # Enums
    "Gender",
    "RiskLevel",
    "AccountType",
    "TransactionType",
    "CommunicationType",
    "CompanyType",
    "IndustryType",
    "RelationshipType",
    # Base
    "BaseEntity",
    # Person
    "Address",
    "PhoneNumber",
    "EmailAddress",
    "IdentificationDocument",
    "Employment",
    "Person",
    # Company
    "CompanyAddress",
    "CompanyOfficer",
    "Company",
    # Account
    "Account",
    # Transaction
    "Transaction",
    # Trade
    "Trade",
    # Communication
    "Communication",
    # Relationship
    "Relationship",
    # Pattern
    "Pattern",
]
