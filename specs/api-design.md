# AI Knowledge Base - API Design Specification

## API Architecture Overview

### Design Principles
- **Type Safety**: Full end-to-end type safety with tRPC
- **RESTful Compliance**: REST endpoints for external integrations
- **GraphQL Support**: Optional GraphQL layer for complex queries
- **Real-time Updates**: WebSocket support for live data
- **Versioning**: Semantic versioning with backward compatibility
- **Rate Limiting**: Tiered rate limits based on user roles

## tRPC Router Structure

### Core Routers

```typescript
// Main API Router Structure
export const appRouter = createRouter()
  .merge('auth.', authRouter)
  .merge('search.', searchRouter)
  .merge('documents.', documentsRouter)
  .merge('analytics.', analyticsRouter)
  .merge('ercot.', ercotRouter)
  .merge('ai.', aiRouter)
  .merge('admin.', adminRouter)
```

## API Endpoints

### 1. Authentication & Authorization

#### `auth.login`
```typescript
input: {
  email: string
  password: string
  mfaCode?: string
}
output: {
  user: User
  accessToken: string
  refreshToken: string
}
```

#### `auth.refresh`
```typescript
input: {
  refreshToken: string
}
output: {
  accessToken: string
  refreshToken: string
}
```

#### `auth.logout`
```typescript
input: {
  refreshToken: string
}
output: {
  success: boolean
}
```

### 2. Search API

#### `search.query`
```typescript
input: {
  query: string
  filters?: {
    documentType?: DocumentType[]
    dateRange?: { start: Date, end: Date }
    source?: string[]
    tags?: string[]
  }
  searchType?: 'semantic' | 'fulltext' | 'hybrid'
  limit?: number
  offset?: number
}
output: {
  results: SearchResult[]
  totalCount: number
  facets: SearchFacets
  queryId: string
  executionTime: number
}
```

#### `search.suggest`
```typescript
input: {
  partial: string
  context?: string
}
output: {
  suggestions: string[]
  relatedQueries: string[]
}
```

#### `search.history`
```typescript
input: {
  userId: string
  limit?: number
}
output: {
  searches: SearchHistory[]
}
```

### 3. Document Management API

#### `documents.get`
```typescript
input: {
  documentId: string
  includeContent?: boolean
  includeMetadata?: boolean
}
output: {
  document: Document
  relatedDocuments?: Document[]
  annotations?: Annotation[]
}
```

#### `documents.create`
```typescript
input: {
  title: string
  content: string
  type: DocumentType
  metadata: Record<string, any>
  tags?: string[]
}
output: {
  documentId: string
  document: Document
}
```

#### `documents.update`
```typescript
input: {
  documentId: string
  updates: Partial<Document>
}
output: {
  document: Document
  version: number
}
```

#### `documents.annotate`
```typescript
input: {
  documentId: string
  annotation: {
    text: string
    position: { start: number, end: number }
    type: AnnotationType
    metadata?: Record<string, any>
  }
}
output: {
  annotationId: string
  annotation: Annotation
}
```

### 4. ERCOT Data API

#### `ercot.marketData`
```typescript
input: {
  dataType: 'NPRR' | 'NOGRR' | 'ESR' | 'BESS'
  filters?: {
    ktc?: string[]
    dateRange?: DateRange
    status?: string[]
  }
}
output: {
  data: ERCOTData[]
  metadata: ERCOTMetadata
}
```

#### `ercot.analyze`
```typescript
input: {
  documentIds: string[]
  analysisType: AnalysisType
  parameters?: Record<string, any>
}
output: {
  analysis: AnalysisResult
  insights: Insight[]
  recommendations: Recommendation[]
}
```

#### `ercot.compliance`
```typescript
input: {
  entityId: string
  complianceType: ComplianceType
  asOfDate?: Date
}
output: {
  status: ComplianceStatus
  requirements: Requirement[]
  violations: Violation[]
  recommendations: string[]
}
```

### 5. AI Services API

#### `ai.ask`
```typescript
input: {
  question: string
  context?: string[]
  documentIds?: string[]
  model?: 'gpt-4' | 'claude' | 'custom'
}
output: {
  answer: string
  sources: Source[]
  confidence: number
  metadata: {
    tokensUsed: number
    modelUsed: string
    executionTime: number
  }
}
```

#### `ai.summarize`
```typescript
input: {
  documentIds: string[]
  summaryType: 'executive' | 'technical' | 'bullets'
  maxLength?: number
}
output: {
  summary: string
  keyPoints: string[]
  entities: Entity[]
}
```

#### `ai.generate`
```typescript
input: {
  prompt: string
  template?: 'report' | 'analysis' | 'email'
  data?: Record<string, any>
  format?: 'markdown' | 'html' | 'pdf'
}
output: {
  content: string
  format: string
  metadata: GenerationMetadata
}
```

### 6. Analytics API

