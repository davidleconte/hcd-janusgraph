
# Synthetic Data Generators for Banking Compliance

**Version:** 1.0.0  
**Date:** 2026-01-28  
**Purpose:** Generate realistic synthetic data for testing advanced financial crime detection patterns

---

## Overview

This module provides comprehensive synthetic data generation capabilities for:
- **Multi-modal communications** (SMS, email, phone, chat, video, social media)
- **Multi-lingual content** (50+ languages with sentiment analysis)
- **Multi-currency transactions** (150+ fiat currencies + cryptocurrencies)
- **Multi-jurisdictional entities** (200+ countries, time zones)
- **Complex networks** (6 degrees of separation, hidden connections)
- **Behavioral patterns** (normal + suspicious activities)

---

## Directory Structure

```
banking/data_generators/
├── README.md                          # This file
├── __init__.py                        # Package initialization
├── requirements.txt                   # Python dependencies
├── config.yaml                        # Configuration file
│
├── core/                              # Core entity generators
│   ├── __init__.py
│   ├── person_generator.py           # Generate individuals
│   ├── company_generator.py          # Generate companies/shell companies
│   ├── account_generator.py          # Generate bank/brokerage accounts
│   ├── device_generator.py           # Generate devices/fingerprints
│   └── location_generator.py         # Generate addresses/GPS/IP
│
├── relationships/                     # Relationship generators
│   ├── __init__.py
│   ├── family_relationships.py       # Family connections
│   ├── social_relationships.py       # Friends/colleagues
│   ├── corporate_relationships.py    # Employment/ownership
│   └── communication_links.py        # Call/email/message links
│
├── events/                            # Event generators
│   ├── __init__.py
│   ├── transaction_generator.py      # Financial transactions
│   ├── trade_generator.py            # Stock/options/futures trades
│   ├── communication_generator.py    # Multi-lingual communications
│   ├── travel_generator.py           # Flights/hotels/border crossings
│   └── document_generator.py         # Invoices/contracts/reports
│
├── patterns/                          # Pattern generators
│   ├── __init__.py
│   ├── insider_trading_pattern.py    # Insider trading scenarios
│   ├── tbml_pattern.py               # Trade-based money laundering
│   ├── fraud_ring_pattern.py         # Coordinated fraud networks
│   ├── structuring_pattern.py        # Smurfing/structuring
│   └── cato_pattern.py               # Corporate account takeover
│
└── utils/                             # Utility functions
    ├── __init__.py
    ├── data_models.py                # Pydantic data models
    ├── deterministic.py              # Seeded UUID + reference timestamp for reproducibility
    ├── constants.py                  # Constants (countries, currencies, etc.)
    ├── helpers.py                    # Helper functions
    └── validators.py                 # Data validation
```

---

## Deterministic Pipeline

All generators produce **fully reproducible output** given the same seed. This is enforced by three mechanisms:

1. **Seeded UUIDs** — `data_models.py` default factories use `seeded_uuid_hex()` (SHA-256 counter) instead of `uuid.uuid4()`
2. **Fixed Reference Timestamp** — all date ranges use `REFERENCE_TIMESTAMP = 2026-01-15T12:00:00Z` instead of `datetime.now()`
3. **Counter Reset** — `BaseGenerator.__init__` resets the deterministic counter when a seed is provided

```python
from banking.data_generators.core.person_generator import PersonGenerator

gen1 = PersonGenerator(seed=42)
gen2 = PersonGenerator(seed=42)

p1 = gen1.generate()
p2 = gen2.generate()

assert p1.id == p2.id              # Same ID
assert p1.full_name == p2.full_name  # Same name
assert p1.created_at == p2.created_at  # Same timestamp
```

The deterministic utilities are in `banking/data_generators/utils/deterministic.py`.

---

## Installation

### Prerequisites
```bash
# Python 3.9+
python --version

# Install dependencies
pip install -r requirements.txt
```

### Dependencies
- `faker>=20.0.0` - Generate fake data
- `pydantic>=2.0.0` - Data validation
- `numpy>=1.24.0` - Numerical operations
- `pandas>=2.0.0` - Data manipulation
- `langdetect>=1.0.9` - Language detection
- `googletrans>=4.0.0` - Translation
- `textblob>=0.17.1` - Sentiment analysis
- `phonenumbers>=8.13.0` - Phone number generation
- `pycountry>=22.3.5` - Country/currency data

---

## Quick Start

### Example 1: Generate a Person
```python
from banking.data_generators.core.person_generator import PersonGenerator

# Initialize generator
person_gen = PersonGenerator(seed=42)

# Generate a person
person = person_gen.generate(
    country='USA',
    occupation='CFO',
    is_insider=True
)

print(f"Name: {person.full_name}")
print(f"Email: {person.email}")
print(f"Phone: {person.phone_primary}")
print(f"Occupation: {person.occupation}")
```

