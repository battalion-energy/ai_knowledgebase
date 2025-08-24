# Energence.ai - AI Knowledge Base Platform
# Makefile for common development and deployment tasks

# Colors for terminal output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Environment
SHELL := /bin/bash
.DEFAULT_GOAL := help

# Database settings (using existing PostgreSQL)
POSTGRES_HOST := localhost
POSTGRES_PORT := 5432
POSTGRES_DB := energence_db
POSTGRES_USER := postgres
POSTGRES_PASSWORD := postgres

# Python settings
PYTHON_API_PORT := 8105
VENV_PATH := .venv

# Next.js settings
NEXT_PORT := 3105

.PHONY: help
help: ## Show this help message
	@echo -e "${BLUE}Energence.ai - Available Commands${NC}"
	@echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "${GREEN}%-20s${NC} %s\n", $$1, $$2}'

# ========================================
# Installation & Setup
# ========================================

.PHONY: install
install: ## Install all dependencies (Node.js and Python)
	@echo -e "${BLUE}Installing Node.js dependencies...${NC}"
	pnpm install
	@echo -e "${BLUE}Installing Python dependencies...${NC}"
	@if command -v uv >/dev/null 2>&1; then \
		cd apps/search-api && uv pip install -r requirements.txt; \
	else \
		cd apps/search-api && pip install -r requirements.txt; \
	fi
	@echo -e "${GREEN}✓ All dependencies installed${NC}"

.PHONY: setup
setup: install db-setup ## Complete initial setup (install deps + setup database)
	@echo -e "${GREEN}✓ Setup complete! Run 'make dev' to start development${NC}"

.PHONY: clean
clean: ## Clean all generated files and dependencies
	@echo -e "${YELLOW}Cleaning project...${NC}"
	rm -rf node_modules .next out dist build
	rm -rf apps/web/node_modules apps/web/.next
	rm -rf apps/search-api/__pycache__
	rm -rf energy-data-search/__pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo -e "${GREEN}✓ Clean complete${NC}"

.PHONY: clean-all
clean-all: clean db-drop ## Clean everything including database
	@echo -e "${GREEN}✓ Full clean complete${NC}"

# ========================================
# Database Management
# ========================================

.PHONY: db-create-user
db-create-user: ## Create PostgreSQL user and database from .env configuration
	@echo -e "${BLUE}Setting up PostgreSQL user and database...${NC}"
	@chmod +x scripts/setup-postgres.sh
	@bash scripts/setup-postgres.sh
	@echo -e "${GREEN}✓ PostgreSQL setup complete${NC}"

.PHONY: db-setup
db-setup: ## Complete database setup (create user, database, and run migrations)
	@echo -e "${BLUE}Complete database setup...${NC}"
	@$(MAKE) db-create-user
	@$(MAKE) db-migrate
	@echo -e "${GREEN}✓ Database fully configured and ready!${NC}"

.PHONY: db-setup-only
db-setup-only: ## Only create database structure (assumes user exists)
	@echo -e "${BLUE}Running database migrations...${NC}"
	@cd apps/web && cp ../../.env.local .env 2>/dev/null || true
	cd apps/web && pnpm prisma migrate dev --name init
	@echo -e "${GREEN}✓ Database structure created${NC}"

.PHONY: db-drop
db-drop: ## Drop the database (requires sudo)
	@echo -e "${RED}Dropping database...${NC}"
	@echo -e "${YELLOW}This will delete all data! Press Ctrl+C to cancel.${NC}"
	@sleep 3
	@source .env.local && sudo -u postgres psql -c "DROP DATABASE IF EXISTS $$DB_NAME;"
	@echo -e "${GREEN}✓ Database dropped${NC}"

.PHONY: db-reset-hard
db-reset-hard: ## Complete reset: drop user, database, and recreate everything
	@echo -e "${RED}Complete database reset...${NC}"
	@echo -e "${YELLOW}This will delete EVERYTHING! Press Ctrl+C to cancel.${NC}"
	@sleep 5
	@source .env.local && sudo -u postgres psql -c "DROP DATABASE IF EXISTS $$DB_NAME;" || true
	@source .env.local && sudo -u postgres psql -c "DROP USER IF EXISTS $$DB_USER;" || true
	@$(MAKE) db-setup
	@echo -e "${GREEN}✓ Complete reset done${NC}"

.PHONY: db-migrate
db-migrate: ## Run database migrations
	@echo -e "${BLUE}Running migrations...${NC}"
	@cd apps/web && cp ../../.env.local .env 2>/dev/null || true
	cd apps/web && pnpm prisma migrate dev
	@echo -e "${GREEN}✓ Migrations complete${NC}"

.PHONY: db-generate
db-generate: ## Generate Prisma client
	@echo -e "${BLUE}Generating Prisma client...${NC}"
	cd apps/web && pnpm prisma generate
	@echo -e "${GREEN}✓ Prisma client generated${NC}"

