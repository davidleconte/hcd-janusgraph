
# Enterprise Advanced Patterns & Use Cases - Master Plan

**Date:** 2026-01-28  
**Author:** IBM Bob  
**Purpose:** Plan the most advanced, complex, and business-valuable patterns for retail, corporate, and investment banking

---

## Executive Summary

This document outlines **Phase 8-10** implementation plans for ultra-advanced financial crime detection patterns that incorporate:
- **Multi-modal data** (SMS, email, phone, chat, documents)
- **Multi-lingual analysis** (NLP across 50+ languages)
- **Multi-currency** (150+ currencies, crypto, commodities)
- **Multi-jurisdictional** (200+ countries, time zones, regulations)
- **Multi-entity** (individuals, companies, subsidiaries, banks, regulators)
- **Multi-channel** (retail, corporate, investment banking, wealth management)
- **Real-time + Historical** analysis
- **Graph + Vector + Time-series** hybrid analytics

---

## Table of Contents

1. [Current State Assessment](#current-state-assessment)
2. [Advanced Pattern Categories](#advanced-pattern-categories)
3. [Phase 8: Multi-Modal Intelligence](#phase-8-multi-modal-intelligence)
4. [Phase 9: Cross-Entity Network Analysis](#phase-9-cross-entity-network-analysis)
5. [Phase 10: Predictive & Prescriptive Analytics](#phase-10-predictive-prescriptive-analytics)
6. [Data Model Extensions](#data-model-extensions)
7. [Technology Stack Enhancements](#technology-stack-enhancements)
8. [Implementation Roadmap](#implementation-roadmap)

---

## Current State Assessment

### ✅ What We Have (Phases 1-7)

**Infrastructure:**
- JanusGraph + HCD (Cassandra)
- OpenSearch 3.4.0 with k-NN
- Vector embeddings (384-dim)
- Docker orchestration
- Monitoring (Prometheus, Grafana)

**Use Cases Implemented:**
1. Sanctions screening (vector similarity)
2. AML structuring detection (pattern matching)
3. Fraud detection (anomaly detection)
4. Customer 360 (graph relationships)

**Capabilities:**
- Transaction-level analysis
- Basic relationship detection
- Vector similarity search
- Time-series aggregations
- Simple risk scoring

### ❌ What We Need (Phases 8-10)

**Missing Dimensions:**
1. **Communication analysis** (SMS, email, phone, chat)
2. **Multi-lingual NLP** (sentiment, entity extraction, translation)
3. **Document intelligence** (contracts, invoices, reports)
4. **Behavioral biometrics** (typing patterns, mouse movements)
5. **Geospatial analysis** (location tracking, movement patterns)
6. **Social network analysis** (LinkedIn, Twitter, Facebook)
7. **News & media monitoring** (adverse media, PEP screening)
8. **Regulatory intelligence** (rule changes, enforcement actions)
9. **Market data integration** (prices, volumes, volatility)
10. **Predictive modeling** (ML/AI for future risk)

---

## Advanced Pattern Categories

### Category 1: Retail Banking Patterns

#### 1.1 Consumer Fraud Rings
**Complexity Level:** ⭐⭐⭐⭐⭐

**Pattern Description:**
Organized fraud rings targeting retail banking:
- Synthetic identity fraud (fake SSNs, addresses)
- Account takeover (credential stuffing, SIM swapping)
- Check kiting across multiple banks
- ATM skimming networks
- Mobile banking trojans
- P2P payment fraud (Zelle, Venmo scams)

**Data Sources:**
- Transaction data (deposits, withdrawals, transfers)
- Device fingerprints (IP, browser, mobile device)
- Biometric data (face ID, fingerprint, voice)
- Communication logs (SMS, email, app notifications)
- Geolocation data (GPS, cell tower, WiFi)
- Social media profiles (Facebook, Instagram, TikTok)
- Credit bureau data (FICO, Experian, Equifax)
- Dark web monitoring (stolen credentials, card dumps)

**Graph Model:**
```
Person → owns → Account → has → Transaction
Person → uses → Device → has → Fingerprint
Person → located_at → Location → in → GeoFence
Person → communicates_with → Person (via SMS/Email/Call)
Person → connected_to → SocialProfile → friends_with → Person
Device → infected_with → Malware → variant_of → MalwareFamily
Account → linked_to → Account (via shared attributes)
Transaction → flagged_by → FraudRule → severity → RiskScore
```

**Detection Techniques:**
1. **Device fingerprinting** - Detect account takeover
2. **Velocity checks** - Multiple accounts from same device
3. **Geolocation anomalies** - Impossible travel
4. **Behavioral biometrics** - Typing speed, mouse patterns
5. **Social network analysis** - Fraud ring identification
6. **Communication pattern analysis** - Coordinated activity
7. **Synthetic identity detection** - Inconsistent attributes
8. **Dark web correlation** - Stolen credential usage

#### 1.2 Elder Financial Abuse
**Complexity Level:** ⭐⭐⭐⭐

**Pattern Description:**
Exploitation of elderly customers:
- Caregiver theft (unauthorized withdrawals)
- Romance scams (online dating fraud)
- Grandparent scams (fake emergency calls)
- Investment fraud (Ponzi schemes targeting seniors)
- Reverse mortgage fraud
- Power of attorney abuse

**Data Sources:**
- Customer demographics (age, cognitive status)
- Transaction patterns (sudden large withdrawals)
- Communication logs (phone calls, emails)
- Relationship data (family, caregivers, POA)
- Behavioral changes (login frequency, transaction types)
- Medical records (dementia, Alzheimer's diagnosis)
- Court records (guardianship, conservatorship)

**Detection Techniques:**
1. **Behavioral change detection** - Sudden pattern shifts
2. **Relationship analysis** - New contacts with access
3. **Communication monitoring** - Suspicious conversations
4. **Cognitive decline indicators** - Erratic behavior
5. **Caregiver background checks** - Criminal history
6. **Transaction anomaly detection** - Unusual amounts/frequency

### Category 2: Corporate Banking Patterns

#### 2.1 Trade-Based Money Laundering (TBML) - Enhanced
**Complexity Level:** ⭐⭐⭐⭐⭐⭐

**Pattern Description:**
Sophisticated TBML schemes involving:
- Over/under-invoicing (price manipulation)
- Multiple invoicing (same shipment, multiple payments)
- Phantom shipments (no actual goods)
- Misrepresented quality/quantity
- Circular trading (goods loop through multiple entities)
- Free trade zone abuse (Dubai, Hong Kong, Singapore)
- Cryptocurrency settlement (bypass banking system)
- Shell company networks (100+ entities)
- Correspondent banking chains (10+ banks)

**Data Sources:**
- Trade finance documents (invoices, bills of lading, letters of credit)
- Customs declarations (import/export data)
- Shipping manifests (container tracking, vessel movements)
- Commodity price databases (market prices for comparison)
- Company registries (beneficial ownership, incorporation dates)
- Sanctions lists (OFAC, EU, UN, local)
- News & media (adverse media, PEP mentions)
- Bank statements (multiple jurisdictions)
- Cryptocurrency transactions (blockchain analysis)
- Email communications (between traders)
- Phone call logs (international calls)
- Meeting records (in-person, video conferences)
- Contract documents (purchase agreements)
- Insurance policies (cargo insurance)
- Warehouse receipts (storage locations)

**Multi-Dimensional Analysis:**

**Dimension 1: Geographic**
- Origin country (high-risk jurisdictions)
- Destination country (sanctions, tax havens)
- Transit countries (free trade zones)
- Shipping routes (unusual paths)
- Time zones (coordination timing)

**Dimension 2: Temporal**
- Trade frequency (velocity)
- Seasonal patterns (commodity cycles)
- Time between trades (rapid cycling)
- Payment timing (advance, delayed)
- Document timing (backdating)

**Dimension 3: Financial**
- Price variance (vs. market rates)
- Currency used (exotic currencies)
- Payment method (wire, crypto, cash)
- Amount patterns (just below reporting threshold)
- Profit margins (unrealistic)

**Dimension 4: Entity**
- Company age (newly incorporated)
- Ownership structure (complex, opaque)
- Business activity (inconsistent with trade)
- Employee count (shell company indicators)
- Physical presence (no office, no staff)

**Dimension 5: Commodity**
- Product type (dual-use goods, luxury items)
- Quality grade (misrepresented)
- Quantity (impossible volumes)
- Unit of measure (inconsistent)
- HS codes (tariff classification manipulation)

**Dimension 6: Communication**
- Email sentiment (urgency, secrecy)
- Language used (multiple languages)
- Communication frequency (coordinated)
- Participants (hidden relationships)
- Content analysis (code words, euphemisms)

**Graph Model (Extended):**
```
Company → incorporated_in → Country → has_risk_level → RiskScore
Company → owned_by → Person → has_relationship → Person
Company → trades_with → Company → via → Trade
Trade → documented_by → Invoice → has_price → Price
Trade → shipped_via → Vessel → docked_at → Port
Trade → involves → Commodity → has_market_price → MarketPrice
Trade → paid_through → Bank → located_in → Country
Trade → settled_in → Currency → exchange_rate → Rate
Trade → insured_by → InsurancePolicy → issued_by → Insurer
Person → communicates_via → Email → contains → Entity
Person → calls → Person → from → PhoneNumber → in → Country
Person → meets_with → Person → at → Location → on → Date
Company → mentioned_in → NewsArticle → sentiment → Sentiment
Company → sanctioned_by → Regulator → effective_date → Date
Bank → correspondent_of → Bank → in → Country
Trade → flagged_by → TBMLRule → confidence → Score
```

**Detection Algorithm (Pseudo-code):**
```python
def detect_advanced_tbml(trade_network):
    """
    Ultra-advanced TBML detection with 20+ indicators
    """
    risk_score = 0
    indicators = []
    
    # 1. CIRCULAR TRADING DETECTION
    cycles = find_circular_paths(
        start_company=trade.origin,
        max_hops=10,
        time_window='90d'
    )
    if len(cycles) > 0:
        risk_score += 25
        indicators.append('CIRCULAR_TRADING')
    
    # 2. PRICE MANIPULATION ANALYSIS
    market_price = get_market_price(
        commodity=trade.commodity,
        date=trade.date,
        quality=trade.quality
    )
    price_variance = abs(trade.price - market_price) / market_price * 100
    if price_variance > 50:
        risk_score += 20
        indicators.append('PRICE_MANIPULATION')
    
    # 3. SHELL COMPANY NETWORK
    shell_indicators = analyze_company_network(trade.companies)
    # - No physical office
    # - Incorporated in last 6 months
    # - No employees
    # - No website
    # - Shared address with 10+ other companies
    # - Nominee directors
    shell_count = sum(1 for c in shell_indicators if c.is_shell)
    if shell_count >= 3:
        risk_score += 30
        indicators.append('SHELL_NETWORK')
    
    # 4. SANCTIONS EXPOSURE
    sanctions_hits = check_sanctions(
        entities=trade.all_entities,
        lists=['OFAC', 'EU', 'UN', 'UK', 'OFSI']
    )
    if sanctions_hits > 0:
        risk_score += 40
        indicators.append('SANCTIONS_EXPOSURE')
    
    # 5. HIGH-RISK JURISDICTIONS
    high_risk_countries = [
        'North Korea', 'Iran', 'Syria', 'Venezuela',
        'Myanmar', 'Belarus', 'Zimbabwe'
    ]
    jurisdiction_risk = sum(
        1 for country in trade.countries 
        if country in high_risk_countries
    )
    if jurisdiction_risk > 0:
        risk_score += 15 * jurisdiction_risk
        indicators.append('HIGH_RISK_JURISDICTION')
    
    # 6. COMMUNICATION ANALYSIS
    emails = get_communications(
        entities=trade.participants,
        types=['email', 'sms', 'chat'],
        time_window='30d'
    )
    
    # Multi-lingual sentiment analysis
    sentiments = []
    for email in emails:
        # Detect language
        lang = detect_language(email.content)
        # Translate to English if needed
        if lang != 'en':
            email.content = translate(email.content, target='en')
        # Sentiment analysis
        sentiment = analyze_sentiment(email.content)
        sentiments.append(sentiment)
        
        # Check for suspicious keywords
        suspicious_keywords = [
            'urgent', 'confidential', 'off the books',
            'cash only', 'no questions', 'under the table',
            'backdated', 'fake invoice', 'shell company'
        ]
        if any(kw in email.content.lower() for kw in suspicious_keywords):
            risk_score += 10
            indicators.append('SUSPICIOUS_COMMUNICATION')
    
    # 7. TEMPORAL PATTERN ANALYSIS
    trade_velocity = calculate_velocity(
        company=trade.origin,
        time_window='30d'
    )
    if trade_velocity > 10:  # >10 trades per month
        risk_score += 15
        indicators.append('HIGH_VELOCITY')
    
    # 8. CRYPTOCURRENCY SETTLEMENT
    crypto_txns = find_crypto_transactions(
        entities=trade.participants,
        time_window='7d'
    )
    if len(crypto_txns) > 0:
        risk_score += 20
        indicators.append('CRYPTO_SETTLEMENT')
    
    # 9. CORRESPONDENT BANKING CHAIN
    bank_chain = trace_payment_path(trade.payment)
    if len(bank_chain) > 5:
        risk_score += 15
        indicators.append('COMPLEX_BANKING_CHAIN')
    
    # 10. DOCUMENT INCONSISTENCIES
    docs = [trade.invoice, trade.bill_of_lading, trade.customs_declaration]
    inconsistencies = check_document_consistency(docs)
    if inconsistencies > 0:
        risk_score += 10 * inconsistencies
        indicators.append('DOCUMENT_INCONSISTENCY')
    
    # 11. GEOSPATIAL ANOMALIES
    shipping_route = get_shipping_route(trade.vessel)
    expected_route = calculate_optimal_route(
        origin=trade.origin_port,
        destination=trade.destination_port
    )
    route_deviation = calculate_deviation(shipping_route, expected_route)
    if route_deviation > 500:  # >500 nautical miles
        risk_score += 15
        indicators.append('UNUSUAL_SHIPPING_ROUTE')
    
    # 12. BEHAVIORAL BIOMETRICS (for online trades)
    if trade.is_online:
        biometrics = analyze_biometrics(trade.user_session)
        if biometrics.is_anomalous:
            risk_score += 10
            indicators.append('BIOMETRIC_ANOMALY')
    
    # 13. SOCIAL NETWORK ANALYSIS
    social_connections = analyze_social_networks(
        participants=trade.participants,
        platforms=['LinkedIn', 'Facebook', 'Twitter']
    )
    hidden_relationships = find_hidden_connections(social_connections)
    if len(hidden_relationships) > 0:
        risk_score += 15
        indicators.append('HIDDEN_RELATIONSHIPS')
    
    # 14. NEWS & MEDIA MONITORING
    adverse_media = search_adverse_media(
        entities=trade.all_entities,
        time_window='365d'
    )
    if len(adverse_media) > 0:
        risk_score += 10 * len(adverse_media)
        indicators.append('ADVERSE_MEDIA')
    
    # 15. REGULATORY INTELLIGENCE
    enforcement_actions = check_enforcement_actions(
        entities=trade.all_entities,
        regulators=['FinCEN', 'FCA', 'BaFin', 'FINMA']
    )
    if len(enforcement_actions) > 0:
        risk_score += 25
        indicators.append('REGULATORY_ACTION')
    
    # 16. MARKET DATA CORRELATION
    market_volatility = get_market_volatility(
        commodity=trade.commodity,
        date=trade.date
    )
    if market_volatility > 0.3:  # High volatility
        # Check if trade price exploits volatility
        if abs(trade.price - market_price) / market_price > market_volatility:
            risk_score += 10
            indicators.append('VOLATILITY_EXPLOITATION')
    
    # 17. MULTI-CURRENCY ANALYSIS
    currencies_used = get_currencies(trade.payment_chain)
    if len(currencies_used) > 3:
        risk_score += 10
        indicators.append('MULTI_CURRENCY_LAYERING')
    
    # 18. TIME ZONE COORDINATION
    time_zones = [get_timezone(c.country) for c in trade.companies]
    if len(set(time_zones)) > 5:
        # Check if communications/trades coordinated across time zones
        coordination_score = analyze_temporal_coordination(
            events=trade.all_events,
            time_zones=time_zones
        )
        if coordination_score > 0.7:
            risk_score += 15
            indicators.append('TIMEZONE_COORDINATION')
    
    # 19. SUBSIDIARY NETWORK ANALYSIS
    subsidiaries = find_all_subsidiaries(trade.companies)
    if len(subsidiaries) > 20:
        # Complex corporate structure
        risk_score += 20
        indicators.append('COMPLEX_CORPORATE_STRUCTURE')
    
    # 20. BANK NETWORK ANALYSIS
    banks_involved = get_all_banks(trade.payment_chain)
    if len(banks_involved) > 10:
        risk_score += 15
        indicators.append('COMPLEX_BANK_NETWORK')
    
    # FINAL RISK ASSESSMENT
    risk_level = classify_risk(risk_score)
    
    return {
        'risk_score': min(100, risk_score),
        'risk_level': risk_level,
        'indicators': indicators,
        'recommendation': get_recommendation(risk_level),
        'priority': get_priority(risk_level),
        'assigned_to': assign_investigator(risk_level),
        'sla': get_sla(risk_level)
    }
```

#### 2.2 Corporate Account Takeover (CATO)
**Complexity Level:** ⭐⭐⭐⭐⭐

**Pattern Description:**
Sophisticated attacks on corporate banking:
- Business email compromise (BEC)
- CEO fraud (fake wire transfer requests)
- Vendor impersonation (fake invoices)
- Payroll diversion (employee account changes)
- ACH fraud (unauthorized debits)
- API credential theft (OAuth token hijacking)

**Data Sources:**
- Email headers (SPF, DKIM, DMARC validation)
- Login patterns (IP, device, time, location)
- Transaction authorization (dual control, maker-checker)
- Communication logs (email, phone, chat)
- Employee directory (org chart, reporting lines)
- Vendor database (legitimate vendors, payment terms)
- API logs (authentication, authorization, rate limiting)
- Network traffic (DDoS, port scanning, malware)

**Detection Techniques:**
1. **Email authentication** - SPF/DKIM/DMARC failures
2. **Behavioral analysis** - Login anomalies
3. **Authorization bypass** - Single-person approvals
4. **Communication verification** - Out-of-band confirmation
5. **Vendor validation** - Bank account changes
6. **API security** - Token theft, replay attacks
7. **Network monitoring** - Malware, C2 communication

### Category 3: Investment Banking Patterns

#### 3.1 Market Manipulation - Enhanced Insider Trading
**Complexity Level:** ⭐⭐⭐⭐⭐⭐

**Pattern Description:**
Ultra-sophisticated insider trading networks:
- **Information flow:** Corporate insiders → Family → Friends → Offshore entities
- **Communication channels:** SMS, WhatsApp, Signal, Telegram, encrypted email
- **Languages:** English, Mandarin, Spanish, Arabic, Russian, French, German
- **Currencies:** USD, EUR, GBP, JPY, CHF, crypto (BTC, ETH, USDT)
- **Countries:** USA, UK, Switzerland, Singapore, Hong Kong, Cayman Islands
- **Time zones:** EST, GMT, CET, SGT, HKT (coordinated trading)
- **Entities:** Individuals, family trusts, shell companies, hedge funds
- **Subsidiaries:** Parent company → 50+ subsidiaries → offshore SPVs
- **Banks:** 20+ banks across 10+ countries
- **Brokers:** Multiple brokers to avoid detection
- **Accounts:** Personal, corporate, trust, nominee accounts

**Data Sources (Comprehensive):**

**1. Trading Data:**
- Order book (limit orders, market orders, stop-loss)
- Execution data (fills, partial fills, cancellations)
- Position data (long, short, options, futures)
- Margin data (leverage, margin calls, liquidations)
- Dark pool trades (off-exchange transactions)
- High-frequency trading (HFT) patterns

**2. Communication Data:**
- **SMS messages** (50+ languages, sentiment analysis)
- **Email** (headers, attachments, metadata)
- **Phone calls** (duration, frequency, participants, transcripts)
- **Instant messaging** (WhatsApp, Signal, Telegram, WeChat)
- **Video conferences** (Zoom, Teams, WebEx recordings)
- **Social media** (LinkedIn, Twitter, Facebook, Instagram)
- **Meeting calendars** (in-person meetings, locations)
- **Travel records** (flights, hotels, expense reports)

**3. Corporate Data:**
- **Press releases** (earnings, M&A, product launches)
- **SEC filings** (10-K, 10-Q, 8-K, insider transactions)
- **Board minutes** (confidential discussions)
- **Employee access logs** (who accessed what, when)
- **Email server logs** (internal communications)
- **Document management** (confidential documents)

**4. Financial Data:**
- **Bank statements** (multiple banks, multiple countries)
- **Brokerage statements** (multiple brokers)
- **Tax returns** (income sources, capital gains)
- **Trust documents** (beneficial ownership)
- **Corporate registries** (company ownership, directors)
- **Real estate records** (property ownership, transfers)

**5. Behavioral Data:**
- **Login patterns** (time, location, device)
- **Trading patterns** (frequency, size, timing)
- **Communication patterns** (who talks to whom, when)
- **Travel patterns** (business trips, vacations)
- **Lifestyle changes** (sudden wealth, luxury purchases)

**6. External Data:**
- **News & media** (Bloomberg, Reuters, WSJ, FT)
- **Social media sentiment** (Twitter, StockTwits, Reddit)
- **Analyst reports** (buy/sell recommendations)
- **Market data** (prices, volumes, volatility)
- **Economic indicators** (GDP, inflation, interest rates)
- **Regulatory filings** (enforcement actions, investigations)

**Multi-Dimensional Graph Model:**

```
# ENTITIES
Person → works_for → Company → subsidiary_of → ParentCompany
Person → family_of → Person → friend_of → Person
Person → owns → Account → at → Broker → in → Country
Person → owns → TrustAccount → beneficiary → Person
Person → director_of → ShellCompany → incorporated_in → TaxHaven
Person → member_of → ColleagueGroup → works_in → Department

# COMMUNICATIONS (Multi-lingual, Multi-channel)
Person → sends_sms → Person → in_language → Language → sentiment → Sentiment
Person → sends_email → Person → contains_attachment → Document
Person → calls → Person → duration → Minutes → from → Country
Person → messages → Person → via → Platform → encrypted → Boolean
Person → meets_with → Person → at → Location → on → Date
Person → travels_to → Country → on → Date → for → Purpose

# TRADING
Person → places_order → Order → for → Security → at → Price
Order → executed_at → Timestamp → in → TimeZone
Order → filled_by → Trade → volume → Shares → value → Amount
Trade → settled_in → Currency → exchange_rate → Rate
Account → holds_position → Position → in → Security → quantity → Shares

# CORPORATE EVENTS
Company → announces → Event → on → Date → type → EventType
Event → affects → Security → price_impact → Percentage
Person → has_access_to → Event → access_date → Date
Person → attended_meeting → Meeting → about → Event

# RELATIONSHIPS (Hidden connections)
Person → related_to → Person → via → Relationship → strength → Score
Person → connected_via → SocialMedia → platform → Platform
Person → shares_address → Person → address → Address
Person → shares_phone → Person → phone → PhoneNumber
Person → shares_email_domain → Person → domain → Domain

# FINANCIAL FLOWS
Account → transfers_to → Account → amount → Amount → on → Date
Account → receives_from → Account → amount → Amount → currency → Currency
Account → wires_to → Bank → via → CorrespondentBank → in → Country

# SUBSIDIARIES & CORPORATE STRUCTURE
ParentCompany → owns → Subsidiary → percentage → Ownership
Subsidiary → located_in → Country → jurisdiction → Jurisdiction
Subsidiary → has_director → Person → appointed_on → Date
Subsidiary → transacts_with → Subsidiary → amount → Amount

# BANKS & BROKERS
Bank → correspondent_of → Bank → in → Country
Broker → clears_through → ClearingHouse → in → Country
Account → linked_to → Account → via → SharedAttribute

# REGULATORY
Person → investigated_by → Regulator → case_id → CaseID
Company → fined_by → Regulator → amount → Amount → reason → Reason
Trade → flagged_by → SurveillanceSystem → rule → RuleName

# GEOSPATIAL
Person → located_at → Location → at → Timestamp
Location → in → City → in → Country → timezone → TimeZone
Trade → originated_from → IPAddress → in → Country

# TEMPORAL
Event → occurred_at → Timestamp → in → TimeZone
Trade → placed_before → Event → days → Days
Communication → sent_before → Trade → hours → Hours
```

**Advanced Detection Algorithm:**

```python
def detect_ultra_advanced_insider_trading(
    target_company,
    announcement_date,
    lookback_days=90
):
    """
    Ultra-advanced insider trading detection with 30+ dimensions
    """
    
    # PHASE 1: IDENTIFY INSIDERS
    insiders = g.V().hasLabel('Person'). \
        or_(
            # Direct employees
            out('works_for').has('company_id', target_company),
            # Board members
            out('director_of').has('company_id', target_company),
            # Consultants
            out('consults_for').has('company_id', target_company),
            # Lawyers
            out('legal_counsel_for').has('company_id', target_company),
            # Auditors
            out('audits').has('company_id', target_company),
            # Investment bankers
            out('advises').has('company_id', target_company)
        ). \
        has('has_material_nonpublic_info', True). \
        dedup(). \
        toList()
    
    # PHASE 2: MAP SOCIAL NETWORKS (6 degrees of separation)
    network = {}
    for insider in insiders:
        # Level 1: Direct family
        family = g.V(insider). \
            out('family_of'). \
            dedup(). \
            toList()
        
        # Level 2: Close friends
        friends = g.V(insider). \
            out('friend_of'). \
            has('relationship_strength', gte(0.7)). \
            dedup(). \
            toList()
        
        # Level 3: Colleagues
        colleagues = g.V(insider). \
            out('works_with'). \
            dedup(). \
            toList()
        
        # Level 4: Social media connections
        social = g.V(insider). \
            out('connected_via'). \
            hasLabel('SocialMedia'). \
            in('connected_via'). \
            dedup(). \
            toList()
        
        # Level 5: Shared addresses/phones (hidden connections)
        hidden = g.V(insider). \
            or_(
                out('shares_address'),
                out('shares_phone'),
                out('shares_email_domain')
            ). \
            dedup(). \
            toList()
        
        # Level 6: Offshore entities
        offshore = g.V(insider). \
            out('owns'). \
            hasLabel('ShellCompany'). \
            out('incorporated_in'). \
            has('is_tax_haven', True). \
            in('incorporated_in'). \
            out('owned_by'). \
            dedup(). \
            toList()
        
        network[insider] = {
            'family': family,
            'friends': friends,
            'colleagues': colleagues,
            'social': social,
            'hidden': hidden,
            'offshore': offshore,
            'all': list(set(family + friends + colleagues + social + hidden + offshore))
        }
    
    # PHASE 3: ANALYZE COMMUNICATIONS (Multi-lingual, Multi-channel)
    suspicious_communications = []
    
    for insider, connections in network.items():
        for person in connections['all']:
            # Get all communications in lookback period
            comms = g.V(insider). \
                outE('sends_sms', 'sends_email', 'calls', 'messages'). \
                has('timestamp', between(
                    announcement_date - timedelta(days=lookback_days),
                    announcement_date
                )). \
                inV(). \
                has('person_id', person). \
                path(). \
                toList()
            
            for comm in comms:
                # Extract communication details
                channel = comm.edge.label
                timestamp = comm.edge['timestamp']
                
                # Multi-lingual sentiment analysis
                if channel in ['sends_sms', 'sends_email', 'messages']:
                    content = comm.edge.get('content', '')
                    
                    # Detect language
                    language = detect_language(content)
                    
                    # Translate to English if needed
                    if language != 'en':
                        content_en = translate(
                            content,
                            source=language,
                            target='en'
                        )
                    else:
                        content_en = content
                    
                    # Sentiment analysis
                    sentiment = analyze_sentiment(content_en)
                    
                    # Entity extraction
                    entities = extract_entities(content_en)
                    
                    # Check for suspicious keywords
                    suspicious_keywords = [
                        'insider', 'tip', 'confidential', 'secret',
                        'buy now', 'sell now', 'before announcement',
                        'material information', 'non-public',
                        'don\'t tell anyone', 'delete this message',
                        'use cash', 'offshore account', 'shell company',
                        'nominee', 'trust', 'bearer shares'
                    ]
                    
                    keyword_matches = [
                        kw for kw in suspicious_keywords
                        if kw in content_en.lower()
                    ]
                    
                    if keyword_matches or sentiment['urgency'] > 0.7:
                        suspicious_communications.append({
                            'from': insider,
                            'to': person,
                            'channel': channel,
                            'timestamp': timestamp,
                            'language': language,
                            'sentiment': sentiment,
                            'entities': entities,
                            'keywords': keyword_matches,
                            'content': content_en[:200]  # First 200 chars
                        })
                
                # Phone call analysis
                elif channel == 'calls':
                    duration = comm.edge.get('duration', 0)
                    from_country = comm.edge.get('from_country')
                    to_country = comm.edge.get('to_country')
                    
                    # Suspicious if:
                    # - Long duration (>30 min)
                    # - International call
                    # - Late night/early morning (unusual time)
                    hour = timestamp.hour
                    is_unusual_time = hour < 6 or hour > 22
                    
                    if duration > 30 or from_country != to_country or is_unusual_time:
                        suspicious_communications.append({
                            'from': insider,
                            'to': person,
                            'channel': 'phone_call',
                            'timestamp': timestamp,
                            'duration': duration,
                            'from_country': from_country,
                            'to_country': to_country,
                            'unusual_time': is_unusual_time
                        })
    
    # PHASE 4: ANALYZE TRADING ACTIVITY
    suspicious_trades = []
    
    for insider, connections in network.items():
        for person in connections['all']:
            # Get all accounts owned by person
            accounts = g.V(person). \
                out('owns'). \
                hasLabel('Account'). \
                toList()
            
            for account in accounts:
                # Get trades in lookback period
                trades = g.V(account). \
                    out('places_order'). \
                    has('security_id', target_company.stock_symbol). \
                    has('timestamp', between(
                        announcement_date - timedelta(days=lookback_days),
                        announcement_date
                    )). \
                    toList()
                
                for trade in trades:
                    # Calculate days before announcement
                    days_before = (announcement_date - trade['timestamp']).days
                    
                    # Get trade details
                    trade_type = trade['trade_type']  # BUY, SELL, OPTION
                    volume = trade['volume']
                    price = trade['price']
                    value = volume * price
                    
                    # Get account details
                    broker = g.V(account).out('at').next()
                    country = g.V(broker).out('in').next()
                    
                    # Calculate historical average
                    historical_trades = g.V(account). \
                        out('places_order'). \
                        has('timestamp', between(
                            announcement_date - timedelta(days=365),
                            announcement_date - timedelta(days=lookback_days)
                        )). \
                        toList()
                    
                    avg_volume = np.mean([t['volume'] for t in historical_trades]) if historical_trades else 0
                    avg_value = np.mean([t['volume'] * t['price'] for t in historical_trades]) if historical_trades else 0
                    
                    # Suspicious if:
                    # - Volume >3x average
                    # - Value >5x average
                    # - Within 30 days of announcement
                    # - Offshore account
                    # - Options trading (higher leverage)
                    
                    is_suspicious = (
                        (volume > 3 * avg_volume if avg_volume > 0 else volume > 1000) or
                        (value > 5 * avg_value if avg_value > 0 else value > 100000) or
                        (days_before <= 30) or
                        (country.get('is_tax_haven', False)) or
                        (trade_type == 'OPTION')
                    )
                    
                    if is_suspicious:
                        suspicious_trades.append({
                            'insider': insider,
                            'trader': person,
                            'account': account,
                            'broker': broker,
                            'country': country,
                            'trade_type': trade_type,
                            'volume': volume,
                            'price': price,
                            'value': value,
                            'days_before': days_before,
                            'volume_ratio': volume / avg_volume if avg_volume > 0 else float('inf'),
                            'value_ratio': value / avg_value if avg_value > 0 else float('inf')
                        })
    
    # PHASE 5: TEMPORAL CORRELATION ANALYSIS
    # Check if communications preceded trades
    temporal_correlations = []
    
    for comm in suspicious_communications:
        for trade in suspicious_trades:
            if comm['to'] == trade['trader']:
                time_diff = (trade['timestamp'] - comm['timestamp']).total_seconds() / 3600  # hours
                
                # Suspicious if trade within 48 hours of communication
                if 0 < time_diff < 48:
                    temporal_correlations.append({
                        'communication': comm,
                        'trade': trade,
                        'time_diff_hours': time_diff
                    })
    
    # PHASE 6: GEOSPATIAL ANALYSIS
    # Check for impossible travel or coordinated activity across time zones
    geospatial_anomalies = []
    
    for insider, connections in network.items():
        # Get all locations for insider and network
        locations = g.V(insider). \
            union(
                identity(),
                out('family_of', 'friend_of', 'colleague_of')
            ). \
            out('located_at'). \
            has('timestamp', between(
                announcement_date - timedelta(days=lookback_days),
                announcement_date
            )). \
            order().by('timestamp'). \
            toList()
        
        # Check for impossible travel
        for i in range(len(locations) - 1):
            loc1 = locations[i]
            loc2 = locations[i + 1]
            
            distance = calculate_distance(loc1, loc2)  # km
            time_diff = (loc2['timestamp'] - loc1['timestamp']).total_seconds() / 3600  # hours
            
            # Impossible if distance > 1000km and time < 2 hours
            if distance > 1000 and time_diff < 2:
                geospatial_anomalies.append({
                    'person': insider,
                    'from': loc1,
                    'to': loc2,
                    'distance_km': distance,
                    'time_hours': time_diff,
                    'type': 'IMPOSSIBLE_TRAVEL'
                })
    
    # PHASE 7: MULTI-CURRENCY ANALYSIS
    # Check for currency conversions and offshore transfers
    currency_flows = []
    
    for trade in suspicious_trades:
        # Trace money flow
        flow = g.V(trade['account']). \
            outE('transfers_to', 'wires_to'). \
            has('timestamp', between(
                trade['timestamp'] - timedelta(days=7),
                trade['timestamp'] + timedelta(days=7)
            )). \
            inV(). \
            path(). \
            toList()
        
        # Analyze currencies used
        currencies = set()
        countries = set()
        
        for step in flow:
            if 'currency' in step.edge:
                currencies.add(step.edge['currency'])
            if hasattr(step.vertex, 'country'):
                countries.add(step.vertex['country'])
        
        # Suspicious if >3 currencies or >5 countries
        if len(currencies) > 3 or len(countries) > 5:
            currency_flows.append({
                'trade': trade,
                'currencies': list(currencies),
                'countries': list(countries),
                'flow_path': flow
            })
    
    # PHASE 8: SUBSIDIARY & CORPORATE STRUCTURE ANALYSIS
    # Check for complex corporate structures
    corporate_structures = []
    
    for insider, connections in network.items():
        # Find all companies owned/controlled
        companies = g.V(insider). \
            out('owns', 'director_of', 'controls'). \
            hasLabel('Company', 'ShellCompany'). \
            toList()
        
        for company in companies:
            # Map subsidiary structure
            subsidiaries = g.V(company). \
                repeat(out('owns')).times(5).emit(). \
                dedup(). \
                toList()
            
            # Check for offshore entities
            offshore_subs = [
                s for s in subsidiaries
                if g.V(s).out('incorporated_in').has('is_tax_haven', True).hasNext()
            ]
            
            # Suspicious if >10 subsidiaries or >3 offshore
            if len(subsidiaries) > 10 or len(offshore_subs) > 3:
                corporate_structures.append({
                    'insider': insider,
                    'parent_company': company,
                    'total_subsidiaries': len(subsidiaries),
                    'offshore_subsidiaries': len(offshore_subs),
                    'structure': subsidiaries
                })
    
    # PHASE 9: BANK NETWORK ANALYSIS
    # Check for complex banking relationships
    bank_networks = []
    
    for trade in suspicious_trades:
        # Trace payment through correspondent banks
        bank_chain = g.V(trade['account']). \
            out('at'). \
            repeat(out('correspondent_of')).times(10).emit(). \
            dedup(). \
            path(). \
            toList()
        
        # Suspicious if >5 banks in chain
        if len(bank_chain) > 5:
            bank_networks.append({
                'trade': trade,
                'bank_chain': bank_chain,
                'chain_length': len(bank_chain)
            })
    
    # PHASE 10: CALCULATE OVERALL RISK SCORE
    risk_scores = []
    
    for insider, connections in network.items():
        # Get all suspicious activity for this insider's network
        network_comms = [c for c in suspicious_communications if c['from'] == insider]
        network_trades = [t for t in suspicious_trades if t['insider'] == insider]
        network_correlations = [tc for tc in temporal_correlations if tc['communication']['from'] == insider]
        
        # Calculate risk components
        communication_risk = len(network_comms) * 5
        trading_risk = sum(t['value_ratio'] for t in network_trades) * 10
        correlation_risk = len(network_correlations) * 20
        timing_risk = sum(30 - t['days_before'] for t in network_trades if t['days_before'] < 30)
        network_size_risk = len(connections['all']) * 2
        offshore_risk = len(connections['offshore']) * 15
        
        # Multi-lingual communication risk
        languages = set(c['language'] for c in network_comms)
        multilingual_risk = len(languages) * 5 if len(languages) > 2 else 0
        
        # Multi-currency risk
        network_currencies = [cf for cf in currency_flows if cf['trade']['insider'] == insider]
        multicurrency_risk = sum(len(cf['currencies']) * 5 for cf in network_currencies)
        
        # Multi-country risk
        countries = set()
        for trade in network_trades:
            countries.add(trade['country']['name'])
        multicountry_risk = len(countries) * 5 if len(countries) > 3 else 0
        
        # Time zone coordination risk
        time_zones = set()
        for trade in network_trades:
            tz = get_timezone(trade['country']['name'])
            time_zones.add(tz)
        timezone_risk = len(time_zones) * 5 if len(time_zones) > 3 else 0
        
        # Corporate structure risk
        network_structures = [cs for cs in corporate_structures if cs['insider'] == insider]
        structure_risk = sum(cs['total_subsidiaries'] + cs['offshore_subsidiaries'] * 2 for cs in network_structures)
        
        # Bank network risk
        network_banks = [bn for bn in bank_networks if bn['trade']['insider'] == insider]
        bank_risk = sum(bn['chain_length'] * 3 for bn in network_banks)
        
        # Geospatial risk
        network_geo = [ga for ga in geospatial_anomalies if ga['person'] == insider]
        geo_risk = len(network_geo) * 15
        
        # Total risk score
        total_risk = (
            communication_risk +
            trading_risk +
            correlation_risk +
            timing_risk +
            network_size_risk +
            offshore_risk +
            multilingual_risk +
            multicurrency_risk +
            multicountry_risk +
            timezone_risk +
            structure_risk +
            bank_risk +
            geo_risk
        )
        
        # Normalize to 0-100
        normalized_risk = min(100, total_risk)
        
        # Classify risk level
        if normalized_risk >= 80:
            risk_level = 'CRITICAL'
            recommendation = 'IMMEDIATE SEC REFERRAL - Strong insider trading indicators'
            priority = 'P0'
            sla = '24 hours'
        elif normalized_risk >= 60:
            risk_level = 'HIGH'
            recommendation = 'ESCALATE TO COMPLIANCE - Suspicious pattern detected'
            priority = 'P1'
            sla = '72 hours'
        elif normalized_risk >= 40:
            risk_level = 'MEDIUM'
            recommendation = 'ENHANCED MONITORING - Potential coincidence'
            priority = 'P2'
            sla = '7 days'
        else:
            risk_level = 'LOW'
            recommendation = 'ROUTINE MONITORING'
            priority = 'P3'
            sla = '30 days'
        
        risk_scores.append({
            'insider': insider,
            'network_size': len(connections['all']),
            'suspicious_communications': len(network_comms),
            'suspicious_trades': len(network_trades),
            'temporal_correlations': len(network_correlations),
            'languages_used': list(languages),
            'currencies_used': len(set(cf['currencies'] for cf in network_currencies)),
            'countries_involved': list(countries),
            'time_zones': list(time_zones),
            'subsidiaries': sum(cs['total_subsidiaries'] for cs in network_structures),
            'offshore_entities': sum(cs['offshore_subsidiaries'] for cs in network_structures),
            'bank_chain_length': max([bn['chain_length'] for bn in network_banks], default=0),
            'geospatial_anomalies': len(network_geo),
            'risk_score': normalized_risk,
            'risk_level': risk_level,
            'recommendation': recommendation,
            'priority': priority,
            'sla': sla,
            'details': {
                'communications': network_comms,
                'trades': network_trades,
                'correlations': network_correlations,
                'currency_flows': network_currencies,
                'corporate_structures': network_structures,
