# Battalion Platform Integration Specification (v2 - Simplified)

## Overview
Streamlined integration between the AI Knowledge Base and Battalion Platform, focusing on practical implementation using shared technologies and avoiding over-engineering.

## Simplified Integration Architecture

### Shared Technology Stack
```yaml
shared_stack:
  framework: Next.js 15
  database: PostgreSQL with Prisma
  auth: NextAuth.js
  state: Zustand + React Query
  styling: Tailwind CSS
  ui_components: Radix UI + Headless UI
  storage: AWS S3
  package_manager: pnpm
  
ai_kb_additions:
  vector_search: ChromaDB (existing)
  python_api: FastAPI (for ChromaDB wrapper)
  ai: OpenAI API (already in Battalion)
```

### Service Communication
```yaml
services:
  battalion-platform:
    url: https://platform.battalion.energy
    port: 3000
    
  ai-knowledge-base:
    url: https://kb.battalion.energy
    port: 3001
    
  search-api:
    url: http://search-api:8000
    port: 8000
    internal_only: true
```

## Authentication Integration

### Single Sign-On (SSO) with NextAuth.js
```typescript
// lib/auth/config.ts
import { NextAuthOptions } from 'next-auth';
import { PrismaAdapter } from '@next-auth/prisma-adapter';
import CredentialsProvider from 'next-auth/providers/credentials';
import GoogleProvider from 'next-auth/providers/google';
import { prisma } from '@/lib/prisma';

export const authOptions: NextAuthOptions = {
  adapter: PrismaAdapter(prisma),
  providers: [
    // Standard providers
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    
    // Battalion Platform SSO
    CredentialsProvider({
      id: 'battalion-sso',
      name: 'Battalion Platform',
      credentials: {},
      async authorize(credentials, req) {
        // Verify token with Battalion Platform
        const response = await fetch('https://platform.battalion.energy/api/auth/verify', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${req.headers?.authorization}`,
          },
        });
        
        if (response.ok) {
          const user = await response.json();
          return {
            id: user.battalionId,
            email: user.email,
            name: user.name,
            image: user.image,
            battalionId: user.battalionId,
            role: user.role,
          };
        }
        
        return null;
      },
    }),
  ],
  callbacks: {
    async session({ session, token }) {
      // Add Battalion user data to session
      if (token.battalionId) {
        session.user.battalionId = token.battalionId;
        session.user.role = token.role;
      }
      return session;
    },
  },
};
```

### Shared User Model
```prisma
// prisma/schema.prisma
model User {
  id            String    @id @default(cuid())
  email         String    @unique
  name          String?
  image         String?
  battalionId   String?   @unique  // Link to Battalion Platform
  role          UserRole  @default(VIEWER)
  
  // ... other fields
  
  @@index([battalionId])
}
```

## Data Integration

### Document Storage Strategy
```typescript
// Simple S3 integration (same as Battalion)
import { S3Client, PutObjectCommand, GetObjectCommand } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';

const s3Client = new S3Client({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

export async function uploadDocument(file: File, key: string) {
  const command = new PutObjectCommand({
    Bucket: process.env.S3_BUCKET,
    Key: `documents/${key}`,
    Body: Buffer.from(await file.arrayBuffer()),
    ContentType: file.type,
  });
  
  await s3Client.send(command);
  
  // Trigger ChromaDB indexing
  await fetch('http://localhost:8000/index/update', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      type: 'incremental',
      directories: [`documents/${key}`]
    }),
  });
  
  return `documents/${key}`;
}
```

### Database Synchronization
```typescript
// Simple user sync when logging in
async function syncUserFromBattalion(battalionId: string) {
  // Fetch user data from Battalion
  const battalionUser = await fetch(
    `https://platform.battalion.energy/api/users/${battalionId}`,
    {
      headers: {
        'X-API-Key': process.env.BATTALION_API_KEY!,
      },
    }
  ).then(res => res.json());
  
  // Update or create user in our database
  const user = await prisma.user.upsert({
    where: { battalionId },
    update: {
      name: battalionUser.name,
      email: battalionUser.email,
      role: battalionUser.role,
    },
    create: {
      battalionId,
      email: battalionUser.email,
      name: battalionUser.name,
      role: battalionUser.role,
    },
  });
  
  return user;
}
```

## UI Integration

### Shared Component Library
```typescript
// packages/ui/index.ts
// Shared components between Battalion and AI KB
export { Button } from './components/Button';
export { Card } from './components/Card';
export { Table } from './components/Table';
export { Modal } from './components/Modal';
export { Form } from './components/Form';
export { Chart } from './components/Chart';

