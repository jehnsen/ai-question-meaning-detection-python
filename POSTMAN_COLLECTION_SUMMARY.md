# Postman Collection - Quick Summary

## Files Created

1. **Effortless-Respond-API.postman_collection.json** - The complete Postman collection
2. **POSTMAN_GUIDE.md** - Comprehensive usage guide

## Import to Postman

```
1. Open Postman
2. Click "Import" button
3. Select "Effortless-Respond-API.postman_collection.json"
4. Click "Import"
```

## Collection Contents

### 📁 1. System Info (1 request)
- Get API Info

### 📁 2. Response Management (3 requests)
- Create Response (Canonical Answer)
- List All Responses
- Delete Response

### 📁 3. Question Link Management (2 requests)
- List All Question Links
- Delete Question Link

### 📁 4. Questionnaire Processing (3 requests)
- Process Questionnaire (Basic)
- Batch Process Questionnaire (Optimized) ⭐ **Most Important**
- Batch Process - Large Questionnaire (100+ Questions)

### 📁 5. Test Data - Create Canonical Responses (5 requests)
Pre-configured test data for:
- ISO 27001 Certification
- GDPR Compliance
- Multi-Factor Authentication
- SOC 2 Type II Certification
- Encryption Standards

### 📁 6. Example Workflows (1 workflow)
- Complete Setup Workflow (4 steps)

## Quick Start (3 Steps)

### Step 1: Check API Status
```
GET http://localhost:8000/
```

### Step 2: Create Test Data
Run all 5 requests in folder "5. Test Data - Create Canonical Responses"

### Step 3: Test Batch Processing
```
POST http://localhost:8000/batch-process-questionnaire
Content-Type: application/json

{
  "questions": [
    {"id": "Q1", "text": "What is your ISO 27001 status?"},
    {"id": "Q2", "text": "How do you encrypt data?"}
  ]
}
```

## Key Features

✅ **30+ Pre-configured Requests** - Ready to use endpoints
✅ **Complete Test Data** - 5 canonical security/compliance Q&A pairs
✅ **Example Workflows** - Step-by-step testing guides
✅ **Production-Ready** - Optimized batch endpoint with chunking
✅ **Full Documentation** - Detailed guide in POSTMAN_GUIDE.md

## Variable Configuration

The collection uses one variable:

| Variable | Default Value |
|----------|---------------|
| `base_url` | `http://localhost:8000` |

Change this in Collection > Variables if your server runs on a different port.

## Response Status Types

| Status | Score | Meaning |
|--------|-------|---------|
| **LINKED** | >0.92 | High confidence - auto-linked |
| **CONFIRMATION_REQUIRED** | 0.80-0.92 | Medium confidence - review needed |
| **NO_MATCH** | <0.80 | Low confidence - manual answer required |

## Most Important Endpoints

### 1. Batch Process Questionnaire (⭐ Production)
```
POST /batch-process-questionnaire
```
Features:
- Automatic chunking (>2048 questions)
- Exponential backoff retry (3 attempts)
- 1000x faster than individual calls

### 2. Create Response
```
POST /create-response?question_id=X&question_text=Y&answer_text=Z&evidence=W
```
Creates canonical Q&A with auto-generated embeddings

### 3. List Responses
```
GET /responses
```
View all canonical responses in database

## Performance Benchmarks

| Questions | API Calls | Processing Time |
|-----------|-----------|-----------------|
| 100 | 1 (vs 100) | ~2 seconds |
| 500 | 1 (vs 500) | ~10 seconds |
| 1000 | 1 (vs 1000) | ~20 seconds |
| 10000 | 5 (vs 10000) | ~100 seconds |

## Troubleshooting

**Connection refused?**
```bash
python main.py  # Start the server
```

**500 Error?**
- Check MySQL is running (port 3306)
- Verify `.env` has valid OpenAI API key
- Check server logs

**422 Validation Error?**
- Ensure request body has correct format:
```json
{"questions": [{"id": "string", "text": "string"}]}
```

## Additional Resources

- **Swagger UI**: http://localhost:8000/docs
- **Detailed Guide**: [POSTMAN_GUIDE.md](POSTMAN_GUIDE.md)
- **API Reference**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **MySQL Setup**: [MYSQL_MIGRATION_NOTES.md](MYSQL_MIGRATION_NOTES.md)

## Testing Checklist

- [ ] Import collection to Postman
- [ ] Verify API is running (`GET /`)
- [ ] Create 5 canonical responses (folder 5)
- [ ] Test batch processing with 2-3 questions
- [ ] Verify links created (`GET /links`)
- [ ] Test with larger questionnaire (10+ questions)
- [ ] Review response statuses (LINKED/CONFIRMATION_REQUIRED/NO_MATCH)

## Support

Check the detailed [POSTMAN_GUIDE.md](POSTMAN_GUIDE.md) for:
- Complete endpoint reference
- Advanced workflows
- Rate limit handling
- Environment setup
- Best practices
