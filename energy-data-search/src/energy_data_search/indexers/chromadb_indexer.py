"""ChromaDB indexer for document storage and retrieval."""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import hashlib
import chromadb
from chromadb.config import Settings
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


class ChromaDBIndexer:
    """Manage ChromaDB vector store for document indexing and search."""
    
    def __init__(
        self,
        persist_directory: Path,
        collection_name: str = "energy_documents",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """Initialize ChromaDB indexer."""
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        self.client = None
        self.collection = None
        self._initialize_chromadb()
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Create persistent client - this will create/load the database
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                    is_persistent=True
                )
            )
            
            # Try to get existing collection first
            try:
                self.collection = self.client.get_collection(
                    name=self.collection_name
                )
                logger.info(f"Loaded existing collection '{self.collection_name}'")
            except Exception:
                # Collection doesn't exist, create it
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"Created new collection '{self.collection_name}'")
            
            logger.info(f"Initialized ChromaDB at {self.persist_directory}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def _generate_id(self, content: str, metadata: Dict[str, Any]) -> str:
        """Generate a unique ID for a document."""
        # Create ID from content hash and source
        source = metadata.get('source', 'unknown')
        content_hash = hashlib.md5(f"{source}:{content}".encode()).hexdigest()
        return content_hash
    
    def add_documents(self, documents: List[Document], batch_size: int = 50) -> int:
        """Add documents to the vector store in batches."""
        if not documents:
            logger.warning("No documents to add")
            return 0
        
        if not self.collection:
            logger.error("Collection not initialized")
            return 0
        
        total_added = 0
        failed_batches = 0
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            try:
                # Prepare batch data
                ids = []
                texts = []
                metadatas = []
                
                for doc in batch:
                    # Generate ID
                    doc_id = self._generate_id(doc.page_content, doc.metadata)
                    ids.append(doc_id)
                    texts.append(doc.page_content)
                    metadatas.append(doc.metadata)
                
                # Generate embeddings for the batch
                batch_embeddings = self.embeddings.embed_documents(texts)
                
                # Add to collection (upsert to handle duplicates)
                self.collection.upsert(
                    ids=ids,
                    documents=texts,
                    metadatas=metadatas,
                    embeddings=batch_embeddings
                )
                
                total_added += len(batch)
                logger.info(f"Added batch {i//batch_size + 1}: {len(batch)} documents")
                
            except Exception as e:
                logger.error(f"Error adding batch {i//batch_size + 1}: {e}")
                failed_batches += 1
        
        if failed_batches > 0:
            logger.warning(f"Failed to add {failed_batches} batches")
        
        logger.info(f"Total documents added: {total_added}")
        return total_added
    
    def search(
        self,
        query: str,
        k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
        score_threshold: Optional[float] = None
    ) -> List[Tuple[Document, float]]:
        """Search for similar documents."""
        if not self.collection:
            logger.error("Collection not initialized")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Build where clause for filtering
            where_clause = None
            if filter_dict:
                where_clause = filter_dict
            
            # Perform search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=where_clause if where_clause else None
            )
            
            # Process results
            output = []
            if results and results['ids'] and len(results['ids'][0]) > 0:
                for idx, doc_id in enumerate(results['ids'][0]):
                    # Calculate similarity score (distance to similarity)
                    # ChromaDB returns distances, convert to similarity scores
                    distance = results['distances'][0][idx]
                    similarity = 1 - distance  # For cosine distance
                    
                    # Apply score threshold if provided
                    if score_threshold is not None and similarity < score_threshold:
                        continue
                    
                    # Create Document object
                    doc = Document(
                        page_content=results['documents'][0][idx],
                        metadata=results['metadatas'][0][idx] if results['metadatas'][0][idx] else {}
                    )
                    output.append((doc, similarity))
            
            logger.info(f"Found {len(output)} documents for query: {query[:50]}...")
            return output
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        try:
            count = self.collection.count() if self.collection else 0
            
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": str(self.persist_directory),
                "embedding_model": self.embeddings.model_name
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
    
    def clear_collection(self):
        """Clear all documents from the collection."""
        try:
            if self.collection:
                # Delete the collection and recreate it
                self.client.delete_collection(name=self.collection_name)
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"Cleared collection '{self.collection_name}'")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
    
    def update_document(self, document_id: str, document: Document):
        """Update a specific document in the collection."""
        try:
            # Generate embedding for the new content
            embedding = self.embeddings.embed_documents([document.page_content])[0]
            
            # Update in collection
            self.collection.update(
                ids=[document_id],
                documents=[document.page_content],
                metadatas=[document.metadata],
                embeddings=[embedding]
            )
            logger.info(f"Updated document {document_id}")
        except Exception as e:
            logger.error(f"Error updating document {document_id}: {e}")