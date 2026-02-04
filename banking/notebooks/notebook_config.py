"""
Notebook Configuration Module
==============================
Centralized configuration for all banking notebooks.
Provides consistent connection settings and path management.

Author: IBM Bob
Date: 2026-02-04
"""

import os
import sys
from pathlib import Path


def setup_project_paths():
    """Add project root to Python path for imports."""
    # Find project root by looking for pyproject.toml
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists():
            project_root = parent
            break
    else:
        # Fallback: assume notebooks are in banking/notebooks/
        project_root = Path(__file__).parent.parent.parent
    
    # Add to path if not already present
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    
    return project_root


def verify_conda_environment():
    """Verify the correct conda environment is active."""
    expected_env = "janusgraph-analysis"
    current_env = os.environ.get('CONDA_DEFAULT_ENV', '')
    
    if expected_env not in current_env:
        print(f"⚠️  Warning: Expected conda env '{expected_env}', got '{current_env}'")
        print(f"   Run: conda activate {expected_env}")
        return False
    return True


# Connection Configuration
# Override with environment variables for different environments
JANUSGRAPH_CONFIG = {
    'url': os.getenv('GREMLIN_URL', 'ws://localhost:18182/gremlin'),
    'traversal_source': 'g',
}

OPENSEARCH_CONFIG = {
    'host': os.getenv('OPENSEARCH_HOST', 'localhost'),
    'port': int(os.getenv('OPENSEARCH_PORT', 9200)),
    'use_ssl': os.getenv('OPENSEARCH_USE_SSL', 'false').lower() == 'true',
    'verify_certs': False,
}

HCD_CONFIG = {
    'host': os.getenv('HCD_HOST', 'localhost'),
    'port': int(os.getenv('HCD_PORT', 9042)),
}

# Data paths (relative to project root)
DATA_PATHS = {
    'aml_transactions': 'banking/data/aml/aml_data_transactions.csv',
    'aml_accounts': 'banking/data/aml/aml_data_accounts.csv',
    'aml_persons': 'banking/data/aml/aml_data_persons.csv',
    'aml_addresses': 'banking/data/aml/aml_data_addresses.csv',
    'aml_phones': 'banking/data/aml/aml_data_phones.csv',
    'aml_structuring': 'banking/data/aml/aml_structuring_data.json',
}


def get_data_path(key: str) -> Path:
    """Get absolute path to a data file."""
    project_root = setup_project_paths()
    return project_root / DATA_PATHS.get(key, key)


def get_gremlin_client():
    """Create and return a Gremlin client."""
    from gremlin_python.driver import client
    return client.Client(
        JANUSGRAPH_CONFIG['url'],
        JANUSGRAPH_CONFIG['traversal_source']
    )


def get_opensearch_client():
    """Create and return an OpenSearch client."""
    from opensearchpy import OpenSearch
    import warnings
    
    # Suppress SSL warnings for non-SSL connections
    warnings.filterwarnings('ignore', message='.*verify_certs.*')
    
    # Use dict-based host specification (more reliable than URL strings)
    return OpenSearch(
        hosts=[{
            'host': OPENSEARCH_CONFIG['host'],
            'port': OPENSEARCH_CONFIG['port']
        }],
        http_compress=False,
        use_ssl=False,  # Explicitly False for local dev
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
    )


# Standard notebook initialization
def init_notebook(check_env: bool = True, check_services: bool = False):
    """
    Standard notebook initialization.
    
    Args:
        check_env: Verify conda environment
        check_services: Test connections to JanusGraph and OpenSearch
    
    Returns:
        dict with project_root and optionally clients
    """
    import nest_asyncio
    nest_asyncio.apply()
    
    result = {
        'project_root': setup_project_paths()
    }
    
    if check_env:
        result['env_ok'] = verify_conda_environment()
    
    if check_services:
        # Test JanusGraph
        try:
            gc = get_gremlin_client()
            gc.submit('g.V().count()').all().result()
            print(f"✅ JanusGraph connected at {JANUSGRAPH_CONFIG['url']}")
            result['janusgraph_client'] = gc
        except Exception as e:
            print(f"❌ JanusGraph connection failed: {e}")
            result['janusgraph_client'] = None
        
        # Test OpenSearch
        try:
            os_client = get_opensearch_client()
            os_client.info()
            print(f"✅ OpenSearch connected at {OPENSEARCH_CONFIG['host']}:{OPENSEARCH_CONFIG['port']}")
            result['opensearch_client'] = os_client
        except Exception as e:
            print(f"❌ OpenSearch connection failed: {e}")
            result['opensearch_client'] = None
    
    return result
