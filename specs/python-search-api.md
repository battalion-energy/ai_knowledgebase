# Python Search API Specification

## Overview
FastAPI wrapper around the existing ChromaDB search implementation to provide HTTP endpoints for the Next.js application.

## Architecture

### Service Structure
```
apps/search-api/
├── main.py                 # FastAPI application
├── routers/
│   ├── search.py          # Search endpoints
│   ├── indexing.py        # Indexing endpoints
│   └── health.py          # Health checks
├── services/
│   ├── search_service.py  # Search business logic
│   └── index_service.py   # Indexing business logic
├── models/
│   └── schemas.py         # Pydantic models
├── config.py              # Configuration
├── Dockerfile             # Container definition
├── requirements.txt       # Python dependencies
└── tests/
    └── test_api.py        # API tests
```

## API Implementation

### Main Application
```python
# apps/search-api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
import os
from pathlib import Path

# Add energy-data-search to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "energy-data-search" / "src"))

from routers import search, indexing, health
from config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources."""
    # Startup
    print(f"Starting Search API on port {settings.port}")
    print(f"ChromaDB directory: {settings.chroma_persist_dir}")
    print(f"Source data directory: {settings.source_data_dir}")
    yield
    # Shutdown
    print("Shutting down Search API")

app = FastAPI(
    title="AI Knowledge Base Search API",
    description="ChromaDB-powered search for ERCOT documents",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(indexing.router, prefix="/index", tags=["indexing"])
app.include_router(health.router, prefix="/health", tags=["health"])

@app.get("/")
async def root():
    return {
        "name": "AI Knowledge Base Search API",
        "version": "1.0.0",
        "status": "running"
    }
```

### Configuration
```python
# apps/search-api/config.py
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List

class Settings(BaseSettings):
    # API Settings
    port: int = 8000
    host: str = "0.0.0.0"
    cors_origins: List[str] = ["http://localhost:3000"]
    
    # Paths
    source_data_dir: Path = Path("/pool/ssd8tb/data/iso/ERCOT")
    chroma_persist_dir: Path = Path("/app/data/chroma_db")
    
    # ChromaDB Settings
    collection_name: str = "energy_documents"
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Search Settings
    max_results: int = 20
    similarity_threshold: float = 0.3
    
    # Performance
    batch_size: int = 50
    max_workers: int = 4
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Search Router
```python
# apps/search-api/routers/search.py
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from services.search_service import SearchService

router = APIRouter()
search_service = SearchService()

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: Optional[int] = Field(20, ge=1, le=100)
    offset: Optional[int] = Field(0, ge=0)
    filters: Optional[Dict[str, Any]] = None
    document_ids: Optional[List[str]] = None
    similarity_threshold: Optional[float] = Field(0.3, ge=0, le=1)

class SearchResult(BaseModel):
    id: str
    content: str
    source: str
    score: float
    metadata: Dict[str, Any]
    highlights: List[str]

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_count: int
    execution_time: float
    query: str