// Battalion design tokens
export { theme } from './theme';
export { colors } from './colors';
export { typography } from './typography';
```

### Embedded Views (iframe approach for MVP)
```typescript
// Battalion Platform can embed AI KB search
<iframe
  src="https://kb.battalion.energy/embed/search"
  width="100%"
  height="600"
  frameBorder="0"
  sandbox="allow-same-origin allow-scripts"
/>

// AI KB can embed Battalion charts
<iframe
  src="https://platform.battalion.energy/embed/market-overview"
  width="100%"
  height="400"
  frameBorder="0"
/>
```

### Navigation Integration
```typescript
// Shared navigation component
export function NavigationBar() {
  const { data: session } = useSession();
  
  return (
    <nav className="flex items-center space-x-4">
      {/* Battalion Platform Links */}
      <Link href="https://platform.battalion.energy/trading">
        Trading
      </Link>
      <Link href="https://platform.battalion.energy/portfolio">
        Portfolio
      </Link>
      
      {/* AI Knowledge Base Links */}
      <Link href="/search" className="font-bold">
        Knowledge Base
      </Link>
      <Link href="/chat">
        AI Assistant
      </Link>
      
      {/* User Menu */}
      <UserMenu user={session?.user} />
    </nav>
  );
}
```

## API Integration

### Simple Cross-Service Calls
```typescript
// AI KB calling Battalion API
export async function getBattalionMarketData(symbols: string[]) {
  const response = await fetch('https://platform.battalion.energy/api/market-data', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': process.env.BATTALION_API_KEY!,
    },
    body: JSON.stringify({ symbols }),
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch market data');
  }
  
  return response.json();
}

// Battalion calling AI KB API
export async function searchKnowledgeBase(query: string) {
  const response = await fetch('https://kb.battalion.energy/api/search', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': process.env.KB_API_KEY!,
    },
    body: JSON.stringify({ query }),
  });
  
  return response.json();
}
```

## Deployment Strategy

### Docker Compose for Development
```yaml
# docker-compose.yml
version: '3.8'

services:
  # AI Knowledge Base Web
  kb-web:
    build: ./apps/web
    ports:
      - "3001:3000"
    environment:
      DATABASE_URL: postgresql://user:pass@postgres:5432/aidb
      NEXTAUTH_URL: http://localhost:3001
      SEARCH_API_URL: http://search-api:8000
      BATTALION_API_URL: https://platform.battalion.energy
    depends_on:
      - postgres
      - search-api

  # Python Search API
  search-api:
    build: ./apps/search-api
    ports:
      - "8000:8000"
    volumes:
      - ./energy-data-search:/app/energy-data-search
      - /pool/ssd8tb/data/iso/ERCOT:/data:ro
    environment:
      SOURCE_DATA_DIR: /data
      CHROMA_PERSIST_DIR: /app/data/chroma_db

  # Shared PostgreSQL
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: aidb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### Production Deployment (Simple)
```yaml
# Deploy to AWS ECS or similar
services:
  kb-web:
    image: battalion/ai-knowledge-base:latest
    cpu: 1024
    memory: 2048
    environment:
      - DATABASE_URL
      - NEXTAUTH_SECRET
      - OPENAI_API_KEY
    
  search-api:
    image: battalion/search-api:latest
    cpu: 512
    memory: 1024
    environment:
      - SOURCE_DATA_DIR
      - CHROMA_PERSIST_DIR
```

