# AI Knowledge Base - API Design (v3 - Feature Module APIs)

## Overview
Minimal API surface using Next.js Server Components with direct Prisma calls, only exposing REST endpoints for ChromaDB search and AI streaming.

## Core Principles

### Server-First Architecture
- **Server Components**: Direct database access via Prisma
- **Server Actions**: Form mutations without API routes
- **API Routes**: Only for external services (ChromaDB, OpenAI)
- **No unnecessary APIs**: If it can be a Server Component, it is

## API Structure

```
app/
├── api/                    # Minimal API routes
│   ├── search/            # ChromaDB proxy
│   ├── chat/              # OpenAI streaming
│   └── webhooks/          # External webhooks
│
features/
├── search/
│   └── server/            # Server-only modules
│       ├── search-service.ts
│       └── actions.ts     # Server Actions
├── documents/
│   └── server/
│       ├── document-service.ts
│       └── actions.ts
└── chat/
    └── server/
        ├── chat-service.ts
        └── actions.ts
```

## Server Components (No API Needed)

### Direct Database Access
```typescript
// app/(auth)/documents/page.tsx
import { prisma } from '@/lib/prisma';
import { documentService } from '@/features/documents';

export default async function DocumentsPage() {
  // Direct Prisma query - no API needed!
  const documents = await prisma.document.findMany({
    where: { status: 'ACTIVE' },
    orderBy: { createdAt: 'desc' },
    take: 20,
    include: {
      _count: {
        select: { annotations: true }
      }
    }
  });
  
  return <DocumentGrid documents={documents} />;
}
```

### Server Actions for Mutations
```typescript
// features/documents/server/actions.ts
'use server';

import { prisma } from '@/lib/prisma';
import { revalidatePath } from 'next/cache';
import { z } from 'zod';
import { getCurrentUser } from '@/lib/auth';

const CreateAnnotationSchema = z.object({
  documentId: z.string(),
  text: z.string().min(1).max(5000),
  position: z.object({
    start: z.number(),
    end: z.number()
  })
});

export async function createAnnotation(data: unknown) {
  const user = await getCurrentUser();
  if (!user) throw new Error('Unauthorized');
  
  const validated = CreateAnnotationSchema.parse(data);
  
  const annotation = await prisma.annotation.create({
    data: {
      ...validated,
      userId: user.id
    }
  });
  
  revalidatePath(`/documents/${validated.documentId}`);
  return annotation;
}

export async function deleteAnnotation(id: string) {
  const user = await getCurrentUser();
  if (!user) throw new Error('Unauthorized');
  
  // Verify ownership
  const annotation = await prisma.annotation.findUnique({
    where: { id, userId: user.id }
  });
  
  if (!annotation) throw new Error('Not found');
  
  await prisma.annotation.delete({ where: { id } });
  revalidatePath(`/documents/${annotation.documentId}`);
}
```

### Using Server Actions in Client Components
```tsx
// features/documents/components/AnnotationForm.tsx
'use client';

import { useTransition } from 'react';
import { createAnnotation } from '../server/actions';

export function AnnotationForm({ documentId }: { documentId: string }) {
  const [isPending, startTransition] = useTransition();
  
  async function handleSubmit(formData: FormData) {
    startTransition(async () => {
      await createAnnotation({
        documentId,
        text: formData.get('text'),
        position: { start: 0, end: 100 }
      });
    });
  }
  
  return (
    <form action={handleSubmit}>
      <textarea name="text" required />
      <button disabled={isPending}>
        {isPending ? 'Saving...' : 'Add Note'}
      </button>
    </form>
  );
}
```

## Minimal API Routes

### 1. Search API (ChromaDB Proxy)

```typescript
// app/api/search/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { searchService } from '@/features/search';
import { validateRequest } from '@/lib/api-utils';

const SearchSchema = z.object({
  query: z.string().min(1).max(500),
  limit: z.number().min(1).max(100).default(20),
  filters: z.object({
    documentType: z.array(z.string()).optional(),
    dateRange: z.object({
      start: z.string().datetime(),
      end: z.string().datetime()
    }).optional()
  }).optional()
});

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const validated = SearchSchema.parse(body);
    
    // Call Python ChromaDB API
    const response = await fetch('http://search-api:8000/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(validated)
    });
    
    if (!response.ok) {
      throw new Error('Search service unavailable');
    }
    
    const results = await response.json();
    
    // Record search in database (non-blocking)
    searchService.recordSearch(validated.query).catch(console.error);
    
    return NextResponse.json(results);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Invalid request', details: error.errors },
        { status: 400 }
      );
    }
    
    return NextResponse.json(
      { error: 'Search failed' },
      { status: 500 }
    );
  }
}

// Typeahead suggestions
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const query = searchParams.get('q');
  
  if (!query || query.length < 2) {
    return NextResponse.json({ suggestions: [] });
  }
  
  // Get suggestions from Python API
  const response = await fetch(
    `http://search-api:8000/suggestions?q=${encodeURIComponent(query)}`
  );
  
  const suggestions = await response.json();
  return NextResponse.json(suggestions);
}
```

### 2. Chat API (OpenAI Streaming)

```typescript
// app/api/chat/route.ts
import { NextRequest } from 'next/server';
import { OpenAI } from 'openai';
import { z } from 'zod';
import { getCurrentUser } from '@/lib/auth';
import { chatService } from '@/features/chat';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY!
});

