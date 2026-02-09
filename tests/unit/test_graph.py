from gremlin_python.driver import client

gc = client.Client("ws://localhost:18182/gremlin", "g")

try:
    # Check current state
    v_count = gc.submit("g.V().count()").all().result()[0]
    e_count = gc.submit("g.E().count()").all().result()[0]
    print(f"Current: {v_count} vertices, {e_count} edges")

    # Try to get vertex labels
    labels = gc.submit("g.V().label().dedup()").all().result()
    print(f"Vertex labels: {labels}")

    # Check schema
    mgmt_result = (
        gc.submit(
            "mgmt = graph.openManagement(); labels = mgmt.getVertexLabels(); labelNames = []; labels.each { labelNames.add(it.name()) }; mgmt.rollback(); labelNames"
        )
        .all()
        .result()
    )
    print(f"Schema vertex labels: {mgmt_result}")

except Exception as e:
    print(f"Error: {e}")
finally:
    gc.close()