.PHONY: db-studio
db-studio: ## Open Prisma Studio
	@echo -e "${BLUE}Opening Prisma Studio...${NC}"
	cd apps/web && pnpm prisma studio

.PHONY: db-seed
db-seed: ## Seed database with sample data
	@echo -e "${BLUE}Seeding database...${NC}"
	cd apps/web && pnpm prisma db seed
	@echo -e "${GREEN}✓ Database seeded${NC}"

.PHONY: db-reset
db-reset: ## Reset database (drop + setup + seed)
	@echo -e "${YELLOW}Resetting database...${NC}"
	cd apps/web && pnpm prisma migrate reset --force
	@echo -e "${GREEN}✓ Database reset complete${NC}"

# ========================================
# Development
# ========================================

.PHONY: dev
dev: ## Start all development servers (Next.js + Python API)
	@echo -e "${BLUE}Starting development servers...${NC}"
	@make -j2 dev-web dev-api

.PHONY: dev-web
dev-web: ## Start Next.js development server
	@echo -e "${BLUE}Starting Next.js on port $(NEXT_PORT)...${NC}"
	cd apps/web && pnpm dev

.PHONY: dev-api
dev-api: ## Start Python search API
	@echo -e "${BLUE}Starting Python API on port $(PYTHON_API_PORT)...${NC}"
	@if command -v uv >/dev/null 2>&1; then \
		cd apps/search-api && uv run uvicorn main:app --reload --port $(PYTHON_API_PORT); \
	else \
		cd apps/search-api && python -m uvicorn main:app --reload --port $(PYTHON_API_PORT); \
	fi

.PHONY: dev-web-only
dev-web-only: ## Start only Next.js (no Python API)
	@echo -e "${BLUE}Starting Next.js only...${NC}"
	cd apps/web && pnpm dev

# ========================================
# ChromaDB & Indexing
# ========================================

.PHONY: index-update
index-update: ## Update ChromaDB index (incremental)
	@echo -e "${BLUE}Updating ChromaDB index...${NC}"
	cd apps/search-api && uv run python -m scripts.update_index
	@echo -e "${GREEN}✓ Index updated${NC}"

.PHONY: index-full
index-full: ## Full reindex of all documents
	@echo -e "${YELLOW}Running full reindex (this may take a while)...${NC}"
	cd energy-data-search && python -m query.search_engine --index-all
	@echo -e "${GREEN}✓ Full reindex complete${NC}"

.PHONY: index-stats
index-stats: ## Show ChromaDB index statistics
	@echo -e "${BLUE}ChromaDB Index Statistics:${NC}"
	cd energy-data-search && python -c "from query.search_engine import EnergyDataSearchEngine; engine = EnergyDataSearchEngine(); print(engine.get_statistics())"

# ========================================
# Testing
# ========================================

.PHONY: test
test: ## Run all tests
	@echo -e "${BLUE}Running tests...${NC}"
	pnpm test
	@echo -e "${GREEN}✓ Tests complete${NC}"

.PHONY: test-web
test-web: ## Run Next.js tests
	@echo -e "${BLUE}Running Next.js tests...${NC}"
	cd apps/web && pnpm test

.PHONY: test-api
test-api: ## Run Python API tests
	@echo -e "${BLUE}Running Python API tests...${NC}"
	cd apps/search-api && uv run pytest

.PHONY: test-e2e
test-e2e: ## Run end-to-end tests
	@echo -e "${BLUE}Running E2E tests...${NC}"
	pnpm test:e2e

# ========================================
# Code Quality
# ========================================

.PHONY: lint
lint: ## Run linters
	@echo -e "${BLUE}Running linters...${NC}"
	pnpm lint
	@echo -e "${GREEN}✓ Linting complete${NC}"

.PHONY: lint-fix
lint-fix: ## Fix linting issues
	@echo -e "${BLUE}Fixing linting issues...${NC}"
	pnpm lint --fix
	@echo -e "${GREEN}✓ Linting fixed${NC}"

.PHONY: format
format: ## Format code with Prettier
	@echo -e "${BLUE}Formatting code...${NC}"
	pnpm prettier --write "**/*.{ts,tsx,js,jsx,json,md}"
	@echo -e "${GREEN}✓ Formatting complete${NC}"

.PHONY: type-check
type-check: ## Run TypeScript type checking
	@echo -e "${BLUE}Type checking...${NC}"
	pnpm type-check
	@echo -e "${GREEN}✓ Type check complete${NC}"

# ========================================
# Building & Production
# ========================================

.PHONY: build
build: ## Build for production
	@echo -e "${BLUE}Building for production...${NC}"
	pnpm build
	@echo -e "${GREEN}✓ Build complete${NC}"

.PHONY: build-web
build-web: ## Build Next.js for production
	@echo -e "${BLUE}Building Next.js...${NC}"
	cd apps/web && pnpm build
	@echo -e "${GREEN}✓ Next.js build complete${NC}"

