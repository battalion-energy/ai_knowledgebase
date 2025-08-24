# AI Knowledge Base - Next.js Application Architecture (v3 - Feature-Based Modularity)

## Overview
A pragmatic Next.js 15 application architecture that achieves modularity through feature-based organization, avoiding the complexity of micro-frontends while maintaining team autonomy and code isolation.

## Core Principles

### What We're NOT Doing
- ❌ **No Web Components** - Poor DX, complex data passing
- ❌ **No Module Federation** - Incompatible with App Router
- ❌ **No Micro-frontends** - Unnecessary complexity
- ❌ **No Multiple Frameworks** - Stick with Next.js + React

### What We ARE Doing
- ✅ **Feature-based modules** - Clear boundaries, team ownership
- ✅ **Monorepo with pnpm** - Shared dependencies, fast installs
- ✅ **Direct Prisma calls** - SSR with Server Components
- ✅ **Python services via uv** - Fast Python tooling
- ✅ **Makefile orchestration** - Simple command interface

## Technology Stack

```yaml
frontend:
  framework: Next.js 15 (App Router)
  language: TypeScript 5.3+
  styling: Tailwind CSS 3.4+
  state: Zustand + React Query v5
  forms: React Hook Form + Zod
  ui: Radix UI + Custom components
  charts: Recharts

backend:
  database: PostgreSQL 15+ with Prisma ORM
  vector_search: ChromaDB (existing implementation)
  file_storage: AWS S3
  auth: NextAuth.js v4
  email: AWS SES

tooling:
  monorepo: pnpm workspaces
  python: uv (replaces pip/poetry)
  orchestration: Make
  testing: Vitest + Playwright
  ci_cd: GitHub Actions
  deployment: AWS ECS/Fargate
```

## Project Structure

```
ai-knowledge-base/
├── Makefile                     # Root orchestration
├── package.json                 # pnpm workspace config
├── pnpm-workspace.yaml         # Workspace definition
├── .env.example                # Environment template
├── docker-compose.yml          # Local development
│
├── apps/
│   ├── web/                    # Next.js application
│   │   ├── app/                # App Router pages
│   │   │   ├── (auth)/        # Authenticated routes
│   │   │   │   ├── layout.tsx
│   │   │   │   ├── dashboard/page.tsx
│   │   │   │   ├── search/page.tsx
│   │   │   │   ├── documents/[id]/page.tsx
│   │   │   │   └── chat/page.tsx
│   │   │   ├── api/           # Minimal API routes
│   │   │   │   ├── search/route.ts      # ChromaDB proxy
│   │   │   │   ├── chat/route.ts        # OpenAI streaming
│   │   │   │   └── webhooks/[...path]/route.ts
│   │   │   └── layout.tsx
│   │   │
│   │   ├── features/           # Feature modules
│   │   │   ├── search/        # Search feature
│   │   │   │   ├── components/
│   │   │   │   │   ├── SearchBar.tsx
│   │   │   │   │   ├── SearchResults.tsx
│   │   │   │   │   └── SearchFilters.tsx
│   │   │   │   ├── server/
│   │   │   │   │   ├── search-service.ts
│   │   │   │   │   └── chromadb-client.ts
│   │   │   │   ├── hooks/
│   │   │   │   │   └── use-search.ts
│   │   │   │   ├── stores/
│   │   │   │   │   └── search-store.ts
│   │   │   │   ├── types.ts
│   │   │   │   └── index.ts   # Public API
│   │   │   │
│   │   │   ├── documents/     # Documents feature
│   │   │   │   ├── components/
│   │   │   │   ├── server/
│   │   │   │   ├── hooks/
│   │   │   │   └── index.ts
│   │   │   │
│   │   │   ├── chat/          # AI Chat feature
│   │   │   │   ├── components/
│   │   │   │   ├── server/
│   │   │   │   ├── hooks/
│   │   │   │   └── index.ts
│   │   │   │
│   │   │   └── analytics/     # Analytics feature
│   │   │       ├── components/
│   │   │       ├── server/
│   │   │       └── index.ts
│   │   │
│   │   ├── lib/                # Shared utilities
│   │   │   ├── prisma.ts
│   │   │   ├── auth.ts
│   │   │   └── s3.ts
│   │   │
│   │   ├── prisma/
│   │   │   └── schema.prisma
│   │   └── package.json
│   │
│   └── search-api/             # Python FastAPI service
│       ├── pyproject.toml     # uv configuration
│       ├── Makefile           # Python-specific commands
│       ├── main.py
│       ├── routers/
│       └── services/
│
├── packages/                   # Shared packages
│   ├── ui/                    # Shared UI components
│   │   ├── src/
│   │   └── package.json
│   ├── types/                 # Shared TypeScript types
│   │   └── package.json
│   └── utils/                 # Shared utilities
│       └── package.json
│
├── energy-data-search/         # Existing ChromaDB implementation
│   ├── pyproject.toml        # Converted to uv
│   └── src/
│
└── ercot_code/                # ERCOT Python scripts
    └── pyproject.toml        # Converted to uv
```