const ChatSchema = z.object({
  message: z.string().min(1).max(4000),
  context: z.array(z.string()).optional(), // Document IDs
  sessionId: z.string().optional()
});

export async function POST(request: NextRequest) {
  const user = await getCurrentUser();
  if (!user) {
    return new Response('Unauthorized', { status: 401 });
  }
  
  const body = await request.json();
  const { message, context, sessionId } = ChatSchema.parse(body);
  
  // Get context documents if provided
  let contextDocs = [];
  if (context?.length) {
    contextDocs = await chatService.getContextDocuments(context);
  }
  
  // Create streaming response
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      try {
        const completion = await openai.chat.completions.create({
          model: 'gpt-4',
          messages: [
            {
              role: 'system',
              content: 'You are an expert on ERCOT energy markets.'
            },
            ...contextDocs.map(doc => ({
              role: 'system' as const,
              content: `Context: ${doc.content.slice(0, 2000)}`
            })),
            {
              role: 'user',
              content: message
            }
          ],
          stream: true,
          temperature: 0.7,
          max_tokens: 2000
        });
        
        for await (const chunk of completion) {
          const text = chunk.choices[0]?.delta?.content || '';
          if (text) {
            const event = `data: ${JSON.stringify({ 
              type: 'token', 
              content: text 
            })}\n\n`;
            controller.enqueue(encoder.encode(event));
          }
        }
        
        // Save message to database (non-blocking)
        chatService.saveMessage({
          sessionId,
          userId: user.id,
          message,
          response: 'streamed'
        }).catch(console.error);
        
        controller.enqueue(encoder.encode('data: {"type": "done"}\n\n'));
      } catch (error) {
        controller.enqueue(
          encoder.encode(`data: ${JSON.stringify({ 
            type: 'error', 
            error: 'Failed to generate response' 
          })}\n\n`)
        );
      } finally {
        controller.close();
      }
    }
  });
  
  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    }
  });
}
```

### 3. Webhook API

```typescript
// app/api/webhooks/stripe/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { headers } from 'next/headers';
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

export async function POST(request: NextRequest) {
  const body = await request.text();
  const signature = headers().get('stripe-signature')!;
  
  try {
    const event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    );
    
    switch (event.type) {
      case 'payment_intent.succeeded':
        // Handle successful payment
        break;
      case 'customer.subscription.updated':
        // Handle subscription update
        break;
    }
    
    return NextResponse.json({ received: true });
  } catch (error) {
    return NextResponse.json(
      { error: 'Webhook error' },
      { status: 400 }
    );
  }
}
```

## Feature Service Modules

### Search Service
```typescript
// features/search/server/search-service.ts
import 'server-only';
import { prisma } from '@/lib/prisma';
import { cache } from 'react';

export class SearchService {
  // Cache for request deduplication
  search = cache(async (query: string) => {
    // Record search (fire and forget)
    this.recordSearch(query).catch(console.error);
    
    // Call Python API
    const response = await fetch('http://search-api:8000/search', {
      method: 'POST',
      body: JSON.stringify({ query }),
      next: { revalidate: 300 } // Cache for 5 minutes
    });
    
    return response.json();
  });
  
  async recordSearch(query: string) {
    const userId = await getCurrentUserId();
    if (!userId) return;
    
    await prisma.searchHistory.create({
      data: { query, userId }
    });
  }
  
  async getRecentSearches(userId: string) {
    return prisma.searchHistory.findMany({
      where: { userId },
      orderBy: { createdAt: 'desc' },
      take: 10,
      distinct: ['query']
    });
  }
  
  async getPopularSearches() {
    return prisma.$queryRaw`
      SELECT query, COUNT(*) as count
      FROM search_history
      WHERE created_at > NOW() - INTERVAL '7 days'
      GROUP BY query
      ORDER BY count DESC
      LIMIT 10
    `;
  }
}

export const searchService = new SearchService();
```

### Document Service
```typescript
// features/documents/server/document-service.ts
import 'server-only';
import { prisma } from '@/lib/prisma';
import { s3Client } from '@/lib/s3';
import { cache } from 'react';

export class DocumentService {
  // Cached document fetching
  getDocument = cache(async (id: string) => {
    return prisma.document.findUnique({
      where: { id },
      include: {
        annotations: {
          include: { user: true }
        },
        category: true
      }
    });
  });
  
