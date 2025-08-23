#!/usr/bin/env python
"""Test ChromaDB directly without LangChain."""

import chromadb
from pathlib import Path
import shutil

# Clean up first
test_dir = Path("./test_direct_chroma")
if test_dir.exists():
    shutil.rmtree(test_dir)

# Create directory
test_dir.mkdir(parents=True, exist_ok=True, mode=0o777)

print(f"Creating ChromaDB at {test_dir.absolute()}")

# Try creating a persistent client
client = chromadb.PersistentClient(path=str(test_dir))

# Create a collection
collection = client.create_collection(name="test")

# Add some test data
collection.add(
    documents=["This is a test document", "Another test document"],
    metadatas=[{"source": "test1"}, {"source": "test2"}],
    ids=["id1", "id2"]
)

print("✓ Successfully added documents")

# Query
results = collection.query(
    query_texts=["test"],
    n_results=2
)

print(f"✓ Query returned {len(results['ids'][0])} results")

# Check what files were created
import os
for root, dirs, files in os.walk(test_dir):
    level = root.replace(str(test_dir), "").count(os.sep)
    indent = " " * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = " " * 2 * (level + 1)
    for file in files:
        print(f"{subindent}{file}")

print("\n✓ Test completed successfully!")