.PHONY: start
start: ## Start production servers
	@echo -e "${BLUE}Starting production servers...${NC}"
	@make -j2 start-web start-api

.PHONY: start-web
start-web: ## Start Next.js in production mode
	@echo -e "${BLUE}Starting Next.js production server...${NC}"
	cd apps/web && pnpm start

.PHONY: start-api
start-api: ## Start Python API in production mode
	@echo -e "${BLUE}Starting Python API production server...${NC}"
	cd apps/search-api && uv run uvicorn main:app --host 0.0.0.0 --port $(PYTHON_API_PORT)

# ========================================
# Docker
# ========================================

.PHONY: docker-build
docker-build: ## Build Docker images
	@echo -e "${BLUE}Building Docker images...${NC}"
	docker-compose build
	@echo -e "${GREEN}✓ Docker build complete${NC}"

.PHONY: docker-up
docker-up: ## Start all services with Docker Compose
	@echo -e "${BLUE}Starting Docker services...${NC}"
	docker-compose up -d
	@echo -e "${GREEN}✓ Services running${NC}"

.PHONY: docker-down
docker-down: ## Stop all Docker services
	@echo -e "${YELLOW}Stopping Docker services...${NC}"
	docker-compose down
	@echo -e "${GREEN}✓ Services stopped${NC}"

.PHONY: docker-logs
docker-logs: ## Show Docker logs
	docker-compose logs -f

# ========================================
# Git Helpers
# ========================================

.PHONY: git-status
git-status: ## Show git status
	@git status

.PHONY: git-commit
git-commit: ## Commit all changes
	@read -p "Enter commit message: " msg; \
	git add -A && git commit -m "$$msg"

.PHONY: git-push
git-push: ## Push to origin
	@git push origin master

.PHONY: git-pull
git-pull: ## Pull from origin
	@git pull origin master

# ========================================
# Utilities
# ========================================

.PHONY: env-copy
env-copy: ## Copy .env.example to .env.local
	@echo -e "${BLUE}Setting up environment variables...${NC}"
	@cp .env.example .env.local 2>/dev/null || true
	@cp .env.example apps/web/.env.local 2>/dev/null || true
	@echo -e "${GREEN}✓ Environment files created. Please edit .env.local with your values${NC}"

.PHONY: kill-ports
kill-ports: ## Kill processes on default ports
	@echo -e "${YELLOW}Killing processes on ports $(NEXT_PORT) and $(PYTHON_API_PORT)...${NC}"
	@lsof -ti:$(NEXT_PORT) | xargs kill -9 2>/dev/null || true
	@lsof -ti:$(PYTHON_API_PORT) | xargs kill -9 2>/dev/null || true
	@echo -e "${GREEN}✓ Ports cleared${NC}"

.PHONY: logs
logs: ## Show all logs
	@tail -f apps/web/.next/server/app.log apps/search-api/logs/*.log 2>/dev/null || echo "No logs found"

.PHONY: status
status: ## Show status of all services
	@echo -e "${BLUE}Service Status:${NC}"
	@echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
	@echo -n "PostgreSQL: "; pg_isready -h $(POSTGRES_HOST) -p $(POSTGRES_PORT) > /dev/null 2>&1 && echo -e "${GREEN}Running on port $(POSTGRES_PORT)${NC}" || echo -e "${RED}Not available${NC}"
	@echo -n "Next.js:    "; lsof -ti:$(NEXT_PORT) > /dev/null 2>&1 && echo -e "${GREEN}Running on port $(NEXT_PORT)${NC}" || echo -e "${RED}Stopped${NC}"
	@echo -n "Python API: "; lsof -ti:$(PYTHON_API_PORT) > /dev/null 2>&1 && echo -e "${GREEN}Running on port $(PYTHON_API_PORT)${NC}" || echo -e "${RED}Stopped${NC}"

.PHONY: info
info: ## Show project information
	@echo -e "${BLUE}Energence.ai - Project Information${NC}"
	@echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
	@echo "Project:    AI Knowledge Base Platform"
	@echo "By:         Battalion Energy"
	@echo "Repository: https://github.com/battalion-energy/ai_knowledgebase"
	@echo ""
	@echo "URLs when running:"
	@echo "  Next.js:    http://localhost:$(NEXT_PORT)"
	@echo "  Python API: http://localhost:$(PYTHON_API_PORT)"
	@echo "  API Docs:   http://localhost:$(PYTHON_API_PORT)/docs"
	@echo "  Prisma:     http://localhost:5555 (when studio is running)"
	@echo ""
	@echo "Run 'make help' to see all available commands"

# ========================================
# Quick Commands (Aliases)
# ========================================

.PHONY: d
d: dev ## Alias for 'make dev'

.PHONY: b
b: build ## Alias for 'make build'

.PHONY: t
t: test ## Alias for 'make test'

.PHONY: s
s: status ## Alias for 'make status'

.PHONY: up
up: docker-up ## Alias for 'make docker-up'

.PHONY: down
down: docker-down ## Alias for 'make docker-down'