## Monitoring & Analytics

### Simple Monitoring with Existing Tools
```typescript
// Use Battalion's existing monitoring
import { track } from '@battalion/analytics';

export async function trackSearch(query: string, resultCount: number) {
  await track('kb_search', {
    query,
    resultCount,
    timestamp: new Date(),
    userId: session?.user?.id,
  });
}

export async function trackDocumentView(documentId: string) {
  await track('kb_document_view', {
    documentId,
    timestamp: new Date(),
    userId: session?.user?.id,
  });
}
```

## Implementation Phases

### Phase 1: Core Integration (Week 1-2)
- [ ] Set up NextAuth.js with Battalion SSO
- [ ] Create shared user model
- [ ] Deploy ChromaDB search API
- [ ] Basic search interface

### Phase 2: Data Integration (Week 3-4)
- [ ] S3 document storage
- [ ] Document upload and indexing
- [ ] PostgreSQL metadata storage
- [ ] Search history tracking

### Phase 3: UI Polish (Week 5-6)
- [ ] Apply Battalion design system
- [ ] Create embedded views
- [ ] Add navigation integration
- [ ] Mobile responsive design

### Phase 4: AI Features (Week 7-8)
- [ ] OpenAI chat integration
- [ ] Document summarization
- [ ] Context-aware responses
- [ ] Streaming responses

### Phase 5: Testing & Launch (Week 9-10)
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Documentation
- [ ] Production deployment

## Success Metrics

### Technical Metrics
- **Search Speed**: < 500ms
- **Page Load**: < 2s
- **API Response**: < 200ms
- **Uptime**: 99.9%

### Business Metrics
- **User Adoption**: 50% in first month
- **Daily Active Users**: 100+
- **Search Queries**: 500+ per day
- **Document Discovery**: 2x improvement

## Security Considerations

### API Security
```typescript
// Simple API key validation
export async function validateApiKey(request: Request) {
  const apiKey = request.headers.get('X-API-Key');
  
  if (!apiKey) {
    return { valid: false };
  }
  
  const validKey = await prisma.apiKey.findFirst({
    where: { 
      key: hashApiKey(apiKey),
      revokedAt: null,
    },
  });
  
  return { valid: !!validKey, userId: validKey?.userId };
}
```

### Data Access Control
```typescript
// Simple document access control
export async function canAccessDocument(userId: string, documentId: string) {
  const document = await prisma.document.findUnique({
    where: { id: documentId },
  });
  
  if (!document) return false;
  
  // Public documents are accessible to all
  if (document.visibility === 'PUBLIC') return true;
  
  // Check user permissions
  const user = await prisma.user.findUnique({
    where: { id: userId },
  });
  
  // Admins can access everything
  if (user?.role === 'ADMIN') return true;
  
  // Check specific permissions
  // ... additional logic
  
  return false;
}
```

## Migration Strategy

### Data Migration
```sql
-- Migrate existing Battalion users
INSERT INTO users (email, name, battalion_id, role)
SELECT email, name, id, role
FROM battalion_platform.users
WHERE active = true;

-- Migrate document metadata
INSERT INTO documents (title, source, type, created_at)
SELECT title, source, 'LEGACY', created_at
FROM battalion_platform.documents;
```

## Maintenance & Support

### Documentation
- API documentation with OpenAPI/Swagger
- User guides for Battalion team
- Developer documentation
- Troubleshooting guides

### Support Process
1. Battalion support team handles tier 1
2. AI KB team handles search/indexing issues
3. Shared Slack channel for coordination
4. Weekly sync meetings

## Future Enhancements (Not MVP)

### Later Phases
- WebSocket for real-time updates
- Redis caching layer
- Advanced analytics dashboard
- Mobile application
- Multi-tenant support
- Kubernetes deployment
- GraphQL API (if needed)