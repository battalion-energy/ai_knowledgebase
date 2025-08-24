# API Validation & OpenAPI Specification

## Overview
Complete API validation using Zod schemas with automatic OpenAPI documentation generation for both Next.js and Python FastAPI services.

## Next.js API with Zod & OpenAPI

### Dependencies
```json
{
  "dependencies": {
    "zod": "^3.24.1",
    "zod-to-openapi": "^6.0.0",
    "@asteasolutions/zod-to-openapi": "^6.0.0",
    "swagger-ui-react": "^5.11.0",
    "next-swagger-doc": "^0.4.0"
  }
}
```

### Zod Schemas with OpenAPI

#### Base Schemas
```typescript
// lib/validation/schemas.ts
import { z } from 'zod';
import { extendZodWithOpenApi } from '@asteasolutions/zod-to-openapi';

// Extend Zod with OpenAPI support
extendZodWithOpenApi(z);

// ============================================
// Common Schemas
// ============================================

export const PaginationSchema = z.object({
  page: z.number().int().min(1).default(1).openapi({ example: 1 }),
  limit: z.number().int().min(1).max(100).default(20).openapi({ example: 20 }),
  total: z.number().int().min(0).openapi({ example: 100 })
});

export const DateRangeSchema = z.object({
  start: z.coerce.date().openapi({ example: '2024-01-01T00:00:00Z' }),
  end: z.coerce.date().openapi({ example: '2024-12-31T23:59:59Z' })
}).openapi({ description: 'Date range for filtering' });

export const ErrorResponseSchema = z.object({
  error: z.object({
    code: z.string().openapi({ example: 'VALIDATION_ERROR' }),
    message: z.string().openapi({ example: 'Invalid request data' }),
    details: z.any().optional()
  }),
  timestamp: z.string().datetime()
}).openapi({ description: 'Standard error response' });

// ============================================
// Search API Schemas
// ============================================

export const SearchFiltersSchema = z.object({
  documentType: z.array(z.enum(['NPRR', 'NOGRR', 'PROTOCOL', 'GUIDE', 'REPORT', 'TARIFF', 'REGULATORY', 'OTHER'])).optional(),
  dateRange: DateRangeSchema.optional(),
  source: z.array(z.string()).optional(),
  tags: z.array(z.string()).optional()
}).openapi({ description: 'Search filters' });

export const SearchRequestSchema = z.object({
  query: z.string().min(1).max(500).openapi({ 
    example: 'ERCOT battery storage requirements',
    description: 'Search query text'
  }),
  filters: SearchFiltersSchema.optional(),
  limit: z.number().int().min(1).max(100).default(20),
  offset: z.number().int().min(0).default(0),
  similarityThreshold: z.number().min(0).max(1).default(0.3).openapi({
    description: 'Minimum similarity score for results'
  })
}).openapi({
  description: 'Search request parameters',
  example: {
    query: 'battery energy storage',
    limit: 20,
    filters: {
      documentType: ['NPRR', 'NOGRR']
    }
  }
});

export const SearchResultSchema = z.object({
  id: z.string().openapi({ example: 'doc_12345' }),
  content: z.string().openapi({ 
    example: 'This document describes battery energy storage requirements...' 
  }),
  source: z.string().openapi({ example: '/documents/NPRR1234.pdf' }),
  score: z.number().min(0).max(1).openapi({ example: 0.85 }),
  metadata: z.record(z.any()),
  highlights: z.array(z.string())
}).openapi({ description: 'Individual search result' });

export const SearchResponseSchema = z.object({
  results: z.array(SearchResultSchema),
  totalCount: z.number().int(),
  executionTime: z.number(),
  query: z.string()
}).openapi({ description: 'Search response with results' });

// ============================================
// Document API Schemas
// ============================================

export const DocumentSchema = z.object({
  id: z.string(),
  chromaId: z.string(),
  title: z.string(),
  type: z.enum(['NPRR', 'NOGRR', 'PROTOCOL', 'GUIDE', 'REPORT', 'TARIFF', 'REGULATORY', 'OTHER']),
  source: z.string(),
  sourceUrl: z.string().url().nullable(),
  s3Key: z.string().nullable(),
  ktc: z.string().nullable(),
  status: z.enum(['ACTIVE', 'DRAFT', 'ARCHIVED', 'DELETED']),
  visibility: z.enum(['PUBLIC', 'PRIVATE', 'RESTRICTED']),
  version: z.number().int(),
  fileHash: z.string(),
  fileSize: z.number().int().nullable(),
  pageCount: z.number().int().nullable(),
  summary: z.string().nullable(),
  tags: z.array(z.string()),
  effectiveDate: z.coerce.date().nullable(),
  reviewDate: z.coerce.date().nullable(),
  createdAt: z.coerce.date(),
  updatedAt: z.coerce.date()
}).openapi({ description: 'Document model' });

export const AnnotationSchema = z.object({
  text: z.string().min(1).max(5000),
  position: z.object({
    page: z.number().int().optional(),
    start: z.number().int(),
    end: z.number().int()
  }),
  type: z.enum(['note', 'highlight', 'question', 'correction'])
}).openapi({ description: 'Document annotation' });

// ============================================
// Chat API Schemas
// ============================================

export const ChatRequestSchema = z.object({
  message: z.string().min(1).max(4000).openapi({
    example: 'What are the requirements for battery storage in ERCOT?'
  }),
  context: z.array(z.string()).optional().openapi({
    description: 'Document IDs to use as context'
  }),
  model: z.enum(['gpt-4', 'gpt-3.5-turbo']).default('gpt-4'),
  stream: z.boolean().default(true)
}).openapi({ description: 'Chat request to AI assistant' });

export const ChatMessageSchema = z.object({
  role: z.enum(['user', 'assistant', 'system']),
  content: z.string(),
  timestamp: z.coerce.date()
}).openapi({ description: 'Chat message' });

// ============================================
// Analytics API Schemas
// ============================================

export const AnalyticsEventSchema = z.object({
  event: z.enum(['search', 'view_document', 'download', 'annotation', 'ai_chat']),
  data: z.record(z.any()),
  timestamp: z.coerce.date().optional()
}).openapi({ description: 'Analytics event to track' });

export const DashboardMetricsSchema = z.object({
  period: z.enum(['1d', '7d', '30d', '90d']).default('7d')
}).openapi({ description: 'Dashboard metrics request' });

export const MetricsResponseSchema = z.object({
  metrics: z.object({
    totalSearches: z.number().int(),
    uniqueUsers: z.number().int(),
    documentsViewed: z.number().int(),
    aiInteractions: z.number().int()
  }),
  trends: z.object({
    searches: z.array(z.object({
      date: z.string(),
      count: z.number().int()
    })),
    documents: z.array(z.object({
      date: z.string(),
      count: z.number().int()
    }))
  }),
  topSearches: z.array(z.object({
    query: z.string(),
    count: z.number().int()
  })),
  topDocuments: z.array(z.object({
    title: z.string(),
    views: z.number().int()
  }))
}).openapi({ description: 'Dashboard metrics response' });
```

