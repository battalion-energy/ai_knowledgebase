.PHONY: help install dev-install index search interactive stats clear clean test lint format run build

PYTHON := python
UV := uv
PROJECT_NAME := energy-data-search
SRC_DIR := src/energy_data_search

help: ## Show this help message
	@echo "============================================================"
	@echo "      Energy Data Search - Makefile Commands"
	@echo "============================================================"
	@echo ""
	@echo "Core Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Quick Start:"
	@echo "  1. \033[36mmake full-reindex\033[0m   - Complete reset and reindex"
	@echo "  2. \033[36mmake update\033[0m         - Index only new files"
	@echo "  3. \033[36mmake search QUERY=\"...\"\033[0m - Search documents"

install: ## Install project dependencies using uv
	$(UV) sync

dev-install: ## Install project with development dependencies
	$(UV) sync --dev

build: ## Build the project package
	$(UV) build

run: ## Run the CLI application
	$(UV) run python -m energy_data_search

index: ## Index all documents from source directories
	$(UV) run energy-search index

index-clear: ## Clear and reindex all documents
	$(UV) run energy-search index --clear

search: ## Search for documents (usage: make search QUERY="your query here")
	@if [ -z "$(QUERY)" ]; then \
		echo "Please provide a query: make search QUERY=\"your query\""; \
		exit 1; \
	fi
	$(UV) run energy-search search "$(QUERY)"

interactive: ## Start interactive query mode
	$(UV) run energy-search interactive

stats: ## Show index statistics
	$(UV) run energy-search stats

status: ## Show detailed indexing status and tracking info
	$(UV) run energy-search status

clear: ## Clear all indexed documents
	$(UV) run energy-search clear

update: ## Index only new/modified documents (incremental update)
	$(UV) run energy-search update

update-auto: ## Auto-index new documents without confirmation
	$(UV) run energy-search update --auto

check-new: ## Check for new documents without indexing
	$(UV) run energy-search status | grep "New Files"

reindex-file: ## Force reindex a specific file (usage: make reindex-file FILE=/path/to/file)
	@if [ -z "$(FILE)" ]; then \
		echo "Please provide a file: make reindex-file FILE=/path/to/file"; \
		exit 1; \
	fi
	$(UV) run energy-search reindex "$(FILE)"

reset-tracker: ## Reset index tracker (marks all files as unindexed)
	$(UV) run energy-search reset-tracker

full-reindex: ## Delete database and reindex everything with progress tracking
	@echo "============================================================"
	@echo "    FULL REINDEX - Complete Database Reset & Rebuild"
	@echo "============================================================"
	@echo ""
	$(UV) run energy-search full-reindex

full-reindex-yes: ## Full reindex without confirmation (automated)
	@echo "Starting automated full reindex..."
	$(UV) run energy-search full-reindex --yes

clean-db: ## Delete ChromaDB database only (use with caution)
	@echo "Deleting ChromaDB database..."
	@rm -rf data/chroma_db
	@echo "✓ Database deleted"

test: ## Run tests
	$(UV) run pytest tests/ -v

test-coverage: ## Run tests with coverage report
	$(UV) run pytest tests/ --cov=$(SRC_DIR) --cov-report=html --cov-report=term

lint: ## Run linting checks
	$(UV) run ruff check $(SRC_DIR)
	$(UV) run mypy $(SRC_DIR) --ignore-missing-imports

format: ## Format code using ruff
	$(UV) run ruff format $(SRC_DIR)
	$(UV) run ruff check --fix $(SRC_DIR)

clean: ## Clean build artifacts and cache files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

venv: ## Create and activate virtual environment with pyenv
	pyenv virtualenv 3.12.11 $(PROJECT_NAME) || true
	pyenv local $(PROJECT_NAME)
	@echo "Virtual environment created. Run 'pyenv activate $(PROJECT_NAME)' to activate"

setup: venv install ## Complete project setup (create venv and install dependencies)
	@echo "Project setup complete!"

docker-build: ## Build Docker container for the application
	docker build -t $(PROJECT_NAME):latest .

docker-run: ## Run the application in Docker
	docker run -it --rm \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/.env:/app/.env \
		$(PROJECT_NAME):latest

update-deps: ## Update all dependencies to latest versions
	$(UV) sync --upgrade

freeze: ## Export requirements to requirements.txt
	$(UV) pip freeze > requirements.txt

quick-test: ## Run a quick test query
	@$(UV) run python -c "from energy_data_search.query.search_engine import EnergyDataSearchEngine; \
		engine = EnergyDataSearchEngine(); \
		print('Engine initialized successfully!')"