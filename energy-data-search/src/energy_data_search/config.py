"""Configuration management for Energy Data Search."""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class Config(BaseModel):
    """Application configuration."""
    
    source_data_dir: Path = Field(
        default_factory=lambda: Path(os.getenv("SOURCE_DATA_DIR", "/pool/ssd8tb/data/iso/"))
    )
    chroma_persist_dir: Path = Field(
        default_factory=lambda: Path("./data/chroma_db").absolute()
    )
    collection_name: str = Field(default="energy_documents")
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    chunk_size: int = Field(default=1000)
    chunk_overlap: int = Field(default=200)
    batch_size: int = Field(default=50)
    
    max_results: int = Field(default=10)
    similarity_threshold: float = Field(default=0.3)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def get_subdirectories(self) -> list[Path]:
        """Get all subdirectories from source data directory."""
        if not self.source_data_dir.exists():
            raise ValueError(f"Source data directory does not exist: {self.source_data_dir}")
        
        subdirs = []
        for item in self.source_data_dir.iterdir():
            if item.is_dir():
                subdirs.append(item)
        return subdirs


config = Config()