### API Route with Validation
```typescript
// app/api/search/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { SearchRequestSchema, SearchResponseSchema, ErrorResponseSchema } from '@/lib/validation/schemas';
import { ZodError } from 'zod';

export async function POST(request: NextRequest) {
  try {
    // Parse and validate request body
    const body = await request.json();
    const validatedData = SearchRequestSchema.parse(body);
    
    // Call Python search API with validated data
    const pythonResponse = await fetch('http://localhost:8000/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(validatedData)
    });
    
    const results = await pythonResponse.json();
    
    // Validate response
    const validatedResponse = SearchResponseSchema.parse(results);
    
    return NextResponse.json(validatedResponse);
    
  } catch (error) {
    if (error instanceof ZodError) {
      const errorResponse = ErrorResponseSchema.parse({
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Invalid request data',
          details: error.errors
        },
        timestamp: new Date().toISOString()
      });
      
      return NextResponse.json(errorResponse, { status: 400 });
    }
    
    const errorResponse = ErrorResponseSchema.parse({
      error: {
        code: 'INTERNAL_ERROR',
        message: 'An unexpected error occurred'
      },
      timestamp: new Date().toISOString()
    });
    
    return NextResponse.json(errorResponse, { status: 500 });
  }
}
```

### OpenAPI Documentation Generation
```typescript
// lib/openapi/generator.ts
import { OpenAPIRegistry, OpenApiGeneratorV31 } from '@asteasolutions/zod-to-openapi';
import * as schemas from '@/lib/validation/schemas';

export function generateOpenAPIDocument() {
  const registry = new OpenAPIRegistry();
  
  // Register schemas
  registry.register('SearchRequest', schemas.SearchRequestSchema);
  registry.register('SearchResponse', schemas.SearchResponseSchema);
  registry.register('Document', schemas.DocumentSchema);
  registry.register('ErrorResponse', schemas.ErrorResponseSchema);
  
  // Define API paths
  registry.registerPath({
    method: 'post',
    path: '/api/search',
    description: 'Search documents using semantic search',
    summary: 'Search documents',
    tags: ['Search'],
    request: {
      body: {
        content: {
          'application/json': {
            schema: schemas.SearchRequestSchema
          }
        }
      }
    },
    responses: {
      200: {
        description: 'Successful search',
        content: {
          'application/json': {
            schema: schemas.SearchResponseSchema
          }
        }
      },
      400: {
        description: 'Invalid request',
        content: {
          'application/json': {
            schema: schemas.ErrorResponseSchema
          }
        }
      }
    }
  });
  
  // Generate OpenAPI document
  const generator = new OpenApiGeneratorV31(registry.definitions);
  
  return generator.generateDocument({
    openapi: '3.1.0',
    info: {
      title: 'AI Knowledge Base API',
      version: '1.0.0',
      description: 'API for searching and managing ERCOT documents'
    },
    servers: [
      {
        url: 'http://localhost:3000',
        description: 'Development server'
      },
      {
        url: 'https://api.battalion.energy',
        description: 'Production server'
      }
    ]
  });
}
```

