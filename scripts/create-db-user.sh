#!/bin/bash

# PostgreSQL setup script for Energence.ai
# Run this as: sudo bash scripts/create-db-user.sh

echo "Setting up PostgreSQL for Energence.ai..."

# Run commands separately to avoid transaction block issue
sudo -u postgres psql -c "CREATE USER energence WITH PASSWORD 'energence123!' CREATEDB;"
sudo -u postgres psql -c "CREATE DATABASE energence_db OWNER energence;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE energence_db TO energence;"

echo "✓ PostgreSQL setup complete!"
echo ""
echo "Database credentials:"
echo "  User: energence"
echo "  Password: energence123!"
echo "  Database: energence_db"
echo ""
echo "Connection string for .env.local:"
echo "  DATABASE_URL=\"postgresql://energence:energence123!@localhost:5432/energence_db?schema=public\""