## Feature Module Architecture

### Feature Module Structure
```typescript
// features/search/index.ts - Public API
export { SearchBar } from './components/SearchBar';
export { SearchResults } from './components/SearchResults';
export { useSearch } from './hooks/use-search';
export { searchService } from './server/search-service';
export type { SearchResult, SearchFilters } from './types';

// NOTHING ELSE is exported - everything else is private
```

### Feature Boundaries
```typescript
// ✅ GOOD - Import from public API
import { SearchBar, useSearch } from '@/features/search';

// ❌ BAD - Import internal implementation
import { ChromaDBClient } from '@/features/search/server/chromadb-client';
```

### Server/Client Separation
```typescript
// features/search/server/search-service.ts
import 'server-only'; // This file can only run on server
import { prisma } from '@/lib/prisma';

export class SearchService {
  async search(query: string) {
    // Direct Prisma calls
    const history = await prisma.searchHistory.create({
      data: { query, userId: await getCurrentUserId() }
    });
    
    // Call Python API for ChromaDB
    const results = await fetch('http://search-api:8000/search', {
      method: 'POST',
      body: JSON.stringify({ query })
    });
    
    return results.json();
  }
}

export const searchService = new SearchService();
```

### Using Features in Pages
```typescript
// app/(auth)/search/page.tsx
import { searchService } from '@/features/search';
import { SearchBar, SearchResults } from '@/features/search';

export default async function SearchPage({
  searchParams
}: {
  searchParams: { q?: string }
}) {
  // Server Component - runs on server
  let results = null;
  if (searchParams.q) {
    results = await searchService.search(searchParams.q);
  }
  
  // Get recent searches with direct Prisma
  const recentSearches = await prisma.searchHistory.findMany({
    where: { userId: await getCurrentUserId() },
    take: 5
  });
  
  return (
    <>
      <SearchBar defaultValue={searchParams.q} />
      <SearchResults results={results} />
      <RecentSearches searches={recentSearches} />
    </>
  );
}
```

## pnpm Monorepo Configuration

### Root package.json
```json
{
  "name": "ai-knowledge-base",
  "private": true,
  "packageManager": "pnpm@8.15.0",
  "scripts": {
    "dev": "pnpm --parallel run dev",
    "build": "pnpm run build:packages && pnpm run build:apps",
    "build:packages": "pnpm --filter './packages/**' run build",
    "build:apps": "pnpm --filter './apps/**' run build",
    "test": "pnpm run test:unit && pnpm run test:e2e",
    "test:unit": "pnpm --parallel run test",
    "test:e2e": "pnpm --filter web run test:e2e",
    "lint": "pnpm --parallel run lint",
    "clean": "pnpm --parallel run clean && rm -rf node_modules",
    "db:migrate": "pnpm --filter web run db:migrate",
    "db:studio": "pnpm --filter web run db:studio"
  },
  "devDependencies": {
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "eslint": "^8.57.0",
    "prettier": "^3.2.0",
    "turbo": "^1.11.0",
    "typescript": "^5.3.0"
  }
}
```

### pnpm-workspace.yaml
```yaml
packages:
  - 'apps/*'
  - 'packages/*'
  - 'energy-data-search'
  - 'ercot_code'
```

### Shared Package Example
```json
// packages/ui/package.json
{
  "name": "@battalion/ui",
  "version": "0.1.0",
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "exports": {
    ".": "./src/index.ts",
    "./styles": "./src/styles/index.css"
  },
  "dependencies": {
    "@radix-ui/react-dialog": "^1.0.0",
    "clsx": "^2.0.0",
    "react": "^18.3.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "typescript": "^5.3.0"
  }
}
```

## Python with uv Configuration

