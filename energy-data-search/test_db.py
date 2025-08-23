#!/usr/bin/env python
"""Test ChromaDB functionality."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from langchain.schema import Document
from energy_data_search.indexers.chromadb_indexer import ChromaDBIndexer

def test_chromadb():
    """Test basic ChromaDB operations."""
    print("Testing ChromaDB...")
    
    # Initialize
    indexer = ChromaDBIndexer(
        persist_directory=Path("data/test_chroma"),
        collection_name="test_collection"
    )
    
    # Create test documents
    test_docs = [
        Document(page_content="This is a test document about BESS", metadata={"source": "test1.txt"}),
        Document(page_content="Another document about energy storage", metadata={"source": "test2.txt"}),
    ]
    
    # Add documents
    print("Adding test documents...")
    count = indexer.add_documents(test_docs, batch_size=2)
    print(f"Added {count} documents")
    
    # Search
    print("\nSearching for 'BESS'...")
    results = indexer.search("BESS", k=2)
    for doc, score in results:
        print(f"  Score: {score:.3f} - {doc.page_content[:50]}...")
    
    print("\n✓ Test completed successfully!")
    
    # Clean up
    import shutil
    shutil.rmtree("data/test_chroma", ignore_errors=True)

if __name__ == "__main__":
    test_chromadb()