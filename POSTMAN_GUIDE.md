# Effortless-Respond API - Postman Collection Guide

## Overview

This guide covers how to use the Postman collection for testing and interacting with the Effortless-Respond API v3.0.

## Import Instructions

### Option 1: Import from File
1. Open Postman
2. Click **Import** button (top-left)
3. Select **File** tab
4. Choose `Effortless-Respond-API.postman_collection.json`
5. Click **Import**

### Option 2: Import from URL
If the collection is hosted, use the share link.

## Collection Structure

The collection is organized into 6 main folders:

### 1. System Info
- **Get API Info** - Check API status, version, and features

### 2. Response Management
- **Create Response (Canonical Answer)** - Add new canonical Q&A pairs with auto-generated embeddings
- **List All Responses** - View all stored canonical responses
- **Delete Response** - Remove a canonical response by ID

### 3. Question Link Management
- **List All Question Links** - View saved question-to-answer mappings
- **Delete Question Link** - Remove a link by ID

### 4. Questionnaire Processing
- **Process Questionnaire (Basic)** - Standard batch processing endpoint
- **Batch Process Questionnaire (Optimized)** - Production-ready endpoint with chunking and retry logic
- **Batch Process - Large Questionnaire** - Example with 10+ questions

### 5. Test Data - Create Canonical Responses
Pre-configured requests to create 5 common security/compliance canonical responses:
- ISO 27001 Certification
- GDPR Compliance
- Multi-Factor Authentication
- SOC 2 Type II Certification
- Encryption Standards

### 6. Example Workflows
- **Workflow 1: Complete Setup** - Step-by-step guide from API check to processing questionnaires

## Variables

The collection uses one environment variable:

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `base_url` | `http://localhost:8000` | API base URL |

### Setting Variables

#### Collection Variables (Recommended)
1. Click on the collection name
2. Go to **Variables** tab
3. Modify `base_url` if needed
4. Click **Save**

#### Environment Variables (Advanced)
1. Create a new environment (e.g., "Development", "Production")
2. Add variable `base_url` with appropriate value
3. Select the environment from dropdown

## Quick Start Guide

### Step 1: Verify API is Running

**Request:** `1. System Info > Get API Info`

```http
GET http://localhost:8000/
```

**Expected Response:**
```json
{
  "message": "Welcome to Effortless-Respond API v3.0",
  "docs": "/docs",
  "version": "3.0.0",
  "ai_provider": "OpenAI",
  "embedding_model": "text-embedding-3-small",
  "features": ["batch_processing", "4_step_logic", "auto_linking"]
}
```

### Step 2: Create Canonical Responses

Run all 5 requests in folder **5. Test Data - Create Canonical Responses** to populate your database with sample data.

**Example Request:** `5. Test Data > Create - ISO 27001`

```http
POST http://localhost:8000/create-response?question_id=CANONICAL-ISO27001&question_text=What is ISO 27001 certification?&answer_text=ISO 27001 is an international standard...&evidence=ISO/IEC 27001:2013
```

**Expected Response:**
```json
{
  "id": 1,
  "question_id": "CANONICAL-ISO27001",
  "question_text": "What is ISO 27001 certification?",
  "answer_text": "ISO 27001 is an international standard...",
  "evidence": "ISO/IEC 27001:2013",
  "message": "Response created successfully"
}
```

### Step 3: Process a Questionnaire

**Request:** `4. Questionnaire Processing > Batch Process Questionnaire (Optimized)`

```http
POST http://localhost:8000/batch-process-questionnaire
Content-Type: application/json

{
  "questions": [
    {
      "id": "VRM-001",
      "text": "What is your company's ISO 27001 certification status?"
    },
    {
      "id": "VRM-002",
      "text": "Describe your encryption protocols for data at rest."
    }
  ]
}
```

**Expected Response:**
```json
{
  "total_questions": 2,
  "processing_time_seconds": 1.23,
  "results": [
    {
      "id": "VRM-001",
      "status": "CONFIRMATION_REQUIRED",
      "data": {
        "canonical_question_text": "What is ISO 27001 certification?",
        "answer_text": "ISO 27001 is an international standard...",
        "evidence": "ISO/IEC 27001:2013",
        "similarity_score": 0.87
      }
    },
    {
      "id": "VRM-002",
      "status": "CONFIRMATION_REQUIRED",
      "data": {
        "canonical_question_text": "What encryption standards should be used?",
        "answer_text": "Industry-standard encryption includes AES-256...",
        "evidence": "NIST FIPS 140-2, TLS 1.3 RFC 8446",
        "similarity_score": 0.85
      }
    }
  ]
}
```

## Response Status Types

The API returns three status types based on confidence scores:

### 1. LINKED (High Confidence)
- **Similarity Score:** > 0.92
- **Meaning:** Very high confidence match - auto-linked
- **Action:** Answer can be used directly

### 2. CONFIRMATION_REQUIRED (Medium Confidence)
- **Similarity Score:** 0.80 - 0.92
- **Meaning:** Good match but requires human review
- **Action:** Review the suggested answer before using

### 3. NO_MATCH (Low Confidence)
- **Similarity Score:** < 0.80
- **Meaning:** No suitable match found
- **Action:** Manual answer required

