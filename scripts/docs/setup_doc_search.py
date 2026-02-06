#!/usr/bin/env python3
"""
AI-Powered Documentation Search Setup

Sets up semantic search for documentation using OpenSearch vector embeddings.
This enables natural language queries like "how do I configure SSL?"

Usage:
    python scripts/docs/setup_doc_search.py --index
    python scripts/docs/setup_doc_search.py --search "how to configure JanusGraph"
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Generator, List, Optional

try:
    from opensearchpy import OpenSearch
    from sentence_transformers import SentenceTransformer
    DEPS_AVAILABLE = True
except ImportError:
    DEPS_AVAILABLE = False


# Configuration
DOC_INDEX = "documentation-search"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
CHUNK_SIZE = 500  # Characters per chunk
CHUNK_OVERLAP = 100


def get_opensearch_client() -> Optional[OpenSearch]:
    """Create OpenSearch client."""
    host = os.getenv('OPENSEARCH_HOST', 'localhost')
    port = int(os.getenv('OPENSEARCH_PORT', 9200))
    use_ssl = os.getenv('OPENSEARCH_USE_SSL', 'false').lower() == 'true'
    
    try:
        client = OpenSearch(
            hosts=[{'host': host, 'port': port}],
            use_ssl=use_ssl,
            verify_certs=False,
            ssl_show_warn=False
        )
        # Test connection
        client.info()
        return client
    except Exception as e:
        print(f"Failed to connect to OpenSearch: {e}", file=sys.stderr)
        return None


def create_index(client: OpenSearch) -> bool:
    """Create the documentation search index."""
    index_body = {
        "settings": {
            "index": {
                "knn": True,
                "number_of_shards": 1,
                "number_of_replicas": 0
            }
        },
        "mappings": {
            "properties": {
                "content": {"type": "text"},
                "file_path": {"type": "keyword"},
                "section": {"type": "keyword"},
                "title": {"type": "text"},
                "chunk_id": {"type": "keyword"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": EMBEDDING_DIM,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "lucene"
                    }
                }
            }
        }
    }
    
    try:
        if client.indices.exists(index=DOC_INDEX):
            print(f"Index '{DOC_INDEX}' already exists. Deleting...")
            client.indices.delete(index=DOC_INDEX)
        
        client.indices.create(index=DOC_INDEX, body=index_body)
        print(f"Created index '{DOC_INDEX}'")
        return True
    except Exception as e:
        print(f"Failed to create index: {e}", file=sys.stderr)
        return False


def chunk_document(content: str, file_path: str) -> Generator[Dict, None, None]:
    """Split document into overlapping chunks."""
    # Extract title from first heading
    lines = content.split('\n')
    title = file_path
    for line in lines[:10]:
        if line.startswith('# '):
            title = line[2:].strip()
            break
    
    # Extract sections
    current_section = "Introduction"
    current_content = []
    
    for line in lines:
        if line.startswith('## '):
            # Yield previous section chunks
            if current_content:
                section_text = '\n'.join(current_content)
                for i, chunk in enumerate(_chunk_text(section_text)):
                    chunk_id = hashlib.md5(
                        f"{file_path}:{current_section}:{i}".encode()
                    ).hexdigest()[:12]
                    yield {
                        'content': chunk,
                        'file_path': str(file_path),
                        'section': current_section,
                        'title': title,
                        'chunk_id': chunk_id
                    }
            current_section = line[3:].strip()
            current_content = []
        else:
            current_content.append(line)
    
    # Yield final section
    if current_content:
        section_text = '\n'.join(current_content)
        for i, chunk in enumerate(_chunk_text(section_text)):
            chunk_id = hashlib.md5(
                f"{file_path}:{current_section}:{i}".encode()
            ).hexdigest()[:12]
            yield {
                'content': chunk,
                'file_path': str(file_path),
                'section': current_section,
                'title': title,
                'chunk_id': chunk_id
            }


def _chunk_text(text: str) -> Generator[str, None, None]:
    """Split text into overlapping chunks."""
    if len(text) <= CHUNK_SIZE:
        if text.strip():
            yield text.strip()
        return
    
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end]
        
        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind('. ')
            if last_period > CHUNK_SIZE // 2:
                chunk = chunk[:last_period + 1]
                end = start + last_period + 1
        
        if chunk.strip():
            yield chunk.strip()
        
        start = end - CHUNK_OVERLAP
        if start >= len(text):
            break


def index_documents(
    client: OpenSearch,
    model: SentenceTransformer,
    docs_path: Path
) -> int:
    """Index all markdown documents."""
    indexed = 0
    
    # Find all markdown files
    md_files = list(docs_path.rglob('*.md'))
    md_files.extend(Path('.').glob('*.md'))  # Root level
    
    # Exclude certain patterns
    exclude = ['archive', 'node_modules', 'hcd-1.2.3']
    md_files = [
        f for f in md_files
        if not any(ex in str(f) for ex in exclude)
    ]
    
    print(f"Found {len(md_files)} markdown files")
    
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
            chunks = list(chunk_document(content, str(md_file)))
            
            if not chunks:
                continue
            
            # Generate embeddings for all chunks
            texts = [c['content'] for c in chunks]
            embeddings = model.encode(texts, show_progress_bar=False)
            
            # Index each chunk
            for chunk, embedding in zip(chunks, embeddings):
                doc = {
                    **chunk,
                    'embedding': embedding.tolist()
                }
                client.index(
                    index=DOC_INDEX,
                    id=chunk['chunk_id'],
                    body=doc
                )
                indexed += 1
            
            print(f"  Indexed {len(chunks)} chunks from {md_file}")
            
        except Exception as e:
            print(f"  Error indexing {md_file}: {e}", file=sys.stderr)
    
    # Refresh index
    client.indices.refresh(index=DOC_INDEX)
    
    return indexed


def search_docs(
    client: OpenSearch,
    model: SentenceTransformer,
    query: str,
    top_k: int = 5
) -> List[Dict]:
    """Search documentation using semantic search."""
    # Generate query embedding
    query_embedding = model.encode(query).tolist()
    
    # Search
    search_query = {
        "size": top_k,
        "query": {
            "knn": {
                "embedding": {
                    "vector": query_embedding,
                    "k": top_k
                }
            }
        },
        "_source": ["content", "file_path", "section", "title"]
    }
    
    response = client.search(index=DOC_INDEX, body=search_query)
    
    results = []
    for hit in response['hits']['hits']:
        results.append({
            'score': hit['_score'],
            'file': hit['_source']['file_path'],
            'section': hit['_source']['section'],
            'title': hit['_source']['title'],
            'content': hit['_source']['content'][:300] + '...'
        })
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Documentation semantic search')
    parser.add_argument('--index', action='store_true', help='Index all documentation')
    parser.add_argument('--search', type=str, help='Search query')
    parser.add_argument('--top-k', type=int, default=5, help='Number of results')
    
    args = parser.parse_args()
    
    if not DEPS_AVAILABLE:
        print("Required dependencies not installed. Run:")
        print("  pip install opensearch-py sentence-transformers")
        sys.exit(1)
    
    client = get_opensearch_client()
    if not client:
        print("Cannot connect to OpenSearch. Is it running?")
        sys.exit(1)
    
    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    if args.index:
        print("\nCreating search index...")
        if not create_index(client):
            sys.exit(1)
        
        print("\nIndexing documentation...")
        docs_path = Path('docs')
        count = index_documents(client, model, docs_path)
        print(f"\n✅ Indexed {count} document chunks")
    
    if args.search:
        print(f"\nSearching for: '{args.search}'")
        print("-" * 60)
        
        results = search_docs(client, model, args.search, args.top_k)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. [{result['score']:.3f}] {result['title']}")
            print(f"   File: {result['file']}")
            print(f"   Section: {result['section']}")
            print(f"   Preview: {result['content']}")
    
    if not args.index and not args.search:
        parser.print_help()


if __name__ == '__main__':
    main()
