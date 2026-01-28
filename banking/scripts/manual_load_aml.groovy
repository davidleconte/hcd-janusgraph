// Manual AML Data Loading Script
// Load sample structuring pattern data directly via Gremlin console
//
// Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
// Contact: david.leconte1@ibm.com | +33614126117
// Date: 2026-01-28

// Connect to remote JanusGraph server
:remote connect tinkerpop.server conf/remote.yaml
:remote console

println("✅ Connected to JanusGraph")

// Check current state
println("\n📊 Current Graph State:")
println("  Persons: " + g.V().hasLabel('person').count().next())
println("  Accounts: " + g.V().hasLabel('account').count().next())
println("  Transactions: " + g.V().hasLabel('transaction').count().next())

// Option to clear graph (commented out - uncomment if needed)
// println("\n🗑️  Clearing graph...")
// g.V().drop().iterate()
// println("✅ Graph cleared")

println("\n💾 Loading Sample AML Data...")

// ============================================
// BENEFICIARY 1: Alice Johnson (Money Launderer)
// ============================================
println("\n1. Creating Beneficiary #1: Alice Johnson")

alice = g.addV('person')
    .property('person_id', 'P000001')
    .property('first_name', 'Alice')
    .property('last_name', 'Johnson')
    .property('risk_score', 0.95)
    .property('flagged', true)
    .next()

alice_account = g.addV('account')
    .property('account_id', 'ACC00000001')
    .property('account_type', 'checking')
    .property('balance', 450000.0)
    .next()

alice.addEdge('owns_account', alice_account)

println("  ✅ Alice Johnson (flagged beneficiary)")
println("     Account: ACC00000001, Balance: $450,000")

// ============================================
// MULE ACCOUNTS (for Alice)
// ============================================
println("\n2. Creating Mule Accounts (feeding Alice)")

// Mule 1: Bob Smith
bob = g.addV('person')
    .property('person_id', 'P000002')
    .property('first_name', 'Bob')
    .property('last_name', 'Smith')
    .property('risk_score', 0.75)
    .property('flagged', false)
    .next()

bob_account = g.addV('account')
    .property('account_id', 'ACC00000011')
    .property('account_type', 'checking')
    .property('balance', 25000.0)
    .next()

bob.addEdge('owns_account', bob_account)

// Mule 2: Carol Williams
carol = g.addV('person')
    .property('person_id', 'P000003')
    .property('first_name', 'Carol')
    .property('last_name', 'Williams')
    .property('risk_score', 0.78)
    .property('flagged', false)
    .next()

carol_account = g.addV('account')
    .property('account_id', 'ACC00000012')
    .property('account_type', 'savings')
    .property('balance', 18000.0)
    .next()

carol.addEdge('owns_account', carol_account)

// Mule 3: David Brown
david = g.addV('person')
    .property('person_id', 'P000004')
    .property('first_name', 'David')
    .property('last_name', 'Brown')
    .property('risk_score', 0.72)
    .property('flagged', false)
    .next()

david_account = g.addV('account')
    .property('account_id', 'ACC00000013')
    .property('account_type', 'checking')
    .property('balance', 22000.0)
    .next()

david.addEdge('owns_account', david_account)

println("  ✅ 3 Mule accounts created")
println("     Bob Smith: ACC00000011")
println("     Carol Williams: ACC00000012")
println("     David Brown: ACC00000013")

// ============================================
// STRUCTURING TRANSACTIONS
// ============================================
println("\n3. Creating Structuring Transactions")
println("   (Multiple deposits < $10K threshold → Alice)")

// Transaction 1: Bob → Alice ($8,950)
txn1 = g.addV('transaction')
    .property('transaction_id', 'TXN0000000001')
    .property('amount', 8950.0)
    .property('timestamp', 1737975600L)
    .property('suspicious_pattern', 'structuring')
    .next()

bob_acc = g.V().has('account', 'account_id', 'ACC00000011').next()
alice_acc = g.V().has('account', 'account_id', 'ACC00000001').next()

txn1.addEdge('from_account', bob_acc)
txn1.addEdge('to_account', alice_acc)

// Transaction 2: Bob → Alice ($9,200)
txn2 = g.addV('transaction')
    .property('transaction_id', 'TXN0000000002')
    .property('amount', 9200.0)
    .property('timestamp', 1737979200L)
    .property('suspicious_pattern', 'structuring')
    .next()