### Search API pyproject.toml
```toml
# apps/search-api/pyproject.toml
[project]
name = "search-api"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "httpx>=0.26.0",
    "python-multipart>=0.0.6",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Energy Data Search pyproject.toml (updated)
```toml
# energy-data-search/pyproject.toml
[project]
name = "energy-data-search"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "chromadb>=1.0.20",
    "langchain>=0.3.27",
    "langchain-chroma>=0.2.5",
    "langchain-huggingface>=0.3.1",
    "sentence-transformers>=5.1.0",
    "pypdf>=6.0.0",
    "python-dotenv>=1.1.1",
    "click>=8.2.1",
    "rich>=14.1.0",
]

[tool.uv.pip]
system = false
python = "3.12"

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "ruff>=0.1.0",
]
```

## Makefile Configuration

### Root Makefile
```makefile
# ai-knowledge-base/Makefile

# Variables
DOCKER_COMPOSE := docker-compose
PNPM := pnpm
UV := uv
PORT_WEB := 3000
PORT_API := 8000

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

.PHONY: help
help: ## Show this help message
	@echo '${GREEN}AI Knowledge Base - Available Commands${NC}'
	@echo ''
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make ${YELLOW}<target>${NC}\n\n"} \
		/^[a-zA-Z_-]+:.*?##/ { printf "  ${YELLOW}%-20s${NC} %s\n", $$1, $$2 } \
		/^##@/ { printf "\n${GREEN}%s${NC}\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development

.PHONY: install
install: ## Install all dependencies (Node + Python)
	@echo "${GREEN}Installing Node dependencies with pnpm...${NC}"
	$(PNPM) install
	@echo "${GREEN}Installing Python dependencies with uv...${NC}"
	cd apps/search-api && $(UV) pip sync requirements.txt
	cd energy-data-search && $(UV) pip sync requirements.txt
	@echo "${GREEN}Dependencies installed!${NC}"

.PHONY: dev
dev: ## Start development servers (Next.js + Python API)
	@echo "${GREEN}Starting development servers...${NC}"
	$(MAKE) -j2 dev-web dev-api

.PHONY: dev-web
dev-web: ## Start Next.js development server
	cd apps/web && $(PNPM) dev

.PHONY: dev-api
dev-api: ## Start Python search API
	cd apps/search-api && $(UV) run uvicorn main:app --reload --port $(PORT_API)

.PHONY: dev-docker
dev-docker: ## Start all services with Docker Compose
	$(DOCKER_COMPOSE) up

##@ Database

.PHONY: db-migrate
db-migrate: ## Run database migrations
	cd apps/web && $(PNPM) prisma migrate dev

.PHONY: db-studio
db-studio: ## Open Prisma Studio
	cd apps/web && $(PNPM) prisma studio

.PHONY: db-seed
db-seed: ## Seed database with sample data
	cd apps/web && $(PNPM) prisma db seed

.PHONY: db-reset
db-reset: ## Reset database (WARNING: destroys all data)
	@echo "${RED}WARNING: This will destroy all data!${NC}"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		cd apps/web && $(PNPM) prisma migrate reset; \
	fi

##@ Search Index

.PHONY: index
index: ## Run full ChromaDB indexing
	cd energy-data-search && $(UV) run energy-search index

.PHONY: index-update
index-update: ## Update ChromaDB index (incremental)
	cd energy-data-search && $(UV) run energy-search update

.PHONY: index-status
index-status: ## Check ChromaDB index status
	cd energy-data-search && $(UV) run energy-search status

.PHONY: search
search: ## Search ChromaDB (usage: make search QUERY="your query")
	cd energy-data-search && $(UV) run energy-search search "$(QUERY)"

##@ Testing

.PHONY: test
test: ## Run all tests
	$(MAKE) test-unit test-e2e test-python

.PHONY: test-unit
test-unit: ## Run unit tests
	$(PNPM) test:unit

.PHONY: test-e2e
test-e2e: ## Run E2E tests with Playwright
	cd apps/web && $(PNPM) test:e2e

.PHONY: test-python
test-python: ## Run Python tests
	cd apps/search-api && $(UV) run pytest
	cd energy-data-search && $(UV) run pytest

.PHONY: test-watch
test-watch: ## Run tests in watch mode
	$(PNPM) test:watch

##@ Code Quality

.PHONY: lint
lint: ## Run linters (ESLint + Ruff)
	$(PNPM) lint
	cd apps/search-api && $(UV) run ruff check .
	cd energy-data-search && $(UV) run ruff check .