### Swagger UI Page
```typescript
// app/api-docs/page.tsx
'use client';

import SwaggerUI from 'swagger-ui-react';
import 'swagger-ui-react/swagger-ui.css';
import { useEffect, useState } from 'react';

export default function ApiDocsPage() {
  const [spec, setSpec] = useState(null);
  
  useEffect(() => {
    fetch('/api/openapi.json')
      .then(res => res.json())
      .then(setSpec);
  }, []);
  
  if (!spec) return <div>Loading API documentation...</div>;
  
  return (
    <div className="min-h-screen">
      <SwaggerUI 
        spec={spec}
        tryItOutEnabled={true}
        persistAuthorization={true}
      />
    </div>
  );
}

// app/api/openapi.json/route.ts
import { NextResponse } from 'next/server';
import { generateOpenAPIDocument } from '@/lib/openapi/generator';

export async function GET() {
  const document = generateOpenAPIDocument();
  return NextResponse.json(document);
}
```

## Python FastAPI with Automatic OpenAPI

FastAPI automatically generates OpenAPI documentation from Pydantic models:

### Enhanced Pydantic Models with OpenAPI
```python
# apps/search-api/models/schemas.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    NPRR = "NPRR"
    NOGRR = "NOGRR"
    PROTOCOL = "PROTOCOL"
    GUIDE = "GUIDE"
    REPORT = "REPORT"
    TARIFF = "TARIFF"
    REGULATORY = "REGULATORY"
    OTHER = "OTHER"

class SearchFilters(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "document_type": ["NPRR", "NOGRR"],
            "tags": ["battery", "storage"]
        }
    })
    
    document_type: Optional[List[DocumentType]] = Field(
        None,
        description="Filter by document types"
    )
    date_range: Optional[Dict[str, datetime]] = Field(
        None,
        description="Date range with 'start' and 'end' keys"
    )
    source: Optional[List[str]] = Field(
        None,
        description="Filter by document sources"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Filter by tags"
    )

class SearchRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "query": "battery energy storage requirements",
            "limit": 20,
            "filters": {
                "document_type": ["NPRR"]
            }
        }
    })
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query text"
    )
    limit: Optional[int] = Field(
        20,
        ge=1,
        le=100,
        description="Maximum number of results"
    )
    offset: Optional[int] = Field(
        0,
        ge=0,
        description="Pagination offset"
    )
    filters: Optional[SearchFilters] = Field(
        None,
        description="Search filters"
    )
    document_ids: Optional[List[str]] = Field(
        None,
        description="Limit search to specific document IDs"
    )
    similarity_threshold: Optional[float] = Field(
        0.3,
        ge=0,
        le=1,
        description="Minimum similarity score (0-1)"
    )

class SearchResult(BaseModel):
    id: str = Field(..., description="Document ID")
    content: str = Field(..., description="Document content excerpt")
    source: str = Field(..., description="Document source path")
    score: float = Field(..., ge=0, le=1, description="Relevance score")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    highlights: List[str] = Field(..., description="Highlighted text snippets")

class SearchResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "results": [
                {
                    "id": "doc_12345",
                    "content": "Battery energy storage systems must...",
                    "source": "/documents/NPRR1234.pdf",
                    "score": 0.85,
                    "metadata": {"type": "NPRR", "date": "2024-01-15"},
                    "highlights": ["battery energy storage"]
                }
            ],
            "total_count": 42,
            "execution_time": 0.235,
            "query": "battery storage"
        }
    })
    
    results: List[SearchResult] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total number of results")
    execution_time: float = Field(..., description="Search execution time in seconds")
    query: str = Field(..., description="Original search query")

class ErrorResponse(BaseModel):
    error: Dict[str, Any] = Field(
        ...,
        description="Error details",
        json_schema_extra={
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request data",
                "details": ["Field 'query' is required"]
            }
        }
    )
    timestamp: datetime = Field(..., description="Error timestamp")
```

