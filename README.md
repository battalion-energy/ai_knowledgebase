# Energence.ai - AI-Enabled Energy Intelligence Platform

An advanced document search and AI-powered analysis platform for ERCOT energy market data, built by Battalion Energy.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- PostgreSQL 15+
- Python 3.10+
- pnpm (for Node.js package management)
- uv (for Python package management, optional)

### Setup

1. **Configure Database**
   
   Edit `.env.local` (or `apps/web/.env`) with your PostgreSQL credentials:
   ```env
   DATABASE_URL="postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/energence_db?schema=public"
   ```

2. **Create Database**
   
   Create the database manually:
   ```bash
   createdb -U YOUR_USER energence_db
   # OR using psql:
   psql -U YOUR_USER -c "CREATE DATABASE energence_db;"
   ```

3. **Install Dependencies & Setup**
   ```bash
   make setup
   # OR manually:
   pnpm install
   cd apps/search-api && pip install -r requirements.txt
   cd ../web && npx prisma migrate dev
   ```

4. **Start Development Servers**
   ```bash
   make dev
   # This starts both Next.js (port 3105) and Python API (port 8105)
   ```

5. **Open Browser**
   - Next.js App: http://localhost:3105
   - Python API: http://localhost:8105
   - API Docs: http://localhost:8105/docs

## 📦 Project Structure

```
ai_knowledgebase/
├── apps/
│   ├── web/                 # Next.js application
│   │   ├── app/             # App Router pages
│   │   ├── components/      # React components
│   │   ├── lib/            # Utilities
│   │   └── prisma/         # Database schema
│   └── search-api/         # Python FastAPI service
├── energy-data-search/     # ChromaDB implementation
├── ercot_code/            # ERCOT Python scripts
├── specs/                 # Architecture specifications
└── Makefile              # All commands
```

## 🛠️ Available Commands

Run `make help` to see all available commands:

### Common Commands
- `make dev` - Start development servers
- `make status` - Check service status
- `make build` - Build for production
- `make test` - Run tests
- `make clean` - Clean generated files

### Database Commands
- `make db-setup` - Setup database
- `make db-migrate` - Run migrations
- `make db-studio` - Open Prisma Studio
- `make db-reset` - Reset database

### Index Commands
- `make index-update` - Update ChromaDB index
- `make index-full` - Full reindex
- `make index-stats` - Show statistics

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env.local` and configure:

```env
# Database
DATABASE_URL="postgresql://user:password@localhost:5432/energence_db"

# NextAuth
NEXTAUTH_URL="http://localhost:3000"
NEXTAUTH_SECRET="your-secret-key"

# OpenAI (for AI chat)
OPENAI_API_KEY="sk-..."

# Data Directories
SOURCE_DATA_DIR="/pool/ssd8tb/data/iso/"
ERCOT_DATA_DIR="/pool/ssd8tb/data/iso/ERCOT/"
```

## 🏗️ Architecture

- **Frontend**: Next.js 15 with App Router, TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python) for search API
- **Database**: PostgreSQL (via Prisma) + ChromaDB (vector search)
- **Authentication**: NextAuth.js
- **UI**: Glassmorphism design with animated gradients

## 📝 License

Copyright © 2024 Battalion Energy. All rights reserved.

## 🤝 Contributing

Please read our contributing guidelines before submitting PRs.

## 📞 Support

For issues and feedback, please visit: https://github.com/battalion-energy/ai_knowledgebase/issues