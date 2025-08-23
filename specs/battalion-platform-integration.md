# Battalion Platform Integration Specification

## Overview
Seamless integration between the AI Knowledge Base and Battalion Platform to create a unified energy market intelligence ecosystem.

## Integration Architecture

### Microservices Communication
```yaml
services:
  ai-knowledge-base:
    port: 3000
    protocols: [HTTP, WebSocket, gRPC]
    
  battalion-platform:
    port: 8080
    protocols: [HTTP, WebSocket, gRPC]
    
  shared-services:
    - authentication-service
    - notification-service
    - analytics-service
    - data-pipeline-service
```

### Service Mesh Configuration
- **Istio** for service-to-service communication
- **Envoy** proxy for load balancing
- **Consul** for service discovery
- **Vault** for secrets management

## Authentication & Authorization

### Single Sign-On (SSO)
```typescript
interface BattalionAuth {
  provider: 'battalion-platform'
  endpoint: 'https://auth.battalion.energy'
  clientId: string
  clientSecret: string
  scopes: ['read', 'write', 'admin']
  tokenEndpoint: '/oauth/token'
  userInfoEndpoint: '/oauth/userinfo'
  logoutEndpoint: '/oauth/logout'
}
```

### Token Exchange Flow
1. User logs into Battalion Platform
2. Battalion issues JWT token
3. AI Knowledge Base validates token
4. Session established with shared claims
5. Refresh token rotation

### Shared User Model
```typescript
interface BattalionUser {
  // Battalion Platform fields
  battalionId: string
  organizationId: string
  tenantId: string
  
  // Shared fields
  email: string
  firstName: string
  lastName: string
  roles: Role[]
  permissions: Permission[]
  
  // AI Knowledge Base extensions
  aiPreferences?: {
    defaultModel: string
    searchSettings: SearchSettings
    notificationPrefs: NotificationPrefs
  }
}
```

### Permission Mapping
```typescript
const permissionMapping = {
  battalion: {
    'energy.trader': ['kb.search', 'kb.view', 'kb.export'],
    'energy.analyst': ['kb.search', 'kb.view', 'kb.annotate', 'kb.ai'],
    'energy.admin': ['kb.*'],
    'energy.viewer': ['kb.search', 'kb.view']
  }
}
```

## Data Integration

### Shared Data Lake
```typescript
interface DataLakeConfig {
  provider: 'AWS S3' | 'Azure Blob' | 'GCS'
  bucket: 'battalion-energy-data'
  regions: ['us-east-1', 'eu-west-1']
  
  partitions: {
    ercot: 's3://battalion-energy-data/ercot/',
    documents: 's3://battalion-energy-data/documents/',
    analytics: 's3://battalion-energy-data/analytics/'
  }
  
  formats: ['parquet', 'json', 'csv']
  compression: 'snappy'
}
```

### Data Pipeline Integration
```yaml
pipelines:
  ercot-ingestion:
    source: ERCOT API
    processors:
      - battalion-transformer
      - ai-kb-enrichment
    sinks:
      - data-lake
      - knowledge-base
      - battalion-platform
    
  document-processing:
    source: document-uploads
    processors:
      - ocr-service
      - nlp-extraction
      - embedding-generation
    sinks:
      - vector-database
      - search-index
```

### Event Streaming
```typescript
interface EventBus {
  broker: 'Kafka' | 'Pulsar'
  topics: {
    'battalion.trades': TradeEvent
    'battalion.alerts': AlertEvent
    'kb.documents': DocumentEvent
    'kb.searches': SearchEvent
    'kb.ai': AIEvent
  }
  
  consumers: {
    'ai-knowledge-base': ['battalion.*']
    'battalion-platform': ['kb.*']
  }
}
```

## UI/UX Integration

### Shared Design System
```typescript
// Battalion Design Tokens
import { battalionTheme } from '@battalion/design-system'

const theme = {
  ...battalionTheme,
  colors: {
    ...battalionTheme.colors,
    // AI KB specific colors
    ai: {
      primary: '#3B82F6',
      secondary: '#10B981'
    }
  },
  components: {
    ...battalionTheme.components,
    // Extended components
    SearchBar: SearchBarTheme,
    DocumentViewer: DocumentViewerTheme
  }
}
```

### Component Library
```tsx
// Shared Battalion Components
import {
  Button,
  Card,
  Table,
  Chart,
  Modal,
  Form
} from '@battalion/ui-components'

// AI KB Extensions
import {
  SearchInterface,
  DocumentGrid,
  AIChat,
  AnalyticsDashboard
} from '@ai-kb/components'
```

### Navigation Integration
```typescript
interface NavigationConfig {
  battalionNav: [
    { label: 'Trading', href: '/trading', icon: 'chart' },
    { label: 'Portfolio', href: '/portfolio', icon: 'briefcase' },
    { label: 'Analytics', href: '/analytics', icon: 'analytics' }
  ],
  
  aiKbNav: [
    { label: 'Knowledge Base', href: '/kb', icon: 'book' },
    { label: 'AI Assistant', href: '/ai', icon: 'robot' },
    { label: 'Documents', href: '/documents', icon: 'folder' }
  ],
  
  merged: boolean // Show as unified navigation
}
```

### Embedded Views
```tsx
// Battalion Platform can embed AI KB views
<BattalionLayout>
  <AIKnowledgeBaseWidget
    view="search"
    context={currentTradingContext}
    filters={battalionFilters}
  />
</BattalionLayout>

// AI KB can embed Battalion views
<AIKBLayout>
  <BattalionTradingWidget
    view="market-overview"
    instruments={relevantInstruments}
  />
</AIKBLayout>
```

## API Integration