  async createDocument(data: CreateDocumentInput) {
    // Upload to S3
    const s3Key = await this.uploadToS3(data.file);
    
    // Create database record
    const document = await prisma.document.create({
      data: {
        title: data.title,
        type: data.type,
        s3Key,
        fileHash: await this.calculateHash(data.file),
        fileSize: data.file.size,
        status: 'ACTIVE'
      }
    });
    
    // Trigger indexing in ChromaDB
    await this.triggerIndexing(document.id);
    
    return document;
  }
  
  private async triggerIndexing(documentId: string) {
    // Call Python API to index document
    await fetch('http://search-api:8000/index', {
      method: 'POST',
      body: JSON.stringify({ documentId })
    });
  }
}

export const documentService = new DocumentService();
```

## Client Hooks for API Calls

### Search Hook
```typescript
// features/search/hooks/use-search.ts
'use client';

import { useQuery } from '@tanstack/react-query';
import { useDebounce } from '@/lib/hooks';

export function useSearch(query: string) {
  const debouncedQuery = useDebounce(query, 300);
  
  return useQuery({
    queryKey: ['search', debouncedQuery],
    queryFn: async () => {
      if (!debouncedQuery) return null;
      
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: debouncedQuery })
      });
      
      if (!response.ok) throw new Error('Search failed');
      return response.json();
    },
    enabled: debouncedQuery.length > 2,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
```

### Chat Hook
```typescript
// features/chat/hooks/use-chat.ts
'use client';

import { useState, useCallback } from 'react';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  
  const sendMessage = useCallback(async (content: string) => {
    setIsStreaming(true);
    setMessages(prev => [...prev, 
      { role: 'user', content },
      { role: 'assistant', content: '' }
    ]);
    
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content })
      });
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            
            if (data.type === 'token') {
              setMessages(prev => {
                const newMessages = [...prev];
                newMessages[newMessages.length - 1].content += data.content;
                return newMessages;
              });
            }
          }
        }
      }
    } finally {
      setIsStreaming(false);
    }
  }, []);
  
  return { messages, sendMessage, isStreaming };
}
```

## API Documentation with OpenAPI

### Auto-generated from Zod Schemas
```typescript
// lib/openapi.ts
import { generateOpenAPIDocument } from '@asteasolutions/zod-to-openapi';
import { SearchSchema, ChatSchema } from './schemas';

export function generateAPIDocs() {
  return generateOpenAPIDocument({
    openapi: '3.1.0',
    info: {
      title: 'AI Knowledge Base API',
      version: '1.0.0',
      description: 'Minimal API for search and chat'
    },
    paths: {
      '/api/search': {
        post: {
          summary: 'Search documents',
          requestBody: {
            content: {
              'application/json': {
                schema: SearchSchema
              }
            }
          }
        }
      },
      '/api/chat': {
        post: {
          summary: 'Chat with AI',
          requestBody: {
            content: {
              'application/json': {
                schema: ChatSchema
              }
            }
          }
        }
      }
    }
  });
}
```

## Performance Optimizations

### Request Deduplication
```typescript
import { cache } from 'react';

// This ensures the same query isn't made multiple times in one request
const getCachedDocuments = cache(async (type: string) => {
  return prisma.document.findMany({ where: { type } });
});
```

### Streaming Large Results
```typescript
// For large document lists, use streaming
export async function GET() {
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      const documents = await prisma.document.findMany({
        take: 1000
      });
      
      for (const doc of documents) {
        controller.enqueue(
          encoder.encode(JSON.stringify(doc) + '\n')
        );
      }
      
      controller.close();
    }
  });
  
  return new Response(stream, {
    headers: { 'Content-Type': 'application/x-ndjson' }
  });
}
```

## Security

### API Route Protection
```typescript
// lib/api-utils.ts
import { getCurrentUser } from '@/lib/auth';
import { NextResponse } from 'next/server';

export async function requireAuth() {
  const user = await getCurrentUser();
  if (!user) {
    throw new Response('Unauthorized', { status: 401 });
  }
  return user;
}

export async function requireRole(role: string) {
  const user = await requireAuth();
  if (user.role !== role) {
    throw new Response('Forbidden', { status: 403 });
  }
  return user;
}
```

### Rate Limiting
```typescript
// lib/rate-limit.ts
const rateLimitMap = new Map();

export function rateLimit(identifier: string, limit = 10) {
  const now = Date.now();
  const windowMs = 60 * 1000; // 1 minute
  
  const current = rateLimitMap.get(identifier) || { count: 0, reset: now + windowMs };
  
  if (now > current.reset) {
    current.count = 0;
    current.reset = now + windowMs;
  }
  
  current.count++;
  rateLimitMap.set(identifier, current);
  
  if (current.count > limit) {
    throw new Response('Rate limit exceeded', { status: 429 });
  }
}
```

## Summary

This API design:
- **Minimizes API surface** - Most operations use Server Components
- **Optimizes performance** - Direct DB access, no unnecessary hops
- **Simplifies development** - Less code, fewer abstractions
- **Maintains flexibility** - Can add APIs when truly needed
- **Ensures type safety** - Zod validation where APIs exist