### Example 2: Generate Insider Trading Scenario
```python
from banking.data_generators.patterns.insider_trading_pattern import InsiderTradingPatternGenerator

# Initialize generator
pattern_gen = InsiderTradingPatternGenerator(seed=42)

# Generate complete scenario
scenario = pattern_gen.generate_scenario(
    company_symbol='AAPL',
    announcement_date='2024-02-15',
    announcement_type='EARNINGS',
    price_impact=0.25,  # 25% price increase
    network_size=50,
    languages=['en', 'zh', 'es'],
    countries=['USA', 'Switzerland', 'Singapore'],
    currencies=['USD', 'EUR', 'CHF']
)

print(f"Scenario ID: {scenario.scenario_id}")
print(f"Insider: {scenario.insider.full_name}")
print(f"Network Size: {len(scenario.network['all'])}")
print(f"Communications: {len(scenario.communications)}")
print(f"Trades: {len(scenario.trades)}")
print(f"Risk Score: {scenario.risk_score}/100")
```

### Example 3: Generate Multi-Lingual Communications
```python
from banking.data_generators.events.communication_generator import CommunicationGenerator

# Initialize generator
comm_gen = CommunicationGenerator(seed=42)

# Generate suspicious SMS in Mandarin
sms = comm_gen.generate_suspicious_sms(
    from_person=insider,
    to_person=friend,
    language='zh',
    urgency=0.9
)

print(f"From: {sms.from_number}")
print(f"To: {sms.to_number}")
print(f"Language: {sms.language}")
print(f"Content: {sms.content}")
print(f"Sentiment: {sms.sentiment}")
print(f"Suspicious: {sms.contains_suspicious_keywords}")
```

---

## Business Use Cases

### 1. Insider Trading Detection
**Business Value:** Prevent illegal insider trading, avoid SEC fines ($millions), protect market integrity

**Generated Data:**
- Corporate insiders with MNPI access
- Social networks (family, friends, colleagues)
- Multi-lingual communications (SMS, email, phone, chat)
- Coordinated trading activity
- Offshore accounts and shell companies
- Multi-currency flows
- Time zone coordination patterns

**Detection Capabilities:**
- Temporal correlation (communication → trade within 48 hours)
- Network analysis (6 degrees of separation)
- Sentiment analysis (urgency, secrecy)
- Geospatial anomalies (impossible travel)
- Behavioral changes (unusual trading volume)

### 2. Trade-Based Money Laundering (TBML)
**Business Value:** Detect sophisticated money laundering, comply with AML regulations, prevent terrorist financing

**Generated Data:**
- Circular trading networks (10+ hops)
- Price manipulation (over/under-invoicing)
- Shell company networks (100+ entities)
- Multi-currency layering
- Correspondent banking chains (10+ banks)
- Cryptocurrency settlement
- Document inconsistencies

**Detection Capabilities:**
- Circular path detection
- Price variance analysis (vs. market rates)
- Shell company identification
- Sanctions screening
- High-risk jurisdiction flagging

### 3. Fraud Ring Detection
**Business Value:** Prevent coordinated fraud, reduce losses, protect customers

**Generated Data:**
- Multiple accounts with shared attributes
- Coordinated transaction timing
- Similar transaction amounts (low variance)
- Device fingerprint sharing
- Geolocation clustering

**Detection Capabilities:**
- Velocity checks
- Amount variance analysis
- Device fingerprinting
- Geospatial clustering
- Communication pattern analysis

### 4. AML Structuring Detection
**Business Value:** Detect smurfing, comply with BSA/AML, prevent money laundering

**Generated Data:**
- Multiple deposits just below $10K threshold
- Distributed across time and locations
- Multiple accounts/individuals
- Coordinated timing patterns

**Detection Capabilities:**
- Threshold proximity detection
- Temporal pattern analysis
- Account linkage
- Coordination scoring

### 5. Corporate Account Takeover (CATO)
**Business Value:** Prevent BEC fraud, protect corporate accounts, reduce wire fraud losses

**Generated Data:**
- Email spoofing (SPF/DKIM failures)
- Login anomalies (unusual IP, device, time)
- Authorization bypass attempts
- Vendor impersonation
- API credential theft

**Detection Capabilities:**
- Email authentication validation
- Behavioral analysis
- Authorization workflow monitoring
- Vendor validation
- API security monitoring

---

## Technical Architecture

### Data Flow
```
┌─────────────────────────────────────────────────────────────┐
│                   Configuration                              │
│              (config.yaml + seed)                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                Core Entity Generators                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Person  │  │ Company  │  │ Account  │  │ Location │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
