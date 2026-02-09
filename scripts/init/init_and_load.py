import time

from gremlin_python.driver import client

gc = client.Client("ws://localhost:18182/gremlin", "g")

print("Step 2: Initializing schema...")

try:
    # Initialize schema
    schema_script = """
mgmt = graph.openManagement()

person = mgmt.makeVertexLabel('person').make()
company = mgmt.makeVertexLabel('company').make()
product = mgmt.makeVertexLabel('product').make()

mgmt.makeEdgeLabel('knows').multiplicity(MULTI).make()
mgmt.makeEdgeLabel('worksFor').multiplicity(MANY2ONE).make()
mgmt.makeEdgeLabel('created').multiplicity(ONE2MANY).make()
mgmt.makeEdgeLabel('uses').multiplicity(MULTI).make()

name = mgmt.makePropertyKey('name').dataType(String.class).make()
age = mgmt.makePropertyKey('age').dataType(Integer.class).make()
email = mgmt.makePropertyKey('email').dataType(String.class).make()
location = mgmt.makePropertyKey('location').dataType(String.class).make()
since = mgmt.makePropertyKey('since').dataType(Integer.class).make()
role = mgmt.makePropertyKey('role').dataType(String.class).make()
founded = mgmt.makePropertyKey('founded').dataType(Integer.class).make()
price = mgmt.makePropertyKey('price').dataType(Float.class).make()
category = mgmt.makePropertyKey('category').dataType(String.class).make()

mgmt.buildIndex('personByName', Vertex.class).addKey(name).indexOnly(person).buildCompositeIndex()
mgmt.buildIndex('personByEmail', Vertex.class).addKey(email).unique().indexOnly(person).buildCompositeIndex()
mgmt.buildIndex('companyByName', Vertex.class).addKey(name).indexOnly(company).buildCompositeIndex()
mgmt.buildIndex('productByName', Vertex.class).addKey(name).indexOnly(product).buildCompositeIndex()

mgmt.commit()
'Schema created'
"""

    result = gc.submit(schema_script).all().result()
    print(f"   ✅ Schema initialized: {result}")
    time.sleep(2)

    print("\nStep 3: Loading sample data...")

    # Create all vertices first
    data_script = """
alice = g.addV('person').property('name', 'Alice Johnson').property('age', 30).property('email', 'alice@example.com').property('location', 'San Francisco').next()
bob = g.addV('person').property('name', 'Bob Smith').property('age', 25).property('email', 'bob@example.com').property('location', 'New York').next()
carol = g.addV('person').property('name', 'Carol Williams').property('age', 35).property('email', 'carol@example.com').property('location', 'Seattle').next()
david = g.addV('person').property('name', 'David Brown').property('age', 28).property('email', 'david@example.com').property('location', 'San Francisco').next()
eve = g.addV('person').property('name', 'Eve Davis').property('age', 32).property('email', 'eve@example.com').property('location', 'Austin').next()

datastax = g.addV('company').property('name', 'DataStax').property('location', 'Santa Clara').property('founded', 2010).next()
acme = g.addV('company').property('name', 'Acme Corp').property('location', 'New York').property('founded', 2015).next()
techstart = g.addV('company').property('name', 'TechStart').property('location', 'Austin').property('founded', 2018).next()

janusgraph = g.addV('product').property('name', 'JanusGraph').property('category', 'Database').property('price', 0.0f).next()
cloudService = g.addV('product').property('name', 'Cloud Service Platform').property('category', 'SaaS').property('price', 99.99f).next()
analyticsEngine = g.addV('product').property('name', 'Analytics Engine').property('category', 'Analytics').property('price', 199.99f).next()

g.V(alice).addE('knows').to(g.V(bob)).property('since', 2018).next()
g.V(alice).addE('knows').to(g.V(carol)).property('since', 2019).next()
g.V(alice).addE('knows').to(g.V(david)).property('since', 2020).next()
g.V(bob).addE('knows').to(g.V(david)).property('since', 2019).next()
g.V(carol).addE('knows').to(g.V(eve)).property('since', 2017).next()
g.V(david).addE('knows').to(g.V(eve)).property('since', 2021).next()

g.V(alice).addE('worksFor').to(g.V(datastax)).property('role', 'Senior Engineer').property('since', 2018).next()
g.V(bob).addE('worksFor').to(g.V(acme)).property('role', 'Product Manager').property('since', 2020).next()
g.V(carol).addE('worksFor').to(g.V(datastax)).property('role', 'Director').property('since', 2016).next()
g.V(david).addE('worksFor').to(g.V(datastax)).property('role', 'Engineer').property('since', 2021).next()
g.V(eve).addE('worksFor').to(g.V(techstart)).property('role', 'CTO').property('since', 2018).next()

g.V(datastax).addE('created').to(g.V(janusgraph)).property('since', 2017).next()
g.V(acme).addE('created').to(g.V(cloudService)).property('since', 2019).next()
g.V(techstart).addE('created').to(g.V(analyticsEngine)).property('since', 2020).next()

g.V(alice).addE('uses').to(g.V(janusgraph)).property('since', 2019).next()
g.V(bob).addE('uses').to(g.V(cloudService)).property('since', 2020).next()
g.V(carol).addE('uses').to(g.V(janusgraph)).property('since', 2018).next()
g.V(david).addE('uses').to(g.V(janusgraph)).property('since', 2021).next()
g.V(eve).addE('uses').to(g.V(analyticsEngine)).property('since', 2020).next()

graph.tx().commit()
'Data loaded'
"""

    result = gc.submit(data_script).all().result()
    print(f"   ✅ Data loaded: {result}")
    time.sleep(2)

    print("\nStep 4: Verifying...")

    vertex_count = gc.submit("g.V().count()").all().result()[0]
    edge_count = gc.submit("g.E().count()").all().result()[0]

    print(f"\n{'='*50}")
    print(f"✅ Initialization Complete!")
    print(f"{'='*50}")
    print(f"Vertices: {vertex_count}")
    print(f"Edges: {edge_count}")
    print(f"\nSample data:")

    people = gc.submit("g.V().hasLabel('person').values('name')").all().result()
    print(f"  People: {people}")

    companies = gc.submit("g.V().hasLabel('company').values('name')").all().result()
    print(f"  Companies: {companies}")

    products = gc.submit("g.V().hasLabel('product').values('name')").all().result()
    print(f"  Products: {products}")

    print(f"\n{'='*50}")
    print("Expected: 11 vertices and 19 edges")
    print(f"{'='*50}\n")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
finally:
    gc.close()