@router.post("/", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """
    Search documents using ChromaDB semantic search.
    
    - **query**: Search query text
    - **limit**: Maximum number of results (1-100)
    - **filters**: Metadata filters (e.g., {"type": "NPRR"})
    - **document_ids**: Limit search to specific document IDs
    - **similarity_threshold**: Minimum similarity score (0-1)
    """
    try:
        results = await search_service.search(
            query=request.query,
            limit=request.limit,
            offset=request.offset,
            filters=request.filters,
            document_ids=request.document_ids,
            similarity_threshold=request.similarity_threshold
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/suggestions")
async def get_suggestions(
    q: str = Query(..., min_length=2, max_length=100)
):
    """Get search suggestions based on partial query."""
    try:
        suggestions = await search_service.get_suggestions(q)
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/similar/{document_id}")
async def find_similar_documents(
    document_id: str,
    limit: int = Query(10, ge=1, le=50)
):
    """Find documents similar to a given document."""
    try:
        similar = await search_service.find_similar(document_id, limit)
        return {"similar_documents": similar}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Search Service
```python
# apps/search-api/services/search_service.py
import time
from typing import Optional, List, Dict, Any
from energy_data_search.query.search_engine import EnergyDataSearchEngine
from energy_data_search.config import Config

class SearchService:
    def __init__(self):
        self.config = Config()
        self.search_engine = EnergyDataSearchEngine(self.config)
    
    async def search(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        document_ids: Optional[List[str]] = None,
        similarity_threshold: float = 0.3
    ) -> Dict[str, Any]:
        """Perform semantic search using ChromaDB."""
        start_time = time.time()
        
        # Perform search
        results = self.search_engine.search(
            query=query,
            max_results=limit + offset,
            similarity_threshold=similarity_threshold,
            filters=filters
        )
        
        # Apply offset
        if offset > 0:
            results = results[offset:]
        
        # Limit results
        results = results[:limit]
        
        # Format response
        formatted_results = []
        for r in results:
            formatted_results.append({
                "id": r.metadata.get("document_id", ""),
                "content": r.content[:500],  # Truncate for response
                "source": r.source,
                "score": r.score,
                "metadata": r.metadata,
                "highlights": self._extract_highlights(r.content, query)
            })
        
        execution_time = time.time() - start_time
        
        return {
            "results": formatted_results,
            "total_count": len(results),
            "execution_time": execution_time,
            "query": query
        }
    
    async def get_suggestions(self, partial_query: str) -> List[str]:
        """Get search suggestions based on partial query."""
        # This could be enhanced with actual suggestion logic
        # For now, return common ERCOT terms that match
        common_terms = [
            "ERCOT", "NPRR", "NOGRR", "battery", "storage",
            "market", "protocol", "energy", "ancillary", "services",
            "real-time", "day-ahead", "settlement", "compliance"
        ]
        
        suggestions = [
            term for term in common_terms 
            if partial_query.lower() in term.lower()
        ]
        
        return suggestions[:5]
    
    async def find_similar(
        self,
        document_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find documents similar to a given document."""
        # Get the document's embedding from ChromaDB
        # Then search for similar documents
        # This requires implementing in the search_engine
        
        # Placeholder implementation
        return []
    
    def _extract_highlights(
        self,
        content: str,
        query: str,
        context_words: int = 10
    ) -> List[str]:
        """Extract highlighted snippets from content."""
        highlights = []
        query_words = query.lower().split()
        content_lower = content.lower()
        
        for word in query_words:
            if word in content_lower:
                # Find word position and extract context
                pos = content_lower.find(word)
                if pos != -1:
                    start = max(0, pos - 50)
                    end = min(len(content), pos + 50 + len(word))
                    highlight = content[start:end]
                    if start > 0:
                        highlight = "..." + highlight
                    if end < len(content):
                        highlight = highlight + "..."
                    highlights.append(highlight)
        
        return highlights[:3]  # Return top 3 highlights
```

### Indexing Router
```python
# apps/search-api/routers/indexing.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from services.index_service import IndexService

router = APIRouter()
index_service = IndexService()

class IndexRequest(BaseModel):
    type: str = "incremental"  # "full" or "incremental"
    directories: Optional[List[str]] = None
    force: bool = False

class IndexResponse(BaseModel):
    status: str
    message: str
    task_id: Optional[str] = None

@router.post("/update", response_model=IndexResponse)
async def update_index(
    request: IndexRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger document indexing.
    
    - **type**: "incremental" for new/changed files, "full" for complete reindex
    - **directories**: Specific directories to index (optional)
    - **force**: Force reindex even if files haven't changed
    """
    try:
        if request.type == "full":
            background_tasks.add_task(
                index_service.full_reindex,
                request.directories,
                request.force
            )
            return IndexResponse(
                status="started",
                message="Full reindex started in background"
            )
        else:
            background_tasks.add_task(
                index_service.incremental_update,
                request.directories
            )
            return IndexResponse(
                status="started",
                message="Incremental update started in background"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_index_status():
    """Get current index status and statistics."""
    try:
        status = await index_service.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clear")
async def clear_index():
    """Clear the entire index (requires confirmation)."""
    try:
        result = await index_service.clear_index()
        return {"status": "success", "message": "Index cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Deployment

#### Dockerfile
```dockerfile
# apps/search-api/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy energy-data-search
COPY ../../energy-data-search /app/energy-data-search

# Copy API code
COPY . /app/search-api

WORKDIR /app/search-api

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

#### Requirements
```txt
# apps/search-api/requirements.txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-multipart==0.0.6

# Include energy-data-search dependencies
chromadb>=1.0.20
langchain>=0.3.27
langchain-chroma>=0.2.5
langchain-huggingface>=0.3.1
sentence-transformers>=5.1.0
pypdf>=6.0.0
python-dotenv>=1.1.1
```

## Integration with Next.js

### API Client
```typescript
// lib/search-api.ts
const SEARCH_API_URL = process.env.SEARCH_API_URL || 'http://localhost:8000';

export async function searchDocuments(
  query: string,
  options?: SearchOptions
): Promise<SearchResponse> {
  const response = await fetch(`${SEARCH_API_URL}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      limit: options?.limit || 20,
      filters: options?.filters,
      similarity_threshold: options?.threshold || 0.3
    })
  });
  
  if (!response.ok) {
    throw new Error('Search failed');
  }
  
  return response.json();
}