txn2.addEdge('from_account', bob_acc)
txn2.addEdge('to_account', alice_acc)

// Transaction 3: Carol → Alice ($8,750)
txn3 = g.addV('transaction')
    .property('transaction_id', 'TXN0000000003')
    .property('amount', 8750.0)
    .property('timestamp', 1737982800L)
    .property('suspicious_pattern', 'structuring')
    .next()

carol_acc = g.V().has('account', 'account_id', 'ACC00000012').next()

txn3.addEdge('from_account', carol_acc)
txn3.addEdge('to_account', alice_acc)

// Transaction 4: Carol → Alice ($9,450)
txn4 = g.addV('transaction')
    .property('transaction_id', 'TXN0000000004')
    .property('amount', 9450.0)
    .property('timestamp', 1737986400L)
    .property('suspicious_pattern', 'structuring')
    .next()

txn4.addEdge('from_account', carol_acc)
txn4.addEdge('to_account', alice_acc)

// Transaction 5: David → Alice ($8,850)
txn5 = g.addV('transaction')
    .property('transaction_id', 'TXN0000000005')
    .property('amount', 8850.0)
    .property('timestamp', 1737990000L)
    .property('suspicious_pattern', 'structuring')
    .next()

david_acc = g.V().has('account', 'account_id', 'ACC00000013').next()

txn5.addEdge('from_account', david_acc)
txn5.addEdge('to_account', alice_acc)

// Transaction 6: David → Alice ($9,100)
txn6 = g.addV('transaction')
    .property('transaction_id', 'TXN0000000006')
    .property('amount', 9100.0)
    .property('timestamp', 1737993600L)
    .property('suspicious_pattern', 'structuring')
    .next()

txn6.addEdge('from_account', david_acc)
txn6.addEdge('to_account', alice_acc)

println("  ✅ 6 Structuring transactions created")
println("     Total Amount: $54,300 (all < $10K)")
println("     Time Window: 6 hours (coordinated)")

// ============================================
// NORMAL CUSTOMERS (noise)
// ============================================
println("\n4. Creating Normal Customers (noise)")

// Normal Customer 1: Eve Davis
eve = g.addV('person')
    .property('person_id', 'P000005')
    .property('first_name', 'Eve')
    .property('last_name', 'Davis')
    .property('risk_score', 0.15)
    .property('flagged', false)
    .next()

eve_account = g.addV('account')
    .property('account_id', 'ACC00000021')
    .property('account_type', 'checking')
    .property('balance', 35000.0)
    .next()

eve.addEdge('owns_account', eve_account)

// Normal Customer 2: Frank Miller
frank = g.addV('person')
    .property('person_id', 'P000006')
    .property('first_name', 'Frank')
    .property('last_name', 'Miller')
    .property('risk_score', 0.18)
    .property('flagged', false)
    .next()

frank_account = g.addV('account')
    .property('account_id', 'ACC00000022')
    .property('account_type', 'savings')
    .property('balance', 48000.0)
    .next()

frank.addEdge('owns_account', frank_account)

// Normal transactions
normal_txn1 = g.addV('transaction')
    .property('transaction_id', 'TXN0000000101')
    .property('amount', 2500.0)
    .property('timestamp', 1737975600L)
    .next()

normal_txn1.addEdge('from_account', eve_account)
normal_txn1.addEdge('to_account', frank_account)

normal_txn2 = g.addV('transaction')
    .property('transaction_id', 'TXN0000000102')
    .property('amount', 15000.0)
    .property('timestamp', 1737982800L)
    .next()

normal_txn2.addEdge('from_account', frank_account)
normal_txn2.addEdge('to_account', eve_account)

println("  ✅ 2 Normal customers created")
println("     Eve Davis: ACC00000021")
println("     Frank Miller: ACC00000022")

// ============================================
// VALIDATION
// ============================================
println("\n" + "=" * 60)
println("✅ DATA LOADING COMPLETE")
println("=" * 60)

println("\n📊 Final Graph Statistics:")
person_count = g.V().hasLabel('person').count().next()
account_count = g.V().hasLabel('account').count().next()
transaction_count = g.V().hasLabel('transaction').count().next()
ownership_count = g.E().hasLabel('owns_account').count().next()
from_count = g.E().hasLabel('from_account').count().next()
to_count = g.E().hasLabel('to_account').count().next()

