// AML Structuring Detection Queries
// Gremlin queries to detect smurfing/structuring patterns
//
// Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
// Contact: david.leconte1@ibm.com | +33614126117
// Date: 2026-01-28

// ============================================
// QUERY 1: Find All Structuring Transactions
// Transactions just below $10,000 threshold
// ============================================

// Find transactions between $8,000 and $9,999 (typical structuring range)
g.V().hasLabel('transaction')
    .has('amount', gte(8000))
    .has('amount', lt(10000))
    .valueMap(true)

// ============================================
// QUERY 2: Detect Coordinated Deposits
// Multiple accounts depositing to same beneficiary
// within 24-hour window
// ============================================

// Find beneficiary accounts receiving multiple structuring-sized deposits
g.V().hasLabel('transaction')
    .has('amount', gte(8000))
    .has('amount', lt(10000))
    .out('to_account')
    .groupCount()
    .unfold()
    .where(values.is(gte(5)))  // At least 5 suspicious transactions
    .select(keys)
    .valueMap(true)

// ============================================
// QUERY 3: Find Mule Accounts
// Accounts that deposit to multiple beneficiaries
// or have shared identifiers
// ============================================

// Find accounts making multiple structuring deposits
g.V().hasLabel('transaction')
    .has('amount', gte(8000))
    .has('amount', lt(10000))
    .out('from_account')
    .groupCount()
    .unfold()
    .where(values.is(gte(2)))  // At least 2 suspicious transactions
    .select(keys)
    .as('mule')
    .in('owns_account')
    .as('person')
    .select('mule', 'person')
    .by(valueMap(true))
    .by(valueMap(true))

// ============================================
// QUERY 4: Shared Address Pattern
// Multiple persons sharing same address
// who all make structuring deposits
// ============================================

// Find addresses shared by multiple persons who make structuring transactions
g.V().hasLabel('address')
    .as('address')
    .in('has_address').hasLabel('person')
    .out('owns_account')
    .in('from_account').hasLabel('transaction')
    .has('amount', gte(8000))
    .has('amount', lt(10000))
    .select('address')
    .dedup()
    .valueMap(true)

// ============================================
// QUERY 5: Temporal Clustering
// Transactions within specific time window
// (coordinated timing indicator)
// ============================================

// Find structuring transactions clustered in 24-hour windows
// Note: Replace TARGET_TIMESTAMP with actual timestamp
g.V().hasLabel('transaction')
    .has('amount', gte(8000))
    .has('amount', lt(10000))
    .has('timestamp', between(TARGET_TIMESTAMP, TARGET_TIMESTAMP + 86400))
    .order().by('timestamp')
    .valueMap(true)

// ============================================
// QUERY 6: Full Structuring Ring Detection
// End-to-end: Find beneficiary, all mule accounts,
// shared identifiers, and transaction timeline
// ============================================

// Complete pattern: beneficiary <- multiple mules with shared identifiers
g.V().hasLabel('account')
    .where(
        in('to_account').hasLabel('transaction')
            .has('amount', gte(8000))
            .has('amount', lt(10000))
            .count().is(gte(10))  // At least 10 suspicious deposits
    )
    .as('beneficiary')
    .in('to_account').hasLabel('transaction')
    .has('amount', gte(8000))
    .has('amount', lt(10000))
    .as('transaction')
    .out('from_account').as('mule_account')
    .in('owns_account').as('mule_person')
    .select('beneficiary', 'transaction', 'mule_account', 'mule_person')
    .by(valueMap(true))
    .by(valueMap('transaction_id', 'amount', 'timestamp'))
    .by(valueMap('account_id'))
    .by(valueMap('person_id', 'first_name', 'last_name'))

// ============================================
// QUERY 7: Risk Score Aggregation
// Calculate risk score for each account based on
// structuring transaction patterns
// ============================================

// Aggregate structuring risk per account
g.V().hasLabel('account')
    .as('account')
    .map(
        in('to_account').hasLabel('transaction')
            .has('amount', gte(8000))
            .has('amount', lt(10000))
            .count()
    ).as('suspicious_deposit_count')
    .map(
        out('from_account').hasLabel('transaction')
            .has('amount', gte(8000))
            .has('amount', lt(10000))
            .count()
    ).as('suspicious_withdrawal_count')
    .select('account', 'suspicious_deposit_count', 'suspicious_withdrawal_count')
    .by(valueMap('account_id', 'balance'))
    .by()
    .by()

// ============================================
// QUERY 8: Network Analysis
// Find connected components of suspicious accounts
// (accounts linked by shared persons, addresses, phones)
// ============================================

// Find clusters of related accounts via shared identifiers
g.V().hasLabel('account')
    .where(
        in('to_account').hasLabel('transaction')
            .has('amount', gte(8000))
            .has('amount', lt(10000))
    )
    .as('account')
    .union(
        in('owns_account').out('has_address').in('has_address'),
        in('owns_account').out('has_phone').in('has_phone')
    )
    .out('owns_account')
    .where(neq('account'))
    .dedup()
    .path()
    .by(valueMap('account_id'))
    .limit(100)

// ============================================
// QUERY 9: Flagged Accounts Report
// Generate comprehensive report for flagged accounts
// ============================================

// Full report for all flagged beneficiary accounts
g.V().hasLabel('person')
    .has('flagged', true)
    .as('person')
    .out('owns_account').as('account')
    .project('person', 'account', 'total_deposits', 'num_transactions', 'addresses', 'phones')
        .by(select('person').valueMap('person_id', 'first_name', 'last_name', 'risk_score'))
        .by(select('account').valueMap('account_id', 'balance'))
        .by(
            select('account')
                .in('to_account')
                .values('amount')
                .sum()
        )
        .by(
            select('account')
                .in('to_account')
                .count()
        )
        .by(
            select('person')
                .out('has_address')
                .valueMap('street', 'city', 'state')
                .fold()
        )
        .by(
            select('person')
                .out('has_phone')
                .values('phone_number')
                .fold()
        )

// ============================================
// QUERY 10: Time Series Analysis
// Transaction patterns over time for an account
// ============================================

// Time series of transactions for a specific account
// Note: Replace ACCOUNT_ID with actual account ID
g.V().has('account', 'account_id', 'ACCOUNT_ID')
    .in('to_account').hasLabel('transaction')
    .order().by('timestamp')
    .project('date', 'amount', 'type', 'from_account')
        .by(values('date'))
        .by(values('amount'))
        .by(values('transaction_type'))
        .by(out('from_account').values('account_id'))

// Signature: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117
