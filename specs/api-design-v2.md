# AI Knowledge Base - API Design Specification (v2)

## Overview
Simplified API architecture using Next.js API routes and a Python FastAPI service for ChromaDB operations. No GraphQL, no tRPC, no unnecessary complexity.

## API Architecture

### Design Principles
- **Simple REST**: Standard Next.js API routes
- **Python Integration**: FastAPI wrapper for ChromaDB
- **Streaming Support**: Server-Sent Events for AI responses
- **Type Safety**: TypeScript + Zod validation
- **Aligned with Battalion**: Same patterns as existing platform

## Next.js API Routes

### 1. Search API

#### POST `/api/search`
Search documents using ChromaDB.

```typescript
// Request
interface SearchRequest {
  query: string;
  filters?: {
    documentType?: string[];
    dateRange?: { start: Date; end: Date };
    source?: string[];
    tags?: string[];
  };
  limit?: number;  // Default: 20
  offset?: number; // For pagination
}

// Response
interface SearchResponse {
  results: Array<{
    id: string;
    content: string;
    source: string;
    score: number;
    metadata: Record<string, any>;
    highlights: string[];
  }>;
  totalCount: number;
  executionTime: number;
}

// Implementation
export async function POST(request: Request) {
  const body = await request.json();
  const validated = searchSchema.parse(body);
  
  // Call Python search API
  const pythonResponse = await fetch('http://localhost:8000/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(validated)
  });
  
  const results = await pythonResponse.json();
  
  // Enrich with PostgreSQL metadata
  const enrichedResults = await prisma.document.findMany({
    where: {
      chromaId: {
        in: results.results.map(r => r.id)
      }
    }
  });
  
  // Record search in history
  await prisma.searchHistory.create({
    data: {
      query: validated.query,
      userId: session.user.id,
      resultCount: results.results.length
    }
  });
  
  return NextResponse.json(results);
}
```

#### GET `/api/search/suggestions`
Get search suggestions based on partial query.

```typescript
// Query params: ?q=partial_query
// Response
{
  suggestions: string[];
  recentSearches: string[];
}
```

#### GET `/api/search/history`
Get user's search history.

```typescript
// Response
{
  searches: Array<{
    id: string;
    query: string;
    timestamp: Date;
    resultCount: number;
  }>;
}
```

### 2. Document API

#### GET `/api/documents`
List documents with metadata from PostgreSQL.

```typescript
// Query params: ?type=NPRR&status=active&page=1&limit=20
// Response
{
  documents: Array<{
    id: string;
    title: string;
    type: string;
    source: string;
    createdAt: Date;
    tags: string[];
    status: string;
  }>;
  pagination: {
    page: number;
    limit: number;
    total: number;
  };
}
```

#### GET `/api/documents/[id]`
Get single document details.

```typescript
// Response
{
  document: {
    id: string;
    title: string;
    content: string; // From ChromaDB
    metadata: Record<string, any>;
    s3Url: string;
    annotations: Annotation[];
  };
}
```

#### POST `/api/documents/[id]/annotate`
Add annotation to document.

```typescript
// Request
{
  text: string;
  position: { start: number; end: number };
  type: 'note' | 'highlight' | 'question';
}

// Response
{
  annotation: {
    id: string;
    text: string;
    userId: string;
    createdAt: Date;
  };
}
```

#### POST `/api/documents/index`
Trigger reindexing of documents.

```typescript
// Request
{
  type: 'full' | 'incremental';
  directories?: string[];
}

// Response
{
  status: 'started' | 'in_progress' | 'completed';
  stats: {
    filesProcessed: number;
    newDocuments: number;
    updatedDocuments: number;
  };
}
```

### 3. AI Chat API

#### POST `/api/chat`
Send message to AI with streaming response.

```typescript
// Request
{
  message: string;
  context?: string[]; // Document IDs for context
  model?: 'gpt-4' | 'gpt-3.5-turbo';
}

// Response: Server-Sent Events stream
// Each event:
{
  type: 'token' | 'done' | 'error';
  content?: string;
  usage?: { prompt: number; completion: number };
}

// Implementation with streaming
export async function POST(request: Request) {
  const { message, context } = await request.json();
  
  // Get context documents from ChromaDB if needed
  let contextDocs = [];
  if (context?.length) {
    const searchResponse = await fetch('http://localhost:8000/get_documents', {
      method: 'POST',
      body: JSON.stringify({ ids: context })
    });
    contextDocs = await searchResponse.json();
  }
  
  // Create streaming response
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      const completion = await openai.chat.completions.create({
        model: 'gpt-4',
        messages: [
          { role: 'system', content: 'You are an ERCOT market expert.' },
          ...contextDocs.map(doc => ({
            role: 'system',
            content: `Context: ${doc.content.slice(0, 2000)}`
          })),
          { role: 'user', content: message }
        ],
        stream: true,
      });
      
      for await (const chunk of completion) {
        const text = chunk.choices[0]?.delta?.content || '';
        const event = `data: ${JSON.stringify({ type: 'token', content: text })}\n\n`;
        controller.enqueue(encoder.encode(event));
      }
      
      controller.enqueue(encoder.encode('data: {"type": "done"}\n\n'));
      controller.close();
    },
  });
  
  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}
```

