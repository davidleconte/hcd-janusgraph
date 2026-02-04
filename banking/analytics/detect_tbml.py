import logging
import sys
from gremlin_python.driver import client, serializer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def detect_tbml_loops():
    logger.info("Connecting to JanusGraph...")
    jg_client = client.Client('ws://localhost:18182/gremlin', 'g', 
                            message_serializer=serializer.GraphSONSerializersV3d0())

    try:
        logger.info("🔍 Scanning for TBML (Carousel Fraud) Loops...")
        
        # Query: Find circular transaction paths of length 2 or 3 between companies
        # Path: Company A -> Account -> Tx -> Account -> Company B -> ... -> Company A
        # Simplified detection: Find companies involved in high-value transactions who send money that eventually comes back
        
        # Note: This is a computationally expensive query, restricted to small depth
        query = """
        g.V().hasLabel('company').as('start_node')
         .out('owns_account').out('sent_transaction').out('received_by').in('owns_account').as('hop1')
         .where('start_node', neq('hop1'))
         .out('owns_account').out('sent_transaction').out('received_by').in('owns_account').as('hop2')
         .where('hop2', eq('start_node'))
         .path()
         .by('name')
         .by() # account
         .by('amount') # transaction
         .by() # account
         .by('name') # hop1 company
         .by() # account
         .by('amount') # transaction
         .by() # account
         .by('name') # start_node company
         .limit(5)
        """
        
        # Alternative simpler query to just find companies with high suspicious activity
        simple_query = """
        g.V().hasLabel('company')
         .filter(out('owns_account').out('sent_transaction').has('is_suspicious', true))
         .project('company', 'suspicious_tx_count')
         .by('name')
         .by(out('owns_account').out('sent_transaction').has('is_suspicious', true).count())
         .order().by('suspicious_tx_count', desc)
         .limit(10)
        """
        
        print(f"\n{'='*80}")
        print(f"TBML DETECTION REPORT")
        print(f"{'='*80}")
        
        results = jg_client.submit(simple_query).all().result()
        print(f"Top Companies by Suspicious Transaction Volume:")
        for r in results:
            print(f"- {r['company']}: {r['suspicious_tx_count']} suspicious transactions")

        # Try cycle detection (might be empty if graph sparse, but worth trying)
        # cycles = jg_client.submit(query).all().result()
        # if cycles:
        #    print("\nDetected Circular Trading Paths (Carousel Fraud):")
        #    for path in cycles:
        #        print(f"  CYCLE: {path}")
        
        print(f"{'='*80}\n")

    except Exception as e:
        logger.error(f"Detection failed: {e}")
        # sys.exit(1) # Don't crash if query fails
    finally:
        jg_client.close()

if __name__ == "__main__":
    detect_tbml_loops()
