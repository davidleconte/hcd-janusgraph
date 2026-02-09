# Banking Analytics & Fraud Detection

This directory contains the analytics modules and detection scripts for the banking platform.

## Detection Scripts

We provide standalone Python scripts to detect specific fraud patterns injected by the generator.

### 1. Insider Trading Detection

Scans the graph for `Trade` vertices with high values connected to `Person` entities, typically identifying "pre-announcement" trading anomalies.

**Usage:**

```bash
conda activate janusgraph-analysis
python banking/analytics/detect_insider_trading.py
```

**What it looks for:**

* Trades with unusually high amounts.
* Connection to specific Traders (Person vertices).
* (Logic can be extended to check timestamps relative to corporate announcements).

### 2. TBML (Trade-Based Money Laundering)

Scans for "Carousel Fraud" loops and companies with high volumes of suspicious transactions.

**Usage:**

```bash
conda activate janusgraph-analysis
python banking/analytics/detect_tbml.py
```

**What it looks for:**

* Circular transaction paths (Company A -> B -> C -> A).
* Companies flagged with `suspicious_activity` flags on their transactions.

## Core Modules

* `aml_structuring_detector.py`: Logic for detecting "smurfing" (breaking large transactions into smaller ones).