#### GET `/api/chat/history`
Get chat history for current user.

```typescript
// Response
{
  conversations: Array<{
    id: string;
    messages: Message[];
    createdAt: Date;
    updatedAt: Date;
  }>;
}
```

### 4. Analytics API

#### GET `/api/analytics/dashboard`
Get dashboard metrics.

```typescript
// Query params: ?period=7d
// Response
{
  metrics: {
    totalSearches: number;
    uniqueUsers: number;
    documentsViewed: number;
    aiInteractions: number;
  };
  trends: {
    searches: Array<{ date: string; count: number }>;
    documents: Array<{ date: string; count: number }>;
  };
  topSearches: Array<{ query: string; count: number }>;
  topDocuments: Array<{ title: string; views: number }>;
}
```

#### POST `/api/analytics/track`
Track user events.

```typescript
// Request
{
  event: 'search' | 'view_document' | 'download' | 'ai_chat';
  data: Record<string, any>;
}

// Response
{
  success: boolean;
}
```

### 5. User API

#### GET `/api/user/profile`
Get current user profile.

```typescript
// Response
{
  user: {
    id: string;
    email: string;
    name: string;
    preferences: UserPreferences;
    role: string;
  };
}
```

#### PATCH `/api/user/preferences`
Update user preferences.

```typescript
// Request
{
  theme?: 'light' | 'dark';
  defaultSearchFilters?: SearchFilters;
  emailNotifications?: boolean;
}

// Response
{
  preferences: UserPreferences;
}
```

## Python FastAPI Service

### Search API Wrapper

```python
# apps/search-api/main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
import os

# Add energy-data-search to path
sys.path.append('/app/energy-data-search/src')
from energy_data_search.query.search_engine import EnergyDataSearchEngine
from energy_data_search.config import Config

app = FastAPI(title="AI Knowledge Base Search API")

# CORS for Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize search engine
config = Config()
search_engine = EnergyDataSearchEngine(config)

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 20
    filters: Optional[Dict[str, Any]] = None
    document_ids: Optional[List[str]] = None

class IndexRequest(BaseModel):
    type: str = "incremental"  # "full" or "incremental"
    directories: Optional[List[str]] = None

@app.post("/search")
async def search(request: SearchRequest):
    """Search documents using ChromaDB."""
    try:
        results = search_engine.search(
            query=request.query,
            max_results=request.limit,
            filters=request.filters
        )
        
        return {
            "results": [
                {
                    "id": r.metadata.get("id"),
                    "content": r.content,
                    "source": r.source,
                    "score": r.score,
                    "metadata": r.metadata,
                    "highlights": []  # TODO: Add highlighting
                }
                for r in results
            ],
            "totalCount": len(results),
            "executionTime": 0  # TODO: Add timing
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index")
async def index_documents(
    request: IndexRequest,
    background_tasks: BackgroundTasks
):
    """Trigger document indexing."""
    if request.type == "full":
        # Clear and rebuild index
        background_tasks.add_task(rebuild_index, request.directories)
    else:
        # Incremental update
        background_tasks.add_task(update_index, request.directories)
    
    return {
        "status": "started",
        "type": request.type
    }

@app.get("/stats")
async def get_statistics():
    """Get index statistics."""
    stats = search_engine.get_statistics()
    return {
        "totalDocuments": stats.get("total_documents", 0),
        "totalChunks": stats.get("total_chunks", 0),
        "lastUpdated": stats.get("last_updated"),
        "indexSize": stats.get("index_size_mb", 0)
    }

@app.post("/get_documents")
async def get_documents(ids: List[str]):
    """Get specific documents by ID."""
    documents = []
    for doc_id in ids:
        result = search_engine.get_document(doc_id)
        if result:
            documents.append({
                "id": doc_id,
                "content": result.content,
                "metadata": result.metadata
            })
    return documents

async def rebuild_index(directories: Optional[List[str]] = None):
    """Background task to rebuild index."""
    if directories:
        for directory in directories:
            search_engine.index_directory(directory)
    else:
        search_engine.index_all_sources()

async def update_index(directories: Optional[List[str]] = None):
    """Background task for incremental index update."""
    # Use existing incremental indexing logic
    search_engine.update_index()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
```

## Authentication & Authorization

### NextAuth.js Middleware
```typescript
// middleware.ts
import { withAuth } from "next-auth/middleware";

export default withAuth({
  callbacks: {
    authorized({ req, token }) {
      // Public routes
      if (req.nextUrl.pathname.startsWith("/api/public")) {
        return true;
      }
      
      // Require authentication for all other routes
      return !!token;
    },
  },
});

export const config = {
  matcher: ["/api/:path*", "/dashboard/:path*"],
};
```

