#!/bin/bash

# Database setup script for Energence.ai
# This script creates the database and runs migrations

echo "Setting up Energence.ai database..."

# Try to create database (will fail silently if it exists)
echo "Creating database energence_db (if not exists)..."
createdb energence_db 2>/dev/null || echo "Database may already exist, continuing..."

# Run Prisma migrations
echo "Running database migrations..."
cd apps/web && npx prisma migrate dev --name init

echo "Database setup complete!"