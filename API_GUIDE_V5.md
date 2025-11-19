# Effortless-Respond API v5.0 - Quick Reference Guide

## Base URL
```
http://localhost:8000
```

---

## Core Endpoints

### 1. Process Questionnaire (Batch Optimized) ⭐ RECOMMENDED
**Endpoint:** `POST /questionnaire/batch-process`

**Description:** Process multiple questions using the Intelligent Fallback Chain with optimized batch embedding.

**Request Body:**
```json
{
  "vendor_id": "vendor1",
  "questions": [
    {"id": 1, "text": "What is your refund policy?"},
    {"id": 2, "text": "What is your return policy?"},
    {"id": 3, "text": "How do I cancel my order?"}
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "id": 1,
      "status": "LINKED",
      "data": {
        "answer_text": "Our refund policy allows...",
        "evidence": "Section 3.2 of Terms",
        "canonical_question_text": "What is your refund policy?",
        "similarity_score": 1.0
      }
    },
    {
      "id": 2,
      "status": "LINKED",
      "data": {
        "answer_text": "Our return policy allows...",
        "evidence": null,
        "canonical_question_text": "What is your refund policy?",
        "similarity_score": 0.95
      }
    },
    {
      "id": 3,
      "status": "CONFIRMATION_REQUIRED",
      "data": {
        "answer_text": "To cancel your order...",
        "evidence": null,
        "canonical_question_text": "How can I cancel?",
        "similarity_score": 0.85
      }
    }
  ]
}
```

**Status Codes:**
- `LINKED` - Confident match found (auto-linked)
- `CONFIRMATION_REQUIRED` - Possible match, needs human review
- `NO_MATCH` - No suitable match found

---

### 2. Create Canonical Responses (Batch)
**Endpoint:** `POST /responses/batch-create`

**Description:** Create multiple canonical Q&A pairs for a vendor.

**Request Body:**
```json
{
  "vendor_id": "vendor1",
  "responses": [
    {
      "question_id": "q1",
      "question_text": "What is your refund policy?",
      "answer_text": "Our refund policy allows returns within 30 days...",
      "evidence": "Section 3.2 of Terms"
    },
    {
      "question_id": "q2",
      "question_text": "How do I cancel my order?",
      "answer_text": "To cancel your order, visit your account page...",
      "evidence": null
    }
  ]
}
```

**Response:**
```json
{
  "message": "Successfully created 2 responses",
  "count": 2,
  "responses": [
    {
      "question_id": "q1",
      "question_text": "What is your refund policy?",
      "status": "created"
    },
    {
      "question_id": "q2",
      "question_text": "How do I cancel my order?",
      "status": "created"
    }
  ]
}
```

---

### 3. List Canonical Responses
**Endpoint:** `GET /responses/list?vendor_id=vendor1`

**Description:** List all canonical responses for a vendor.

**Response:**
```json
[
  {
    "id": 1,
    "vendor_id": "vendor1",
    "question_id": "q1",
    "question_text": "What is your refund policy?",
    "answer_text": "Our refund policy allows...",
    "evidence": "Section 3.2 of Terms"
  }
]
```

---

### 4. List Question Links (Admin)
**Endpoint:** `GET /admin/links`

**Description:** View all saved question-to-response links.

**Response:**
```json
[
  {
    "id": 1,
    "vendor_id": "vendor1",
    "new_question_id": 123,
    "linked_response_id": 5
  }
]
```

---

## Understanding the Intelligent Fallback Chain

### Flow Diagram
```
Question Received
     ↓
Step 1: ID Match?
     ├─ Yes → LINKED (confidence: 1.0) ✓
     └─ No ↓
Step 2: Fuzzy Match (>0.90)?
     ├─ Yes → LINKED (confidence: 0.90-1.0) ✓
     └─ No ↓
Step 3: Semantic Search (AI)
     ↓
Step 4: Confidence Check
     ├─ >0.92 → LINKED (auto-save)
     ├─ ≥0.80 → CONFIRMATION_REQUIRED
     └─ <0.80 → NO_MATCH
```