.PHONY: format
format: ## Format code (Prettier + Black)
	$(PNPM) format
	cd apps/search-api && $(UV) run ruff format .
	cd energy-data-search && $(UV) run ruff format .

.PHONY: type-check
type-check: ## Run TypeScript type checking
	$(PNPM) type-check

##@ Building

.PHONY: build
build: ## Build all applications
	@echo "${GREEN}Building applications...${NC}"
	$(PNPM) build
	cd apps/search-api && $(UV) build

.PHONY: build-docker
build-docker: ## Build Docker images
	$(DOCKER_COMPOSE) build

##@ Deployment

.PHONY: deploy-staging
deploy-staging: ## Deploy to staging environment
	@echo "${GREEN}Deploying to staging...${NC}"
	./scripts/deploy-staging.sh

.PHONY: deploy-prod
deploy-prod: ## Deploy to production (requires confirmation)
	@echo "${RED}WARNING: Deploying to production!${NC}"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		./scripts/deploy-prod.sh; \
	fi

##@ Utilities

.PHONY: clean
clean: ## Clean build artifacts and dependencies
	rm -rf node_modules apps/*/node_modules packages/*/node_modules
	rm -rf apps/*/.next apps/*/dist packages/*/dist
	rm -rf apps/search-api/.venv energy-data-search/.venv
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

.PHONY: setup
setup: ## Initial project setup
	@echo "${GREEN}Setting up project...${NC}"
	cp .env.example .env
	$(MAKE) install
	$(MAKE) db-migrate
	$(MAKE) db-seed
	@echo "${GREEN}Setup complete! Run 'make dev' to start developing.${NC}"

.PHONY: logs
logs: ## Show logs from Docker containers
	$(DOCKER_COMPOSE) logs -f

.PHONY: ps
ps: ## Show running Docker containers
	$(DOCKER_COMPOSE) ps

.PHONY: shell-web
shell-web: ## Open shell in web container
	$(DOCKER_COMPOSE) exec web /bin/bash

.PHONY: shell-api
shell-api: ## Open shell in API container
	$(DOCKER_COMPOSE) exec search-api /bin/bash
```

## Enforcing Module Boundaries

### ESLint Configuration
```javascript
// .eslintrc.js
module.exports = {
  extends: ['next/core-web-vitals'],
  rules: {
    'no-restricted-imports': [
      'error',
      {
        patterns: [
          {
            group: ['@/features/*/server/*', '@/features/*/internal/*'],
            message: 'Cannot import internal feature modules. Use the public API from @/features/[feature]'
          },
          {
            group: ['*/components/*', '!@/features/*/components'],
            message: 'Import components from feature public API, not directly'
          }
        ]
      }
    ],
    '@typescript-eslint/no-restricted-imports': [
      'error',
      {
        paths: [
          {
            name: '@/lib/prisma',
            message: 'Only import prisma in server components and feature server modules',
            allowTypeImports: true
          }
        ]
      }
    ]
  }
};
```

### TypeScript Path Configuration
```json
// tsconfig.json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./app/*"],
      "@/features/*": ["./features/*"],
      "@/lib/*": ["./lib/*"],
      "@battalion/ui": ["../../packages/ui/src"],
      "@battalion/types": ["../../packages/types/src"],
      "@battalion/utils": ["../../packages/utils/src"]
    }
  }
}
```

## Development Workflow

### Quick Start
```bash
# Initial setup
make setup

# Start development
make dev

# Run tests
make test

# Search documents
make search QUERY="battery storage"
```

### Feature Development
```bash
# 1. Create new feature
mkdir -p features/new-feature/{components,server,hooks}

# 2. Define public API
echo "export * from './components'" > features/new-feature/index.ts

# 3. Develop in isolation
cd features/new-feature && pnpm test:watch

# 4. Integrate with pages
# app/(auth)/new-feature/page.tsx
```

## Benefits of This Architecture

1. **Modularity without complexity** - Features are isolated but in same app
2. **Great DX** - Full TypeScript, hot reload, single dev server
3. **Team autonomy** - Teams own features, clear boundaries
4. **Performance** - SSR by default, direct DB queries
5. **Simplicity** - One deployment, one database, one auth system
6. **Flexibility** - Can extract features to services later if needed

## Migration Strategy

### From Current State
1. Keep existing Next.js structure
2. Gradually move code to feature folders
3. Implement boundaries with linting
4. Extract Python services where needed

### Future Options
- Feature can become a package
- Feature can become a service
- Feature can be deleted cleanly
- No architectural lock-in