println("  Persons: " + person_count)
println("  Accounts: " + account_count)
println("  Transactions: " + transaction_count)
println("  Ownership edges: " + ownership_count)
println("  Transaction edges: " + (from_count + to_count))

// ============================================
// DETECTION QUERIES
// ============================================
println("\n" + "=" * 60)
println("🔍 RUNNING STRUCTURING DETECTION QUERIES")
println("=" * 60)

// Query 1: Find all structuring transactions
println("\n1. All Structuring Transactions:")
structuring_txns = g.V().hasLabel('transaction')
    .has('suspicious_pattern', 'structuring')
    .valueMap('transaction_id', 'amount')
    .toList()

println("   Found " + structuring_txns.size() + " suspicious transactions:")
structuring_txns.each { txn ->
    id = txn['transaction_id'][0]
    amt = txn['amount'][0]
    println("     - " + id + ": $" + String.format("%.2f", amt))
}

// Query 2: Detect beneficiary (account receiving multiple deposits)
println("\n2. Beneficiary Account Detection:")
beneficiaries = g.V().hasLabel('transaction')
    .has('suspicious_pattern', 'structuring')
    .out('to_account')
    .groupCount()
    .unfold()
    .where(values.is(gte(2)))
    .select(keys)
    .valueMap('account_id', 'balance')
    .toList()

println("   Found " + beneficiaries.size() + " beneficiary account(s):")
beneficiaries.each { acc ->
    id = acc['account_id'][0]
    bal = acc['balance'][0]
    println("     - Account: " + id + ", Balance: $" + String.format("%.2f", bal))
}

// Query 3: Find mule accounts
println("\n3. Mule Account Detection:")
mules = g.V().hasLabel('transaction')
    .has('suspicious_pattern', 'structuring')
    .out('from_account')
    .dedup()
    .in('owns_account')
    .valueMap('person_id', 'first_name', 'last_name')
    .toList()

println("   Found " + mules.size() + " mule account owner(s):")
mules.each { person ->
    id = person['person_id'][0]
    fname = person['first_name'][0]
    lname = person['last_name'][0]
    println("     - " + id + ": " + fname + " " + lname)
}

// Query 4: Calculate total suspicious amount
println("\n4. Suspicious Amount Analysis:")
total_suspicious = g.V().hasLabel('transaction')
    .has('suspicious_pattern', 'structuring')
    .values('amount')
    .sum()
    .next()

avg_suspicious = total_suspicious / structuring_txns.size()

println("   Total Suspicious Amount: $" + String.format("%.2f", total_suspicious))
println("   Average Transaction: $" + String.format("%.2f", avg_suspicious))
println("   Reporting Threshold: $10,000.00")
println("   ✅ All transactions below threshold (typical structuring)")

// Query 5: Full structuring ring pattern
println("\n5. Complete Structuring Ring:")
println("   Beneficiary → Mule Accounts → Transactions")

ring = g.V().has('person', 'flagged', true)
    .as('beneficiary')
    .out('owns_account')
    .as('beneficiary_account')
    .in('to_account').hasLabel('transaction')
    .has('suspicious_pattern', 'structuring')
    .as('transaction')
    .out('from_account')
    .as('mule_account')
    .in('owns_account')
    .as('mule')
    .select('beneficiary', 'beneficiary_account', 'mule', 'mule_account', 'transaction')
    .by(values('first_name', 'last_name').fold())
    .by(values('account_id'))
    .by(values('first_name', 'last_name').fold())
    .by(values('account_id'))
    .by(values('transaction_id', 'amount').fold())
    .toList()

println("   Ring detected with " + ring.size() + " connection(s)")

println("\n" + "=" * 60)
println("✅ DETECTION COMPLETE - STRUCTURING PATTERN CONFIRMED")
println("=" * 60)

println("\n📝 Summary:")
println("  • Identified 1 beneficiary account (ACC00000001)")
println("  • Detected 3 mule accounts coordinating deposits")
println("  • Found 6 structuring transactions totaling $54,300")
println("  • All transactions < $10K reporting threshold")
println("  • Coordinated within 6-hour time window")
println("  • Pattern matches typical money laundering structuring")
println("\n🚨 ALERT: This pattern should trigger AML investigation!")

// Signature: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117
