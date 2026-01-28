// Load AML schema via remote connection
:remote connect tinkerpop.server conf/remote.yaml
:remote console

// Now load the schema
mgmt = graph.openManagement()

// Vertex labels
person = mgmt.makeVertexLabel('person').make()
account = mgmt.makeVertexLabel('account').make()
transaction = mgmt.makeVertexLabel('transaction').make()
address = mgmt.makeVertexLabel('address').make()
phone = mgmt.makeVertexLabel('phone').make()
company = mgmt.makeVertexLabel('company').make()

// Edge labels
owns_account = mgmt.makeEdgeLabel('owns_account').make()
from_account = mgmt.makeEdgeLabel('from_account').make()
to_account = mgmt.makeEdgeLabel('to_account').make()
has_address = mgmt.makeEdgeLabel('has_address').make()
has_phone = mgmt.makeEdgeLabel('has_phone').make()
beneficial_owner = mgmt.makeEdgeLabel('beneficial_owner').make()
owns_company = mgmt.makeEdgeLabel('owns_company').make()
shared_address = mgmt.makeEdgeLabel('shared_address').make()
shared_phone = mgmt.makeEdgeLabel('shared_phone').make()

// Properties
person_id = mgmt.makePropertyKey('person_id').dataType(String.class).make()
first_name = mgmt.makePropertyKey('first_name').dataType(String.class).make()
last_name = mgmt.makePropertyKey('last_name').dataType(String.class).make()
ssn = mgmt.makePropertyKey('ssn').dataType(String.class).make()
date_of_birth = mgmt.makePropertyKey('date_of_birth').dataType(String.class).make()

account_id = mgmt.makePropertyKey('account_id').dataType(String.class).make()
account_type = mgmt.makePropertyKey('account_type').dataType(String.class).make()
account_status = mgmt.makePropertyKey('account_status').dataType(String.class).make()
balance = mgmt.makePropertyKey('balance').dataType(Double.class).make()
open_date = mgmt.makePropertyKey('open_date').dataType(String.class).make()

transaction_id = mgmt.makePropertyKey('transaction_id').dataType(String.class).make()
amount = mgmt.makePropertyKey('amount').dataType(Double.class).make()
transaction_type = mgmt.makePropertyKey('transaction_type').dataType(String.class).make()
timestamp = mgmt.makePropertyKey('timestamp').dataType(Long.class).make()
date = mgmt.makePropertyKey('date').dataType(String.class).make()
description = mgmt.makePropertyKey('description').dataType(String.class).make()

address_id = mgmt.makePropertyKey('address_id').dataType(String.class).make()
street = mgmt.makePropertyKey('street').dataType(String.class).make()
city = mgmt.makePropertyKey('city').dataType(String.class).make()
state = mgmt.makePropertyKey('state').dataType(String.class).make()
zip_code = mgmt.makePropertyKey('zip_code').dataType(String.class).make()

phone_id = mgmt.makePropertyKey('phone_id').dataType(String.class).make()
phone_number = mgmt.makePropertyKey('phone_number').dataType(String.class).make()

company_id = mgmt.makePropertyKey('company_id').dataType(String.class).make()
company_name = mgmt.makePropertyKey('company_name').dataType(String.class).make()
registration_number = mgmt.makePropertyKey('registration_number').dataType(String.class).make()
company_type = mgmt.makePropertyKey('company_type').dataType(String.class).make()

risk_score = mgmt.makePropertyKey('risk_score').dataType(Double.class).make()
flagged = mgmt.makePropertyKey('flagged').dataType(Boolean.class).make()
flag_reason = mgmt.makePropertyKey('flag_reason').dataType(String.class).make()
suspicious_pattern = mgmt.makePropertyKey('suspicious_pattern').dataType(String.class).make()

// Indices
mgmt.buildIndex('personById', Vertex.class).addKey(person_id).indexOnly(person).unique().buildCompositeIndex()
mgmt.buildIndex('accountById', Vertex.class).addKey(account_id).indexOnly(account).unique().buildCompositeIndex()
mgmt.buildIndex('transactionById', Vertex.class).addKey(transaction_id).indexOnly(transaction).unique().buildCompositeIndex()
mgmt.buildIndex('transactionByTimestamp', Vertex.class).addKey(timestamp).indexOnly(transaction).buildCompositeIndex()
mgmt.buildIndex('transactionByAmount', Vertex.class).addKey(amount).indexOnly(transaction).buildCompositeIndex()
mgmt.buildIndex('addressById', Vertex.class).addKey(address_id).indexOnly(address).unique().buildCompositeIndex()
mgmt.buildIndex('phoneByNumber', Vertex.class).addKey(phone_number).indexOnly(phone).unique().buildCompositeIndex()
mgmt.buildIndex('companyById', Vertex.class).addKey(company_id).indexOnly(company).unique().buildCompositeIndex()
mgmt.buildIndex('flaggedEntities', Vertex.class).addKey(flagged).buildCompositeIndex()

mgmt.commit()

println("✅ AML Banking Schema loaded successfully")