## API Endpoints Reference

### GET Endpoints

| Endpoint | Description | Auth Required |
|----------|-------------|---------------|
| `/` | Get API info and version | No |
| `/responses` | List all canonical responses | No |
| `/links` | List all question links | No |
| `/docs` | Swagger UI documentation | No |

### POST Endpoints

| Endpoint | Description | Request Body | Auth Required |
|----------|-------------|--------------|---------------|
| `/create-response` | Create canonical response | Query params | No |
| `/process-questionnaire` | Process questionnaire (basic) | JSON | No |
| `/batch-process-questionnaire` | Process questionnaire (optimized) | JSON | No |

### DELETE Endpoints

| Endpoint | Description | Auth Required |
|----------|-------------|---------------|
| `/responses/{id}` | Delete canonical response | No |
| `/links/{id}` | Delete question link | No |

## Advanced Features

### Batch Processing Optimization

The `/batch-process-questionnaire` endpoint includes:

1. **Automatic Chunking**
   - Splits requests > 2048 questions into chunks
   - Processes each chunk sequentially

2. **Exponential Backoff Retry**
   - Retries on rate limit errors (429)
   - 3 attempts: 2s, 4s, 8s delays

3. **Single Embedding Call**
   - One OpenAI API call per chunk
   - Dramatically faster than individual calls

### Performance Comparison

| Questions | Old Endpoint | New Endpoint | Speedup |
|-----------|--------------|--------------|---------|
| 100 | 100 API calls | 1 API call | 100x |
| 500 | 500 API calls | 1 API call | 500x |
| 1000 | 1000 API calls | 1 API call | 1000x |
| 10000 | 10000 API calls | 5 API calls | 2000x |

## Testing Workflows

### Workflow 1: Complete E2E Test

Run these requests in order:

1. `1. System Info > Get API Info` - Verify API
2. `5. Test Data > Create - ISO 27001` - Add test data
3. `5. Test Data > Create - GDPR Compliance` - Add test data
4. `4. Questionnaire Processing > Batch Process Questionnaire (Optimized)` - Process
5. `3. Question Link Management > List All Question Links` - Verify links

### Workflow 2: Load Testing

1. Use `4. Questionnaire Processing > Batch Process - Large Questionnaire`
2. Modify the body to include 100-1000 questions
3. Monitor processing time in response
4. Verify all questions are processed

### Workflow 3: Data Management

1. `2. Response Management > List All Responses` - Check current data
2. `2. Response Management > Delete Response` - Clean up (use ID from list)
3. `3. Question Link Management > List All Question Links` - Check links
4. `3. Question Link Management > Delete Question Link` - Clean up links

## Troubleshooting

### Common Issues

#### Issue 1: Connection Refused
**Error:** `Error: connect ECONNREFUSED 127.0.0.1:8000`

**Solution:**
```bash
# Start the server
python main.py
```

#### Issue 2: 404 Not Found
**Error:** `404 Not Found`

**Solution:** Check that the endpoint path is correct in the request URL.

#### Issue 3: 500 Internal Server Error
**Error:** `500 Internal Server Error`

**Solutions:**
- Check server logs for detailed error
- Verify database is running (MySQL on port 3306)
- Ensure OpenAI API key is valid in `.env` file

#### Issue 4: 422 Validation Error
**Error:** `422 Unprocessable Entity`

**Solution:** Check request body matches the required schema:
```json
{
  "questions": [
    {
      "id": "string",
      "text": "string"
    }
  ]
}
```

## Environment Setup

### Development Environment
```
base_url = http://localhost:8000
```

### Production Environment
```
base_url = https://api.yourcompany.com
```

### Staging Environment
```
base_url = https://staging-api.yourcompany.com
```

## Rate Limits

The API uses OpenAI's embedding API which has rate limits:

- **Free Tier:** 3 requests/minute
- **Pay-as-you-go:** 3,000 requests/minute
- **Batch endpoint:** Automatically handles rate limits with retry logic

## Best Practices

1. **Use Batch Endpoint**
   - Always use `/batch-process-questionnaire` for production
   - Handles large volumes efficiently

2. **Create Canonical Responses First**
   - Build a library of canonical Q&A pairs
   - Better matches = higher accuracy

3. **Review CONFIRMATION_REQUIRED**
   - Don't auto-accept medium confidence matches
   - Human review improves quality

4. **Monitor Processing Time**
   - Check `processing_time_seconds` in responses
   - Optimize if consistently slow

5. **Clean Up Test Data**
   - Delete test responses and links after testing
   - Keeps database clean

## Additional Resources

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **GitHub:** (Your repository URL)
- **API Documentation:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

## Support

For issues or questions:
- Check server logs with `echo=True` SQLAlchemy logging
- Review [MYSQL_MIGRATION_NOTES.md](MYSQL_MIGRATION_NOTES.md) for database setup
- Test connection with `python create_mysql_database.py`

## Version History

### v3.0 (Current)
- MySQL database support
- Optimized batch processing
- Automatic chunking
- Exponential backoff retry

### v2.0
- PostgreSQL with pgvector
- Basic batch processing

### v1.0
- Initial release
- Single question processing
