# Quick Setup Guide

## Step 1: Install PostgreSQL

### Windows (Using XAMPP)
Since you're using XAMPP, you can either:

**Option A: Use existing PostgreSQL installation**
1. Check if PostgreSQL is already installed: `psql --version`

**Option B: Install PostgreSQL separately**
1. Download from: https://www.postgresql.org/download/windows/
2. Run installer and remember your postgres password
3. Default port: 5432

## Step 2: Install pgvector Extension

### Windows
```bash
# Download prebuilt binaries from:
# https://github.com/pgvector/pgvector/releases

# Or use Docker (easier option):
# See docker-compose.yml in this project
```

## Step 3: Create Database

```bash
# Open PostgreSQL command line (psql)
# Windows: Search for "SQL Shell (psql)" in Start Menu

# Login as postgres user, then run:
CREATE DATABASE effortless_respond;

# Connect to the database
\c effortless_respond

# Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

# Verify it's installed
SELECT * FROM pg_extension WHERE extname = 'vector';
```

## Step 4: Configure Environment

```bash
# Copy the example file
cp .env.example .env

# Edit .env and update DATABASE_URL with your credentials
# Example: DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/effortless_respond
```

## Step 5: Run the Application

```bash
# Activate virtual environment
source venv/Scripts/activate  # Windows

# Run the application
python main.py

# The application will:
# 1. Create the pgvector extension (if not exists)
# 2. Create all database tables
# 3. Load the AI model
# 4. Start the server on http://localhost:8000
```

## EASIER OPTION: Use Docker

If you have Docker installed, use the provided docker-compose.yml:

```bash
# Start PostgreSQL with pgvector
docker-compose up -d

# The database will be ready at:
# postgresql://postgres:postgres@localhost:5432/effortless_respond

# Then run the FastAPI app
source venv/Scripts/activate
python main.py
```

## Testing the API

Once running, visit: http://localhost:8000/docs

The interactive API documentation will allow you to test all endpoints directly from your browser.