### API Key Authentication (for service-to-service)
```typescript
// lib/api-auth.ts
export async function validateApiKey(request: Request) {
  const apiKey = request.headers.get('X-API-Key');
  
  if (!apiKey) {
    return { valid: false, error: 'Missing API key' };
  }
  
  const keyRecord = await prisma.apiKey.findFirst({
    where: { 
      key: hashApiKey(apiKey),
      revokedAt: null
    }
  });
  
  if (!keyRecord) {
    return { valid: false, error: 'Invalid API key' };
  }
  
  // Update last used
  await prisma.apiKey.update({
    where: { id: keyRecord.id },
    data: { lastUsedAt: new Date() }
  });
  
  return { valid: true, userId: keyRecord.userId };
}
```

## Error Handling

### Standard Error Response
```typescript
interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: any;
  };
  timestamp: string;
}

// Error handler
export function handleApiError(error: unknown): NextResponse {
  console.error('API Error:', error);
  
  if (error instanceof ZodError) {
    return NextResponse.json({
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Invalid request data',
        details: error.errors
      },
      timestamp: new Date().toISOString()
    }, { status: 400 });
  }
  
  if (error instanceof PrismaClientKnownRequestError) {
    return NextResponse.json({
      error: {
        code: 'DATABASE_ERROR',
        message: 'Database operation failed',
        details: error.code
      },
      timestamp: new Date().toISOString()
    }, { status: 500 });
  }
  
  return NextResponse.json({
    error: {
      code: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred'
    },
    timestamp: new Date().toISOString()
  }, { status: 500 });
}
```

## Rate Limiting

### Simple Rate Limiting with Upstash (or in-memory)
```typescript
// lib/rate-limit.ts
import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(100, "1 h"),
});

export async function checkRateLimit(identifier: string) {
  const { success, limit, reset, remaining } = await ratelimit.limit(
    identifier
  );
  
  return { success, limit, reset, remaining };
}

// Usage in API route
export async function POST(request: Request) {
  const ip = request.headers.get("x-forwarded-for") ?? "127.0.0.1";
  const { success } = await checkRateLimit(ip);
  
  if (!success) {
    return NextResponse.json(
      { error: "Rate limit exceeded" },
      { status: 429 }
    );
  }
  
  // Process request...
}
```

## Caching Strategy

### React Query (Client-side)
```typescript
// Automatic caching with React Query
const { data, isLoading } = useQuery({
  queryKey: ['search', query],
  queryFn: () => searchDocuments(query),
  staleTime: 5 * 60 * 1000,      // Consider data fresh for 5 minutes
  cacheTime: 10 * 60 * 1000,     // Keep in cache for 10 minutes
  refetchOnWindowFocus: false,
});
```

### Next.js Data Cache (Server-side)
```typescript
// Cached server component
export default async function DocumentList() {
  // This will be cached by Next.js
  const documents = await prisma.document.findMany({
    take: 20,
    orderBy: { createdAt: 'desc' }
  });
  
  return <DocumentGrid documents={documents} />;
}

// With revalidation
export const revalidate = 3600; // Revalidate every hour
```

## Monitoring & Logging

### Structured Logging
```typescript
// lib/logger.ts
import winston from 'winston';

export const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.Console({
      format: winston.format.simple(),
    }),
  ],
});

// Usage in API
logger.info('Search performed', {
  query,
  userId: session.user.id,
  resultCount: results.length,
  executionTime
});
```

### Performance Monitoring
```typescript
// lib/monitoring.ts
export async function trackApiCall(
  endpoint: string,
  method: string,
  duration: number,
  status: number
) {
  await prisma.apiMetric.create({
    data: {
      endpoint,
      method,
      duration,
      status,
      timestamp: new Date()
    }
  });
}
```

## Testing

### API Route Testing
```typescript
// __tests__/api/search.test.ts
import { POST } from '@/app/api/search/route';
import { prismaMock } from '@/lib/prisma-mock';

describe('Search API', () => {
  it('should return search results', async () => {
    const request = new Request('http://localhost:3000/api/search', {
      method: 'POST',
      body: JSON.stringify({
        query: 'ERCOT market rules',
        limit: 10
      })
    });
    
    const response = await POST(request);
    const data = await response.json();
    
    expect(response.status).toBe(200);
    expect(data.results).toBeInstanceOf(Array);
    expect(data.results.length).toBeLessThanOrEqual(10);
  });
});
```

## Security Considerations

1. **Input Validation**: Zod schemas for all inputs
2. **SQL Injection**: Prisma prevents SQL injection
3. **XSS Prevention**: React escapes content by default
4. **CSRF Protection**: NextAuth.js CSRF tokens
5. **Rate Limiting**: Prevent abuse
6. **API Keys**: For service-to-service auth
7. **Content Security Policy**: Configured in Next.js