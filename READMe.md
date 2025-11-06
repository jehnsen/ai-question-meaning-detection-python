# Effortless-Respond API

A FastAPI application that finds saved answers to new questions using AI-driven semantic search with PostgreSQL and pgvector.

## Features

- **Semantic Search**: Uses sentence-transformers (all-MiniLM-L6-v2) for AI-driven question matching
- **User-Confirmed Links**: Stores mappings between new questions and confirmed answers
- **Vector Similarity**: Leverages pgvector for efficient cosine similarity search
- **Smart Workflow**: Checks existing links first, then uses AI if no link exists
- **Threshold-Based Suggestions**: Only suggests answers with >80% similarity

## Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with pgvector extension
- **ORM**: SQLModel (built on SQLAlchemy)
- **AI Model**: sentence-transformers (all-MiniLM-L6-v2)
- **Validation**: Pydantic

## Prerequisites

- Python 3.10+
- PostgreSQL 12+ with pgvector extension
- Virtual environment (venv)

## Installation

### 1. Clone and Setup Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
source venv/Scripts/activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

Install PostgreSQL and the pgvector extension:

```bash
# Install PostgreSQL (if not already installed)
# Windows: Download from https://www.postgresql.org/download/windows/
# macOS: brew install postgresql
# Linux: sudo apt-get install postgresql

# Install pgvector extension
# Follow instructions at: https://github.com/pgvector/pgvector
```

Create the database:

```sql
CREATE DATABASE effortless_respond;
```

### 3. Environment Configuration

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Edit `.env` with your database credentials:

```
ENV:
DATABASE_URL=postgresql://username:password@localhost:5432/effortless_respond
DATABASE_URL=mysql+pymysql://root:password123@localhost:3306/sbb_db
# OpenAI API Configuration
OPENAI_API_KEY=
```

## Running the Application

### Development Mode

```bash
# Activate virtual environment
source venv/Scripts/activate  # Windows
source venv/bin/activate      # macOS/Linux

# Run the application
python main.py

# Or use uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### 1. Process Question (Main Endpoint)

**POST** `/process-question`

Process a new question and find matching answers.

**Request Body:**
```json
{
  "question_text": "What are the ISO 27001 requirements?"
}
```

**Response Types:**

**a) Linked Response** (existing confirmed link found):
```json
{
  "status": "linked",
  "data": {
    "answer": "ISO 27001 requires...",
    "evidence": "ISO 27001:2013",
    "canonical_question": "What are ISO 27001 requirements?"
  }
}
```

**b) Confirmation Required** (similar questions found):
```json
{
  "status": "confirmation_required",
  "suggestions": [
    {
      "response": {
        "answer": "ISO 27001 requires...",
        "evidence": "ISO 27001:2013",
        "canonical_question": "What are ISO 27001 requirements?"
      },
      "similarity_score": 0.9245
    }
  ]
}
```

**c) No Match Found** (no similar questions above threshold):
```json
{
  "status": "no_match_found"
}
```

### 2. Create Link

**POST** `/create-link`

Create a confirmed link between a new question and an existing response.

**Request Body:**
```json
{
  "new_question_text": "What does ISO 27001 require?",
  "confirmed_response_id": 1
}
```

**Response:**
```json
{
  "id": 1,
  "new_question_text": "What does ISO 27001 require?",
  "linked_response_id": 1
}
```

### 3. Create New Response

**POST** `/create-new-response`

Create a new response entry with answer and embedding.

**Request Body:**
```json
{
  "question_text": "What are GDPR requirements?",
  "answer_text": "GDPR requires...",
  "evidence": "GDPR Article 32"
}
```

**Response:**
```json
{
  "id": 2,
  "canonical_question": "What are GDPR requirements?",
  "answer": "GDPR requires...",
  "evidence": "GDPR Article 32",
  "embedding": [0.123, 0.456, ...]
}
```

### 4. Utility Endpoints

**GET** `/responses` - List all response entries
**GET** `/links` - List all question links
**DELETE** `/responses/{response_id}` - Delete a response
**DELETE** `/links/{link_id}` - Delete a link

## Database Schema

### ResponseEntry Table

| Column              | Type        | Description                          |
|---------------------|-------------|--------------------------------------|
| id                  | Integer     | Primary key                          |
| canonical_question  | String      | Original source question (indexed)   |
| answer              | String      | Saved answer text                    |
| evidence            | String      | Compliance info (nullable)           |
| embedding           | Vector(384) | 384-dimension vector                 |

### QuestionLink Table

| Column              | Type    | Description                              |
|---------------------|---------|------------------------------------------|
| id                  | Integer | Primary key                              |
| new_question_text   | String  | New question text (indexed, unique)      |
| linked_response_id  | Integer | Foreign key to responseentry.id          |

## Workflow

### Acceptance Criterion #1: AI Search
When a question is processed, the system generates an embedding and searches for similar questions using cosine similarity.

### Acceptance Criterion #2: Confirmation Required
If similar questions are found (similarity > 80%), the system returns suggestions for user confirmation.

### Acceptance Criterion #3: Existing Links First
Before running AI search, the system checks if a user-confirmed link already exists for the exact question text.

## Example Usage

### 1. Create a new response

```bash
curl -X POST "http://localhost:8000/create-new-response" \
  -H "Content-Type: application/json" \
  -d '{
    "question_text": "What are ISO 27001 security controls?",
    "answer_text": "ISO 27001 specifies 114 security controls...",
    "evidence": "ISO 27001:2013 Annex A"
  }'
```

### 2. Process a similar question

```bash
curl -X POST "http://localhost:8000/process-question" \
  -H "Content-Type: application/json" \
  -d '{
    "question_text": "What security controls does ISO 27001 have?"
  }'
```

### 3. Confirm a suggestion

```bash
curl -X POST "http://localhost:8000/create-link" \
  -H "Content-Type: application/json" \
  -d '{
    "new_question_text": "What security controls does ISO 27001 have?",
    "confirmed_response_id": 1
  }'
```

### 4. Process the same question again

```bash
curl -X POST "http://localhost:8000/process-question" \
  -H "Content-Type: application/json" \
  -d '{
    "question_text": "What security controls does ISO 27001 have?"
  }'
# Now returns status: "linked" immediately
```

## Configuration

### Similarity Threshold

The default similarity threshold is 0.80 (80%). You can adjust this in [main.py:228](main.py#L228):

```python
SIMILARITY_THRESHOLD = 0.80  # Adjust as needed
```

### AI Model

The application uses `all-MiniLM-L6-v2` by default. To use a different model, modify [main.py:81](main.py#L81):

```python
model = SentenceTransformer('your-model-name')
```

Note: If you change the model, update the embedding dimension in the Vector field accordingly.

## Troubleshooting

### Database Connection Error

Ensure PostgreSQL is running and the DATABASE_URL is correct:

```bash
# Check PostgreSQL status
# Windows: Check services
# macOS: brew services list
# Linux: sudo systemctl status postgresql
```

### pgvector Extension Error

Install the pgvector extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Model Download Issues

The first run will download the AI model (~80MB). Ensure you have internet connection and sufficient disk space.

## Deactivating Virtual Environment

```bash
deactivate
```

## License

MIT License

## Support

For issues and questions, please create an issue in the repository.