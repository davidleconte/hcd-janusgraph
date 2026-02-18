# File: load_data.py
# Created: 2026-01-28T08:34:23.3N
# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)

import time

from gremlin_python.driver import client

gc = client.Client("ws://localhost:18182/gremlin", "g")

print("Loading sample data...")

try:
    # Clear any existing data
    gc.submit("g.V().drop()").all().result()
    time.sleep(1)

    # Load people
    print("Creating people...")
    gc.submit("""
        g.addV('person').property('name', 'Alice Johnson').property('age', 30).property('email', 'alice@example.com').property('location', 'San Francisco').as('alice')
         .addV('person').property('name', 'Bob Smith').property('age', 25).property('email', 'bob@example.com').property('location', 'New York').as('bob')
         .addV('person').property('name', 'Carol Williams').property('age', 35).property('email', 'carol@example.com').property('location', 'Seattle').as('carol')
         .addV('person').property('name', 'David Brown').property('age', 28).property('email', 'david@example.com').property('location', 'San Francisco').as('david')
         .addV('person').property('name', 'Eve Davis').property('age', 32).property('email', 'eve@example.com').property('location', 'Austin').as('eve')
         .iterate()
    """).all().result()
    time.sleep(1)

    # Load companies
    print("Creating companies...")
    gc.submit("""
        g.addV('company').property('name', 'DataStax').property('location', 'Santa Clara').property('founded', 2010).as('datastax')
         .addV('company').property('name', 'Acme Corp').property('location', 'New York').property('founded', 2015).as('acme')
         .addV('company').property('name', 'TechStart').property('location', 'Austin').property('founded', 2018).as('techstart')
         .iterate()
    """).all().result()
    time.sleep(1)

    # Load products
    print("Creating products...")
    gc.submit("""
        g.addV('product').property('name', 'JanusGraph').property('category', 'Database').property('price', 0.0)
         .addV('product').property('name', 'Cloud Service Platform').property('category', 'SaaS').property('price', 99.99)
         .addV('product').property('name', 'Analytics Engine').property('category', 'Analytics').property('price', 199.99)
         .iterate()
    """).all().result()
    time.sleep(1)

    # Load relationships
    print("Creating relationships...")
    gc.submit("""
        alice = g.V().has('person','name','Alice Johnson').next()
        bob = g.V().has('person','name','Bob Smith').next()
        carol = g.V().has('person','name','Carol Williams').next()
        david = g.V().has('person','name','David Brown').next()
        eve = g.V().has('person','name','Eve Davis').next()

        g.V(alice).addE('knows').to(bob).property('since', 2018)
         .V(alice).addE('knows').to(carol).property('since', 2019)
         .V(alice).addE('knows').to(david).property('since', 2020)
         .V(bob).addE('knows').to(david).property('since', 2019)
         .V(carol).addE('knows').to(eve).property('since', 2017)
         .V(david).addE('knows').to(eve).property('since', 2021)
         .iterate()
    """).all().result()
    time.sleep(1)

    gc.submit("""
        alice = g.V().has('person','name','Alice Johnson').next()
        bob = g.V().has('person','name','Bob Smith').next()
        carol = g.V().has('person','name','Carol Williams').next()
        david = g.V().has('person','name','David Brown').next()
        eve = g.V().has('person','name','Eve Davis').next()
        datastax = g.V().has('company','name','DataStax').next()
        acme = g.V().has('company','name','Acme Corp').next()
        techstart = g.V().has('company','name','TechStart').next()

        g.V(alice).addE('worksFor').to(datastax).property('role', 'Senior Engineer').property('since', 2018)
         .V(bob).addE('worksFor').to(acme).property('role', 'Product Manager').property('since', 2020)
         .V(carol).addE('worksFor').to(datastax).property('role', 'Director').property('since', 2016)
         .V(david).addE('worksFor').to(datastax).property('role', 'Engineer').property('since', 2021)
         .V(eve).addE('worksFor').to(techstart).property('role', 'CTO').property('since', 2018)
         .iterate()
    """).all().result()
    time.sleep(1)

    gc.submit("""
        datastax = g.V().has('company','name','DataStax').next()
        acme = g.V().has('company','name','Acme Corp').next()
        techstart = g.V().has('company','name','TechStart').next()
        janusgraph = g.V().has('product','name','JanusGraph').next()
        cloudService = g.V().has('product','name','Cloud Service Platform').next()
        analyticsEngine = g.V().has('product','name','Analytics Engine').next()

        g.V(datastax).addE('created').to(janusgraph).property('since', 2017)
         .V(acme).addE('created').to(cloudService).property('since', 2019)
         .V(techstart).addE('created').to(analyticsEngine).property('since', 2020)
         .iterate()
    """).all().result()
    time.sleep(1)

    gc.submit("""
        alice = g.V().has('person','name','Alice Johnson').next()
        bob = g.V().has('person','name','Bob Smith').next()
        carol = g.V().has('person','name','Carol Williams').next()
        david = g.V().has('person','name','David Brown').next()
        eve = g.V().has('person','name','Eve Davis').next()
        janusgraph = g.V().has('product','name','JanusGraph').next()
        cloudService = g.V().has('product','name','Cloud Service Platform').next()
        analyticsEngine = g.V().has('product','name','Analytics Engine').next()

        g.V(alice).addE('uses').to(janusgraph).property('since', 2019)
         .V(bob).addE('uses').to(cloudService).property('since', 2020)
         .V(carol).addE('uses').to(janusgraph).property('since', 2018)
         .V(david).addE('uses').to(janusgraph).property('since', 2021)
         .V(eve).addE('uses').to(analyticsEngine).property('since', 2020)
         .iterate()
    """).all().result()

    print("\n✅ Data loading complete!")

    # Verify
    v_count = gc.submit("g.V().count()").all().result()[0]
    e_count = gc.submit("g.E().count()").all().result()[0]
    print("\nVerification:")
    print(f"  Vertices: {v_count}")
    print(f"  Edges: {e_count}")

    people = gc.submit("g.V().hasLabel('person').values('name')").all().result()
    print(f"  People: {people}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
finally:
    gc.close()
