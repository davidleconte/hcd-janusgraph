# TBML Network Investigation Report

**Case ID:** [CASE-ID]  
**Date:** [DATE]  
**Analyst:** [ANALYST-NAME]  
**Classification:** CONFIDENTIAL - AML

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Primary Entity | [ENTITY-ID] |
| Detection Types | [LIST] |
| Total Trade Value | $[AMOUNT] |
| Estimated Value Transfer | $[AMOUNT] |
| Jurisdictions Involved | [COUNT] |
| Risk Score | [SCORE] |
| Recommended Action | [ACTION] |

---

## Trade Flow Summary

### Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  EXPORTER   │────►│   ROUTE     │────►│  IMPORTER   │
│  [COUNTRY]  │     │  [PORTS]    │     │  [COUNTRY]  │
│  [ENTITY]   │     │  [VESSEL]   │     │  [ENTITY]   │
└─────────────┘     └─────────────┘     └─────────────┘
     $[VALUE]            [DAYS]              $[VALUE]
```

### Commodity Details

| Attribute | Value |
|-----------|-------|
| Commodity | [DESCRIPTION] |
| HS Code | [CODE] |
| Declared Quantity | [QTY] |
| Declared Value | $[AMOUNT] |
| Market Value | $[AMOUNT] |
| Deviation | [XX%] |

---

## Detection Analysis

### Invoice Anomalies

| Invoice ID | Declared | Market | Deviation | Risk |
|------------|----------|--------|-----------|------|
| [ID1] | $[AMOUNT] | $[AMOUNT] | +[XX%] | HIGH |
| [ID2] | $[AMOUNT] | $[AMOUNT] | -[XX%] | HIGH |

**Total Value Transfer via Invoice Manipulation:** $[AMOUNT]

### Shell Company Network

```
                    ┌──────────────────┐
                    │   UBO/Controller  │
                    │   [PERSON-ID]     │
                    └────────┬─────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │ Company A     │ │ Company B     │ │ Company C     │
    │ [JURISDICTION]│ │ [JURISDICTION]│ │ [JURISDICTION]│
    │ Shell: YES    │ │ Shell: YES    │ │ Shell: YES    │
    └───────────────┘ └───────────────┘ └───────────────┘
```

### Phantom Shipment Indicators

| Shipment ID | Indicator | Evidence | Risk |
|-------------|-----------|----------|------|
| [ID1] | No container tracking | [DETAILS] | 0.7 |
| [ID2] | Fast transit | [ACTUAL] vs [EXPECTED] days | 0.9 |
| [ID3] | Same load/discharge port | [PORT] | 0.8 |

### Circular Trading Patterns

**Pattern:** [COMPANY-A] → [COMPANY-B] → [COMPANY-C] → [COMPANY-A]

| Leg | Value | Commodity |
|-----|-------|-----------|
| A → B | $[AMOUNT] | [COMMODITY] |
| B → C | $[AMOUNT] | [COMMODITY] |
| C → A | $[AMOUNT] | [COMMODITY] |
| **Total** | $[AMOUNT] | |

---

## Jurisdiction Risk Analysis

### Country Risk Matrix

| Country | Role | FATF Status | CPI Score | Risk Level |
|---------|------|-------------|-----------|------------|
| [COUNTRY1] | Exporter | [STATUS] | [SCORE] | [LEVEL] |
| [COUNTRY2] | Importer | [STATUS] | [SCORE] | [LEVEL] |
| [COUNTRY3] | Transit | [STATUS] | [SCORE] | [LEVEL] |

### Sanctions Screening

| Entity | Sanctions List | Match Status |
|--------|----------------|--------------|
| [ENTITY1] | OFAC SDN | [RESULT] |
| [ENTITY2] | EU Sanctions | [RESULT] |
| [ENTITY3] | UN Sanctions | [RESULT] |

**Sanctioned Corridor:** [YES/NO]

---

## Financial Analysis

### Trade Finance Instruments

| Instrument Type | Bank | Amount | Status |
|-----------------|------|--------|--------|
| Letter of Credit | [BANK] | $[AMOUNT] | [STATUS] |
| Documentary Collection | [BANK] | $[AMOUNT] | [STATUS] |

**Duplicate Financing Detected:** [YES/NO]

### Payment Flows

```
[EXPORTER] ◄───────────────────────────── [IMPORTER]
     ▲                                        │
     │                                        │
     │    ┌─────────────────────────────┐     │
     │    │     CORRESPONDENT BANK      │     │
     │    │         $[AMOUNT]           │     │
     │    └─────────────────────────────┘     │
     │                                        │
     └────────────────────────────────────────┘
```

### Value Transfer Summary

| Method | Amount | Confidence |
|--------|--------|------------|
| Over-invoicing | $[AMOUNT] | [XX%] |
| Under-invoicing | $[AMOUNT] | [XX%] |
| Phantom shipments | $[AMOUNT] | [XX%] |
| Multiple invoicing | $[AMOUNT] | [XX%] |
| **TOTAL** | $[AMOUNT] | |

---

## Regulatory Considerations

### SAR Filing Requirements

| Element | Status |
|---------|--------|
| Trade flow description | ☐ Complete |
| Invoice manipulation details | ☐ Complete |
| Shell company structure | ☐ Complete |
| Jurisdiction analysis | ☐ Complete |
| Phantom shipment evidence | ☐ Complete |
| Value transfer estimate | ☐ Complete |

### Intelligence Sharing

| Agency | Threshold | Status |
|--------|-----------|--------|
| FinCEN | >$100K | ☐ Required |
| Egmont Group | >$1M, multi-jurisdiction | ☐ Required |
| CBP | Customs fraud indicators | ☐ Required |
| OFAC | Sanctioned entities/countries | ☐ Required |

---

## Recommended Actions

### Immediate Actions

- [ ] Block pending transactions: $[AMOUNT]
- [ ] Freeze accounts: [LIST]
- [ ] Notify correspondent banks
- [ ] Alert compliance team

### Investigation Actions

- [ ] Request additional documentation from [ENTITIES]
- [ ] Verify vessel tracking data
- [ ] Cross-reference with customs data
- [ ] Contact foreign FIU (Egmont)

### Regulatory Actions

- [ ] File SAR (Deadline: [DATE])
- [ ] File CTR if applicable
- [ ] Prepare intelligence sharing package
- [ ] Document for OFAC referral

---

## Evidence Package

| File | Description | Size |
|------|-------------|------|
| trade_flow_diagram.png | Network visualization | [SIZE] KB |
| invoice_analysis.xlsx | Price deviation details | [SIZE] KB |
| shell_company_structure.json | Corporate network | [SIZE] KB |
| shipment_tracking.json | Vessel/container data | [SIZE] KB |
| jurisdiction_risk.json | Country risk analysis | [SIZE] KB |
| timeline.pdf | Activity timeline | [SIZE] KB |

**Package ID:** [PACKAGE-ID]  
**Evidence Retention:** 5 years

---

## Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| AML Analyst | [NAME] | [DATE] | |
| AML Supervisor | [NAME] | [DATE] | |
| Compliance Officer | [NAME] | [DATE] | |
| Legal (if required) | [NAME] | [DATE] | |

---

**Distribution:**  
- [ ] AML Compliance Team  
- [ ] Trade Finance Unit  
- [ ] Legal Department  
- [ ] Senior Management (if >$1M)  
- [ ] External Regulators (as required)

---

*This report is confidential and subject to attorney-client privilege. Handle in accordance with AML/KYC data protection requirements.*