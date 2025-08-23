"""Document loaders for various file formats."""

import logging
from pathlib import Path
from typing import List, Optional
from langchain.schema import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class DocumentLoader:
    """Load and process documents from various file formats."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize document loader with text splitting configuration."""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        self.loader_map = {
            ".pdf": self._load_pdf,
            ".txt": self._load_text,
            ".csv": self._load_csv,
            ".html": self._load_html,
            ".htm": self._load_html,
            ".md": self._load_markdown,
            ".markdown": self._load_markdown
        }
    
    def load_document(self, file_path: Path) -> List[Document]:
        """Load a single document and split it into chunks."""
        if not file_path.exists():
            logger.warning(f"File does not exist: {file_path}")
            return []
        
        suffix = file_path.suffix.lower()
        loader_func = self.loader_map.get(suffix)
        
        if not loader_func:
            logger.warning(f"Unsupported file type: {suffix} for {file_path}")
            return []
        
        try:
            documents = loader_func(file_path)
            chunks = self.text_splitter.split_documents(documents)
            
            for chunk in chunks:
                chunk.metadata.update({
                    "source": str(file_path),
                    "file_type": suffix[1:],
                    "file_name": file_path.name,
                    "directory": file_path.parent.name
                })
            
            logger.info(f"Loaded {len(chunks)} chunks from {file_path}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return []
    
    def load_directory(self, directory: Path, recursive: bool = True) -> List[Document]:
        """Load all supported documents from a directory."""
        if not directory.exists() or not directory.is_dir():
            logger.warning(f"Invalid directory: {directory}")
            return []
        
        all_documents = []
        pattern = "**/*" if recursive else "*"
        
        for file_path in directory.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in self.loader_map:
                docs = self.load_document(file_path)
                all_documents.extend(docs)
        
        logger.info(f"Loaded {len(all_documents)} total chunks from {directory}")
        return all_documents
    
    def _load_pdf(self, file_path: Path) -> List[Document]:
        """Load PDF document."""
        loader = PyPDFLoader(str(file_path))
        return loader.load()
    
    def _load_text(self, file_path: Path) -> List[Document]:
        """Load text document."""
        loader = TextLoader(str(file_path), encoding="utf-8")
        try:
            return loader.load()
        except UnicodeDecodeError:
            loader = TextLoader(str(file_path), encoding="latin-1")
            return loader.load()
    
    def _load_csv(self, file_path: Path) -> List[Document]:
        """Load CSV document."""
        loader = CSVLoader(str(file_path))
        return loader.load()
    
    def _load_html(self, file_path: Path) -> List[Document]:
        """Load HTML document as text."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return [Document(page_content=content, metadata={"source": str(file_path)})]
        except Exception as e:
            logger.error(f"Error reading HTML file {file_path}: {e}")
            return []
    
    def _load_markdown(self, file_path: Path) -> List[Document]:
        """Load Markdown document as text."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return [Document(page_content=content, metadata={"source": str(file_path)})]
        except Exception as e:
            logger.error(f"Error reading Markdown file {file_path}: {e}")
            return []