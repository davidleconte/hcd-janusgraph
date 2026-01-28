// AML Banking Schema for JanusGraph
// Anti-Money Laundering Use Case - Structuring/Smurfing Detection
//
// Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
// Contact: david.leconte1@ibm.com | +33614126117
// Date: 2026-01-28

// Open graph management
mgmt = graph.openManagement()

// ============================================
// VERTEX LABELS (Entities)
// ============================================

// Person (customer, beneficial owner)
person = mgmt.makeVertexLabel('person').make()

// Account (checking, savings)
account = mgmt.makeVertexLabel('account').make()

// Transaction (deposit, withdrawal, transfer)
transaction = mgmt.makeVertexLabel('transaction').make()

// Address (physical location)
address = mgmt.makeVertexLabel('address').make()

// Phone (contact number)
phone = mgmt.makeVertexLabel('phone').make()

// Company (legal entity, shell company)
company = mgmt.makeVertexLabel('company').make()

// ============================================
// EDGE LABELS (Relationships)
// ============================================

// Person owns account
owns_account = mgmt.makeEdgeLabel('owns_account').make()

// Transaction from/to account
from_account = mgmt.makeEdgeLabel('from_account').make()
to_account = mgmt.makeEdgeLabel('to_account').make()

// Person/Company has address
has_address = mgmt.makeEdgeLabel('has_address').make()

// Person/Company has phone
has_phone = mgmt.makeEdgeLabel('has_phone').make()

// Person is beneficial owner of company
beneficial_owner = mgmt.makeEdgeLabel('beneficial_owner').make()

// Company owns company (ownership chain)
owns_company = mgmt.makeEdgeLabel('owns_company').make()

// Shared address/phone (implicit relationship)
shared_address = mgmt.makeEdgeLabel('shared_address').make()
shared_phone = mgmt.makeEdgeLabel('shared_phone').make()

// ============================================
// PROPERTIES
// ============================================

// Person properties
person_id = mgmt.makePropertyKey('person_id').dataType(String.class).make()
first_name = mgmt.makePropertyKey('first_name').dataType(String.class).make()
last_name = mgmt.makePropertyKey('last_name').dataType(String.class).make()
ssn = mgmt.makePropertyKey('ssn').dataType(String.class).make()
date_of_birth = mgmt.makePropertyKey('date_of_birth').dataType(String.class).make()

// Account properties
account_id = mgmt.makePropertyKey('account_id').dataType(String.class).make()
account_type = mgmt.makePropertyKey('account_type').dataType(String.class).make()
account_status = mgmt.makePropertyKey('account_status').dataType(String.class).make()
balance = mgmt.makePropertyKey('balance').dataType(Double.class).make()
open_date = mgmt.makePropertyKey('open_date').dataType(String.class).make()

// Transaction properties
transaction_id = mgmt.makePropertyKey('transaction_id').dataType(String.class).make()
amount = mgmt.makePropertyKey('amount').dataType(Double.class).make()
transaction_type = mgmt.makePropertyKey('transaction_type').dataType(String.class).make()
timestamp = mgmt.makePropertyKey('timestamp').dataType(Long.class).make()
date = mgmt.makePropertyKey('date').dataType(String.class).make()
description = mgmt.makePropertyKey('description').dataType(String.class).make()

// Address properties
address_id = mgmt.makePropertyKey('address_id').dataType(String.class).make()
street = mgmt.makePropertyKey('street').dataType(String.class).make()
city = mgmt.makePropertyKey('city').dataType(String.class).make()
state = mgmt.makePropertyKey('state').dataType(String.class).make()
zip_code = mgmt.makePropertyKey('zip_code').dataType(String.class).make()

// Phone properties
phone_id = mgmt.makePropertyKey('phone_id').dataType(String.class).make()
phone_number = mgmt.makePropertyKey('phone_number').dataType(String.class).make()

// Company properties
company_id = mgmt.makePropertyKey('company_id').dataType(String.class).make()
company_name = mgmt.makePropertyKey('company_name').dataType(String.class).make()
registration_number = mgmt.makePropertyKey('registration_number').dataType(String.class).make()
company_type = mgmt.makePropertyKey('company_type').dataType(String.class).make()

// AML-specific properties
risk_score = mgmt.makePropertyKey('risk_score').dataType(Double.class).make()
flagged = mgmt.makePropertyKey('flagged').dataType(Boolean.class).make()
flag_reason = mgmt.makePropertyKey('flag_reason').dataType(String.class).make()
suspicious_pattern = mgmt.makePropertyKey('suspicious_pattern').dataType(String.class).make()

// ============================================
// COMPOSITE INDICES (for fast lookups)
// ============================================

// Person by ID
mgmt.buildIndex('personById', Vertex.class)
    .addKey(person_id)
    .indexOnly(person)
    .unique()
    .buildCompositeIndex()

// Account by ID
mgmt.buildIndex('accountById', Vertex.class)
    .addKey(account_id)
    .indexOnly(account)
    .unique()
    .buildCompositeIndex()

// Transaction by ID
mgmt.buildIndex('transactionById', Vertex.class)
    .addKey(transaction_id)
    .indexOnly(transaction)
    .unique()
    .buildCompositeIndex()

// Transaction by timestamp (for time-based queries)
mgmt.buildIndex('transactionByTimestamp', Vertex.class)
    .addKey(timestamp)
    .indexOnly(transaction)
    .buildCompositeIndex()

// Transaction by amount (for structuring detection)
mgmt.buildIndex('transactionByAmount', Vertex.class)
    .addKey(amount)
    .indexOnly(transaction)
    .buildCompositeIndex()

// Address by ID
mgmt.buildIndex('addressById', Vertex.class)
    .addKey(address_id)
    .indexOnly(address)
    .unique()
    .buildCompositeIndex()

// Phone by number
mgmt.buildIndex('phoneByNumber', Vertex.class)
    .addKey(phone_number)
    .indexOnly(phone)
    .unique()
    .buildCompositeIndex()

// Company by ID
mgmt.buildIndex('companyById', Vertex.class)
    .addKey(company_id)
    .indexOnly(company)
    .unique()
    .buildCompositeIndex()

// Flagged entities (for risk monitoring)
mgmt.buildIndex('flaggedEntities', Vertex.class)
    .addKey(flagged)
    .buildCompositeIndex()

// ============================================
// MIXED INDICES (for text search - requires backend support)
// ============================================

// Person by name (for fuzzy matching)
// Commented out - requires Elasticsearch/Lucene backend
// mgmt.buildIndex('personByName', Vertex.class)
//     .addKey(first_name, Mapping.STRING.asParameter())
//     .addKey(last_name, Mapping.STRING.asParameter())
//     .indexOnly(person)
//     .buildMixedIndex("search")

// ============================================
// COMMIT SCHEMA
// ============================================

mgmt.commit()

println("✅ AML Banking Schema created successfully")
println("   - 6 vertex labels")
println("   - 9 edge labels")
println("   - 30+ properties")
println("   - 10 composite indices")

// Signature: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS) - david.leconte1@ibm.com | +33614126117
