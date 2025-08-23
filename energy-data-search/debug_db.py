#!/usr/bin/env python
"""Debug ChromaDB initialization."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from langchain.schema import Document
from energy_data_search.indexers.chromadb_indexer import ChromaDBIndexer

def debug_chromadb():
    """Debug ChromaDB operations."""
    print("Testing ChromaDB initialization...")
    
    # Clean existing data
    import shutil
    db_path = Path("data/chroma_db")
    if db_path.exists():
        shutil.rmtree(db_path)
    
    # Initialize
    indexer = ChromaDBIndexer(
        persist_directory=db_path,
        collection_name="energy_documents"
    )
    
    print(f"Database file exists: {(db_path / 'chroma.sqlite3').exists()}")
    print(f"Database file size: {(db_path / 'chroma.sqlite3').stat().st_size if (db_path / 'chroma.sqlite3').exists() else 0}")
    
    # Create test documents
    test_docs = [
        Document(page_content="This is a test document about BESS", metadata={"source": "test1.txt"}),
    ]
    
    # Add documents
    print("Adding test document...")
    count = indexer.add_documents(test_docs, batch_size=1)
    print(f"Added {count} documents")
    
    print(f"Database file size after add: {(db_path / 'chroma.sqlite3').stat().st_size if (db_path / 'chroma.sqlite3').exists() else 0}")
    
    # Check what's in the directory
    import os
    for root, dirs, files in os.walk(db_path):
        level = root.replace(str(db_path), "").count(os.sep)
        indent = " " * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = " " * 2 * (level + 1)
        for file in files:
            size = Path(root) / file
            print(f"{subindent}{file} ({size.stat().st_size} bytes)")

if __name__ == "__main__":
    debug_chromadb()