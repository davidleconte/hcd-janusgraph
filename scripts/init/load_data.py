import time

from gremlin_python.driver import client

gc = client.Client("ws://localhost:18182/gremlin", "g")

print("Step 3: Loading sample data...")

try:
    # Step 1: Create vertices
    print("Creating vertices...")
    vertices = (
        gc.submit(
            """
g.addV('person').property('name', 'Alice Johnson').property('age', 30).property('email', 'alice@example.com').property('location', 'San Francisco').next()
g.addV('person').property('name', 'Bob Smith').property('age', 25).property('email', 'bob@example.com').property('location', 'New York').next()
g.addV('person').property('name', 'Carol Williams').property('age', 35).property('email', 'carol@example.com').property('location', 'Seattle').next()
g.addV('person').property('name', 'David Brown').property('age', 28).property('email', 'david@example.com').property('location', 'San Francisco').next()
g.addV('person').property('name', 'Eve Davis').property('age', 32).property('email', 'eve@example.com').property('location', 'Austin').next()
g.addV('company').property('name', 'DataStax').property('location', 'Santa Clara').property('founded', 2010).next()
g.addV('company').property('name', 'Acme Corp').property('location', 'New York').property('founded', 2015).next()
g.addV('company').property('name', 'TechStart').property('location', 'Austin').property('founded', 2018).next()
g.addV('product').property('name', 'JanusGraph').property('category', 'Database').property('price', 0.0f).next()
g.addV('product').property('name', 'Cloud Service Platform').property('category', 'SaaS').property('price', 99.99f).next()
g.addV('product').property('name', 'Analytics Engine').property('category', 'Analytics').property('price', 199.99f).next()
g.tx().commit()
"""
        )
        .all()
        .result()
    )
    time.sleep(1)

    # Step 2: Create edges
    print("Creating edges...")

    # knows edges
    gc.submit(
        """
g.V().has('person','name','Alice Johnson').as('alice')
 .V().has('person','name','Bob Smith').addE('knows').from('alice').property('since', 2018)
 .V().has('person','name','Carol Williams').addE('knows').from('alice').property('since', 2019)
 .V().has('person','name','David Brown').addE('knows').from('alice').property('since', 2020).iterate()
g.V().has('person','name','Bob Smith').as('bob')
 .V().has('person','name','David Brown').addE('knows').from('bob').property('since', 2019).iterate()
g.V().has('person','name','Carol Williams').as('carol')
 .V().has('person','name','Eve Davis').addE('knows').from('carol').property('since', 2017).iterate()
g.V().has('person','name','David Brown').as('david')
 .V().has('person','name','Eve Davis').addE('knows').from('david').property('since', 2021).iterate()
g.tx().commit()
"""
    ).all().result()
    time.sleep(1)

    # worksFor edges
    gc.submit(
        """
g.V().has('person','name','Alice Johnson').as('p')
 .V().has('company','name','DataStax').addE('worksFor').from('p').property('role','Senior Engineer').property('since',2018).iterate()
g.V().has('person','name','Bob Smith').as('p')
 .V().has('company','name','Acme Corp').addE('worksFor').from('p').property('role','Product Manager').property('since',2020).iterate()
g.V().has('person','name','Carol Williams').as('p')
 .V().has('company','name','DataStax').addE('worksFor').from('p').property('role','Director').property('since',2016).iterate()
g.V().has('person','name','David Brown').as('p')
 .V().has('company','name','DataStax').addE('worksFor').from('p').property('role','Engineer').property('since',2021).iterate()
g.V().has('person','name','Eve Davis').as('p')
 .V().has('company','name','TechStart').addE('worksFor').from('p').property('role','CTO').property('since',2018).iterate()
g.tx().commit()
"""
    ).all().result()
    time.sleep(1)

    # created edges
    gc.submit(
        """
g.V().has('company','name','DataStax').as('c')
 .V().has('product','name','JanusGraph').addE('created').from('c').property('since',2017).iterate()
g.V().has('company','name','Acme Corp').as('c')
 .V().has('product','name','Cloud Service Platform').addE('created').from('c').property('since',2019).iterate()
g.V().has('company','name','TechStart').as('c')
 .V().has('product','name','Analytics Engine').addE('created').from('c').property('since',2020).iterate()
g.tx().commit()
"""
    ).all().result()
    time.sleep(1)

    # uses edges
    gc.submit(
        """
g.V().has('person','name','Alice Johnson').as('p')
 .V().has('product','name','JanusGraph').addE('uses').from('p').property('since',2019).iterate()
g.V().has('person','name','Bob Smith').as('p')
 .V().has('product','name','Cloud Service Platform').addE('uses').from('p').property('since',2020).iterate()
g.V().has('person','name','Carol Williams').as('p')
 .V().has('product','name','JanusGraph').addE('uses').from('p').property('since',2018).iterate()
g.V().has('person','name','David Brown').as('p')
 .V().has('product','name','JanusGraph').addE('uses').from('p').property('since',2021).iterate()
g.V().has('person','name','Eve Davis').as('p')
 .V().has('product','name','Analytics Engine').addE('uses').from('p').property('since',2020).iterate()
g.tx().commit()
"""
    ).all().result()

    print("\n✅ Data loading complete!")

    # Step 4: Verify
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
    if vertex_count == 11 and edge_count == 19:
        print("✅ SUCCESS: All data loaded correctly!")
    else:
        print("⚠️  WARNING: Count mismatch!")
    print(f"{'='*50}\n")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
finally:
    gc.close()
