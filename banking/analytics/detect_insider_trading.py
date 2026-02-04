import logging
import sys
from gremlin_python.driver import client, serializer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def detect_insider_trading():
    logger.info("Connecting to JanusGraph...")
    jg_client = client.Client('ws://localhost:18182/gremlin', 'g', 
                            message_serializer=serializer.GraphSONSerializersV3d0())

    try:
        logger.info("🔍 Scaning for Insider Trading Patterns...")
        
        # Query: Find top trades by amount and the person who performed them
        # Logic: High value trades often indicate insider knowledge or significant risk
        query = """
        g.V().hasLabel('trade')
         .order().by('amount', desc)
         .limit(20)
         .project('trade_id', 'symbol', 'amount', 'side', 'trader')
         .by('trade_id')
         .by('symbol')
         .by('amount')
         .by('side')
         .by(__.in('performed_trade').values('first_name', 'last_name').fold())
        """
        
        results = jg_client.submit(query).all().result()
        
        print(f"\n{'='*80}")
        print(f"INSIDER TRADING DETECTION REPORT")
        print(f"{'='*80}")
        print(f"Found {len(results)} high-value suspicious trades:")
        print(f"{'Trade ID':<20} | {'Symbol':<10} | {'Side':<5} | {'Amount':<15} | {'Trader'}")
        print("-" * 80)
        
        for r in results:
            trader = " ".join(r['trader']) if r['trader'] else "Unknown"
            print(f"{r['trade_id']:<20} | {r['symbol']:<10} | {r['side']:<5} | ${r['amount']:<14,.2f} | {trader}")
            
        print(f"{'='*80}\n")
        
        # Verify Trade Vertices count
        count = jg_client.submit("g.V().hasLabel('trade').count()").all().result()[0]
        logger.info(f"Total Trade Vertices in Graph: {count}")

    except Exception as e:
        logger.error(f"Detection failed: {e}")
        sys.exit(1)
    finally:
        jg_client.close()

if __name__ == "__main__":
    detect_insider_trading()
