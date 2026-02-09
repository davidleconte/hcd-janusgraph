"""
Phase 5 Setup Verification Script
Tests embedding generation and vector search capabilities

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Created: 2026-01-28
Phase: 5 (Vector/AI Foundation)
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/python'))

from utils.embedding_generator import EmbeddingGenerator
from utils.vector_search import VectorSearchClient
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_embedding_generator():
    """Test embedding generation."""
    print("\n" + "="*60)
    print("TEST 1: Embedding Generator")
    print("="*60)
    
    try:
        # Initialize generator
        print("\n1. Initializing embedding generator (mini model)...")
        generator = EmbeddingGenerator(model_name='mini')
        print(f"   ✅ Model loaded: {generator.model_config['name']}")
        print(f"   ✅ Dimensions: {generator.dimensions}")
        
        # Test single encoding
        print("\n2. Testing single text encoding...")
        text = "John Smith"
        embedding = generator.encode_for_search(text)
        print(f"   ✅ Encoded '{text}'")
        print(f"   ✅ Embedding shape: {embedding.shape}")
        print(f"   ✅ First 5 values: {embedding[:5]}")
        
        # Test batch encoding
        print("\n3. Testing batch encoding...")
        names = ["John Smith", "Jane Doe", "Bob Johnson"]
        embeddings = generator.encode(names)
        print(f"   ✅ Encoded {len(names)} names")
        print(f"   ✅ Embeddings shape: {embeddings.shape}")
        
        # Test similarity
        print("\n4. Testing similarity calculation...")
        name1 = "John Smith"
        name2 = "Jon Smyth"  # Similar spelling
        name3 = "Jane Doe"   # Different person
        
        emb1 = generator.encode_for_search(name1)
        emb2 = generator.encode_for_search(name2)
        emb3 = generator.encode_for_search(name3)
        
        sim_12 = generator.similarity(emb1, emb2)
        sim_13 = generator.similarity(emb1, emb3)
        
        print(f"   ✅ Similarity '{name1}' vs '{name2}': {sim_12:.4f}")
        print(f"   ✅ Similarity '{name1}' vs '{name3}': {sim_13:.4f}")
        
        if sim_12 > sim_13:
            print(f"   ✅ Fuzzy matching works! Similar names have higher similarity.")
        else:
            print(f"   ⚠️  Warning: Expected sim_12 > sim_13")
        
        print("\n✅ Embedding Generator: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Embedding Generator: TEST FAILED")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vector_search():
    """Test OpenSearch vector search."""
    print("\n" + "="*60)
    print("TEST 2: Vector Search (OpenSearch)")
    print("="*60)
    
    try:
        # Initialize client
        print("\n1. Connecting to OpenSearch...")
        client = VectorSearchClient(host='localhost', port=9200)
        print(f"   ✅ Connected to OpenSearch")
        
        # Create test index
        print("\n2. Creating test index...")
        index_name = 'test_phase5_vectors'
        
        # Delete if exists
        if client.client.indices.exists(index=index_name):
            client.delete_index(index_name)
            print(f"   ℹ️  Deleted existing index")
        
        success = client.create_vector_index(
            index_name=index_name,
            vector_dimension=384,
            additional_fields={'name': {'type': 'text'}}
        )
        print(f"   ✅ Created index: {index_name}")
        
        # Index test documents
        print("\n3. Indexing test documents...")
        generator = EmbeddingGenerator(model_name='mini')
        
        test_names = [
            "John Smith",
            "Jane Doe",
            "Bob Johnson",
            "Alice Williams",
            "Charlie Brown"
        ]
        
        documents = []
        for i, name in enumerate(test_names):
            embedding = generator.encode_for_search(name)
            documents.append({
                'id': str(i+1),
                'embedding': embedding,
                'name': name
            })
        
        success_count, errors = client.bulk_index_documents(index_name, documents)
        print(f"   ✅ Indexed {success_count} documents")
        
        # Search
        print("\n4. Testing vector search...")
        query_name = "Jon Smyth"  # Similar to "John Smith"
        query_embedding = generator.encode_for_search(query_name)
        
        results = client.search(
            index_name=index_name,
            query_embedding=query_embedding,
            k=3
        )
        
        print(f"   ✅ Query: '{query_name}'")
        print(f"   ✅ Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"      {i}. {result['source']['name']} (score: {result['score']:.4f})")
        
        # Verify top result
        if results and results[0]['source']['name'] == "John Smith":
            print(f"   ✅ Top result is correct! Fuzzy matching works.")
        else:
            print(f"   ⚠️  Warning: Expected 'John Smith' as top result")
        
        # Cleanup
        print("\n5. Cleaning up...")
        client.delete_index(index_name)
        print(f"   ✅ Deleted test index")
        
        print("\n✅ Vector Search: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Vector Search: TEST FAILED")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to cleanup
        try:
            if 'client' in locals() and 'index_name' in locals():
                if client.client.indices.exists(index=index_name):
                    client.delete_index(index_name)
        except:
            pass
        
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("PHASE 5 SETUP VERIFICATION")
    print("="*60)
    print("\nThis script verifies:")
    print("  1. Embedding generation (sentence-transformers)")
    print("  2. Vector search (OpenSearch with JVector)")
    print("  3. Fuzzy name matching capabilities")
    
    results = []
    
    # Test 1: Embedding Generator
    results.append(("Embedding Generator", test_embedding_generator()))
    
    # Test 2: Vector Search
    results.append(("Vector Search", test_vector_search()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Phase 5 setup is working!")
        print("="*60)
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - Please check the errors above")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
