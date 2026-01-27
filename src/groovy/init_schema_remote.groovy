// JanusGraph Schema Initialization via Remote Server
// Access graph through remote server connection

println "Creating schema via remote server..."

// Get graph management
mgmt = graph.openManagement()

// Vertex Labels
person = mgmt.makeVertexLabel('person').make()
company = mgmt.makeVertexLabel('company').make()
product = mgmt.makeVertexLabel('product').make()

println "Created vertex labels: person, company, product"

// Edge Labels
knows = mgmt.makeEdgeLabel('knows').multiplicity(MULTI).make()
worksFor = mgmt.makeEdgeLabel('worksFor').multiplicity(MANY2ONE).make()
created = mgmt.makeEdgeLabel('created').multiplicity(ONE2MANY).make()
uses = mgmt.makeEdgeLabel('uses').multiplicity(MULTI).make()

println "Created edge labels: knows, worksFor, created, uses"

// Property Keys
name = mgmt.makePropertyKey('name').dataType(String.class).make()
age = mgmt.makePropertyKey('age').dataType(Integer.class).make()
email = mgmt.makePropertyKey('email').dataType(String.class).make()
location = mgmt.makePropertyKey('location').dataType(String.class).make()
since = mgmt.makePropertyKey('since').dataType(Integer.class).make()
role = mgmt.makePropertyKey('role').dataType(String.class).make()
founded = mgmt.makePropertyKey('founded').dataType(Integer.class).make()
price = mgmt.makePropertyKey('price').dataType(Float.class).make()
category = mgmt.makePropertyKey('category').dataType(String.class).make()

println "Created property keys"

// Composite Indexes (for exact matches)
mgmt.buildIndex('personByName', Vertex.class).addKey(name).indexOnly(person).buildCompositeIndex()
mgmt.buildIndex('personByEmail', Vertex.class).addKey(email).unique().indexOnly(person).buildCompositeIndex()
mgmt.buildIndex('companyByName', Vertex.class).addKey(name).indexOnly(company).buildCompositeIndex()
mgmt.buildIndex('productByName', Vertex.class).addKey(name).indexOnly(product).buildCompositeIndex()

println "Created composite indexes"

// Mixed Indexes (for full-text and range queries)
mgmt.buildIndex('personMixed', Vertex.class)
    .addKey(name, Mapping.TEXT.asParameter())
    .addKey(age)
    .addKey(location, Mapping.TEXT.asParameter())
    .indexOnly(person)
    .buildMixedIndex('search')

mgmt.buildIndex('productMixed', Vertex.class)
    .addKey(name, Mapping.TEXT.asParameter())
    .addKey(category, Mapping.TEXT.asParameter())
    .addKey(price)
    .indexOnly(product)
    .buildMixedIndex('search')

println "Created mixed indexes"

// Commit schema
mgmt.commit()

println "Schema committed successfully!"
println ""
println "Schema Summary:"
println "  Vertex Labels: person, company, product"
println "  Edge Labels: knows, worksFor, created, uses"
println "  Indexes: personByName, personByEmail, companyByName, productByName, personMixed, productMixed"
