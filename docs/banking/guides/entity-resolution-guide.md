# Entity Resolution for Banking: Complete Business Guide

**Author:** David LECONTE - IBM Worldwide | Data & AI | Tiger Team  
**Date:** 2026-03-23  
**Status:** Active  

---

## Executive Summary

Entity Resolution is the process of identifying when multiple records in your systems refer to the same real-world entity (person, company, or account). In banking, this capability is **foundational** to:

- **Customer Onboarding**: Preventing duplicate accounts
- **KYC/AML Compliance**: Accurate identity verification
- **Fraud Detection**: Uncovering hidden relationships
- **Regulatory Reporting**: UBO identification, SAR filings

This guide covers three complexity levels with real business scenarios and implementation approaches.

---

## Table of Contents

1. [What is Entity Resolution?](#what-is-entity-resolution)
2. [Why Graph-Based Resolution?](#why-graph-based-resolution)
3. [Complexity Levels](#complexity-levels)
4. [Business Scenario 1: Standard Resolution](#scenario-1-standard-customer-deduplication)
5. [Business Scenario 2: High-Complexity UBO Resolution](#scenario-2-high-complexity-ubo--sanctions-resolution)
6. [Business Scenario 3: Ultra-High Synthetic Identity Detection](#scenario-3-ultra-high-synthetic-identity-fraud-detection)
7. [Regulatory Requirements](#regulatory-requirements)
8. [Implementation Considerations](#implementation-considerations)
9. [ROI and Business Impact](#roi-and-business-impact)

---

## What is Entity Resolution?

### Definition

**Entity Resolution (ER)** is the computational process of determining whether two or more records refer to the same real-world entity, despite differences in how that entity is represented across data sources.

### The Problem in Banking

```
┌─────────────────────────────────────────────────────────────────────┐
│                     THE DUPLICATE PROBLEM                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   Source A (Core Banking)      Source B (CRM)      Source C (Loans)│
│   ┌──────────────────┐        ┌──────────────────┐  ┌────────────┐ │
│   │ John A. Smith    │        │ Jonathan Smith   │  │ J. Smith   │ │
│   │ DOB: 1985-03-15  │        │ DOB: 1985-03-15  │  │ DOB: ???   │ │
│   │ SSN: 123-45-6789 │        │ SSN: ???         │  │ SSN: ???   │ │
│   │ Phone: 555-1234  │        │ Phone: 555-1234  │  │ Phone: ??? │ │
│   └──────────────────┘        └──────────────────┘  └────────────┘ │
│            │                          │                    │        │
│            └──────────────────────────┴────────────────────┘        │
│                                       │                             │
│                               SAME PERSON?                          │
│                                                                     │
│   Without Resolution:           With Resolution:                    │
│   • 3 separate customer IDs     • 1 unified customer profile        │
│   • Fragmented credit view      • Complete credit picture           │
│   • Duplicate marketing         • Single source of truth            │
│   • Inaccurate risk scoring     • Accurate risk assessment          │
└─────────────────────────────────────────────────────────────────────┘
```

### Types of Entity Resolution

| Type | Description | Example |
|------|-------------|---------|
| **Deduplication** | Finding duplicates within one dataset | Same customer entered twice |
| **Record Linkage** | Matching records across datasets | Customer in core banking + CRM |
| **Canonicalization** | Creating a single "golden record" | Merging 3 profiles into 1 |
| **Identity Resolution** | Linking digital identities | Same person across devices |

---

## Why Graph-Based Resolution?

### Traditional Approach Limitations

Traditional entity resolution uses **pairwise comparison** of attributes:

```
Record A vs Record B
├── Name match?        → Score: 0.85
├── DOB match?         → Score: 1.00
├── Address match?     → Score: 0.70
├── Phone match?       → Score: 1.00
└── Weighted Total     → Score: 0.88
```

**Limitations:**
- Ignores relationships between entities
- Cannot traverse ownership chains
- Misses network-based fraud patterns
- Struggles with multi-jurisdictional entities

### Graph-Based Advantages

```
┌─────────────────────────────────────────────────────────────────────┐
│                   GRAPH-BASED RESOLUTION                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   Person A                    Person B                              │
│   ┌──────────┐                ┌──────────┐                          │
│   │ John     │                │ Jonathan │                          │
│   │ Smith    │                │ Smith    │                          │
│   └────┬─────┘                └────┬─────┘                          │
│        │                           │                                │
│        │    ┌─────────────────┐    │                                │
│        └────┤  SAME ADDRESS   ├────┘   ← Graph Relationship         │
│             │  123 Main St    │                                    │
│             └────────┬────────┘                                    │
│                      │                                             │
│        ┌─────────────┼─────────────┐                               │
│        │             │             │                               │
│   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐                          │
│   │Account 1│   │Account 2│   │Account 3│   ← Shared Accounts      │
│   │Joint    │   │Joint    │   │Joint    │     (strong signal)      │
│   └─────────┘   └─────────┘   └─────────┘                          │
│                                                                     │
│   Graph Resolution: Person A and B are SAME PERSON                  │
│   Confidence: 0.96 (higher than attribute-only: 0.88)               │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Graph-Based Signals

| Signal Type | Weight | Example |
|-------------|--------|---------|
| **Shared Addresses** | High | Same residential address |
| **Joint Accounts** | Very High | Co-owners on accounts |
| **Family Relationships** | Medium | Spouse, parent-child |
| **Employment History** | Medium | Same employer over time |
| **Device/Session** | High | Same device fingerprint |
| **Transaction Patterns** | Medium | Similar spending behavior |

---

## Complexity Levels

### Level 1: Standard Resolution

**Use Case:** Customer deduplication during onboarding

**Characteristics:**
- Single data domain (customer data)
- Direct attribute comparison
- 1-2 hop relationships
- High confidence thresholds

**Typical Accuracy:** 95-98%

### Level 2: High-Complexity Resolution

**Use Case:** UBO identification, sanctions screening

**Characteristics:**
- Multi-domain (companies, persons, trusts)
- Multi-hop traversal (3-5 hops)
- Cross-jurisdictional matching
- Fuzzy name matching across cultures

**Typical Accuracy:** 85-92%

### Level 3: Ultra-High Complexity Resolution

**Use Case:** Synthetic identity fraud, sophisticated money laundering

**Characteristics:**
- Multi-dimensional signals
- Network community analysis
- Behavioral pattern detection
- Device/fingerprint correlation
- Temporal pattern analysis

**Typical Accuracy:** 75-85%

---

## Scenario 1: Standard Customer Deduplication

### Business Context

**Problem:** A customer attempts to open a new account. The bank needs to determine if this person already exists in the system to:
- Prevent duplicate records
- Apply existing KYC status
- Avoid redundant onboarding costs
- Maintain accurate customer count

### The Scenario

```
┌─────────────────────────────────────────────────────────────────────┐
│          SCENARIO: NEW CUSTOMER ONBOARDING                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   New Application              Existing Record A                    │
│   ┌──────────────────┐        ┌──────────────────┐                 │
│   │ Name:            │        │ Name:            │                 │
│   │ Jonathan Smith   │        │ John A. Smith    │                 │
│   │                  │        │                  │                 │
│   │ DOB:             │        │ DOB:             │                 │
│   │ 1985-03-15       │◄──────►│ 1985-03-15       │ ✓ MATCH         │
│   │                  │        │                  │                 │
│   │ SSN:             │        │ SSN:             │                 │
│   │ 123-45-6789      │◄──────►│ 123-45-6789      │ ✓ EXACT MATCH   │
│   │                  │        │                  │                 │
│   │ Phone:           │        │ Phone:           │                 │
│   │ 555-1234         │◄──────►│ 555-1234         │ ✓ MATCH         │
│   │                  │        │                  │                 │
│   │ Email:           │        │ Email:           │                 │
│   │ jon.s@gmail.com  │        │ john.smith@yahoo │ ✗ DIFFERENT     │
│   └──────────────────┘        └──────────────────┘                 │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                    RESOLUTION RESULT                        │  │
│   │                                                             │  │
│   │   Confidence: 0.94                                          │  │
│   │   Action: MERGE - Link to existing customer                 │  │
│   │                                                             │  │
│   │   Signals:                                                  │  │
│   │   • SSN exact match (weight: 0.30, score: 1.0)             │  │
│   │   • DOB exact match (weight: 0.20, score: 1.0)             │  │
│   │   • Phone exact match (weight: 0.15, score: 1.0)           │  │
│   │   • Name fuzzy match "John" ≈ "Jonathan" (weight: 0.15)    │  │
│   │   • Email mismatch (weight: 0.10, score: 0.0)              │  │
│   │                                                             │  │
│   │   Business Impact:                                          │  │
│   │   • Skip re-onboarding (cost savings: $150)                │  │
│   │   • Apply existing KYC Level 2 status                       │  │
│   │   • Link to existing accounts                               │  │
│   └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Resolution Signals (Standard)

| Attribute | Weight | Match Type | Score |
|-----------|--------|------------|-------|
| SSN | 0.30 | Exact | 1.0 or 0.0 |
| DOB | 0.20 | Exact | 1.0 or 0.0 |
| Name | 0.15 | Fuzzy | 0.0-1.0 |
| Phone | 0.15 | Exact | 1.0 or 0.0 |
| Email | 0.10 | Exact | 1.0 or 0.0 |
| Address | 0.10 | Fuzzy | 0.0-1.0 |

### Name Matching Nuances

```
┌─────────────────────────────────────────────────────────────────────┐
│                    NAME MATCHING TYPES                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ 1. EXACT MATCH                                                      │
│    "John Smith" = "John Smith"                      → Score: 1.00   │
│                                                                     │
│ 2. NICKNAME/DIMINUTIVE                                              │
│    "Robert" ≈ "Bob" (nickname)                      → Score: 0.90   │
│    "William" ≈ "Bill" (nickname)                    → Score: 0.90   │
│    "Elizabeth" ≈ "Liz" (nickname)                   → Score: 0.90   │
│                                                                     │
│ 3. FUZZY MATCH (Typos, OCR errors)                                  │
│    "Smith" ≈ "Smyth" (Levenshtein)                  → Score: 0.85   │
│    "Jonathan" ≈ "Jonathon" (transposition)          → Score: 0.90   │
│                                                                     │
│ 4. PHONETIC MATCH                                                   │
│    "Smith" ≈ "Smythe" (Soundex: S530)               → Score: 0.70   │
│    "Catherine" ≈ "Katherine" (phonetic)             → Score: 0.75   │
│                                                                     │
│ 5. CULTURAL EQUIVALENTS                                             │
│    "John" ≈ "Ivan" (Russian)                        → Score: 0.85   │
│    "John" ≈ "Hans" (German)                         → Score: 0.85   │
│    "John" ≈ "Juan" (Spanish)                        → Score: 0.80   │
│    "Smith" ≈ "Schmidt" (German translation)         → Score: 0.85   │
│                                                                     │
│ 6. DERIVATIVE NAMES                                                 │
│    "Jonathan" ≈ "John" (derivative)                 → Score: 0.80   │
│    "Michael" ≈ "Mike" (derivative)                  → Score: 0.80   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Business Impact

| Metric | Before Resolution | After Resolution | Improvement |
|--------|-------------------|------------------|-------------|
| Duplicate rate | 8-12% | <2% | 80% reduction |
| Onboarding cost | $150/customer | $50/customer | 67% savings |
| KYC re-verification | 15% | 5% | 67% reduction |
| Customer complaints | 120/month | 30/month | 75% reduction |

---

## Scenario 2: High-Complexity UBO & Sanctions Resolution

### Business Context

**Problem:** An investigator needs to determine if multiple companies across different jurisdictions are controlled by the same person - and whether that person appears on a sanctions list.

This is **HIGH COMPLEXITY** because:
- Multiple corporate entities across jurisdictions
- Trust structures obscure ownership
- Name variants in different languages
- 3-5 hops through ownership chains
- Sanctions screening with fuzzy matching

### The Scenario

```
┌─────────────────────────────────────────────────────────────────────────────┐
│          SCENARIO: SANCTIONS EVASION INVESTIGATION                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INVESTIGATION TRIGGER:                                                      │
│  Large transaction from "Smith Holdings Ltd" (UK) to offshore account.      │
│  Suspicion: Ultimate Beneficial Owner may be sanctioned.                    │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    CORPORATE STRUCTURE                               │  │
│  │                                                                      │  │
│  │   Smith Holdings Ltd (UK)                                            │  │
│  │   ┌────────────────────┐                                             │  │
│  │   │ Director: J. Smith │                                             │  │
│  │   │ Shareholder:       │                                             │  │
│  │   │ Trust Alpha (BVI) ─┼────► Trust Alpha (BVI)                     │  │
│  │   └────────────────────┘         │                                   │  │
│  │                                  │                                    │  │
│  │                                  ▼                                    │  │
│  │   Smythe Ventures Ltd (BVI)  Trustee: Law Firm X                    │  │
│  │   ┌────────────────────┐         │                                   │  │
│  │   │ Director: J. Smythe│         │                                   │  │
│  │   │ Shareholder:       │         │                                   │  │
│  │   │ Trust Beta (Cyprus)┼────►────┤                                   │  │
│  │   └────────────────────┘         │                                    │  │
│  │                                  │                                    │  │
│  │                                  ▼                                    │  │
│  │   Schmidt GmbH (Cyprus)      Trust Beneficiary:                     │  │
│  │   ┌────────────────────┐         ┌─────────────────────────────┐    │  │
│  │   │ Director: H. Schmidt│        │ ULTIMATE BENEFICIAL OWNER   │    │  │
│  │   │ Shareholder:       │        │                             │    │  │
│  │   │ Trust Gamma (Cyprus)┼────►   │ Name Variants:              │    │  │
│  │   └────────────────────┘        │ • John Smith (UK passport)  │    │  │
│  │                                 │ • Jon Smythe (BVI passport) │    │  │
│  │                                 │ • Hans Schmidt (Cyprus pass)│    │  │
│  │                                 │ • Ivan Smirnov (RU passport)│    │  │
│  │                                 │                             │    │  │
│  │                                 │ DOB: 1965-03-15 (ALL)       │    │  │
│  │                                 │                             │    │  │
│  │                                 │ ⚠️ SANCTIONS CHECK:         │    │  │
│  │                                 │ "Ivan Smirnov" appears on   │    │  │
│  │                                 │ OFAC SDN List (95% match)   │    │  │
│  │                                 └─────────────────────────────┘    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  RESOLUTION RESULT:                                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Confidence: 0.94                                                     │  │
│  │ Action: SANCTIONS ALERT - Freeze accounts, file SAR                  │  │
│  │                                                                      │  │
│  │ Evidence Chain:                                                      │  │
│  │ • 3 companies share same UBO through trust structures               │  │
│  │ • All trustees are same law firm (Law Firm X)                       │  │
│  │ • Name variants match through cultural equivalents                  │  │
│  │ • DOB is identical across all identities                            │  │
│  │ • Fuzzy match to OFAC SDN List entry                                │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### High-Complexity Signals

| Signal Type | Weight | How Detected |
|-------------|--------|--------------|
| **Name Variants** | 0.20 | Cultural equivalents, transliteration |
| **Shared Trustee** | 0.15 | Graph traversal to law firm |
| **DOB Match** | 0.15 | Cross-document verification |
| **Director Overlap** | 0.15 | Shared directors across companies |
| **Address Correlation** | 0.10 | Registered agent addresses |
| **Ownership Chain** | 0.10 | Multi-hop traversal |
| **Sanctions Fuzzy Match** | 0.15 | SDN list screening |

### Regulatory Requirements Met

| Regulation | Requirement | How Addressed |
|------------|-------------|---------------|
| **FATF Rec. 24/25** | UBO identification | Multi-hop ownership traversal |
| **EU AMLD6** | 25% threshold + control | Control relationship inference |
| **UK PSC Register** | Significant control | Direct + indirect ownership |
| **US CTA** | Beneficial ownership | Corporate structure resolution |
| **OFAC** | Sanctions screening | Fuzzy matching + network analysis |

---

## Scenario 3: Ultra-High Synthetic Identity Fraud Detection

### Business Context

**Problem:** A fraud ring has created synthetic identities by combining:
- Real SSNs (stolen from children, elderly, or deceased)
- Fabricated names and addresses
- Artificial credit histories

These identities build credit over 6-12 months, then "bust out" with maximum loans and credit cards.

### Why Ultra-High Complexity?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│       WHY SYNTHETIC IDENTITY DETECTION IS ULTRA-HIGH COMPLEXITY             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. NO OBVIOUS DUPLICATES                                                   │
│     Each synthetic identity appears unique on paper                         │
│     Different SSN, different name, different address                        │
│                                                                             │
│  2. STOLEN SSNs ARE VALID                                                   │
│     SSNs check out (they belong to real people)                             │
│     But the real person is a child, deceased, or unaware                    │
│                                                                             │
│  3. GRADUAL CREDIT BUILDING                                                 │
│     Normal credit behavior for months                                       │
│     No sudden spikes to trigger alerts                                      │
│                                                                             │
│  4. COORDINATED BUST-OUT                                                    │
│     All identities maximize credit simultaneously                           │
│     By the time it's detected, funds are gone                               │
│                                                                             │
│  SOLUTION: Network + Behavioral + Device Analysis                           │
│  ─────────────────────────────────────────────────                          │
│  • Find clusters at same address                                            │
│  • Detect device fingerprint sharing                                        │
│  • Analyze temporal patterns (all created in same period)                   │
│  • Identify behavioral similarities                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The Scenario

```
┌─────────────────────────────────────────────────────────────────────────────┐
│          SCENARIO: SYNTHETIC IDENTITY FRAUD RING                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    FRAUD RING NETWORK                              │    │
│  │                                                                    │    │
│  │   123 Oak Street, Apt 4B                                          │    │
│  │   ┌──────────────────────────────────────────────────────────┐    │    │
│  │   │  Address Hub: 47 synthetic identities registered here    │    │    │
│  │   │                                                          │    │    │
│  │   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │    │    │
│  │   │  │ Marcus  │ │ Maria   │ │ Miguel  │ │ Marta   │        │    │    │
│  │   │  │ Johnson │ │ Johnson │ │ Johnson │ │ Johnson │        │    │    │
│  │   │  │ SSN:    │ │ SSN:    │ │ SSN:    │ │ SSN:    │        │    │    │
│  │   │  │ 123-XX  │ │ 456-XX  │ │ 789-XX  │ │ 321-XX  │        │    │    │
│  │   │  │ DOB:    │ │ DOB:    │ │ DOB:    │ │ DOB:    │        │    │    │
│  │   │  │ 1995-03 │ │ 1995-04 │ │ 1995-05 │ │ 1995-06 │        │    │    │
│  │   │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘        │    │    │
│  │   │       │           │           │           │              │    │    │
│  │   │       └───────────┴─────┬─────┴───────────┘              │    │    │
│  │   │                         │                                │    │    │
│  │   │                         ▼                                │    │    │
│  │   │              ┌─────────────────────┐                     │    │    │
│  │   │              │  SHARED INDICATORS  │                     │    │    │
│  │   │              │                     │                     │    │    │
│  │   │              │ • Same address      │                     │    │    │
│  │   │              │ • Sequential DOBs   │                     │    │    │
│  │   │              │ • Sequential SSNs   │                     │    │    │
│  │   │              │ • Same last name    │                     │    │    │
│  │   │              │ • Sequential phones │                     │    │    │
│  │   │              │ • Shared devices    │                     │    │    │
│  │   │              │ • Same IP subnet    │                     │    │    │
│  │   │              │ • Created same week │                     │    │    │
│  │   │              │ • Identical credit  │                     │    │    │
│  │   │              │   application pattern│                    │    │    │
│  │   │              └─────────────────────┘                     │    │    │
│  │   └──────────────────────────────────────────────────────────┘    │    │
│  │                                                                    │    │
│  │   DETECTION RESULT:                                                │    │
│  │   ┌──────────────────────────────────────────────────────────┐    │    │
│  │   │ Confidence: 0.88                                         │    │    │
│  │   │ Cluster Size: 47 identities                              │    │    │
│  │   │ Estimated Exposure: $2.3M                                │    │    │
│  │   │ Action: FRAUD ALERT - Freeze accounts, investigate       │    │    │
│  │   │                                                          │    │    │
│  │   │ Risk Indicators:                                         │    │    │
│  │   │ • Large cluster at single address                        │    │    │
│  │   │ • Sequential SSN pattern (stolen from same source)       │    │    │
│  │   │ • Device fingerprint correlation (same computer)         │    │    │
│  │   │ • Temporal clustering (all created in 2-week period)     │    │    │
│  │   │ • Behavioral similarity (identical credit applications)  │    │    │
│  │   └──────────────────────────────────────────────────────────┘    │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Ultra-High Complexity Signals

| Signal Category | Signals | Weight | Detection Method |
|-----------------|---------|--------|------------------|
| **Identity** | SSN, Name, DOB | 0.15 | Attribute matching |
| **Contact** | Address, Phone, Email | 0.10 | Cluster analysis |
| **Device** | Fingerprint, Browser, IP | 0.12 | Device intelligence |
| **Behavioral** | Application patterns, Timing | 0.15 | Sequence analysis |
| **Network** | Shared connections, Centrality | 0.20 | Graph algorithms |
| **Temporal** | Creation dates, Activity bursts | 0.10 | Time series |
| **External** | Credit bureau, Consortium | 0.08 | External data |
| **Velocity** | Credit build rate | 0.10 | Velocity checks |

---

## Regulatory Requirements

### Key Regulations Addressed

| Regulation | Entity Resolution Requirement |
|------------|------------------------------|
| **GDPR Article 17** | Right to erasure (find all records for a person) |
| **BSA/AML** | Customer Identification Program (CIP) |
| **FATF Recommendations** | UBO identification, correspondent banking |
| **EU AMLD6** | Beneficial ownership registers |
| **US CTA** | Corporate Transparency Act reporting |
| **OFAC** | Sanctions screening with fuzzy matching |
| **FFIEC Guidance** | Customer due diligence |

### Compliance Benefits

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COMPLIANCE IMPROVEMENT                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   Before Entity Resolution:          After Entity Resolution:       │
│   ─────────────────────────          ─────────────────────────      │
│   • False positive rate: 15%         • False positive rate: 3%      │
│   • Missed duplicates: 8%            • Missed duplicates: 0.5%      │
│   • UBO identification: 70%          • UBO identification: 95%      │
│   • SAR quality score: 65/100        • SAR quality score: 92/100    │
│   • Audit findings: 12/year          • Audit findings: 2/year       │
│                                                                     │
│   Annual Compliance Savings: $2.3M                                  │
│   Risk Reduction: 78%                                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Considerations

### Data Quality Requirements

| Data Element | Quality Requirement | Impact if Poor |
|--------------|---------------------|----------------|
| SSN/Tax ID | >99% populated | High - primary match key |
| DOB | >95% populated, verified | High - disambiguation |
| Name | >99% populated | Medium - fuzzy matching |
| Address | >90% standardized | Medium - correlation signal |
| Phone | >80% populated | Low - secondary signal |

### Performance Considerations

| Scale | Approach | Latency |
|-------|----------|---------|
| <1M entities | Real-time resolution | <100ms |
| 1M-10M entities | Batch + real-time hybrid | <500ms |
| >10M entities | Pre-computed clusters + incremental | <1s |

### False Positive Management

```
Confidence Thresholds:
├── 0.95+  → Auto-merge (no review)
├── 0.85-0.95 → Auto-link (queue for review)
├── 0.70-0.85 → Review required
├── 0.50-0.70 → Investigate
└── <0.50  → No match
```

---

## ROI and Business Impact

### Cost Savings

| Category | Annual Savings |
|----------|---------------|
| Duplicate prevention | $500K |
| KYC efficiency | $300K |
| Fraud prevention | $1.5M |
| Compliance efficiency | $400K |
| Operational overhead | $200K |
| **Total** | **$2.9M/year** |

### Risk Reduction

- **75% reduction** in missed duplicates
- **90% improvement** in UBO identification
- **60% reduction** in false positive alerts
- **85% faster** investigation time

### Strategic Value

1. **Regulatory confidence** - Defensible entity resolution process
2. **Customer experience** - No repeated onboarding
3. **Fraud prevention** - Earlier detection of sophisticated schemes
4. **Data quality** - Single source of truth for customer data

---

## Summary

Entity Resolution is not a single technique but a **continuum of capabilities**:

| Level | Use Case | Complexity | Value |
|-------|----------|------------|-------|
| **Standard** | Customer deduplication | Low | Operational efficiency |
| **High** | UBO/Sanctions | Medium | Compliance, Risk |
| **Ultra-High** | Fraud detection | High | Risk mitigation, Loss prevention |

**Graph-based resolution** provides superior accuracy by incorporating relationship signals that traditional pairwise comparison misses.

---

**Last Updated:** 2026-03-23  
**Version:** 1.0  
**Status:** Active