### Match Methods Logged
- **`ID`** - Found via saved link or exact ID match
- **`FUZZY`** - Found via Levenshtein distance (>90% similar)
- **`SEMANTIC`** - Found via AI embedding search
- **`NONE`** - No match found

---

## Cost Optimization

### Old Approach (v4.0)
```
Every question → OpenAI API call ($$$)
100 questions = 100 API calls = $0.20
```

### New Approach (v5.0)
```
Step 1 (ID Match): 60% of questions → $0.00
Step 2 (Fuzzy):    20% of questions → $0.00
Step 3 (Semantic): 20% of questions → OpenAI call

100 questions = ~20 API calls = $0.04 (80% savings!)
```

---

## Example Usage Scenarios

### Scenario 1: First-Time Question
```bash
# Question: "What's your refund policy?"
# Result: No ID match → No fuzzy match → AI search
# Match found with 0.95 confidence → AUTO-LINKED
# Logged as: match_method="SEMANTIC", confidence=0.95, status="LINKED"
```

### Scenario 2: Slight Typo
```bash
# Question: "Whats your refund pollicy?"
# Result: No ID match → Fuzzy match 0.92 → LINKED
# No AI call needed! Logged as: match_method="FUZZY"
```

### Scenario 3: Repeat Question
```bash
# Question: Same as before (already linked)
# Result: ID match found → LINKED instantly
# No AI call, no fuzzy matching! Logged as: match_method="ID"
```

---

## Testing Tips

### 1. Test ID Match
```bash
# Create a response
curl -X POST http://localhost:8000/responses/batch-create \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_id": "test_vendor",
    "responses": [{
      "question_id": "test_q1",
      "question_text": "Test question?",
      "answer_text": "Test answer"
    }]
  }'

# Process with same question_id
curl -X POST http://localhost:8000/questionnaire/batch-process \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_id": "test_vendor",
    "questions": [{"id": "test_q1", "text": "Different text but same ID"}]
  }'

# Expected: LINKED via ID match (no AI call)
```

### 2. Test Fuzzy Match
```bash
# Process with typo
curl -X POST http://localhost:8000/questionnaire/batch-process \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_id": "test_vendor",
    "questions": [{"id": 999, "text": "Tst questoin?"}]
  }'

# Expected: LINKED via fuzzy match if >90% similar (no AI call)
```

### 3. Test Semantic Search
```bash
# Process with semantically similar question
curl -X POST http://localhost:8000/questionnaire/batch-process \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_id": "test_vendor",
    "questions": [{"id": 1000, "text": "How does the testing process work?"}]
  }'

# Expected: LINKED/CONFIRMATION_REQUIRED via semantic search (AI call)
```

---

## Configuration

### Environment Variables (.env)
```env
# MySQL Database
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/effortless_respond

# OpenAI API
OPENAI_API_KEY=sk-...

# Optional: Adjust thresholds in code
# app/services/question_processor.py:
#   HIGH_CONFIDENCE_THRESHOLD = 0.92
#   MEDIUM_CONFIDENCE_THRESHOLD = 0.80
#   FUZZY_MATCH_THRESHOLD = 0.90
```

---

## API Documentation
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Support & Troubleshooting

### Common Issues

**1. MySQL VECTOR not supported**
- **Solution:** System automatically falls back to Python-based cosine similarity
- **Check:** Ensure MySQL 8.0.40+ for native VECTOR support

**2. High AI costs**
- **Solution:** Ensure fuzzy matching threshold is not too high
- **Check:** Review match logs to see distribution of ID/FUZZY/SEMANTIC matches

**3. Too many CONFIRMATION_REQUIRED**
- **Solution:** Lower MEDIUM_CONFIDENCE_THRESHOLD (currently 0.80)
- **Location:** `app/services/question_processor.py`

---

## Health Check
```bash
curl http://localhost:8000/health
# Response: {"status": "healthy", "version": "5.0.0"}
```

---

## Migration from v4.0
All endpoints are **backward compatible**:
- ✅ `/process-questionnaire` → redirects to `/questionnaire/process`
- ✅ `/batch-process-questionnaire` → redirects to `/questionnaire/batch-process`
- ✅ `/batch-create-responses` → redirects to `/responses/batch-create`

**No client code changes required!**
