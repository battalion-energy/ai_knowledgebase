# AI Knowledge Base - Next.js Application Architecture (v2)

## Overview
A streamlined Next.js application for the ERCOT AI knowledge base, designed to integrate seamlessly with Battalion Platform's existing infrastructure while leveraging the existing ChromaDB search implementation.

## Core Architecture

### Technology Stack (Aligned with Battalion Platform)
- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript 5.3+
- **Styling**: Tailwind CSS 3.4+
- **State Management**: Zustand + React Query (TanStack Query v5)
- **Primary Database**: PostgreSQL with Prisma ORM
- **Vector Search**: ChromaDB (existing implementation)
- **Authentication**: NextAuth.js v4
- **UI Components**: Radix UI + Headless UI
- **Forms**: React Hook Form + Zod
- **Charts**: Recharts (same as Battalion)
- **File Storage**: AWS S3
- **Email**: AWS SES
- **AI Integration**: OpenAI API (already in Battalion)
- **Package Manager**: pnpm (monorepo with workspaces)

### Project Structure
```
ai-knowledge-base/
├── apps/
│   ├── web/                         # Next.js application
│   │   ├── app/                     # App Router
│   │   │   ├── (auth)/             # Protected routes
│   │   │   │   ├── dashboard/      # Main dashboard
│   │   │   │   ├── search/         # Search interface
│   │   │   │   ├── documents/      # Document management
│   │   │   │   ├── chat/           # AI chat interface
│   │   │   │   └── analytics/      # Analytics dashboard
│   │   │   ├── api/                # API routes
│   │   │   │   ├── search/         # ChromaDB search wrapper
│   │   │   │   ├── documents/      # Document operations
│   │   │   │   ├── chat/           # AI chat endpoints
│   │   │   │   └── analytics/      # Analytics endpoints
│   │   │   └── layout.tsx
│   │   ├── components/              # React components
│   │   ├── lib/                     # Utilities
│   │   └── prisma/                  # Database schema
│   │
│   └── search-api/                  # Python FastAPI wrapper
│       ├── main.py                  # FastAPI application
│       ├── routers/                 # API routes
│       └── requirements.txt
│
├── packages/                        # Shared packages
│   ├── ui/                         # Shared UI components
│   ├── types/                      # TypeScript types
│   └── utils/                      # Shared utilities
│
├── energy-data-search/              # Existing ChromaDB implementation
│   └── (existing structure)
│
└── ercot_code/                      # ERCOT Python scripts
    └── (existing structure)
```

## Hybrid Database Architecture

### PostgreSQL (via Prisma)
Handles all structured data and application state:
- User accounts and authentication
- Document metadata (title, source, date, tags)
- Search history and saved searches
- Annotations and comments
- Analytics events
- User preferences
- Access control and permissions

### ChromaDB (Existing Implementation)
Handles document search and embeddings:
- Vector embeddings for semantic search
- Full-text document content
- Document chunking and indexing
- Similarity search
- Already configured and working

### Integration Pattern
```typescript
// Example: Hybrid search combining both databases
async function hybridSearch(query: string, userId: string) {
  // 1. Record search in PostgreSQL
  const searchRecord = await prisma.searchHistory.create({
    data: { query, userId }
  });

  // 2. Get user's accessible documents from PostgreSQL
  const accessibleDocs = await prisma.document.findMany({
    where: { 
      OR: [
        { visibility: 'public' },
        { permissions: { some: { userId } } }
      ]
    },
    select: { id: true, chromaId: true }
  });

  // 3. Search in ChromaDB with document filtering
  const searchResults = await fetch('/api/search', {
    method: 'POST',
    body: JSON.stringify({
      query,
      documentIds: accessibleDocs.map(d => d.chromaId),
      limit: 20
    })
  });

  // 4. Enrich results with PostgreSQL metadata
  const enrichedResults = await enrichSearchResults(searchResults);
  
  return enrichedResults;
}
```

## Key Features

### 1. Document Search (Powered by ChromaDB)
- **Semantic Search**: Leverages existing ChromaDB vector search
- **Incremental Indexing**: Uses existing SHA256 change detection
- **Multi-format Support**: PDF, CSV, TXT, HTML, Markdown (already implemented)
- **Search API**: FastAPI wrapper around existing Python code
- **Metadata Enrichment**: PostgreSQL stores additional document metadata

### 2. AI Chat Interface
- **Streaming Responses**: Server-Sent Events (SSE) for real-time streaming
- **Context-Aware**: Includes relevant documents from ChromaDB
- **Conversation History**: Stored in PostgreSQL
- **Multiple Models**: Support for OpenAI GPT-4 (already in Battalion)
- **No WebSockets Required**: Simpler SSE implementation

### 3. Document Management
- **Metadata in PostgreSQL**: Tags, categories, permissions
- **Content in ChromaDB**: Full-text and embeddings
- **S3 Storage**: Original files stored in AWS S3
- **Version Control**: Document versions tracked in PostgreSQL
- **Annotations**: User notes stored in PostgreSQL

### 4. Analytics Dashboard
- **Usage Metrics**: Stored in PostgreSQL
- **Search Analytics**: Query patterns and popular content
- **Visualization**: Recharts (same as Battalion)
- **Export**: CSV/JSON export capabilities

## API Architecture