### FastAPI with Rich OpenAPI
```python
# apps/search-api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from models.schemas import SearchRequest, SearchResponse, ErrorResponse

app = FastAPI(
    title="AI Knowledge Base Search API",
    description="ChromaDB-powered semantic search for ERCOT documents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="AI Knowledge Base Search API",
        version="1.0.0",
        description="""
        ## Overview
        This API provides semantic search capabilities for ERCOT energy market documents.
        
        ## Features
        - Semantic search using ChromaDB embeddings
        - Document filtering by type, date, tags
        - Incremental indexing
        - Real-time search suggestions
        
        ## Authentication
        API key required for production use (header: X-API-Key)
        """,
        routes=app.routes,
        tags=[
            {
                "name": "search",
                "description": "Document search operations"
            },
            {
                "name": "indexing",
                "description": "Index management operations"
            },
            {
                "name": "health",
                "description": "Health check endpoints"
            }
        ]
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.post(
    "/search",
    response_model=SearchResponse,
    responses={
        200: {
            "description": "Successful search",
            "model": SearchResponse
        },
        400: {
            "description": "Invalid request",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    },
    tags=["search"],
    summary="Search documents",
    description="Perform semantic search across ERCOT documents using ChromaDB"
)
async def search_documents(request: SearchRequest):
    """
    Search for documents using semantic search.
    
    The search uses ChromaDB's vector embeddings to find semantically similar documents.
    You can filter results by document type, date range, source, and tags.
    """
    # Implementation...
    pass
```

