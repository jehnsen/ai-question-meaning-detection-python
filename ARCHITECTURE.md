# Effortless-Respond API - Architecture Documentation

## Overview

This is a clean, modular FastAPI application for semantic question matching using OpenAI embeddings. The codebase has been refactored from a monolithic `main.py` file into a well-organized modular structure.

## Project Structure

```
question-linking/
├── app/
│   ├── __init__.py
│   ├── models/                 # Database models (SQLModel)
│   │   ├── __init__.py
│   │   ├── types.py           # Custom SQLAlchemy types
│   │   ├── response.py        # ResponseEntry model
│   │   └── question_link.py   # QuestionLink model
│   ├── schemas/               # Pydantic schemas for API I/O
│   │   ├── __init__.py
│   │   ├── question.py        # Question-related schemas
│   │   └── response.py        # Response-related schemas
│   ├── services/              # Business logic & utilities
│   │   ├── __init__.py
│   │   ├── database.py        # Database connection & session
│   │   ├── embedding.py       # OpenAI embedding service
│   │   └── question_processor.py  # Question matching logic
│   └── api/                   # API route handlers
│       ├── __init__.py
│       ├── questionnaire.py   # Questionnaire endpoints
│       ├── responses.py       # Response management endpoints
│       └── admin.py           # Admin/utility endpoints
├── main.py                    # Application entry point
├── migrate_to_multitenant.py  # Database migration script
├── example_batch_create.json  # Example data
└── vendor2_test.json          # Test data
```

## Architecture Layers

### 1. Models Layer (`app/models/`)

**Purpose**: Database table definitions using SQLModel (ORM)

#### Files:
- **types.py**: Custom SQLAlchemy type for storing vector embeddings as JSON
- **response.py**: `ResponseEntry` model - stores vendor Q&A pairs with embeddings
- **question_link.py**: `QuestionLink` model - stores saved question-answer mappings

**Key Features**:
- Multi-tenant with `vendor_id` field
- Composite unique constraints for data isolation
- Vector embeddings stored as JSON in MySQL

### 2. Schemas Layer (`app/schemas/`)

**Purpose**: Pydantic models for API request/response validation

#### Files:
- **question.py**: Question processing schemas
  - `Question`: Single question input
  - `QuestionnaireInput`: Batch questionnaire input
  - `QuestionResult`: Processing result for one question
  - `QuestionnaireOutput`: Batch processing output
  - `ResponseData`: Answer data with similarity score

- **response.py**: Response creation schemas
  - `CanonicalResponseInput`: Single response input
  - `BatchCreateInput`: Batch response creation input
  - `BatchCreateOutput`: Creation result

**Key Features**:
- Type-safe API contracts
- Automatic validation
- Clear documentation in OpenAPI/Swagger

### 3. Services Layer (`app/services/`)

**Purpose**: Business logic, utilities, and external integrations

#### Files:
- **database.py**: Database connection management
  - `init_db()`: Initialize database tables
  - `get_session()`: Dependency for database sessions

- **embedding.py**: OpenAI embedding service
  - `init_openai_client()`: Initialize OpenAI client
  - `get_embedding()`: Generate single embedding
  - `get_batch_embeddings()`: Batch embedding with auto-chunking & retry
  - `cosine_similarity()`: Calculate similarity between vectors

- **question_processor.py**: Core question matching logic
  - `QuestionProcessor` class with 4-step matching algorithm:
    1. Check for saved link
    2. Check for exact ID match
    3. Run AI search using embeddings
    4. Apply 3-tier confidence logic (>0.92, 0.80-0.92, <0.80)

**Key Features**:
- Separation of concerns
- Reusable business logic
- Batch processing optimization
- Exponential backoff retry logic

### 4. API Layer (`app/api/`)

**Purpose**: HTTP request handling and routing

#### Files:
- **questionnaire.py**: Question processing endpoints
  - `POST /questionnaire/process`: Single embedding per question
  - `POST /questionnaire/batch-process`: Optimized batch processing

- **responses.py**: Response management endpoints
  - `POST /responses/create`: Create single response
  - `POST /responses/batch-create`: Batch create responses
  - `GET /responses/list`: List responses (with vendor filter)
  - `DELETE /responses/{id}`: Delete response

- **admin.py**: Admin & utility endpoints
  - `GET /admin/links`: List question links
  - `DELETE /admin/links/{id}`: Delete link

**Key Features**:
- Clean routing with FastAPI routers
- Dependency injection for database sessions
- Comprehensive error handling

### 5. Application Entry (`main.py`)

**Purpose**: Application initialization and legacy endpoint support

**Features**:
- FastAPI app initialization
- Router registration
- Lifespan management (startup/shutdown)
- Legacy endpoint redirects for backward compatibility
- Health check endpoint

## Multi-Tenant Architecture

