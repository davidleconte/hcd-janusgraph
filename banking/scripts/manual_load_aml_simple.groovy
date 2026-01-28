// Manual AML Data Loading - Console-Friendly Version
// Single-line statements for Gremlin console
//
// Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team

:remote connect tinkerpop.server conf/remote.yaml
:remote console

// Load beneficiary
alice = g.addV('person').property('person_id', 'P000001').property('first_name', 'Alice').property('last_name', 'Johnson').property('risk_score', 0.95).property('flagged', true).next()
alice_account = g.addV('account').property('account_id', 'ACC00000001').property('account_type', 'checking').property('balance', 450000.0).next()
g.V(alice).addE('owns_account').to(alice_account).next()

// Load mule accounts
bob = g.addV('person').property('person_id', 'P000002').property('first_name', 'Bob').property('last_name', 'Smith').property('risk_score', 0.75).property('flagged', false).next()
bob_account = g.addV('account').property('account_id', 'ACC00000011').property('account_type', 'checking').property('balance', 25000.0).next()
g.V(bob).addE('owns_account').to(bob_account).next()

carol = g.addV('person').property('person_id', 'P000003').property('first_name', 'Carol').property('last_name', 'Williams').property('risk_score', 0.78).property('flagged', false).next()
carol_account = g.addV('account').property('account_id', 'ACC00000012').property('account_type', 'savings').property('balance', 18000.0).next()
g.V(carol).addE('owns_account').to(carol_account).next()

david = g.addV('person').property('person_id', 'P000004').property('first_name', 'David').property('last_name', 'Brown').property('risk_score', 0.72).property('flagged', false).next()
david_account = g.addV('account').property('account_id', 'ACC00000013').property('account_type', 'checking').property('balance', 22000.0).next()
g.V(david).addE('owns_account').to(david_account).next()

// Load structuring transactions
txn1 = g.addV('transaction').property('transaction_id', 'TXN0000000001').property('amount', 8950.0).property('timestamp', 1737975600L).property('suspicious_pattern', 'structuring').next()
g.V(txn1).addE('from_account').to(bob_account).next()
g.V(txn1).addE('to_account').to(alice_account).next()

txn2 = g.addV('transaction').property('transaction_id', 'TXN0000000002').property('amount', 9200.0).property('timestamp', 1737979200L).property('suspicious_pattern', 'structuring').next()
g.V(txn2).addE('from_account').to(bob_account).next()
g.V(txn2).addE('to_account').to(alice_account).next()

txn3 = g.addV('transaction').property('transaction_id', 'TXN0000000003').property('amount', 8750.0).property('timestamp', 1737982800L).property('suspicious_pattern', 'structuring').next()
g.V(txn3).addE('from_account').to(carol_account).next()
g.V(txn3).addE('to_account').to(alice_account).next()

txn4 = g.addV('transaction').property('transaction_id', 'TXN0000000004').property('amount', 9450.0).property('timestamp', 1737986400L).property('suspicious_pattern', 'structuring').next()
g.V(txn4).addE('from_account').to(carol_account).next()
g.V(txn4).addE('to_account').to(alice_account).next()

txn5 = g.addV('transaction').property('transaction_id', 'TXN0000000005').property('amount', 8850.0).property('timestamp', 1737990000L).property('suspicious_pattern', 'structuring').next()
g.V(txn5).addE('from_account').to(david_account).next()
g.V(txn5).addE('to_account').to(alice_account).next()

txn6 = g.addV('transaction').property('transaction_id', 'TXN0000000006').property('amount', 9100.0).property('timestamp', 1737993600L).property('suspicious_pattern', 'structuring').next()
g.V(txn6).addE('from_account').to(david_account).next()
g.V(txn6).addE('to_account').to(alice_account).next()

// Validate
g.V().hasLabel('person').count()
g.V().hasLabel('account').count()
g.V().hasLabel('transaction').count()

// Detection query 1: Find structuring transactions
g.V().hasLabel('transaction').has('suspicious_pattern', 'structuring').valueMap('transaction_id', 'amount').toList()

// Detection query 2: Find beneficiary account
g.V().hasLabel('transaction').has('suspicious_pattern', 'structuring').out('to_account').groupCount().unfold().where(values.is(gte(2))).select(keys).valueMap('account_id', 'balance').toList()

// Detection query 3: Calculate total suspicious amount
g.V().hasLabel('transaction').has('suspicious_pattern', 'structuring').values('amount').sum()
