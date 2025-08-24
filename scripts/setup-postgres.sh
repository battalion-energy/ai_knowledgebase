#!/bin/bash

# PostgreSQL setup script that reads credentials from .env file
# This script creates user and database based on DATABASE_URL

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}PostgreSQL Setup for Energence.ai${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Load environment variables
if [ -f ".env.local" ]; then
    export $(cat .env.local | grep -v '^#' | xargs)
elif [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${RED}Error: No .env.local or .env file found${NC}"
    echo "Please create .env.local with DATABASE_URL and DB_* variables"
    exit 1
fi

# Parse DATABASE_URL or use individual variables
if [ -n "$DATABASE_URL" ]; then
    # Parse DATABASE_URL: postgresql://user:password@host:port/database
    # Remove postgresql:// prefix
    DB_CONN="${DATABASE_URL#postgresql://}"
    
    # Extract user:password
    USER_PASS="${DB_CONN%%@*}"
    DB_USER="${USER_PASS%%:*}"
    
    # Extract password (handle URL encoding)
    TEMP_PASS="${USER_PASS#*:}"
    DB_PASSWORD="${TEMP_PASS%%@*}"
    
    # Extract host:port/database
    HOST_PORT_DB="${DB_CONN#*@}"
    HOST_PORT="${HOST_PORT_DB%%/*}"
    DB_HOST="${HOST_PORT%%:*}"
    DB_PORT="${HOST_PORT#*:}"
    
    # Extract database name
    DB_NAME_PARAMS="${HOST_PORT_DB#*/}"
    DB_NAME="${DB_NAME_PARAMS%%\?*}"
    
    # Decode URL-encoded password
    DB_PASSWORD=$(echo "$DB_PASSWORD" | sed 's/%21/!/g' | sed 's/%40/@/g' | sed 's/%23/#/g' | sed 's/%24/$/g')
else
    # Use individual variables from .env
    DB_USER="${DB_USER:-energence}"
    DB_PASSWORD="${DB_PASSWORD:-energence123!}"
    DB_NAME="${DB_NAME:-energence_db}"
    DB_HOST="${DB_HOST:-localhost}"
    DB_PORT="${DB_PORT:-5432}"
fi

echo -e "${BLUE}Database Configuration:${NC}"
echo "  User:     $DB_USER"
echo "  Database: $DB_NAME"
echo "  Host:     $DB_HOST"
echo "  Port:     $DB_PORT"
echo ""

# Function to check if user exists
user_exists() {
    sudo -u postgres psql -tAc "SELECT 1 FROM pg_user WHERE usename='$1'" | grep -q 1
}

# Function to check if database exists
db_exists() {
    sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$1'" | grep -q 1
}

# Create user if doesn't exist
echo -e "${BLUE}Step 1: Creating user '$DB_USER'...${NC}"
if user_exists "$DB_USER"; then
    echo -e "${YELLOW}User '$DB_USER' already exists, updating password...${NC}"
    sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD' CREATEDB;"
else
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD' CREATEDB;"
    echo -e "${GREEN}✓ User created${NC}"
fi

# Create database if doesn't exist
echo -e "${BLUE}Step 2: Creating database '$DB_NAME'...${NC}"
if db_exists "$DB_NAME"; then
    echo -e "${YELLOW}Database '$DB_NAME' already exists${NC}"
else
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
    echo -e "${GREEN}✓ Database created${NC}"
fi

# Grant privileges
echo -e "${BLUE}Step 3: Granting privileges...${NC}"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
echo -e "${GREEN}✓ Privileges granted${NC}"

# Test connection
echo -e "${BLUE}Step 4: Testing connection...${NC}"
if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; then
    echo -e "${GREEN}✓ Connection successful!${NC}"
else
    echo -e "${YELLOW}Warning: Could not test connection. This might be normal if pg_hba.conf requires different authentication.${NC}"
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}PostgreSQL setup complete!${NC}"
echo ""
echo -e "Connection string for .env.local:"
echo -e "${BLUE}DATABASE_URL=\"postgresql://$DB_USER:$(echo $DB_PASSWORD | sed 's/!/\%21/g')@$DB_HOST:$DB_PORT/$DB_NAME?schema=public\"${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. Run: ${GREEN}make db-migrate${NC} to create tables"
echo -e "  2. Run: ${GREEN}make dev${NC} to start the application"