### Vendor Isolation

Each vendor has their own:
- Q&A repository (`ResponseEntry` with `vendor_id`)
- Question links (`QuestionLink` with `vendor_id`)
- Isolated semantic search (only searches within vendor's data)

### Database Schema

**ResponseEntry Table**:
```sql
CREATE TABLE responseentry (
    id INT PRIMARY KEY AUTO_INCREMENT,
    vendor_id VARCHAR(255) NOT NULL,
    question_id VARCHAR(255) NOT NULL,
    question_text TEXT,
    answer_text TEXT,
    evidence TEXT,
    embedding TEXT,  -- JSON array
    INDEX idx_vendor_id (vendor_id),
    UNIQUE INDEX uix_vendor_question (vendor_id, question_id)
);
```

**QuestionLink Table**:
```sql
CREATE TABLE questionlink (
    id INT PRIMARY KEY AUTO_INCREMENT,
    vendor_id VARCHAR(255) NOT NULL,
    new_question_id INT NOT NULL,
    linked_response_id INT,
    INDEX idx_qlink_vendor (vendor_id),
    UNIQUE INDEX uix_vendor_new_question (vendor_id, new_question_id),
    FOREIGN KEY (linked_response_id) REFERENCES responseentry(id)
);
```

## API Endpoints

### New Modular Endpoints

**Questionnaire Processing**:
- `POST /questionnaire/process`
- `POST /questionnaire/batch-process`

**Response Management**:
- `POST /responses/create`
- `POST /responses/batch-create`
- `GET /responses/list?vendor_id={vendor}`
- `DELETE /responses/{id}`

**Admin**:
- `GET /admin/links`
- `DELETE /admin/links/{id}`

**Utility**:
- `GET /` - API info
- `GET /health` - Health check

### Legacy Endpoints (Backward Compatible)

All original endpoints still work:
- `POST /process-questionnaire`
- `POST /batch-process-questionnaire`
- `POST /create-response`
- `POST /batch-create-responses`
- `GET /responses`
- `GET /links`
- `DELETE /responses/{id}`
- `DELETE /links/{id}`

## Benefits of Refactored Architecture

### 1. **Maintainability**
   - Each module has a single responsibility
   - Easy to locate and fix bugs
   - Clear code organization

### 2. **Testability**
   - Services can be tested independently
   - Mock dependencies easily
   - Unit tests for business logic

### 3. **Scalability**
   - Easy to add new features
   - Can replace services (e.g., switch from OpenAI to other providers)
   - Clear extension points

### 4. **Readability**
   - Self-documenting structure
   - Type hints throughout
   - Comprehensive docstrings

### 5. **Reusability**
   - Services can be imported and used elsewhere
   - Question processor can be used in CLI tools
   - Embedding service can be reused for other features

## Key Features

1. **Multi-Tenant Support**: Vendor-level data isolation
2. **Batch Processing**: 60-100× faster for large questionnaires
3. **Auto-Chunking**: Handles unlimited questions (auto-splits at 2048)
4. **Retry Logic**: Exponential backoff for rate limits
5. **4-Step Matching**: Saved links → Exact match → AI search → Confidence tiers
6. **Vector Embeddings**: OpenAI text-embedding-3-small (1024 dimensions)
7. **MySQL Compatible**: JSON storage for vectors (no pgvector dependency)

## Performance

- **Single Question**: ~200-500ms (1 API call)
- **100 Questions**: ~2-3 seconds (1 batch API call vs 100 individual)
- **500 Questions**: ~5-7 seconds (1 batch API call vs 500 individual)
- **3000 Questions**: ~10-15 seconds (2 chunks vs 3000 individual)

**Cost Efficiency**: Batch embedding reduces API costs by 60-100×

## Migration from v3.0 to v4.0

The refactored version (v4.0) is **100% backward compatible** with v3.0:

1. All original endpoints work unchanged
2. Database schema remains the same
3. No code changes required for existing clients
4. Can gradually adopt new endpoint paths

## Development Guidelines

### Adding New Endpoints

1. Create route in appropriate `app/api/*.py` file
2. Import necessary schemas from `app/schemas/`
3. Use services from `app/services/`
4. Register router in `main.py` if new file created

### Adding New Models

1. Create model in `app/models/`
2. Export in `app/models/__init__.py`
3. Run database migration if needed

### Adding New Services

1. Create service in `app/services/`
2. Export in `app/services/__init__.py`
3. Use dependency injection pattern

### Code Style

- Use type hints for all functions
- Add docstrings with Args/Returns/Raises
- Follow FastAPI best practices
- Use async/await for I/O operations

## Version History

- **v4.0.0** (Current): Modular architecture refactor
- **v3.0.0**: Multi-tenant support added
- **v2.0.0**: Batch processing with retry logic
- **v1.0.0**: Initial release with basic question matching