#### `analytics.dashboard`
```typescript
input: {
  userId?: string
  dateRange: DateRange
  metrics: Metric[]
}
output: {
  metrics: MetricData[]
  charts: ChartData[]
  insights: Insight[]
}
```

#### `analytics.report`
```typescript
input: {
  reportType: ReportType
  parameters: ReportParameters
  format: 'json' | 'csv' | 'pdf'
}
output: {
  reportId: string
  data: any
  downloadUrl?: string
}
```

#### `analytics.trends`
```typescript
input: {
  entity: 'searches' | 'documents' | 'users'
  period: 'day' | 'week' | 'month' | 'year'
  groupBy?: string[]
}
output: {
  trends: TrendData[]
  predictions?: Prediction[]
}
```

## WebSocket Events

### Real-time Search Updates
```typescript
// Client subscribes
socket.emit('subscribe:search', { queryId: string })

// Server emits
socket.emit('search:update', {
  queryId: string
  newResults: SearchResult[]
  timestamp: Date
})
```

### Document Changes
```typescript
// Client subscribes
socket.emit('subscribe:document', { documentId: string })

// Server emits
socket.emit('document:changed', {
  documentId: string
  changes: DocumentChange[]
  version: number
})
```

### System Notifications
```typescript
// Server emits
socket.emit('notification', {
  type: 'info' | 'warning' | 'error'
  message: string
  metadata?: any
})
```

## REST API Endpoints

### Public API (for external integrations)

#### GET `/api/v1/search`
Query parameters:
- `q`: Search query (required)
- `type`: Document type filter
- `limit`: Results limit (default: 20)
- `offset`: Pagination offset

#### GET `/api/v1/documents/{id}`
Returns document by ID

#### POST `/api/v1/documents`
Creates new document

#### GET `/api/v1/ercot/market-data`
Query parameters:
- `type`: Data type (NPRR, NOGRR, etc.)
- `from`: Start date
- `to`: End date

## GraphQL Schema

```graphql
type Query {
  search(query: String!, filters: SearchFilters): SearchResults!
  document(id: ID!): Document
  documents(filter: DocumentFilter, pagination: Pagination): DocumentConnection!
  ercotData(type: ERCOTDataType!, filters: ERCOTFilters): [ERCOTData!]!
  analytics(metrics: [MetricType!]!, range: DateRange!): AnalyticsData!
}

type Mutation {
  createDocument(input: CreateDocumentInput!): Document!
  updateDocument(id: ID!, input: UpdateDocumentInput!): Document!
  deleteDocument(id: ID!): Boolean!
  annotateDocument(documentId: ID!, annotation: AnnotationInput!): Annotation!
}

type Subscription {
  searchUpdates(queryId: ID!): SearchResult!
  documentChanges(documentId: ID!): DocumentChange!
  systemNotifications: Notification!
}
```

## Error Handling

### Error Response Format
```typescript
{
  error: {
    code: string        // e.g., "VALIDATION_ERROR"
    message: string     // Human-readable message
    details?: any       // Additional error details
    timestamp: Date
    traceId: string     // For debugging
  }
}
```

### Standard Error Codes
- `AUTH_REQUIRED`: Authentication required
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `VALIDATION_ERROR`: Input validation failed
- `RATE_LIMITED`: Rate limit exceeded
- `SERVER_ERROR`: Internal server error

## Rate Limiting

### Tiers
```typescript
const rateLimits = {
  anonymous: {
    requests: 100,
    window: '1h'
  },
  authenticated: {
    requests: 1000,
    window: '1h'
  },
  premium: {
    requests: 10000,
    window: '1h'
  },
  admin: {
    requests: Infinity
  }
}
```

## API Versioning

### Version Strategy
- Semantic versioning (e.g., v1, v2)
- Backward compatibility for 2 major versions
- Deprecation notices 6 months in advance
- Version specified in URL path or header

### Version Headers
```
X-API-Version: 1.0
X-API-Deprecated: Field 'oldField' will be removed in v2.0
```

## Authentication & Security

### JWT Token Structure
```typescript
{
  sub: string          // User ID
  email: string
  roles: string[]
  permissions: string[]
  iat: number
  exp: number
  jti: string          // Token ID for revocation
}
```

### API Key Authentication (for service-to-service)
```
Authorization: Bearer API_KEY
X-API-Key: API_KEY
```

## Performance Optimization

### Caching Strategy
- Redis cache for frequent queries
- CDN caching for static resources
- Database query result caching
- Response compression (gzip/brotli)

### Pagination
- Cursor-based for real-time data
- Offset-based for static data
- Maximum page size: 100 items

### Response Optimization
- Field selection/projection
- Eager loading for related data
- Lazy loading for large content
- Response streaming for large datasets

## Monitoring & Analytics

### Metrics to Track
- Request rate and latency
- Error rates by endpoint
- Token usage for AI operations
- Database query performance
- Cache hit rates
- WebSocket connections

### Logging
- Structured JSON logging
- Request/response logging (sanitized)
- Error stack traces
- Performance metrics
- Security events