"""
FastAPI wrapper for ChromaDB search functionality
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Add the parent directory to the path to import energy_data_search
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from energy_data_search.query.search_engine import EnergyDataSearchEngine
except ImportError as e:
    print(f"Warning: Could not import EnergyDataSearchEngine: {e}")
    print("Search functionality will be limited")
    EnergyDataSearchEngine = None

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Energence.ai Search API",
    description="ChromaDB-powered search for ERCOT energy documents",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3105",
        "http://localhost:3000",
        "http://localhost:3001",
        "https://energence.ai",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize search engine
search_engine = None
if EnergyDataSearchEngine:
    try:
        search_engine = EnergyDataSearchEngine()
        print("✓ Search engine initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize search engine: {e}")

# Request/Response models
class SearchRequest(BaseModel):
    query: str
    limit: int = 20
    filters: Optional[Dict[str, Any]] = None
    document_types: Optional[List[str]] = None
    date_range: Optional[Dict[str, str]] = None

class SearchResult(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int
    search_time_ms: float

class IndexUpdateResponse(BaseModel):
    status: str
    files_processed: int
    files_added: int
    files_updated: int
    files_skipped: int
    errors: List[str]

class StatsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    index_size_mb: float
    last_updated: str
    collections: List[str]

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Energence.ai Search API",
        "version": "1.0.0",
        "status": "running",
        "search_engine": "available" if search_engine else "not initialized",
        "endpoints": {
            "search": "/search",
            "index_update": "/index/update",
            "stats": "/stats",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "search_engine": "available" if search_engine else "not initialized"
    }

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Search for documents using semantic search
    """
    if not search_engine:
        # Return mock data if search engine is not available
        return SearchResponse(
            query=request.query,
            results=[
                SearchResult(
                    id="mock_1",
                    content=f"Mock result for query: {request.query}",
                    metadata={
                        "source": "mock_data",
                        "type": "NPRR",
                        "title": "Sample NPRR Document"
                    },
                    score=0.95
                )
            ],
            total_results=1,
            search_time_ms=10.0
        )
    
    try:
        import time
        start_time = time.time()
        
        # Perform the search
        results = search_engine.search(
            query=request.query,
            max_results=request.limit,
            filters=request.filters
        )
        
        search_time_ms = (time.time() - start_time) * 1000
        
        # Transform results to match our response model
        search_results = []
        for result in results:
            search_results.append(SearchResult(
                id=result.get("id", ""),
                content=result.get("content", ""),
                metadata=result.get("metadata", {}),
                score=result.get("score", 0.0)
            ))
        
        return SearchResponse(
            query=request.query,
            results=search_results,
            total_results=len(search_results),
            search_time_ms=search_time_ms
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.post("/index/update", response_model=IndexUpdateResponse)
async def update_index():
    """
    Trigger an incremental index update
    """
    if not search_engine:
        return IndexUpdateResponse(
            status="error",
            files_processed=0,
            files_added=0,
            files_updated=0,
            files_skipped=0,
            errors=["Search engine not initialized"]
        )
    
    try:
        # Call the index update method
        stats = search_engine.index_all_sources()
        
        return IndexUpdateResponse(
            status="success",
            files_processed=stats.get("total_files", 0),
            files_added=stats.get("files_added", 0),
            files_updated=stats.get("files_updated", 0),
            files_skipped=stats.get("files_skipped", 0),
            errors=stats.get("errors", [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index update error: {str(e)}")

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get index statistics
    """
    if not search_engine:
        return StatsResponse(
            total_documents=0,
            total_chunks=0,
            index_size_mb=0.0,
            last_updated="N/A",
            collections=[]
        )
    
    try:
        stats = search_engine.get_statistics()
        
        return StatsResponse(
            total_documents=stats.get("total_documents", 0),
            total_chunks=stats.get("total_chunks", 0),
            index_size_mb=stats.get("index_size_mb", 0.0),
            last_updated=stats.get("last_updated", "N/A"),
            collections=stats.get("collections", [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")

@app.get("/document/{document_id}")
async def get_document(document_id: str):
    """
    Get a specific document by ID
    """
    if not search_engine:
        raise HTTPException(status_code=503, detail="Search engine not available")
    
    try:
        document = search_engine.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving document: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8105, reload=True)