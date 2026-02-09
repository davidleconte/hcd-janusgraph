#!/usr/bin/env python3
"""Quick test to verify JanusGraph connection works"""

import nest_asyncio

nest_asyncio.apply()

from gremlin_python.driver import client

print("Testing JanusGraph connection...")

try:
    # Using host network since we're outside container
    gc = client.Client("ws://localhost:18182/gremlin", "g")

    v_count = gc.submit("g.V().count()").all().result()[0]
    e_count = gc.submit("g.E().count()").all().result()[0]

    print(f"✅ Connection successful!")
    print(f"   Vertices: {v_count}")
    print(f"   Edges: {e_count}")

    gc.close()

except Exception as e:
    print(f"❌ Connection failed: {e}")
    import traceback

    traceback.print_exc()
