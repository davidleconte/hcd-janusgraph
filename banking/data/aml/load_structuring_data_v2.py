#!/usr/bin/env python3
"""
Improved AML Structuring Data Loader
Better error handling and compatibility

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Date: 2026-02-06
"""

import json
import time
from gremlin_python.driver import client

class ImprovedAMLLoader:
    """Load AML data with robust error handling"""
    
    def __init__(self, url='ws://localhost:18182/gremlin'):
        self.url = url
        self.gc = None
        self.stats = {'loaded': 0, 'skipped': 0, 'errors': 0}
    
    def connect(self):
        """Connect to JanusGraph"""
        print(f"📡 Connecting to JanusGraph at {self.url}...")
        try:
            self.gc = client.Client(self.url, 'g')
            result = self.gc.submit('1+1').all().result()
            print(f"✅ Connected (test: 1+1 = {result[0]})")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def vertex_exists(self, label, prop, value):
        """Check if vertex exists"""
        query = f"g.V().hasLabel('{label}').has('{prop}', '{value}').count()"
        try:
            result = self.gc.submit(query).all().result()
            return result[0] > 0 if result else False
        except:
            return False
    
    def create_vertex(self, label, properties):
        """Create vertex with error handling"""
        # Build query
        prop_str = ''.join([f".property('{k}', {self._format_value(v)})" for k, v in properties.items()])
        query = f"g.addV('{label}'){prop_str}.next()"
        
        try:
            result = self.gc.submit(query).all().result()
            self.stats['loaded'] += 1
            return True
        except Exception as e:
            if "already exists" in str(e) or "duplicate" in str(e).lower():
                self.stats['skipped'] += 1
                return True
            else:
                print(f"  ❌ Error creating {label}: {e}")
                self.stats['errors'] += 1
                return False
    
    def _format_value(self, value):
        """Format value for Gremlin query"""
        if isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (int, float)):
            # Use explicit double for floats
            if isinstance(value, float):
                return f"{value}d"
            return str(value)
        else:
            return f"'{str(value)}'"
    
    def create_edge(self, from_label, from_prop, from_val, edge_label, to_label, to_prop, to_val):
        """Create edge with error handling"""
        query = f"""
        from_v = g.V().hasLabel('{from_label}').has('{from_prop}', '{from_val}').next()
        to_v = g.V().hasLabel('{to_label}').has('{to_prop}', '{to_val}').next()
        from_v.addEdge('{edge_label}', to_v)
        """
        
        try:
            self.gc.submit(query).all().result()
            return True
        except Exception as e:
            if "already exists" in str(e) or "duplicate" in str(e).lower():
                self.stats['skipped'] += 1
                return True
            # Vertices might not exist
            return False
    
    def load_sample_data(self):
        """Load sample AML structuring data"""
        print("\n💾 Loading Sample AML Data...")
        print("=" * 50)
        
        # Sample data: beneficiary + 3 mules + 6 structuring transactions
        
        # Beneficiary
        print("\n1. Loading Beneficiary (Alice Johnson)...")
        self.create_vertex('person', {
            'person_id': 'P000001',
            'first_name': 'Alice',
            'last_name': 'Johnson',
            'risk_score': 0.95,
            'flagged': True
        })
        
        self.create_vertex('account', {
            'account_id': 'ACC00000001',
            'account_type': 'checking',
            'balance': 450000.0
        })
        
        self.create_edge('person', 'person_id', 'P000001', 
                        'owns_account', 
                        'account', 'account_id', 'ACC00000001')
        
        print(f"  ✅ Beneficiary loaded")
        
        # Mule Accounts
        print("\n2. Loading Mule Accounts...")
        mules = [
            {'id': 'P000002', 'fname': 'Bob', 'lname': 'Smith', 'acc': 'ACC00000011', 'bal': 25000.0, 'risk': 0.75},
            {'id': 'P000003', 'fname': 'Carol', 'lname': 'Williams', 'acc': 'ACC00000012', 'bal': 18000.0, 'risk': 0.78},
            {'id': 'P000004', 'fname': 'David', 'lname': 'Brown', 'acc': 'ACC00000013', 'bal': 22000.0, 'risk': 0.72}
        ]
        
        for mule in mules:
            self.create_vertex('person', {
                'person_id': mule['id'],
                'first_name': mule['fname'],
                'last_name': mule['lname'],
                'risk_score': mule['risk'],
                'flagged': False
            })
            
            self.create_vertex('account', {
                'account_id': mule['acc'],
                'account_type': 'checking',
                'balance': mule['bal']
            })
            
            self.create_edge('person', 'person_id', mule['id'],
                           'owns_account',
                           'account', 'account_id', mule['acc'])
        
        print(f"  ✅ {len(mules)} mule accounts loaded")
        
        # Structuring Transactions
        print("\n3. Loading Structuring Transactions...")
        transactions = [
            {'id': 'TXN0000000001', 'from': 'ACC00000011', 'to': 'ACC00000001', 'amt': 8950.0, 'ts': 1737975600},
            {'id': 'TXN0000000002', 'from': 'ACC00000011', 'to': 'ACC00000001', 'amt': 9200.0, 'ts': 1737979200},
            {'id': 'TXN0000000003', 'from': 'ACC00000012', 'to': 'ACC00000001', 'amt': 8750.0, 'ts': 1737982800},
            {'id': 'TXN0000000004', 'from': 'ACC00000012', 'to': 'ACC00000001', 'amt': 9450.0, 'ts': 1737986400},
            {'id': 'TXN0000000005', 'from': 'ACC00000013', 'to': 'ACC00000001', 'amt': 8850.0, 'ts': 1737990000},
            {'id': 'TXN0000000006', 'from': 'ACC00000013', 'to': 'ACC00000001', 'amt': 9100.0, 'ts': 1737993600},
        ]
        
        for txn in transactions:
            self.create_vertex('transaction', {
                'transaction_id': txn['id'],
                'amount': txn['amt'],
                'timestamp': txn['ts'],
                'suspicious_pattern': 'structuring'
            })
            
            # Create from/to edges
            self.create_edge('transaction', 'transaction_id', txn['id'],
                           'from_account',
                           'account', 'account_id', txn['from'])
            
            self.create_edge('transaction', 'transaction_id', txn['id'],
                           'to_account',
                           'account', 'account_id', txn['to'])
        
        print(f"  ✅ {len(transactions)} transactions loaded")
        
        print("\n" + "=" * 50)
        print("✅ Sample data loading complete")
        print("=" * 50)
    
    def validate(self):
        """Validate loaded data"""
        print("\n📊 Validation:")
        print("-" * 50)
        
        counts = {
            'person': self.gc.submit("g.V().hasLabel('person').count()").all().result()[0],
            'account': self.gc.submit("g.V().hasLabel('account').count()").all().result()[0],
            'transaction': self.gc.submit("g.V().hasLabel('transaction').count()").all().result()[0],
        }
        
        print(f"  Persons: {counts['person']}")
        print(f"  Accounts: {counts['account']}")
        print(f"  Transactions: {counts['transaction']}")
        
        # Find structuring
        try:
            structuring = self.gc.submit(
                "g.V().hasLabel('transaction').has('suspicious_pattern', 'structuring').count()"
            ).all().result()[0]
            print(f"\n  🚨 Structuring Transactions: {structuring}")
            
            if structuring > 0:
                total_amt = self.gc.submit(
                    "g.V().hasLabel('transaction').has('suspicious_pattern', 'structuring').values('amount').sum()"
                ).all().result()
                if total_amt:
                    print(f"  💰 Total Suspicious Amount: ${total_amt[0]:,.2f}")
        except Exception as e:
            print(f"  ⚠️  Validation query error: {e}")
        
        print(f"\n  Stats: Loaded={self.stats['loaded']}, Skipped={self.stats['skipped']}, Errors={self.stats['errors']}")
    
    def close(self):
        """Close connection"""
        if self.gc:
            self.gc.close()
            print("\n🔌 Disconnected")

def main():
    loader = ImprovedAMLLoader()
    
    if not loader.connect():
        return
    
    try:
        loader.load_sample_data()
        loader.validate()
        
        print("\n✅ Loading successful!")
        print("\nNext steps:")
        print("  1. Run detection queries")
        print("  2. Create Jupyter notebook for analysis")
        print("  3. Visualize structuring rings")
    except Exception as e:
        print(f"\n❌ Loading failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        loader.close()

if __name__ == '__main__':
    main()
