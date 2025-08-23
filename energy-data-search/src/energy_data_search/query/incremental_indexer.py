"""Incremental indexing for energy documents."""

import logging
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

from ..config import Config
from ..indexers.chromadb_indexer import ChromaDBIndexer
from ..loaders.document_loader import DocumentLoader
from ..utils.index_tracker import IndexTracker

logger = logging.getLogger(__name__)


class IncrementalIndexer:
    """Handle incremental indexing of documents."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize incremental indexer."""
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
        
        self.tracker = IndexTracker(
            tracker_file=self.config.chroma_persist_dir / "index_tracker.json"
        )
    
    def index_new_documents(self, directory: Optional[Path] = None) -> Dict:
        """Index only new or modified documents."""
        start_time = datetime.now()
        results = {
            'new_files': [],
            'modified_files': [],
            'removed_files': [],
            'errors': [],
            'total_chunks_added': 0,
            'processing_time': 0
        }
        
        if directory:
            directories = [Path(directory)]
        else:
            try:
                directories = self.config.get_subdirectories()
            except ValueError as e:
                logger.error(f"Error getting source directories: {e}")
                return results
        
        for dir_path in directories:
            logger.info(f"Checking directory for new documents: {dir_path}")
            
            # Get files that need indexing
            files_to_index = self.tracker.get_files_to_index(dir_path, recursive=True)
            
            if not files_to_index:
                logger.info(f"No new or modified files in {dir_path}")
                continue
            
            logger.info(f"Found {len(files_to_index)} files to index in {dir_path}")
            
            for file_path in files_to_index:
                try:
                    # Check if file was previously indexed
                    was_indexed = self.tracker.is_file_indexed(file_path)
                    
                    # Load and index the document
                    logger.info(f"Indexing: {file_path}")
                    documents = self.loader.load_document(file_path)
                    
                    if documents:
                        # Add to ChromaDB
                        self.indexer.add_documents(documents, batch_size=self.config.batch_size)
                        
                        # Track the indexing
                        self.tracker.mark_indexed(file_path, len(documents))
                        
                        # Update results
                        if was_indexed:
                            results['modified_files'].append(str(file_path))
                        else:
                            results['new_files'].append(str(file_path))
                        
                        results['total_chunks_added'] += len(documents)
                        logger.info(f"Indexed {len(documents)} chunks from {file_path}")
                    
                except Exception as e:
                    logger.error(f"Error indexing {file_path}: {e}")
                    results['errors'].append({
                        'file': str(file_path),
                        'error': str(e)
                    })
            
            # Check for removed files
            removed = self.tracker.get_removed_files(dir_path)
            for file_path in removed:
                self.tracker.remove_indexed(Path(file_path))
                results['removed_files'].append(file_path)
                logger.info(f"Removed from tracking: {file_path}")
        
        # Save tracker state
        self.tracker.save_tracker()
        
        # Calculate processing time
        results['processing_time'] = (datetime.now() - start_time).total_seconds()
        
        # Log summary
        logger.info(f"Incremental indexing complete:")
        logger.info(f"  - New files: {len(results['new_files'])}")
        logger.info(f"  - Modified files: {len(results['modified_files'])}")
        logger.info(f"  - Removed files: {len(results['removed_files'])}")
        logger.info(f"  - Total chunks added: {results['total_chunks_added']}")
        logger.info(f"  - Processing time: {results['processing_time']:.2f} seconds")
        
        return results
    
    def check_status(self) -> Dict:
        """Check current indexing status."""
        tracker_stats = self.tracker.get_statistics()
        index_stats = self.indexer.get_collection_stats()
        
        # Check for new files across all directories
        new_files_count = 0
        try:
            for dir_path in self.config.get_subdirectories():
                files_to_index = self.tracker.get_files_to_index(dir_path, recursive=True)
                new_files_count += len(files_to_index)
        except ValueError:
            pass
        
        return {
            'tracker': tracker_stats,
            'index': index_stats,
            'new_files_available': new_files_count,
            'last_update': self._get_last_update_time()
        }
    
    def _get_last_update_time(self) -> Optional[str]:
        """Get the last update time from tracker."""
        if self.tracker.tracker_file.exists():
            try:
                import json
                with open(self.tracker.tracker_file, 'r') as f:
                    data = json.load(f)
                    return data.get('last_updated')
            except Exception:
                pass
        return None
    
    def force_reindex_file(self, file_path: Path) -> Dict:
        """Force reindex a specific file."""
        results = {
            'success': False,
            'chunks_added': 0,
            'error': None
        }
        
        try:
            # Remove from tracker to force reindex
            self.tracker.remove_indexed(file_path)
            
            # Load and index
            documents = self.loader.load_document(file_path)
            
            if documents:
                self.indexer.add_documents(documents, batch_size=self.config.batch_size)
                self.tracker.mark_indexed(file_path, len(documents))
                self.tracker.save_tracker()
                
                results['success'] = True
                results['chunks_added'] = len(documents)
                logger.info(f"Force reindexed {file_path}: {len(documents)} chunks")
            
        except Exception as e:
            results['error'] = str(e)
            logger.error(f"Error force reindexing {file_path}: {e}")
        
        return results
    
    def reset_tracker(self):
        """Reset the tracker (useful for full reindex)."""
        self.tracker.clear()
        logger.info("Tracker reset - all files will be reindexed on next run")