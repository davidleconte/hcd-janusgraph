#!/usr/bin/env python3
# File: scripts/backup/export_graph.py
# Created: 2026-01-28T10:32:15.789
# Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
"""
Export JanusGraph to GraphML format for backup
"""

import argparse
from gremlin_python.driver import client
import sys

def export_graph(output_file: str, gremlin_url: str = 'ws://localhost:18182/gremlin'):
    """Export graph to GraphML"""
    print(f"📤 Exporting graph to {output_file}")
    
    gc = client.Client(gremlin_url, 'g')
    
    try:
        # Export to GraphML
        query = f"""
        graph.io(graphml()).writeGraph('{output_file}')
        """
        result = gc.submit(query).all().result()
        print(f"✅ Graph exported successfully")
        return True
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return False
    finally:
        gc.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Export JanusGraph to GraphML')
    parser.add_argument('--output', required=True, help='Output GraphML file')
    parser.add_argument('--url', default='ws://localhost:18182/gremlin', help='Gremlin server URL')
    
    args = parser.parse_args()
    
    success = export_graph(args.output, args.url)
    sys.exit(0 if success else 1)

# Signature: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
