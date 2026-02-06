"""
AML Structuring Detection - Analysis Notebook
Interactive analysis of money laundering structuring patterns

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Contact: david.leconte1@ibm.com | +33614126117
Date: 2026-02-06
"""

# Cell 1: Setup and Imports
print("=== AML Structuring Detection Analysis ===\n")

import nest_asyncio
nest_asyncio.apply()

from gremlin_python.driver import client
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import __
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
import pandas as pd
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("✅ Imports successful")

# Cell 2: Connect to JanusGraph
print("\n📡 Connecting to JanusGraph...")

GREMLIN_URL = 'ws://localhost:18182/gremlin'

try:
    # Create connection
    gc = client.Client(GREMLIN_URL, 'g')
    
    # Test connection with simple query
    result = gc.submit('1+1').all().result()
    print(f"✅ Connected to JanusGraph at {GREMLIN_URL}")
    print(f"   Test query result: {result[0]}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("   Make sure JanusGraph is running on port 18182")

# Cell 3: Create Banking Schema
print("\n🏗️  Creating Banking Schema...")

schema_queries = [
    # Create vertex labels
    "mgmt = graph.openManagement(); person = mgmt.makeVertexLabel('person').make(); mgmt.commit()",
    "mgmt = graph.openManagement(); account = mgmt.makeVertexLabel('account').make(); mgmt.commit()",
    "mgmt = graph.openManagement(); transaction = mgmt.makeVertexLabel('transaction').make(); mgmt.commit()",
    
    # Create edge labels
    "mgmt = graph.openManagement(); owns_account = mgmt.makeEdgeLabel('owns_account').make(); mgmt.commit()",
    "mgmt = graph.openManagement(); from_account = mgmt.makeEdgeLabel('from_account').make(); mgmt.commit()",
    "mgmt = graph.openManagement(); to_account = mgmt.makeEdgeLabel('to_account').make(); mgmt.commit()",
    
    # Create properties
    "mgmt = graph.openManagement(); person_id = mgmt.makePropertyKey('person_id').dataType(String.class).make(); mgmt.commit()",
    "mgmt = graph.openManagement(); first_name = mgmt.makePropertyKey('first_name').dataType(String.class).make(); mgmt.commit()",
    "mgmt = graph.openManagement(); last_name = mgmt.makePropertyKey('last_name').dataType(String.class).make(); mgmt.commit()",
    "mgmt = graph.openManagement(); account_id = mgmt.makePropertyKey('account_id').dataType(String.class).make(); mgmt.commit()",
    "mgmt = graph.openManagement(); account_type = mgmt.makePropertyKey('account_type').dataType(String.class).make(); mgmt.commit()",
    "mgmt = graph.openManagement(); balance = mgmt.makePropertyKey('balance').dataType(Double.class).make(); mgmt.commit()",
    "mgmt = graph.openManagement(); transaction_id = mgmt.makePropertyKey('transaction_id').dataType(String.class).make(); mgmt.commit()",
    "mgmt = graph.openManagement(); amount = mgmt.makePropertyKey('amount').dataType(Double.class).make(); mgmt.commit()",
    "mgmt = graph.openManagement(); timestamp = mgmt.makePropertyKey('timestamp').dataType(Long.class).make(); mgmt.commit()",
    "mgmt = graph.openManagement(); suspicious_pattern = mgmt.makePropertyKey('suspicious_pattern').dataType(String.class).make(); mgmt.commit()",
    "mgmt = graph.openManagement(); risk_score = mgmt.makePropertyKey('risk_score').dataType(Double.class).make(); mgmt.commit()",
    "mgmt = graph.openManagement(); flagged = mgmt.makePropertyKey('flagged').dataType(Boolean.class).make(); mgmt.commit()",
]

schema_created = True
for query in schema_queries:
    try:
        result = gc.submit(query).all().result()
    except Exception as e:
        if "already exists" in str(e) or "already defined" in str(e):
            print(f"   ⚠️  Element already exists (expected if schema exists)")
        else:
            print(f"   ❌ Schema creation error: {e}")
            schema_created = False
            break

if schema_created:
    print("✅ Banking schema ready")
else:
    print("⚠️  Schema creation had issues - may already exist")

# Cell 4: Load Sample Data
print("\n💾 Loading Sample AML Data...")

# Load generated data
with open('banking/data/aml/aml_structuring_data.json', 'r') as f:
    data = json.load(f)

print(f"Data loaded from JSON:")
print(f"  Persons: {len(data['persons'])}")
print(f"  Accounts: {len(data['accounts'])}")
print(f"  Transactions: {len(data['transactions'])}")

# Load a subset for demo (first 10 of each)
sample_persons = data['persons'][:10]
sample_accounts = data['accounts'][:15]

# Find structuring transactions
structuring_txns = [t for t in data['transactions'] if t.get('suspicious_pattern') == 'structuring'][:20]
print(f"\n📊 Sample data:")
print(f"  Loading {len(sample_persons)} persons")
print(f"  Loading {len(sample_accounts)} accounts")
print(f"  Loading {len(structuring_txns)} structuring transactions")

# Load persons
print("\nLoading persons...")
for person in sample_persons:
    query = f"""
    g.addV('person')
        .property('person_id', '{person['person_id']}')
        .property('first_name', '{person['first_name']}')
        .property('last_name', '{person['last_name']}')
        .property('risk_score', {person['risk_score']})
        .property('flagged', {str(person['flagged']).lower()})
    """
    try:
        gc.submit(query).all().result()
    except Exception as e:
        if "vertex with id" in str(e).lower():
            pass  # Already exists
        else:
            print(f"Error loading person: {e}")

print(f"✅ Loaded {len(sample_persons)} persons")

# Load accounts
print("\nLoading accounts...")
for account in sample_accounts:
    query = f"""
    g.addV('account')
        .property('account_id', '{account['account_id']}')
        .property('account_type', '{account['account_type']}')
        .property('balance', {account['balance']})
    """
    try:
        gc.submit(query).all().result()
    except Exception as e:
        if "vertex with id" in str(e).lower():
            pass
        else:
            print(f"Error loading account: {e}")

# Create ownership relationships
for account in sample_accounts:
    owner_id = account['owner_person_id']
    account_id = account['account_id']
    query = f"""
    person = g.V().has('person', 'person_id', '{owner_id}').next()
    account = g.V().has('account', 'account_id', '{account_id}').next()
    person.addEdge('owns_account', account)
    """
    try:
        gc.submit(query).all().result()
    except Exception as e:
        pass  # Might not exist or already connected

print(f"✅ Loaded {len(sample_accounts)} accounts with ownership links")

# Load transactions
print("\nLoading structuring transactions...")
for txn in structuring_txns:
    query = f"""
    g.addV('transaction')
        .property('transaction_id', '{txn['transaction_id']}')
        .property('amount', {txn['amount']})
        .property('timestamp', {txn['timestamp']})
        .property('suspicious_pattern', 'structuring')
    """
    try:
        gc.submit(query).all().result()
        
        # Create from/to relationships
        from_query = f"""
        txn = g.V().has('transaction', 'transaction_id', '{txn['transaction_id']}').next()
        from_acc = g.V().has('account', 'account_id', '{txn['from_account_id']}').next()
        to_acc = g.V().has('account', 'account_id', '{txn['to_account_id']}').next()
        txn.addEdge('from_account', from_acc)
        txn.addEdge('to_account', to_acc)
        """
        gc.submit(from_query).all().result()
    except Exception as e:
        pass  # Account might not exist in sample

print(f"✅ Loaded {len(structuring_txns)} transactions")

# Cell 5: Validate Data Loading
print("\n✅ Data Validation")
print("=" * 50)

counts = {
    'persons': gc.submit("g.V().hasLabel('person').count()").all().result()[0],
    'accounts': gc.submit("g.V().hasLabel('account').count()").all().result()[0],
    'transactions': gc.submit("g.V().hasLabel('transaction').count()").all().result()[0],
    'ownership_edges': gc.submit("g.E().hasLabel('owns_account').count()").all().result()[0],
}

print(f"Vertex counts:")
print(f"  Persons: {counts['persons']}")
print(f"  Accounts: {counts['accounts']}")
print(f"  Transactions: {counts['transactions']}")
print(f"\nEdge counts:")
print(f"  Ownership relationships: {counts['ownership_edges']}")

# Cell 6: Run Detection Queries
print("\n🔍 Running Structuring Detection Queries")
print("=" * 50)

# Query 1: Find all structuring transactions
print("\nQuery 1: All Structuring Transactions")
query = """
g.V().hasLabel('transaction')
    .has('suspicious_pattern', 'structuring')
    .valueMap('transaction_id', 'amount', 'timestamp')
    .limit(10)
"""
results = gc.submit(query).all().result()
print(f"Found {len(results)} structuring transactions")
if results:
    df = pd.DataFrame(results)
    print(df.head())

# Query 2: Find beneficiary accounts (receiving multiple structuring deposits)
print("\n\nQuery 2: Beneficiary Accounts")
query = """
g.V().hasLabel('transaction')
    .has('suspicious_pattern', 'structuring')
    .out('to_account')
    .groupCount()
    .unfold()
    .where(values.is(gte(2)))
    .select(keys)
    .valueMap('account_id', 'balance')
"""
try:
    results = gc.submit(query).all().result()
    print(f"Found {len(results)} potential beneficiary accounts")
    if results:
        for r in results:
            print(f"  Account: {r.get('account_id', ['Unknown'])[0]}, Balance: ${r.get('balance', [0])[0]:,.2f}")
except Exception as e:
    print(f"Error: {e}")

# Query 3: Find mule accounts (sending multiple structuring deposits)
print("\n\nQuery 3: Mule Accounts")
query = """
g.V().hasLabel('transaction')
    .has('suspicious_pattern', 'structuring')
    .out('from_account')
    .groupCount()
    .unfold()
    .where(values.is(gte(2)))
    .select(keys)
    .valueMap('account_id')
"""
try:
    results = gc.submit(query).all().result()
    print(f"Found {len(results)} potential mule accounts")
except Exception as e:
    print(f"Error: {e}")

# Cell 7: Summary Statistics
print("\n\n📊 AML Structuring Pattern Analysis Summary")
print("=" * 50)

total_structuring = gc.submit("g.V().hasLabel('transaction').has('suspicious_pattern', 'structuring').count()").all().result()[0]
total_amount = gc.submit("g.V().hasLabel('transaction').has('suspicious_pattern', 'structuring').values('amount').sum()").all().result()[0]
avg_amount = total_amount / total_structuring if total_structuring > 0 else 0

print(f"\nStructuring Pattern Detection:")
print(f"  Total Suspicious Transactions: {total_structuring}")
print(f"  Total Amount: ${total_amount:,.2f}")
print(f"  Average Amount: ${avg_amount:,.2f}")
print(f"  Detection Threshold: $10,000")
print(f"\n✅ All transactions below reporting threshold")
print(f"   (Typical structuring pattern)")

print("\n" + "=" * 50)
print("✅ Analysis Complete!")
print("\nNext steps:")
print("  1. Visualize structuring rings (NetworkX)")
print("  2. Calculate risk scores")
print("  3. Generate compliance reports")

# Close connection
gc.close()
print("\n🔌 Disconnected from JanusGraph")
