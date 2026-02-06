#!/usr/bin/env python3
"""
Initialize JanusGraph with schema and sample data.

Run this from the host machine after services are started.

File: initialize_graph.py
Created: 2026-01-28
Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
"""

import logging
import sys
import time

from ..client import ConnectionError, JanusGraphClient, QueryError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


schema_script = """
mgmt = graph.openManagement()

// Vertex labels
person = mgmt.makeVertexLabel('person').make()
company = mgmt.makeVertexLabel('company').make()
product = mgmt.makeVertexLabel('product').make()

// Edge labels
mgmt.makeEdgeLabel('knows').multiplicity(MULTI).make()
mgmt.makeEdgeLabel('worksFor').multiplicity(MANY2ONE).make()
mgmt.makeEdgeLabel('created').multiplicity(ONE2MANY).make()
mgmt.makeEdgeLabel('uses').multiplicity(MULTI).make()

// Properties
name = mgmt.makePropertyKey('name').dataType(String.class).make()
age = mgmt.makePropertyKey('age').dataType(Integer.class).make()
email = mgmt.makePropertyKey('email').dataType(String.class).make()
location = mgmt.makePropertyKey('location').dataType(String.class).make()
since = mgmt.makePropertyKey('since').dataType(Integer.class).make()
role = mgmt.makePropertyKey('role').dataType(String.class).make()
founded = mgmt.makePropertyKey('founded').dataType(Integer.class).make()
price = mgmt.makePropertyKey('price').dataType(Float.class).make()
category = mgmt.makePropertyKey('category').dataType(String.class).make()

// Indexes
mgmt.buildIndex('personByName', Vertex.class).addKey(name).indexOnly(person).buildCompositeIndex()
mgmt.buildIndex('personByEmail', Vertex.class).addKey(email).unique().indexOnly(person).buildCompositeIndex()
mgmt.buildIndex('companyByName', Vertex.class).addKey(name).indexOnly(company).buildCompositeIndex()
mgmt.buildIndex('productByName', Vertex.class).addKey(name).indexOnly(product).buildCompositeIndex()

mgmt.commit()
'Schema created'
"""

data_script = """
// Create sample people
alice = graph.addVertex(label, 'person', 'name', 'Alice Johnson', 'age', 32, 'email', 'alice@example.com', 'location', 'New York')
bob = graph.addVertex(label, 'person', 'name', 'Bob Smith', 'age', 28, 'email', 'bob@example.com', 'location', 'San Francisco')
carol = graph.addVertex(label, 'person', 'name', 'Carol Williams', 'age', 35, 'email', 'carol@example.com', 'location', 'Boston')

// Create sample companies
techCorp = graph.addVertex(label, 'company', 'name', 'TechCorp Inc', 'founded', 2010, 'location', 'San Francisco')
dataLabs = graph.addVertex(label, 'company', 'name', 'DataLabs', 'founded', 2015, 'location', 'New York')

// Create sample products
product1 = graph.addVertex(label, 'product', 'name', 'GraphDB Pro', 'price', 999.99f, 'category', 'Database')
product2 = graph.addVertex(label, 'product', 'name', 'Analytics Suite', 'price', 1499.99f, 'category', 'Analytics')

// Create relationships
alice.addEdge('worksFor', techCorp, 'role', 'Engineer', 'since', 2018)
bob.addEdge('worksFor', techCorp, 'role', 'Manager', 'since', 2016)
carol.addEdge('worksFor', dataLabs, 'role', 'Data Scientist', 'since', 2019)

alice.addEdge('knows', bob, 'since', 2018)
bob.addEdge('knows', carol, 'since', 2020)

alice.addEdge('created', product1, 'since', 2020)
carol.addEdge('uses', product2, 'since', 2021)

graph.tx().commit()
'Sample data loaded'
"""


def initialize_schema(client: JanusGraphClient) -> bool:
    """
    Initialize JanusGraph schema with vertex labels, edge labels, properties, and indexes.

    Args:
        client: Connected JanusGraphClient instance

    Returns:
        True if schema initialized successfully, False otherwise
    """
    logger.info("Initializing schema...")

    try:
        result = client.execute(schema_script)
        logger.info("Schema initialized successfully: %s", result)
        return True
    except QueryError as e:
        logger.warning("Schema initialization failed (may already exist): %s", e)
        return True  # Not fatal if schema exists
    except Exception as e:
        logger.error("Unexpected error initializing schema: %s", e)
        return False


def load_sample_data(client: JanusGraphClient) -> bool:
    """
    Load sample graph data (people, companies, products, and relationships).

    Args:
        client: Connected JanusGraphClient instance

    Returns:
        True if data loaded successfully, False otherwise
    """
    logger.info("Loading sample data...")

    try:
        result = client.execute(data_script)
        logger.info("Sample data loaded successfully: %s", result)
        return True
    except QueryError as e:
        logger.error("Failed to load sample data: %s", e)
        return False
    except Exception as e:
        logger.error("Unexpected error loading data: %s", e)
        return False


def verify_initialization(client: JanusGraphClient) -> bool:
    """
    Verify that schema and data were loaded correctly.

    Args:
        client: Connected JanusGraphClient instance

    Returns:
        True if verification passed, False otherwise
    """
    logger.info("Verifying initialization...")

    try:
        vertex_count = client.execute("g.V().count()")[0]
        edge_count = client.execute("g.E().count()")[0]

        logger.info("=" * 50)
        logger.info("Initialization Complete!")
        logger.info("=" * 50)
        logger.info("Vertices: %d", vertex_count)
        logger.info("Edges: %d", edge_count)

        # Get sample data
        people = client.execute("g.V().hasLabel('person').values('name')")
        companies = client.execute("g.V().hasLabel('company').values('name')")
        products = client.execute("g.V().hasLabel('product').values('name')")

        logger.info("Sample data loaded:")
        logger.info("  People: %s", people)
        logger.info("  Companies: %s", companies)
        logger.info("  Products: %s", products)

        logger.info("=" * 50)
        logger.info("Expected: 11 vertices, 19 edges")
        logger.info("You can now use Jupyter notebooks to explore the graph!")
        logger.info("=" * 50)

        return vertex_count == 11 and edge_count == 19
    except (QueryError, IndexError) as e:
        logger.error("Verification failed: %s", e)
        return False
    except Exception as e:
        logger.error("Unexpected error during verification: %s", e)
        return False


def main() -> int:
    """
    Main entry point for graph initialization.

    Returns:
        0 on success, 1 on failure
    """
    logger.info("Starting JanusGraph initialization")

    try:
        # Create and connect client
        with JanusGraphClient(host="localhost", port=18182) as client:
            # Step 1: Initialize schema
            if not initialize_schema(client):
                logger.error("Schema initialization failed")
                return 1

            time.sleep(2)  # Wait for schema to propagate

            # Step 2: Load sample data
            if not load_sample_data(client):
                logger.error("Data loading failed")
                return 1

            time.sleep(2)  # Wait for data to propagate

            # Step 3: Verify
            if not verify_initialization(client):
                logger.warning("Verification failed - data may not match expected counts")
                return 1

            logger.info("JanusGraph initialization completed successfully")
            return 0

    except ConnectionError as e:
        logger.error("Failed to connect to JanusGraph: %s", e)
        logger.error("Ensure JanusGraph is running at localhost:18182")
        return 1
    except KeyboardInterrupt:
        logger.info("Initialization interrupted by user")
        return 1
    except Exception as e:
        logger.error("Unexpected error during initialization: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