## Type-Safe API Client Generation

### Generate TypeScript Client from OpenAPI
```typescript
// scripts/generate-api-client.ts
import { generateZodClientFromOpenAPI } from 'openapi-zod-client';
import fs from 'fs';

async function generateClient() {
  // Fetch OpenAPI spec from Python API
  const response = await fetch('http://localhost:8000/openapi.json');
  const openApiDoc = await response.json();
  
  // Generate Zod schemas and typed client
  const result = await generateZodClientFromOpenAPI({
    openApiDoc,
    distPath: './lib/api/generated',
    templatePath: './lib/api/templates'
  });
  
  console.log('Generated API client with Zod schemas');
}

generateClient();
```

### Using the Generated Client
```typescript
// lib/api/search-client.ts
import { z } from 'zod';
import { searchApi } from './generated/search-api';

// Type-safe API calls with automatic validation
export async function searchDocuments(query: string, options?: SearchOptions) {
  try {
    // Request is validated with Zod before sending
    const response = await searchApi.search({
      query,
      limit: options?.limit || 20,
      filters: options?.filters
    });
    
    // Response is validated with Zod after receiving
    return response.data;
  } catch (error) {
    if (error instanceof z.ZodError) {
      console.error('Validation error:', error.errors);
      throw new Error('Invalid API request or response');
    }
    throw error;
  }
}
```

## API Testing with Schema Validation

### Next.js API Route Tests
```typescript
// __tests__/api/search.test.ts
import { POST } from '@/app/api/search/route';
import { SearchRequestSchema, SearchResponseSchema } from '@/lib/validation/schemas';

describe('Search API', () => {
  it('validates request schema', async () => {
    const invalidRequest = {
      // Missing required 'query' field
      limit: 10
    };
    
    const request = new Request('http://localhost:3000/api/search', {
      method: 'POST',
      body: JSON.stringify(invalidRequest)
    });
    
    const response = await POST(request);
    expect(response.status).toBe(400);
    
    const error = await response.json();
    expect(error.error.code).toBe('VALIDATION_ERROR');
  });
  
  it('returns valid response schema', async () => {
    const validRequest = SearchRequestSchema.parse({
      query: 'test query',
      limit: 5
    });
    
    const request = new Request('http://localhost:3000/api/search', {
      method: 'POST',
      body: JSON.stringify(validRequest)
    });
    
    const response = await POST(request);
    const data = await response.json();
    
    // This will throw if response doesn't match schema
    const validatedResponse = SearchResponseSchema.parse(data);
    expect(validatedResponse.results).toBeInstanceOf(Array);
  });
});
```

### Python API Tests with Schema Validation
```python
# apps/search-api/tests/test_schemas.py
import pytest
from pydantic import ValidationError
from models.schemas import SearchRequest, SearchResponse

def test_search_request_validation():
    # Valid request
    valid = SearchRequest(
        query="test query",
        limit=10
    )
    assert valid.query == "test query"
    
    # Invalid request - empty query
    with pytest.raises(ValidationError):
        SearchRequest(query="", limit=10)
    
    # Invalid request - limit too high
    with pytest.raises(ValidationError):
        SearchRequest(query="test", limit=1000)

def test_search_response_schema():
    response = SearchResponse(
        results=[],
        total_count=0,
        execution_time=0.1,
        query="test"
    )
    
    # Export as OpenAPI schema
    schema = response.model_json_schema()
    assert "results" in schema["properties"]
```

## Benefits of Zod + OpenAPI

1. **Type Safety**: End-to-end type safety from API to client
2. **Validation**: Automatic request/response validation
3. **Documentation**: Auto-generated, always up-to-date API docs
4. **Client Generation**: Generate typed clients for any language
5. **Testing**: Schema-based testing ensures API contract
6. **Developer Experience**: IntelliSense and autocomplete
7. **Error Handling**: Consistent, typed error responses
8. **Versioning**: Easy to version APIs with schema changes