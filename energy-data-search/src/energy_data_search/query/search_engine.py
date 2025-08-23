"""Search engine for querying energy documents."""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

from ..config import Config
from ..indexers.chromadb_indexer import ChromaDBIndexer
from ..loaders.document_loader import DocumentLoader

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Container for search results."""
    content: str
    source: str
    score: float
    metadata: Dict[str, Any]
    
    def __str__(self) -> str:
        """String representation of search result."""
        return (
            f"Score: {self.score:.3f}\n"
            f"Source: {self.source}\n"
            f"Content: {self.content[:200]}...\n"
        )


class EnergyDataSearchEngine:
    """Main search engine for energy data documents."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize search engine with configuration."""
        self.config = config or Config()
        
        self.indexer = ChromaDBIndexer(
            persist_directory=self.config.chroma_persist_dir,
            collection_name=self.config.collection_name,
            embedding_model=self.config.embedding_model
        )
        
        self.loader = DocumentLoader(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap
        )
    
    def index_directory(self, directory: Path, recursive: bool = True) -> int:
        """Index all documents in a directory."""
        logger.info(f"Indexing directory: {directory}")
        
        documents = self.loader.load_directory(directory, recursive=recursive)
        
        if not documents:
            logger.warning(f"No documents found in {directory}")
            return 0
        
        count = self.indexer.add_documents(documents, batch_size=self.config.batch_size)
        logger.info(f"Indexed {count} document chunks from {directory}")
        return count
    
    def index_all_sources(self) -> Dict[str, int]:
        """Index all configured source directories."""
        results = {}
        
        try:
            subdirs = self.config.get_subdirectories()
            logger.info(f"Found {len(subdirs)} source directories to index")
            
            for subdir in subdirs:
                count = self.index_directory(subdir, recursive=True)
                results[str(subdir)] = count
                
        except ValueError as e:
            logger.error(f"Error accessing source directories: {e}")
            
        return results
    
    def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        filter_directory: Optional[str] = None,
        filter_file_type: Optional[str] = None,
        score_threshold: Optional[float] = None
    ) -> List[SearchResult]:
        """Search for documents matching the query."""
        max_results = max_results or self.config.max_results
        score_threshold = score_threshold or self.config.similarity_threshold
        
        filter_dict = {}
        if filter_directory:
            filter_dict["directory"] = filter_directory
        if filter_file_type:
            filter_dict["file_type"] = filter_file_type
        
        filter_dict = filter_dict or None
        
        results = self.indexer.search(
            query=query,
            k=max_results,
            filter_dict=filter_dict,
            score_threshold=score_threshold
        )
        
        search_results = []
        for doc, score in results:
            search_results.append(
                SearchResult(
                    content=doc.page_content,
                    source=doc.metadata.get("source", "Unknown"),
                    score=score,
                    metadata=doc.metadata
                )
            )
        
        return search_results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the indexed documents."""
        return self.indexer.get_collection_stats()
    
    def clear_index(self):
        """Clear all indexed documents."""
        self.indexer.clear_collection()
        logger.info("Cleared all indexed documents")
    
    def reindex_all(self) -> Dict[str, int]:
        """Clear and reindex all documents."""
        logger.info("Starting full reindex")
        self.clear_index()
        return self.index_all_sources()