export async function triggerIndexUpdate(
  type: 'full' | 'incremental' = 'incremental'
): Promise<void> {
  const response = await fetch(`${SEARCH_API_URL}/index/update`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type })
  });
  
  if (!response.ok) {
    throw new Error('Index update failed');
  }
}

export async function getIndexStatus(): Promise<IndexStatus> {
  const response = await fetch(`${SEARCH_API_URL}/index/status`);
  
  if (!response.ok) {
    throw new Error('Failed to get index status');
  }
  
  return response.json();
}
```

## Development Setup

### Local Development
```bash
# Start the API locally
cd apps/search-api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Or with Docker
docker build -t search-api .
docker run -p 8000:8000 \
  -v $(pwd)/../../energy-data-search:/app/energy-data-search \
  -v /pool/ssd8tb/data/iso/ERCOT:/data:ro \
  search-api
```

### Environment Variables
```env
# apps/search-api/.env
SOURCE_DATA_DIR=/pool/ssd8tb/data/iso/ERCOT
CHROMA_PERSIST_DIR=/app/data/chroma_db
CORS_ORIGINS=["http://localhost:3000"]
PORT=8000
```

## Testing

### API Tests
```python
# apps/search-api/tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_search():
    response = client.post("/search", json={
        "query": "ERCOT market rules",
        "limit": 10
    })
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) <= 10

def test_search_with_filters():
    response = client.post("/search", json={
        "query": "battery storage",
        "filters": {"type": "NPRR"},
        "limit": 5
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) <= 5
```

## Monitoring

### Health Checks
```python
# apps/search-api/routers/health.py
from fastapi import APIRouter
from datetime import datetime
import psutil

router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/detailed")
async def detailed_health():
    """Detailed health check with system metrics."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent
        },
        "chromadb": {
            "connected": True,  # Add actual check
            "collection_exists": True  # Add actual check
        }
    }
```

## Performance Optimization

### Caching
- Consider adding Redis for caching frequent queries
- Cache search results for 5 minutes
- Cache suggestions for 1 hour

### Connection Pooling
- Reuse ChromaDB client connection
- Implement connection health checks

### Async Processing
- Use BackgroundTasks for indexing
- Consider Celery for heavy processing

## Security

### API Authentication
- Add API key validation for production
- Rate limiting per IP/user
- Input validation with Pydantic

### Data Access
- Read-only access to source documents
- Sanitize user inputs
- Log all API requests

## Deployment to Production

### Docker Compose
```yaml
# docker-compose.yml
services:
  search-api:
    build: ./apps/search-api
    ports:
      - "8000:8000"
    volumes:
      - ./energy-data-search:/app/energy-data-search
      - chroma_data:/app/data/chroma_db
      - /pool/ssd8tb/data/iso/ERCOT:/data:ro
    environment:
      - SOURCE_DATA_DIR=/data
      - CHROMA_PERSIST_DIR=/app/data/chroma_db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  chroma_data:
```