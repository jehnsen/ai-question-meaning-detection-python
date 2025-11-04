# Batch Processing Endpoint - Quick Guide

## Overview

The new `POST /process-questionnaire` endpoint processes multiple questions in a single API call using 4-step logic with OpenAI embeddings.

## Database Schema Changes

### ResponseEntry Table
```sql
- id (Integer, Primary Key)
- question_id (String, Unique, Indexed) -- NEW: Canonical question ID
- question_text (String) -- NEW: Question text
- answer_text (String) -- NEW: Answer text
- evidence (String, Nullable) -- Compliance evidence
- embedding (Vector(1024)) -- OpenAI 1024-dim vector
```

### QuestionLink Table
```sql
- id (Integer, Primary Key)
- new_question_id (String, Unique, Indexed) -- NEW: New question ID
- linked_response_id (Integer, Foreign Key) -- Links to responseentry.id
```

## 4-Step Processing Logic

For each question in the batch:

1. **Check Saved Link** → Query `QuestionLink` by `question.id`
   - If found → Return `LINKED` + data

2. **Check Exact ID Match** → Query `ResponseEntry` by `question.id`
   - If found → Return `LINKED` + data

3. **AI Search** → Generate embedding, find top 1 match via pgvector

4. **3-Tier Confidence Logic:**
   - **> 0.92:** Auto-create link, return `LINKED`
   - **0.80-0.92:** Return `CONFIRMATION_REQUIRED` (with data)
   - **< 0.80:** Return `NO_MATCH`

## API Endpoints

### POST /process-questionnaire (Standard)

**Use for:** Small batches (1-50 questions)
**Performance:** Sequential embedding generation (N API calls)

### POST /batch-process-questionnaire (Optimized)

**Use for:** Large batches (50-2000 questions)
**Performance:** Single batch embedding API call (1 API call for all questions)
**Speed improvement:** ~10-100x faster for large batches

**Request:**
```json
{
  "questions": [
    {
      "id": "Q001",
      "text": "What are ISO 27001 security controls?"
    },
    {
      "id": "Q002",
      "text": "What is multi-factor authentication?"
    }
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "Q001",
      "status": "LINKED",
      "data": {
        "answer_text": "ISO 27001 specifies 114 security controls...",
        "evidence": "ISO 27001:2013 Annex A",
        "canonical_question_text": "What are the main ISO 27001 controls?"
      }
    },
    {
      "id": "Q002",
      "status": "CONFIRMATION_REQUIRED",
      "data": {
        "answer_text": "Multi-factor authentication requires...",
        "evidence": "Security Best Practices",
        "canonical_question_text": "What is MFA?"
      }
    }
  ]
}
```

## Testing Steps

### 1. Reset Database (Schema Changed!)
```bash
./venv/Scripts/python reset_database.py 1
```

### 2. Start Server
```bash
./venv/Scripts/python main.py
```

### 3. Create Test Responses

**Using curl (Windows):**
```bash
curl -X POST "http://localhost:8000/create-response?question_id=ISO-27001&question_text=What%20are%20ISO%2027001%20security%20controls?&answer_text=ISO%2027001%20specifies%20114%20security%20controls.&evidence=ISO%2027001:2013%20Annex%20A"
```

**Using PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/create-response" -Method Post -Body @{
    question_id = "ISO-27001"
    question_text = "What are ISO 27001 security controls?"
    answer_text = "ISO 27001 specifies 114 security controls organized in 14 categories."
    evidence = "ISO 27001:2013 Annex A"
} -ContentType "application/x-www-form-urlencoded"
```

### 4. Test Batch Processing

**Standard endpoint (small batches):**
```bash
curl -X POST "http://localhost:8000/process-questionnaire" ^
  -H "Content-Type: application/json" ^
  -d "{\"questions\": [{\"id\": \"Q001\", \"text\": \"What security controls does ISO 27001 have?\"}, {\"id\": \"Q002\", \"text\": \"Why is MFA important?\"}]}"
```

**Optimized endpoint (large batches - RECOMMENDED for 50+ questions):**
```bash
curl -X POST "http://localhost:8000/batch-process-questionnaire" ^
  -H "Content-Type: application/json" ^
  -d "{\"questions\": [{\"id\": \"Q001\", \"text\": \"What security controls does ISO 27001 have?\"}, {\"id\": \"Q002\", \"text\": \"Why is MFA important?\"}, {\"id\": \"Q003\", \"text\": \"What is GDPR?\"}, ... ]}"
```

## Expected Behaviors

### Scenario 1: Exact ID Match
- Input: `question.id = "ISO-27001"` (exists in ResponseEntry)
- Result: `LINKED` (Step 2)

### Scenario 2: Previously Linked
- Input: `question.id = "Q001"` (exists in QuestionLink)
- Result: `LINKED` (Step 1)

### Scenario 3: High Confidence (>0.92)
- Input: Nearly identical question text
- Result: `LINKED` + auto-creates link in QuestionLink (Step 4)

### Scenario 4: Medium Confidence (0.80-0.92)
- Input: Similar but not identical question
- Result: `CONFIRMATION_REQUIRED` with suggested answer (Step 4)

### Scenario 5: Low Confidence (<0.80)
- Input: Unrelated question
- Result: `NO_MATCH` (Step 4)

## Status Codes

- `LINKED` - Answer found (via link, exact match, or high confidence AI match)
- `CONFIRMATION_REQUIRED` - Possible match found, needs user confirmation
- `NO_MATCH` - No suitable answer found

## Utility Endpoints

- `GET /responses` - List all responses
- `GET /links` - List all question links
- `DELETE /responses/{id}` - Delete response
- `DELETE /links/{id}` - Delete link

## Performance Notes

### Standard Endpoint (/process-questionnaire)
- Each question processed sequentially
- OpenAI API call made for each question needing AI search
- **500 questions needing AI search = 500 API calls**

### Optimized Endpoint (/batch-process-questionnaire)
- Questions batched into phases:
  - Phase 1: Process all Steps 1 & 2 (no API calls)
  - Phase 2: Single batch API call for all questions needing AI
  - Phase 3: Process all Steps 3 & 4 with cached embeddings
- **500 questions needing AI search = 1 API call**
- Supports up to 2048 questions in single batch
- ~10-100x faster for large batches

### Common Optimizations (Both Endpoints)
- OpenAI API calls only made if Steps 1 & 2 don't match
- High confidence matches (>0.92) auto-link for future speed
- Database queries use indexed fields for fast lookups

## Performance Comparison

| Scenario | Questions | Steps 1&2 Match | AI Search Needed | Standard Endpoint | Optimized Endpoint |
|----------|-----------|-----------------|------------------|-------------------|---------------------|
| Small batch | 10 | 3 | 7 | 7 API calls | 1 API call |
| Medium batch | 100 | 40 | 60 | 60 API calls | 1 API call |
| Large batch | 500 | 200 | 300 | 300 API calls | 1 API call |
| Very large | 1000 | 400 | 600 | 600 API calls | 1 API call |

**Recommendation:** Use `/batch-process-questionnaire` for any batch > 50 questions
