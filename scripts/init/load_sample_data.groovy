// JanusGraph Sample Data Loading
// Loads sample data into the graph based on the schema

// Open graph connection
graph = JanusGraphFactory.open('/opt/janusgraph/conf/janusgraph-hcd.properties')
g = graph.traversal()

println "Loading sample data..."

// Create People
alice = g.addV('person')
    .property('name', 'Alice Johnson')
    .property('age', 30)
    .property('email', 'alice@example.com')
    .property('location', 'San Francisco')
    .next()

bob = g.addV('person')
    .property('name', 'Bob Smith')
    .property('age', 25)
    .property('email', 'bob@example.com')
    .property('location', 'New York')
    .next()

carol = g.addV('person')
    .property('name', 'Carol Williams')
    .property('age', 35)
    .property('email', 'carol@example.com')
    .property('location', 'Seattle')
    .next()

david = g.addV('person')
    .property('name', 'David Brown')
    .property('age', 28)
    .property('email', 'david@example.com')
    .property('location', 'San Francisco')
    .next()

eve = g.addV('person')
    .property('name', 'Eve Davis')
    .property('age', 32)
    .property('email', 'eve@example.com')
    .property('location', 'Austin')
    .next()

println "Created 5 people"

// Create Companies
datastax = g.addV('company')
    .property('name', 'DataStax')
    .property('location', 'Santa Clara')
    .property('founded', 2010)
    .next()

acme = g.addV('company')
    .property('name', 'Acme Corp')
    .property('location', 'New York')
    .property('founded', 2015)
    .next()

techstart = g.addV('company')
    .property('name', 'TechStart')
    .property('location', 'Austin')
    .property('founded', 2018)
    .next()

println "Created 3 companies"

// Create Products
janusgraph = g.addV('product')
    .property('name', 'JanusGraph')
    .property('category', 'Database')
    .property('price', 0.0f)
    .next()

cloudService = g.addV('product')
    .property('name', 'Cloud Service Platform')
    .property('category', 'SaaS')
    .property('price', 99.99f)
    .next()

analyticsEngine = g.addV('product')
    .property('name', 'Analytics Engine')
    .property('category', 'Analytics')
    .property('price', 199.99f)
    .next()

println "Created 3 products"

// Create Relationships

// Social connections (knows)
g.V(alice).addE('knows').to(g.V(bob)).property('since', 2018).next()
g.V(alice).addE('knows').to(g.V(carol)).property('since', 2019).next()
g.V(alice).addE('knows').to(g.V(david)).property('since', 2020).next()
g.V(bob).addE('knows').to(g.V(david)).property('since', 2019).next()
g.V(carol).addE('knows').to(g.V(eve)).property('since', 2017).next()
g.V(david).addE('knows').to(g.V(eve)).property('since', 2021).next()

println "Created 'knows' relationships"

// Employment (worksFor)
g.V(alice).addE('worksFor').to(g.V(datastax)).property('role', 'Senior Engineer').property('since', 2018).next()
g.V(bob).addE('worksFor').to(g.V(acme)).property('role', 'Product Manager').property('since', 2020).next()
g.V(carol).addE('worksFor').to(g.V(datastax)).property('role', 'Director').property('since', 2016).next()
g.V(david).addE('worksFor').to(g.V(datastax)).property('role', 'Engineer').property('since', 2021).next()
g.V(eve).addE('worksFor').to(g.V(techstart)).property('role', 'CTO').property('since', 2018).next()

println "Created 'worksFor' relationships"

// Product creation (created)
g.V(datastax).addE('created').to(g.V(janusgraph)).property('since', 2017).next()
g.V(acme).addE('created').to(g.V(cloudService)).property('since', 2019).next()
g.V(techstart).addE('created').to(g.V(analyticsEngine)).property('since', 2020).next()

println "Created 'created' relationships"

// Product usage (uses)
g.V(alice).addE('uses').to(g.V(janusgraph)).property('since', 2019).next()
g.V(bob).addE('uses').to(g.V(cloudService)).property('since', 2020).next()
g.V(carol).addE('uses').to(g.V(janusgraph)).property('since', 2018).next()
g.V(david).addE('uses').to(g.V(janusgraph)).property('since', 2021).next()
g.V(eve).addE('uses').to(g.V(analyticsEngine)).property('since', 2020).next()

println "Created 'uses' relationships"

// Commit transaction
graph.tx().commit()

println ""
println "Data loading complete!"
println ""
println "Summary:"
println "  Vertices:"
println "    - 5 persons"
println "    - 3 companies"
println "    - 3 products"
println "  Edges:"
println "    - 6 'knows' connections"
println "    - 5 'worksFor' connections"
println "    - 3 'created' connections"
println "    - 5 'uses' connections"
println ""
println "Sample queries to try:"
println "  g.V().hasLabel('person').values('name')"
println "  g.V().has('person', 'name', 'Alice Johnson').out('knows').values('name')"
println "  g.V().has('company', 'name', 'DataStax').in('worksFor').values('name')"
println "  g.V().hasLabel('person').has('location', 'San Francisco').values('name')"

// Close graph
graph.close()

println ""
println "Graph closed."
