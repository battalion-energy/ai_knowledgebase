"""Document index tracking for incremental updates."""

import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, Optional, List
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class FileMetadata:
    """Metadata for indexed files."""
    file_path: str
    file_hash: str
    file_size: int
    last_modified: float
    indexed_at: str
    chunk_count: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FileMetadata':
        """Create from dictionary."""
        return cls(**data)


class IndexTracker:
    """Track indexed documents for incremental updates."""
    
    def __init__(self, tracker_file: Path = Path("data/index_tracker.json")):
        """Initialize index tracker."""
        self.tracker_file = Path(tracker_file)
        self.tracker_file.parent.mkdir(parents=True, exist_ok=True)
        self.indexed_files: Dict[str, FileMetadata] = {}
        self.load_tracker()
    
    def load_tracker(self):
        """Load existing tracker data."""
        if self.tracker_file.exists():
            try:
                with open(self.tracker_file, 'r') as f:
                    data = json.load(f)
                    self.indexed_files = {
                        path: FileMetadata.from_dict(meta) 
                        for path, meta in data.get('indexed_files', {}).items()
                    }
                    logger.info(f"Loaded tracker with {len(self.indexed_files)} indexed files")
            except Exception as e:
                logger.error(f"Error loading tracker: {e}")
                self.indexed_files = {}
        else:
            logger.info("No existing tracker found, starting fresh")
    
    def save_tracker(self):
        """Save tracker data to disk."""
        try:
            data = {
                'indexed_files': {
                    path: meta.to_dict() 
                    for path, meta in self.indexed_files.items()
                },
                'last_updated': datetime.now().isoformat(),
                'total_files': len(self.indexed_files),
                'total_chunks': sum(m.chunk_count for m in self.indexed_files.values())
            }
            
            with open(self.tracker_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved tracker with {len(self.indexed_files)} files")
        except Exception as e:
            logger.error(f"Error saving tracker: {e}")
    
    def compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file content."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error computing hash for {file_path}: {e}")
            return ""
    
    def is_file_indexed(self, file_path: Path) -> bool:
        """Check if file is already indexed."""
        str_path = str(file_path.absolute())
        return str_path in self.indexed_files
    
    def needs_reindex(self, file_path: Path) -> bool:
        """Check if file needs reindexing due to changes."""
        str_path = str(file_path.absolute())
        
        if str_path not in self.indexed_files:
            return True
        
        metadata = self.indexed_files[str_path]
        
        # Check if file still exists
        if not file_path.exists():
            logger.info(f"File no longer exists: {file_path}")
            del self.indexed_files[str_path]
            return False
        
        # Check modification time
        current_mtime = file_path.stat().st_mtime
        if current_mtime > metadata.last_modified:
            logger.info(f"File modified since indexing: {file_path}")
            return True
        
        # Check file hash for content changes
        current_hash = self.compute_file_hash(file_path)
        if current_hash != metadata.file_hash:
            logger.info(f"File content changed: {file_path}")
            return True
        
        return False
    
    def mark_indexed(self, file_path: Path, chunk_count: int):
        """Mark file as indexed."""
        str_path = str(file_path.absolute())
        
        metadata = FileMetadata(
            file_path=str_path,
            file_hash=self.compute_file_hash(file_path),
            file_size=file_path.stat().st_size,
            last_modified=file_path.stat().st_mtime,
            indexed_at=datetime.now().isoformat(),
            chunk_count=chunk_count
        )
        
        self.indexed_files[str_path] = metadata
        logger.debug(f"Marked as indexed: {file_path} ({chunk_count} chunks)")
    
    def remove_indexed(self, file_path: Path):
        """Remove file from indexed list."""
        str_path = str(file_path.absolute())
        if str_path in self.indexed_files:
            del self.indexed_files[str_path]
            logger.debug(f"Removed from index: {file_path}")
    
    def get_files_to_index(self, directory: Path, recursive: bool = True) -> List[Path]:
        """Get list of files that need indexing."""
        pattern = "**/*" if recursive else "*"
        supported_extensions = {'.pdf', '.txt', '.csv', '.html', '.htm', '.md', '.markdown'}
        
        files_to_index = []
        
        for file_path in directory.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                if self.needs_reindex(file_path):
                    files_to_index.append(file_path)
        
        return files_to_index
    
    def get_removed_files(self, directory: Path) -> List[str]:
        """Get files that were indexed but no longer exist."""
        removed = []
        dir_str = str(directory.absolute())
        
        for file_path in list(self.indexed_files.keys()):
            if file_path.startswith(dir_str):
                if not Path(file_path).exists():
                    removed.append(file_path)
        
        return removed
    
    def get_statistics(self) -> Dict:
        """Get tracker statistics."""
        total_size = sum(m.file_size for m in self.indexed_files.values())
        total_chunks = sum(m.chunk_count for m in self.indexed_files.values())
        
        file_types = {}
        for path in self.indexed_files:
            ext = Path(path).suffix.lower()
            file_types[ext] = file_types.get(ext, 0) + 1
        
        return {
            'total_files': len(self.indexed_files),
            'total_chunks': total_chunks,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_types': file_types,
            'tracker_file': str(self.tracker_file)
        }
    
    def clear(self):
        """Clear all tracking data."""
        self.indexed_files = {}
        self.save_tracker()
        logger.info("Cleared all tracking data")