### Next.js API Routes (Not tRPC or GraphQL)
```typescript
// app/api/search/route.ts
export async function POST(request: Request) {
  const { query, filters } = await request.json();
  
  // Call Python search API
  const results = await searchAPI.search(query, filters);
  
  // Enrich with PostgreSQL data
  const enriched = await enrichResults(results);
  
  return NextResponse.json(enriched);
}

// app/api/chat/route.ts
export async function POST(request: Request) {
  const { message, context } = await request.json();
  
  // Stream response using SSE
  const stream = new ReadableStream({
    async start(controller) {
      const response = await openai.chat.completions.create({
        messages: [...],
        stream: true
      });
      
      for await (const chunk of response) {
        controller.enqueue(encoder.encode(
          `data: ${JSON.stringify(chunk)}\n\n`
        ));
      }
    }
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

### Python Search API (FastAPI Wrapper)
```python
# apps/search-api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from energy_data_search.query.search_engine import EnergyDataSearchEngine

app = FastAPI()
search_engine = EnergyDataSearchEngine()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/search")
async def search(query: str, limit: int = 20, filters: dict = None):
    results = search_engine.search(
        query=query,
        max_results=limit,
        filters=filters
    )
    return {"results": results}

@app.post("/index/update")
async def update_index():
    """Trigger incremental index update"""
    stats = search_engine.index_all_sources()
    return {"status": "success", "stats": stats}

@app.get("/stats")
async def get_stats():
    """Get index statistics"""
    stats = search_engine.get_statistics()
    return stats
```

## State Management

### Zustand Stores (Aligned with Battalion)
```typescript
// stores/searchStore.ts
interface SearchStore {
  query: string;
  results: SearchResult[];
  loading: boolean;
  filters: SearchFilters;
  search: (query: string) => Promise<void>;
  setFilters: (filters: SearchFilters) => void;
}

// stores/chatStore.ts
interface ChatStore {
  messages: Message[];
  streaming: boolean;
  sendMessage: (content: string) => Promise<void>;
  clearHistory: () => void;
}
```

### React Query for Server State
```typescript
// hooks/useDocuments.ts
export function useDocuments(filters?: DocumentFilters) {
  return useQuery({
    queryKey: ['documents', filters],
    queryFn: () => fetchDocuments(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// hooks/useSearch.ts
export function useSearch(query: string) {
  return useQuery({
    queryKey: ['search', query],
    queryFn: () => searchDocuments(query),
    enabled: query.length > 2,
  });
}
```

## Authentication & Authorization

### NextAuth.js Configuration (Same as Battalion)
```typescript
// lib/auth.ts
export const authOptions: NextAuthOptions = {
  adapter: PrismaAdapter(prisma),
  providers: [
    CredentialsProvider({...}),
    GoogleProvider({...}),
    // Battalion SSO provider
    {
      id: 'battalion',
      name: 'Battalion Platform',
      type: 'oauth',
      authorization: 'https://auth.battalion.energy/oauth/authorize',
      token: 'https://auth.battalion.energy/oauth/token',
      userinfo: 'https://auth.battalion.energy/oauth/userinfo',
    }
  ],
  callbacks: {
    async session({ session, token }) {
      // Sync with Battalion user data
      return session;
    }
  }
};
```

## Performance Optimizations

### No Over-Engineering
- **No Redis**: Not needed for MVP
- **No WebSockets**: SSE is simpler and sufficient
- **No GraphQL**: Unnecessary complexity
- **No tRPC**: Standard API routes are fine
- **No Kubernetes**: Start with simple deployment

### Actual Optimizations
- **React Query Caching**: Automatic query caching
- **Incremental Static Regeneration**: For public pages
- **Image Optimization**: Next.js Image component
- **Code Splitting**: Automatic with Next.js
- **Database Indexes**: Proper PostgreSQL indexes
- **ChromaDB Batching**: Already implemented

## Deployment Strategy

### Simple Initial Deployment
```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: ./apps/web
    ports:
      - "3000:3000"
    environment:
      DATABASE_URL: ${DATABASE_URL}
      NEXTAUTH_URL: ${NEXTAUTH_URL}
      SEARCH_API_URL: http://search-api:8000
    depends_on:
      - postgres
      - search-api

  search-api:
    build: ./apps/search-api
    ports:
      - "8000:8000"
    volumes:
      - ./energy-data-search:/app/energy-data-search
      - ${SOURCE_DATA_DIR}:/data:ro
    environment:
      SOURCE_DATA_DIR: /data

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: aiknowledgebase
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Integration with Battalion Platform

### Shared Components
- Use Battalion's UI component library
- Consistent design tokens and theme
- Shared authentication system
- Common navigation patterns

### Data Exchange
- Event bus for real-time updates (if needed later)
- Shared S3 buckets for documents
- API endpoints for cross-platform data access

### Unified Experience
- Consistent look and feel
- Single sign-on
- Shared user preferences
- Integrated analytics

## Development Workflow

### Local Development
```bash
# Start all services
pnpm dev

# Start without Python API (for frontend work)
pnpm dev:web-only

# Run database migrations
pnpm db:migrate

# Update ChromaDB index
pnpm index:update
```

### Testing Strategy
- Unit tests with Vitest
- Integration tests with Playwright
- API tests with pytest (Python)
- No over-testing initially

## Future Enhancements (Not MVP)

### Phase 2
- Redis caching (if performance requires)
- WebSocket support (if real-time collaboration needed)
- Kubernetes deployment (for scale)
- Multi-tenant support

### Phase 3
- Mobile application
- Advanced analytics
- Custom ML models
- Blockchain audit trail

## Success Metrics

### Technical KPIs
- **Search Speed**: < 500ms response time
- **Chat Latency**: < 100ms to first token
- **Page Load**: < 2s time to interactive
- **Uptime**: 99.9% availability

### Business KPIs
- **User Adoption**: 80% of Battalion users
- **Search Usage**: 100+ searches/day
- **Document Discovery**: 50% improvement
- **Time to Insight**: 70% reduction