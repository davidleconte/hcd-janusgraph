#!/usr/bin/env python3
"""
AML Structuring Data Loader

Loads synthetic structuring data into JanusGraph.
Connects entities with proper relationships and validates loading.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Contact: david.leconte1@ibm.com | +33614126117
Date: 2026-02-06
"""

import json
import sys
from datetime import datetime
from gremlin_python.driver import client
from gremlin_python.driver.protocol import GremlinServerError
from tqdm import tqdm
import time

class AMLDataLoader:
    """Load AML data into JanusGraph"""
    
    def __init__(self, gremlin_url='ws://localhost:18182/gremlin'):
        """Initialize loader with JanusGraph connection"""
        self.gremlin_url = gremlin_url
        self.gc = None
        self.stats = {
            'persons': 0,
            'accounts': 0,
            'transactions': 0,
            'addresses': 0,
            'phones': 0,
            'relationships': 0
        }
    
    def connect(self):
        """Connect to JanusGraph"""
        print(f"📡 Connecting to JanusGraph at {self.gremlin_url}...")
        try:
            self.gc = client.Client(self.gremlin_url, 'g')
            # Test connection
            result = self.gc.submit('g.V().limit(1)').all().result()
            print("✅ Connected to JanusGraph")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def close(self):
        """Close connection"""
        if self.gc:
            self.gc.close()
            print("🔌 Disconnected from JanusGraph")
    
    def load_persons(self, persons):
        """Load person vertices"""
        print(f"\n👤 Loading {len(persons)} persons...")
        
        for person in tqdm(persons, desc="Persons"):
            query = """
            person = g.addV('person')
                .property('person_id', person_id)
                .property('first_name', first_name)
                .property('last_name', last_name)
                .property('ssn', ssn)
                .property('date_of_birth', dob)
                .property('risk_score', risk_score)
                .property('flagged', flagged)
            """
            
            if person.get('flag_reason'):
                query += ".property('flag_reason', flag_reason)"
            
            query += ".next()"
            
            bindings = {
                'person_id': person['person_id'],
                'first_name': person['first_name'],
                'last_name': person['last_name'],
                'ssn': person['ssn'],
                'dob': person['date_of_birth'],
                'risk_score': person['risk_score'],
                'flagged': person['flagged'],
                'flag_reason': person.get('flag_reason')
            }
            
            try:
                self.gc.submit(query, bindings).all().result()
                self.stats['persons'] += 1
            except GremlinServerError as e:
                print(f"\n❌ Error loading person {person['person_id']}: {e}")
        
        print(f"✅ Loaded {self.stats['persons']} persons")
    
    def load_accounts(self, accounts):
        """Load account vertices"""
        print(f"\n💳 Loading {len(accounts)} accounts...")
        
        for account in tqdm(accounts, desc="Accounts"):
            query = """
            account = g.addV('account')
                .property('account_id', account_id)
                .property('account_type', account_type)
                .property('account_status', account_status)
                .property('balance', balance)
                .property('open_date', open_date)
                .next()
            """
            
            bindings = {
                'account_id': account['account_id'],
                'account_type': account['account_type'],
                'account_status': account['account_status'],
                'balance': account['balance'],
                'open_date': account['open_date']
            }
            
            try:
                self.gc.submit(query, bindings).all().result()
                self.stats['accounts'] += 1
            except GremlinServerError as e:
                print(f"\n❌ Error loading account {account['account_id']}: {e}")
        
        print(f"✅ Loaded {self.stats['accounts']} accounts")
    
    def load_addresses(self, addresses):
        """Load address vertices"""
        print(f"\n🏠 Loading {len(addresses)} addresses...")
        
        for address in tqdm(addresses, desc="Addresses"):
            query = """
            address = g.addV('address')
                .property('address_id', address_id)
                .property('street', street)
                .property('city', city)
                .property('state', state)
                .property('zip_code', zip_code)
                .next()
            """
            
            bindings = {
                'address_id': address['address_id'],
                'street': address['street'],
                'city': address['city'],
                'state': address['state'],
                'zip_code': address['zip_code']
            }
            
            try:
                self.gc.submit(query, bindings).all().result()
                self.stats['addresses'] += 1
            except GremlinServerError as e:
                print(f"\n❌ Error loading address {address['address_id']}: {e}")
        
        print(f"✅ Loaded {self.stats['addresses']} addresses")
    
    def load_phones(self, phones):
        """Load phone vertices"""
        print(f"\n📞 Loading {len(phones)} phones...")
        
        for phone in tqdm(phones, desc="Phones"):
            query = """
            phone = g.addV('phone')
                .property('phone_id', phone_id)
                .property('phone_number', phone_number)
                .next()
            """
            
            bindings = {
                'phone_id': phone['phone_id'],
                'phone_number': phone['phone_number']
            }
            
            try:
                self.gc.submit(query, bindings).all().result()
                self.stats['phones'] += 1
            except GremlinServerError as e:
                print(f"\n❌ Error loading phone {phone['phone_id']}: {e}")
        
        print(f"✅ Loaded {self.stats['phones']} phones")
    
    def load_transactions(self, transactions):
        """Load transaction vertices"""
        print(f"\n💸 Loading {len(transactions)} transactions...")
        
        for txn in tqdm(transactions, desc="Transactions"):
            query = """
            txn = g.addV('transaction')
                .property('transaction_id', txn_id)
                .property('amount', amount)
                .property('transaction_type', txn_type)
                .property('timestamp', timestamp)
                .property('date', date)
                .property('description', description)
            """
            
            if txn.get('suspicious_pattern'):
                query += ".property('suspicious_pattern', pattern)"
            
            query += ".next()"
            
            bindings = {
                'txn_id': txn['transaction_id'],
                'amount': txn['amount'],
                'txn_type': txn['transaction_type'],
                'timestamp': txn['timestamp'],
                'date': txn['date'],
                'description': txn['description'],
                'pattern': txn.get('suspicious_pattern')
            }
            
            try:
                self.gc.submit(query, bindings).all().result()
                self.stats['transactions'] += 1
            except GremlinServerError as e:
                print(f"\n❌ Error loading transaction {txn['transaction_id']}: {e}")
        
        print(f"✅ Loaded {self.stats['transactions']} transactions")
    
    def create_relationships(self, data):
        """Create all relationships (edges)"""
        print(f"\n🔗 Creating relationships...")
        
        # Person owns Account
        print("  Creating person -> owns_account -> account...")
        for account in tqdm(data['accounts'], desc="Owns relationships"):
            query = """
            person = g.V().has('person', 'person_id', person_id).next()
            account = g.V().has('account', 'account_id', account_id).next()
            person.addEdge('owns_account', account)
            """
            
            bindings = {
                'person_id': account['owner_person_id'],
                'account_id': account['account_id']
            }
            
            try:
                self.gc.submit(query, bindings).all().result()
                self.stats['relationships'] += 1
            except GremlinServerError as e:
                print(f"\n❌ Error creating owns_account relationship: {e}")
        
        # Transaction from/to Account
        print("  Creating transaction -> from_account/to_account -> account...")
        for txn in tqdm(data['transactions'], desc="Transaction relationships"):
            query = """
            txn = g.V().has('transaction', 'transaction_id', txn_id).next()
            from_acc = g.V().has('account', 'account_id', from_account_id).next()
            to_acc = g.V().has('account', 'account_id', to_account_id).next()
            txn.addEdge('from_account', from_acc)
            txn.addEdge('to_account', to_acc)
            """
            
            bindings = {
                'txn_id': txn['transaction_id'],
                'from_account_id': txn['from_account_id'],
                'to_account_id': txn['to_account_id']
            }
            
            try:
                self.gc.submit(query, bindings).all().result()
                self.stats['relationships'] += 2
            except GremlinServerError as e:
                print(f"\n❌ Error creating transaction relationships: {e}")
        
        print(f"✅ Created {self.stats['relationships']} relationships")
    
    def validate_loading(self):
        """Validate data was loaded correctly"""
        print(f"\n✅ Validation")
        print("=" * 50)
        
        # Count vertices by label
        counts = {
            'person': self.gc.submit("g.V().hasLabel('person').count()").all().result()[0],
            'account': self.gc.submit("g.V().hasLabel('account').count()").all().result()[0],
            'transaction': self.gc.submit("g.V().hasLabel('transaction').count()").all().result()[0],
            'address': self.gc.submit("g.V().hasLabel('address').count()").all().result()[0],
            'phone': self.gc.submit("g.V().hasLabel('phone').count()").all().result()[0]
        }
        
        print("Vertex counts:")
        for label, count in counts.items():
            expected = self.stats[f"{label}s"]
            status = "✅" if count == expected else "⚠️"
            print(f"  {status} {label}: {count} (expected {expected})")
        
        # Count edges
        total_edges = self.gc.submit("g.E().count()").all().result()[0]
        print(f"\nEdge count:")
        print(f"  ✅ Total edges: {total_edges}")
        
        # Find structuring transactions
        structuring_count = self.gc.submit(
            "g.V().hasLabel('transaction').has('suspicious_pattern', 'structuring').count()"
        ).all().result()[0]
        print(f"\nStructuring pattern:")
        print(f"  🚨 Suspicious transactions: {structuring_count}")
        
        # Find flagged persons
        flagged_count = self.gc.submit(
            "g.V().hasLabel('person').has('flagged', true).count()"
        ).all().result()[0]
        print(f"  🚩 Flagged persons: {flagged_count}")
        
        print("=" * 50)
    
    def load_all(self, data_file='banking/data/aml/aml_structuring_data.json'):
        """Load all data from JSON file"""
        print(f"\n📂 Loading data from {data_file}")
        
        # Load JSON
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        print(f"✅ Loaded JSON with:")
        print(f"  - {len(data['persons'])} persons")
        print(f"  - {len(data['accounts'])} accounts")
        print(f"  - {len(data['transactions'])} transactions")
        print(f"  - {len(data['addresses'])} addresses")
        print(f"  - {len(data['phones'])} phones")
        
        # Load in sequence
        start_time = time.time()
        
        self.load_persons(data['persons'])
        self.load_accounts(data['accounts'])
        self.load_addresses(data['addresses'])
        self.load_phones(data['phones'])
        self.load_transactions(data['transactions'])
        self.create_relationships(data)
        
        elapsed = time.time() - start_time
        print(f"\n⏱️  Loading completed in {elapsed:.2f} seconds")
        
        # Validate
        self.validate_loading()


def main():
    """Main execution"""
    print("=" * 60)
    print("AML Structuring Data Loader")
    print("=" * 60)
    
    # Create loader
    loader = AMLDataLoader(gremlin_url='ws://localhost:18182/gremlin')
    
    # Connect
    if not loader.connect():
        sys.exit(1)
    
    try:
        # Load data
        loader.load_all('banking/data/aml/aml_structuring_data.json')
        
        print("\n" + "=" * 60)
        print("✅ Loading complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Run detection queries (banking/queries/structuring_detection.groovy)")
        print("  2. Analyze results in Jupyter notebook")
        print("  3. Visualize structuring rings")
        
    except Exception as e:
        print(f"\n❌ Error during loading: {e}")
        import traceback
        traceback.print_exc()
    finally:
        loader.close()


if __name__ == '__main__':
    main()

# Signature: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117