### Unified API Gateway
```yaml
api-gateway:
  routes:
    - path: /api/battalion/*
      service: battalion-platform
      auth: required
      
    - path: /api/kb/*
      service: ai-knowledge-base
      auth: required
      
    - path: /api/shared/*
      services: [battalion-platform, ai-knowledge-base]
      loadBalancer: round-robin
```

### Cross-Service API Calls
```typescript
// Battalion calling AI KB
class BattalionService {
  async getMarketInsights(query: string) {
    const insights = await aiKbClient.search({
      query,
      filters: { type: 'market-analysis' },
      includeAI: true
    })
    return this.enrichWithTradingData(insights)
  }
}

// AI KB calling Battalion
class AIKnowledgeService {
  async enrichDocument(doc: Document) {
    const tradingData = await battalionClient.getRelatedTrades({
      symbols: doc.extractedSymbols,
      dateRange: doc.dateRange
    })
    return { ...doc, tradingContext: tradingData }
  }
}
```

## Real-time Collaboration

### Shared WebSocket Channels
```typescript
interface WebSocketChannels {
  // Battalion channels
  'battalion:trades': TradeUpdate
  'battalion:prices': PriceUpdate
  'battalion:alerts': AlertUpdate
  
  // AI KB channels
  'kb:documents': DocumentUpdate
  'kb:searches': SearchUpdate
  'kb:ai-responses': AIResponse
  
  // Shared channels
  'shared:notifications': Notification
  'shared:presence': UserPresence
  'shared:collaboration': CollaborationEvent
}
```

### Collaborative Features
```typescript
interface CollaborationFeatures {
  // Document collaboration
  documentAnnotations: {
    sync: true,
    realtime: true,
    users: BattalionUser[]
  },
  
  // Shared workspaces
  workspaces: {
    trading: ['charts', 'positions', 'documents'],
    research: ['documents', 'ai-chat', 'analytics']
  },
  
  // Cross-platform chat
  chat: {
    channels: ['general', 'trading', 'research'],
    directMessages: true,
    fileSharing: true
  }
}
```

## Analytics & Monitoring

### Unified Analytics Platform
```typescript
interface AnalyticsIntegration {
  // Shared metrics
  metrics: {
    users: UserMetrics,
    performance: PerformanceMetrics,
    business: BusinessMetrics
  },
  
  // Event tracking
  events: {
    battalion: BattalionEvents[],
    aiKb: AIKBEvents[],
    merged: true // Single analytics dashboard
  },
  
  // Reporting
  reports: {
    schedule: 'daily' | 'weekly' | 'monthly',
    recipients: ['ops@battalion.energy'],
    format: 'pdf' | 'dashboard'
  }
}
```

### Monitoring Stack
```yaml
monitoring:
  metrics:
    - prometheus
    - grafana
    
  logging:
    - elasticsearch
    - logstash
    - kibana
    
  tracing:
    - jaeger
    - zipkin
    
  alerting:
    - pagerduty
    - slack
    - email
```

## Deployment Strategy

### Kubernetes Configuration
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-knowledge-base
  namespace: battalion-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-knowledge-base
  template:
    spec:
      containers:
      - name: ai-kb
        image: battalion/ai-knowledge-base:latest
        env:
        - name: BATTALION_API_URL
          value: "http://battalion-platform:8080"
        - name: SHARED_REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
```

### CI/CD Pipeline
```yaml
pipeline:
  stages:
    - test:
        - unit-tests
        - integration-tests
        - battalion-integration-tests
        
    - build:
        - docker-build
        - security-scan
        - push-to-registry
        
    - deploy:
        - staging:
            - deploy-to-k8s
            - smoke-tests
            - battalion-integration-check
            
        - production:
            - blue-green-deployment
            - health-checks
            - rollback-on-failure
```

## Data Synchronization

### Sync Strategy
```typescript
interface SyncConfig {
  // Real-time sync
  realtime: {
    enabled: true,
    events: ['create', 'update', 'delete'],
    debounce: 100 // ms
  },
  
  // Batch sync
  batch: {
    schedule: '0 */6 * * *', // Every 6 hours
    batchSize: 1000,
    parallel: 4
  },
  
  // Conflict resolution
  conflicts: {
    strategy: 'last-write-wins' | 'merge' | 'manual',
    auditLog: true
  }
}
```

### Data Consistency
```typescript
class DataConsistencyService {
  async ensureConsistency() {
    // Check data integrity
    const battalionHash = await this.getBattalionDataHash()
    const aiKbHash = await this.getAIKbDataHash()
    
    if (battalionHash !== aiKbHash) {
      await this.reconcile()
    }
    
    // Set up two-phase commit
    await this.setupDistributedTransaction()
  }
}
```

## Migration Path

### Phase 1: Authentication Integration (Week 1-2)
- Implement SSO
- Map permissions
- Test user flows

### Phase 2: Data Integration (Week 3-4)
- Connect to data lake
- Set up event streaming
- Implement data sync

### Phase 3: UI Integration (Week 5-6)
- Apply Battalion design system
- Create shared components
- Implement navigation

### Phase 4: API Integration (Week 7-8)
- Set up API gateway
- Implement cross-service calls
- Add monitoring

### Phase 5: Full Integration (Week 9-10)
- End-to-end testing
- Performance optimization
- Production deployment

## Success Metrics

### Integration KPIs
- **SSO Success Rate**: > 99.9%
- **Data Sync Latency**: < 1 second
- **API Response Time**: < 200ms p95
- **UI Load Time**: < 2 seconds
- **Cross-Platform Search**: < 500ms
- **User Adoption**: > 80% within 3 months

### Business Metrics
- **Time to Insight**: -50% reduction
- **Document Discovery**: +200% improvement
- **Collaboration Events**: +150% increase
- **API Usage**: +300% growth
- **User Satisfaction**: > 4.5/5.0