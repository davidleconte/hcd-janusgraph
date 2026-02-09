# Synthetic Data Generator Plan - Enterprise Patterns

**Date:** 2026-01-28
**Author:** David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data GPS
**Purpose:** Comprehensive plan for generating realistic synthetic data matching all advanced patterns

---

## Table of Contents

1. [Overview](#overview)
2. [Data Generator Architecture](#data-generator-architecture)
3. [Generator Modules](#generator-modules)
4. [Implementation Plan](#implementation-plan)
5. [Data Volumes & Scenarios](#data-volumes--scenarios)

---

## Overview

### Objectives

Generate realistic synthetic data for:

- **Multi-modal communications** (SMS, email, phone, chat)
- **Multi-lingual content** (50+ languages)
- **Multi-currency transactions** (150+ currencies)
- **Multi-jurisdictional entities** (200+ countries)
- **Complex networks** (insiders, families, colleagues, subsidiaries, banks)
- **Temporal patterns** (coordinated timing across time zones)
- **Behavioral patterns** (normal + suspicious)

### Key Requirements

1. **Realism** - Data must be indistinguishable from real data
2. **Diversity** - Cover all edge cases and scenarios
3. **Relationships** - Maintain graph consistency
4. **Privacy** - No real PII, fully synthetic
5. **Scalability** - Generate millions of records
6. **Reproducibility** - Seeded random generation
7. **Configurability** - Adjustable parameters

---

## Data Generator Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Master Data Generator                      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Entity     │  │ Relationship │  │   Event      │     │
│  │  Generator   │  │  Generator   │  │  Generator   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                            │                                │
│                            ▼                                │
│                   ┌─────────────────┐                       │
│                   │  Graph Builder  │                       │
│                   └─────────────────┘                       │
│                            │                                │
│         ┌──────────────────┼──────────────────┐            │
│         ▼                  ▼                  ▼            │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐        │
│  │JanusGraph│      │OpenSearch│      │  Files   │        │
│  └──────────┘      └──────────┘      └──────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown

**1. Entity Generators:**

- PersonGenerator (individuals, demographics, attributes)
- CompanyGenerator (corporations, shell companies, subsidiaries)
- AccountGenerator (bank accounts, brokerage accounts, crypto wallets)
- DeviceGenerator (phones, computers, tablets, fingerprints)
- LocationGenerator (addresses, GPS coordinates, IP addresses)

**2. Relationship Generators:**

- FamilyRelationshipGenerator (parent, child, spouse, sibling)
- SocialRelationshipGenerator (friend, colleague, acquaintance)
- CorporateRelationshipGenerator (employee, director, shareholder)
- OwnershipGenerator (owns account, owns company, controls entity)
- CommunicationLinkGenerator (calls, emails, messages)

**3. Event Generators:**

- TransactionGenerator (deposits, withdrawals, transfers, wires)
- TradeGenerator (stock trades, options, futures, forex)
- CommunicationGenerator (SMS, email, phone, chat, video)
- TravelGenerator (flights, hotels, border crossings)
- DocumentGenerator (invoices, contracts, reports)

**4. Pattern Generators:**

- InsiderTradingPatternGenerator
- TBMLPatternGenerator
- FraudRingPatternGenerator
- StructuringPatternGenerator
- CATOPatternGenerator

---

## Generator Modules

### Module 1: Person Generator

**Purpose:** Generate realistic individuals with complete profiles

**Attributes:**

```python
class Person:
    # Identity
    person_id: str
    first_name: str
    last_name: str
    full_name: str
    date_of_birth: date
    ssn: str  # synthetic
    passport_number: str

    # Demographics
    gender: str
    nationality: str
    country_of_residence: str
    city: str
    address: str
    postal_code: str

    # Contact
    email: str
    phone_primary: str
    phone_secondary: str

    # Professional
    occupation: str
    employer: str
    position: str
    annual_income: float

    # Behavioral
    risk_tolerance: str  # low, medium, high
    trading_experience: str  # novice, intermediate, expert

    # Flags
    is_pep: bool  # Politically Exposed Person
    is_insider: bool
    has_material_nonpublic_info: bool
```

**Generation Strategy:**

```python
def generate_person(
    country: str = None,
    occupation: str = None,
    is_insider: bool = False,
    seed: int = None
) -> Person:
    """
    Generate realistic person with cultural/regional accuracy
    """
    faker = Faker(locale=get_locale(country))

    # Generate name appropriate for country
    if country == 'China':
        first_name = faker.first_name_chinese()
        last_name = faker.last_name_chinese()
    elif country == 'Japan':
        first_name = faker.first_name_japanese()
        last_name = faker.last_name_japanese()
    else:
        first_name = faker.first_name()
        last_name = faker.last_name()

    # Generate realistic SSN/ID for country
    ssn = generate_synthetic_id(country)

    # Generate email with realistic patterns
    email_patterns = [
        f"{first_name.lower()}.{last_name.lower()}@{faker.free_email_domain()}",
        f"{first_name[0].lower()}{last_name.lower()}@{faker.company_email()}",
        f"{first_name.lower()}{random.randint(1,999)}@{faker.free_email_domain()}"
    ]
    email = random.choice(email_patterns)

    # Generate phone with country code
    phone = generate_phone_number(country)

    return Person(...)
```

**Realistic Distributions:**

- Age: Normal distribution (mean=45, std=15)
- Income: Log-normal distribution
- Occupation: Based on country's employment statistics
- Location: Based on population density

### Module 2: Company Generator

**Purpose:** Generate companies including shell companies and subsidiaries

**Attributes:**

```python
class Company:
    # Identity
    company_id: str
    company_name: str
    legal_name: str
    registration_number: str
    tax_id: str

    # Incorporation
    country_of_incorporation: str
    incorporation_date: date
    jurisdiction: str

    # Structure
    company_type: str  # LLC, Corp, Partnership, Trust
    is_shell_company: bool
    is_legitimate_business: bool
    parent_company_id: str

    # Operations
    industry: str
    business_description: str
    number_of_employees: int
    annual_revenue: float

    # Physical presence
    has_physical_office: bool
    office_address: str
    website: str

    # Risk indicators
    is_high_risk: bool
    risk_factors: List[str]
```

**Shell Company Indicators:**

```python
def generate_shell_company(
    country: str = 'Panama',
    age_days: int = 180
) -> Company:
    """
    Generate realistic shell company with red flags
    """
    # Shell companies often have:
    # - Generic names
    # - Recent incorporation
    # - No employees
    # - No physical office
    # - Nominee directors
    # - Shared address with many other companies

    generic_names = [
        "Global Trading LLC",
        "International Exports SA",
        "Worldwide Commodities Inc",
        "Universal Holdings Ltd",
        "Premier Investments Corp"
    ]

    # Shared addresses (red flag)
    shell_addresses = [
        "Ugland House, Grand Cayman",  # Famous for 18,000+ companies
        "1209 Orange Street, Wilmington, DE",  # Delaware shell address
        "Trust Company Complex, Tortola, BVI"
    ]

    return Company(
        company_name=random.choice(generic_names),
        incorporation_date=datetime.now() - timedelta(days=age_days),
        country_of_incorporation=country,
        is_shell_company=True,
        has_physical_office=False,
        number_of_employees=0,
        office_address=random.choice(shell_addresses),
        website=None,
        risk_factors=[
            'NO_PHYSICAL_OFFICE',
            'NO_EMPLOYEES',
            'RECENT_INCORPORATION',
            'SHARED_ADDRESS',
            'NOMINEE_DIRECTORS'
        ]
    )
```

### Module 3: Communication Generator

**Purpose:** Generate multi-lingual, multi-channel communications

**Supported Channels:**

- SMS
- Email
- Phone calls
- Instant messaging (WhatsApp, Signal, Telegram)
- Video conferences
- Social media posts

**Multi-Lingual Content:**

```python
class CommunicationGenerator:
    """
    Generate realistic communications in 50+ languages
    """

    LANGUAGES = [
        'en', 'zh', 'es', 'ar', 'ru', 'fr', 'de', 'ja', 'pt', 'hi',
        'ko', 'it', 'tr', 'pl', 'nl', 'sv', 'no', 'da', 'fi', 'el',
        # ... 30 more languages
    ]

    SUSPICIOUS_KEYWORDS = {
        'en': ['insider', 'tip', 'confidential', 'buy now', 'before announcement'],
        'zh': ['内幕', '提示', '机密', '立即购买', '公告前'],
        'es': ['información privilegiada', 'consejo', 'confidencial', 'comprar ahora'],
        'ar': ['معلومات داخلية', 'نصيحة', 'سري', 'اشتر الآن'],
        'ru': ['инсайдер', 'совет', 'конфиденциально', 'купить сейчас'],
        'fr': ['initié', 'conseil', 'confidentiel', 'acheter maintenant'],
        'de': ['Insider', 'Tipp', 'vertraulich', 'jetzt kaufen'],
        # ... more languages
    }

    def generate_suspicious_sms(
        self,
        from_person: Person,
        to_person: Person,
        language: str = 'en',
        urgency: float = 0.8
    ) -> SMS:
        """
        Generate suspicious SMS with realistic content
        """
        templates = {
            'en': [
                "Hey, I heard something big is coming. You should {action} {stock} before {date}.",
                "Confidential info: {company} is about to {event}. Don't tell anyone.",
                "Trust me on this one. {stock} is going to {direction} next week.",
                "Delete this message after reading. {insider_info}."
            ],
            'zh': [
                "嘿，我听说有大事要发生。你应该在{date}之前{action}{stock}。",
                "机密信息：{company}即将{event}。不要告诉任何人。"
            ],
            # ... more languages
        }

        template = random.choice(templates.get(language, templates['en']))

        # Fill in variables
        content = template.format(
            action=random.choice(['buy', 'sell', 'short']),
            stock=generate_stock_symbol(),
            date=generate_future_date(days=7),
            company=generate_company_name(),
            event=random.choice(['announce earnings', 'merge', 'acquire', 'restructure']),
            direction=random.choice(['up', 'down', 'spike', 'crash']),
            insider_info=generate_insider_info(language)
        )

        return SMS(
            from_number=from_person.phone_primary,
            to_number=to_person.phone_primary,
            content=content,
            language=language,
            timestamp=generate_timestamp(),
            sentiment_urgency=urgency,
            contains_suspicious_keywords=True
        )

    def generate_email(
        self,
        from_person: Person,
        to_person: Person,
        subject: str,
        language: str = 'en',
        has_attachment: bool = False
    ) -> Email:
        """
        Generate realistic email with headers
        """
        # Generate realistic email headers
        headers = {
            'From': f"{from_person.full_name} <{from_person.email}>",
            'To': f"{to_person.full_name} <{to_person.email}>",
            'Subject': subject,
            'Date': generate_email_date(),
            'Message-ID': generate_message_id(),
            'MIME-Version': '1.0',
            'Content-Type': 'text/plain; charset=UTF-8',
            # SPF/DKIM/DMARC (can be spoofed for suspicious emails)
            'Authentication-Results': generate_auth_results(is_suspicious=True)
        }

        # Generate body
        body = generate_email_body(language, subject)

        # Generate attachment if needed
        attachment = None
        if has_attachment:
            attachment = generate_attachment(
                filename=f"confidential_{random.randint(1000,9999)}.pdf",
                content_type='application/pdf'
            )

        return Email(
            headers=headers,
            body=body,
            attachment=attachment,
            language=language,
            timestamp=parse_email_date(headers['Date'])
        )
```

### Module 4: Transaction Generator

**Purpose:** Generate realistic financial transactions

**Transaction Types:**

- Deposits (cash, check, wire)
- Withdrawals (ATM, teller, wire)
- Transfers (internal, external, P2P)
- Wire transfers (domestic, international)
- ACH (direct debit, direct credit)
- Card transactions (debit, credit)
- Cryptocurrency (buy, sell, transfer)

**Multi-Currency Support:**

```python
class TransactionGenerator:
    """
    Generate transactions in 150+ currencies
    """

    CURRENCIES = {
        'USD': {'symbol': '$', 'countries': ['USA', 'Ecuador', 'El Salvador']},
        'EUR': {'symbol': '€', 'countries': ['Germany', 'France', 'Italy', 'Spain']},
        'GBP': {'symbol': '£', 'countries': ['UK']},
        'JPY': {'symbol': '¥', 'countries': ['Japan']},
        'CHF': {'symbol': 'Fr', 'countries': ['Switzerland']},
        'CNY': {'symbol': '¥', 'countries': ['China']},
        'AUD': {'symbol': '$', 'countries': ['Australia']},
        'CAD': {'symbol': '$', 'countries': ['Canada']},
        # ... 142 more currencies
    }

    CRYPTO_CURRENCIES = [
        'BTC', 'ETH', 'USDT', 'BNB', 'XRP', 'ADA', 'SOL', 'DOT', 'DOGE', 'MATIC'
    ]

    def generate_structuring_pattern(
        self,
        account: Account,
        total_amount: float = 50000,
        num_deposits: int = 10,
        days: int = 30
    ) -> List[Transaction]:
        """
        Generate structuring pattern (multiple deposits just below $10K)
        """
        transactions = []

        # Split total amount into deposits just below $10K
        amounts = []
        remaining = total_amount
        for i in range(num_deposits):
            # Random amount between $5K and $9.9K
            amount = random.uniform(5000, 9900)
            amounts.append(amount)
            remaining -= amount

        # Distribute over time period
        start_date = datetime.now() - timedelta(days=days)

        for i, amount in enumerate(amounts):
            # Random time within period
            days_offset = random.uniform(0, days)
            timestamp = start_date + timedelta(days=days_offset)

            # Random location (different branches)
            branch = random.choice(['Branch A', 'Branch B', 'Branch C', 'Branch D'])

            transaction = Transaction(
                transaction_id=generate_transaction_id(),
                account_id=account.account_id,
                transaction_type='DEPOSIT',
                amount=amount,
                currency='USD',
                timestamp=timestamp,
                location=branch,
                description='Cash deposit',
                is_suspicious=True,
                risk_indicators=['STRUCTURING', 'JUST_BELOW_THRESHOLD']
            )

            transactions.append(transaction)

        return transactions

    def generate_wire_transfer(
        self,
        from_account: Account,
        to_account: Account,
        amount: float,
        currency: str = 'USD',
        is_international: bool = False
    ) -> Transaction:
        """
        Generate wire transfer with correspondent banking chain
        """
        # Generate correspondent bank chain for international wires
        correspondent_banks = []
        if is_international:
            # Typically 2-5 correspondent banks
            num_correspondents = random.randint(2, 5)
            for i in range(num_correspondents):
                correspondent_banks.append({
                    'bank_name': generate_bank_name(),
                    'swift_code': generate_swift_code(),
                    'country': random.choice(COUNTRIES),
                    'sequence': i + 1
                })

        # Calculate fees
        base_fee = 25 if not is_international else 45
        correspondent_fees = len(correspondent_banks) * 15
        total_fee = base_fee + correspondent_fees

        # Exchange rate if currency conversion
        exchange_rate = None
        if from_account.currency != to_account.currency:
            exchange_rate = get_exchange_rate(
                from_currency=from_account.currency,
                to_currency=to_account.currency,
                date=datetime.now()
            )

        return Transaction(
            transaction_id=generate_transaction_id(),
            from_account_id=from_account.account_id,
            to_account_id=to_account.account_id,
            transaction_type='WIRE_TRANSFER',
            amount=amount,
            currency=currency,
            fee=total_fee,
            exchange_rate=exchange_rate,
            is_international=is_international,
            correspondent_banks=correspondent_banks,
            timestamp=generate_timestamp(),
            swift_message=generate_swift_mt103()
        )
```

### Module 5: Insider Trading Pattern Generator

**Purpose:** Generate complete insider trading scenarios

**Scenario Components:**

1. Corporate insider with MNPI (Material Non-Public Information)
2. Social network (family, friends, colleagues)
3. Communications (multi-lingual, multi-channel)
4. Trading activity (coordinated, suspicious timing)
5. Offshore accounts and shell companies
6. Multi-currency flows
7. Time zone coordination

**Implementation:**

```python
class InsiderTradingPatternGenerator:
    """
    Generate complete insider trading scenario
    """

    def generate_scenario(
        self,
        company: Company,
        announcement_date: datetime,
        announcement_type: str = 'EARNINGS',
        price_impact: float = 0.25,  # 25% price change
        network_size: int = 10,
        languages: List[str] = ['en', 'zh', 'es'],
        countries: List[str] = ['USA', 'Switzerland', 'Cayman Islands'],
        currencies: List[str] = ['USD', 'EUR', 'CHF']
    ) -> InsiderTradingScenario:
        """
        Generate complete insider trading scenario with all dimensions
        """

        # STEP 1: Create corporate insider
        insider = self.person_gen.generate_person(
            country='USA',
            occupation='CFO',
            is_insider=True,
            has_material_nonpublic_info=True
        )

        # Link insider to company
        employment = Employment(
            person_id=insider.person_id,
            company_id=company.company_id,
            position='Chief Financial Officer',
            start_date=datetime.now() - timedelta(days=1825),  # 5 years
            has_access_to_mnpi=True
        )

        # STEP 2: Create social network (6 degrees)
        network = self.create_social_network(
            insider=insider,
            size=network_size,
            countries=countries
        )

        # STEP 3: Create offshore entities for network members
        offshore_entities = []
        for person in network['level_2_friends'] + network['level_3_colleagues']:
            if random.random() < 0.3:  # 30% have offshore entities
                shell_company = self.company_gen.generate_shell_company(
                    country=random.choice(['Cayman Islands', 'BVI', 'Panama', 'Seychelles'])
                )
                offshore_entities.append({
                    'person': person,
                    'company': shell_company
                })

        # STEP 4: Create trading accounts
        accounts = []
        for person in [insider] + network['all']:
            # Personal account
            personal_account = self.account_gen.generate_account(
                owner=person,
                account_type='BROKERAGE',
                country=person.country_of_residence,
                currency=random.choice(currencies)
            )
            accounts.append(personal_account)

            # Offshore account (30% chance)
            if random.random() < 0.3:
                offshore_account = self.account_gen.generate_account(
                    owner=person,
                    account_type='OFFSHORE_BROKERAGE',
                    country=random.choice(['Switzerland', 'Singapore', 'Luxembourg']),
                    currency=random.choice(['CHF', 'EUR', 'USD'])
                )
                accounts.append(offshore_account)

        # STEP 5: Generate communications (multi-lingual, multi-channel)
        communications = []

        # Timeline: 90 days before announcement
        lookback_days = 90
        start_date = announcement_date - timedelta(days=lookback_days)

        # Insider communicates with network
        for person in network['level_1_family'] + network['level_2_friends'][:3]:
            # Choose language based on person's country
            language = self.get_language_for_country(person.country_of_residence)

            # SMS (most common for quick tips)
            if random.random() < 0.7:
                sms = self.comm_gen.generate_suspicious_sms(
                    from_person=insider,
                    to_person=person,
                    language=language,
                    urgency=0.8
                )
                sms.timestamp = start_date + timedelta(
                    days=random.uniform(lookback_days - 30, lookback_days - 1)
                )
                communications.append(sms)

            # Phone call (for more detailed discussion)
            if random.random() < 0.5:
                call = self.comm_gen.generate_phone_call(
                    from_person=insider,
                    to_person=person,
                    duration_minutes=random.randint(15, 45),
                    is_international=(insider.country_of_residence != person.country_of_residence)
                )
                call.timestamp = sms.timestamp + timedelta(hours=random.uniform(1, 24))
                communications.append(call)

            # Email (for sharing documents)
            if random.random() < 0.3:
                email = self.comm_gen.generate_email(
                    from_person=insider,
                    to_person=person,
                    subject=self.generate_suspicious_subject(language),
                    language=language,
                    has_attachment=True  # Confidential document
                )
                email.timestamp = call.timestamp + timedelta(hours=random.uniform(2, 48))
                communications.append(email)

        # STEP 6: Generate trading activity (coordinated timing)
        trades = []

        for person in [insider] + network['all']:
            person_accounts = [a for a in accounts if a.owner_id == person.person_id]

            for account in person_accounts:
                # Trade timing: 1-30 days before announcement
                days_before = random.randint(1, 30)
                trade_date = announcement_date - timedelta(days=days_before)

                # Find if person received communication
                person_comms = [c for c in communications if c.to_person_id == person.person_id]

                if person_comms:
                    # Trade within 48 hours of communication (suspicious!)
                    latest_comm = max(person_comms, key=lambda c: c.timestamp)
                    trade_date = latest_comm.timestamp + timedelta(
                        hours=random.uniform(2, 48)
                    )

                # Trade size: 3-10x normal volume
                historical_avg = account.average_trade_size
                trade_volume = historical_avg * random.uniform(3, 10)

                # Trade type based on announcement impact
                if price_impact > 0:
                    trade_type = 'BUY'  # Positive news
                else:
                    trade_type = 'SELL'  # Negative news

                # Options for higher leverage (more suspicious)
                if random.random() < 0.4:
                    trade = self.trade_gen.generate_option_trade(
                        account=account,
                        security=company.stock_symbol,
                        trade_type='CALL' if price_impact > 0 else 'PUT',
                        contracts=int(trade_volume / 100),
                        strike_price=company.current_stock_price * (1 + price_impact * 0.5),
                        expiration_date=announcement_date + timedelta(days=30),
                        timestamp=trade_date
                    )
                else:
                    trade = self.trade_gen.generate_stock_trade(
                        account=account,
                        security=company.stock_symbol,
                        trade_type=trade_type,
                        shares=int(trade_volume),
                        price=company.current_stock_price,
                        timestamp=trade_date
                    )

                trades.append(trade)

        # STEP 7: Generate currency flows (multi-currency layering)
        currency_flows = []

        for trade in trades:
            if trade.account.currency != 'USD':
                # Currency conversion before trade
                conversion = self.transaction_gen.generate_currency_conversion(
                    from_currency='USD',
                    to_currency=trade.account.currency,
                    amount=trade.total_value,
                    timestamp=trade.timestamp - timedelta(hours=random.uniform(1, 24))
                )
                currency_flows.append(conversion)

        # STEP 8: Generate geospatial data (time zone coordination)
        geospatial_events = []

        for person in [insider] + network['all']:
            # Generate location history
            locations = self.location_gen.generate_location_history(
                person=person,
                start_date=start_date,
                end_date=announcement_date,
                num_locations=random.randint(10, 50)
            )
            geospatial_events.extend(locations)

        # STEP 9: Calculate risk indicators
        risk_indicators = {
            'network_size': len(network['all']),
            'suspicious_communications': len([c for c in communications if c.is_suspicious]),
            'suspicious_trades': len([t for t in trades if t.is_suspicious]),
            'temporal_correlations': self.count_temporal_correlations(communications, trades),
            'languages_used': len(set(c.language for c in communications)),
            'currencies_used': len(set(t.account.currency for t in trades)),
            'countries_involved': len(set(p.country_of_residence for p in [insider] + network['all'])),
            'time_zones': len(set(self.get_timezone(p.country_of_residence) for p in [insider] + network['all'])),
            'offshore_entities': len(offshore_entities),
            'avg_days_before_announcement': np.mean([
                (announcement_date - t.timestamp).days for t in trades
            ])
        }

        # STEP 10: Calculate overall risk score
        risk_score = self.calculate_risk_score(risk_indicators)

        return InsiderTradingScenario(
            scenario_id=generate_scenario_id(),
            company=company,
            announcement_date=announcement_date,
            announcement_type=announcement_type,
            price_impact=price_impact,
            insider=insider,
            network=network,
            offshore_entities=offshore_entities,
            accounts=accounts,
            communications=communications,
            trades=trades,
            currency_flows=currency_flows,
            geospatial_events=geospatial_events,
            risk_indicators=risk_indicators,
            risk_score=risk_score,
            risk_level=self.classify_risk(risk_score)
        )
```

---

## Implementation Plan

### Phase 1: Core Generators (Week 1-2)

- [ ] PersonGenerator
- [ ] CompanyGenerator
- [ ] AccountGenerator
- [ ] DeviceGenerator
- [ ] LocationGenerator

### Phase 2: Relationship Generators (Week 3)

- [ ] FamilyRelationshipGenerator
- [ ] SocialRelationshipGenerator
- [ ] CorporateRelationshipGenerator
- [ ] OwnershipGenerator

### Phase 3: Event Generators (Week 4-5)

- [ ] TransactionGenerator
- [ ] TradeGenerator
- [ ] CommunicationGenerator (multi-lingual)
- [ ] TravelGenerator
- [ ] DocumentGenerator

### Phase 4: Pattern Generators (Week 6-7)

- [ ] InsiderTradingPatternGenerator
- [ ] TBMLPatternGenerator
- [ ] FraudRingPatternGenerator
- [ ] StructuringPatternGenerator
- [ ] CATOPatternGenerator

### Phase 5: Integration & Testing (Week 8)

- [ ] Graph builder integration
- [ ] Data validation
- [ ] Performance optimization
- [ ] Documentation

---

## Data Volumes & Scenarios

### Scenario 1: Insider Trading Network

**Volume:**

- 1 insider
- 50 network members (family, friends, colleagues)
- 10 offshore entities
- 100 accounts
- 500 communications (SMS, email, phone, chat)
- 200 trades
- 50 currency conversions
- 1,000 geospatial events

**Languages:** English, Mandarin, Spanish, French, German
**Countries:** USA, Switzerland, Singapore, Cayman Islands, BVI
**Currencies:** USD, EUR, CHF, SGD
**Time Zones:** EST, CET, SGT

### Scenario 2: TBML Network

**Volume:**

- 20 companies (including 10 shell companies)
- 50 trades
- 200 documents (invoices, bills of lading, contracts)
- 100 communications
- 30 bank accounts across 15 banks
- 10 correspondent banking chains

**Languages:** English, Mandarin, Arabic, Russian
**Countries:** USA, China, UAE, Russia, Panama, Cyprus
**Currencies:** USD, CNY, AED, RUB, EUR

### Scenario 3: Fraud Ring

**Volume:**

- 20 individuals
- 50 accounts
- 1,000 transactions
- 200 devices
- 500 communications

**Languages:** English, Spanish, Portuguese
**Countries:** USA, Mexico, Brazil
**Currencies:** USD, MXN, BRL

---

## Summary

This comprehensive synthetic data generator plan covers:

✅ **Multi-modal** - SMS, email, phone, chat, video, social media
✅ **Multi-lingual** - 50+ languages with realistic content
✅ **Multi-currency** - 150+ currencies + crypto
✅ **Multi-jurisdictional** - 200+ countries, time zones
✅ **Multi-entity** - Individuals, companies, subsidiaries, banks
✅ **Complex networks** - 6 degrees of separation
✅ **Temporal patterns** - Coordinated timing
✅ **Behavioral realism** - Normal + suspicious patterns

**Next Steps:**

1. Review and approve plan
2. Switch to code mode for implementation
3. Generate sample datasets
4. Validate against detection algorithms
5. Deploy to production

---

**Document Version:** 1.0
**Last Updated:** 2026-01-28
**Status:** ✅ Ready for Implementation
