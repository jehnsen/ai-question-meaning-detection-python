# Testing Guide for Batch Processing Endpoint

## Overview

This guide explains how to test the `/batch-process-questionnaire` endpoint with realistic data, including testing for:
- Automatic chunking (>2048 questions)
- Retry logic with exponential backoff
- Performance at scale
- 4-step processing logic

## Test Scripts

### 1. `test_batch_endpoint.py` - Realistic 1000 Question Test

**Purpose:** Test with 1000 realistic vendor risk management questions

**Features:**
- Generates 1000 realistic questions across 10 categories:
  - Information Security (ISO 27001, encryption, pen testing)
  - Data Privacy (GDPR, CCPA, data handling)
  - Business Continuity (DR, BCP, uptime SLAs)
  - Compliance (PCI DSS, HIPAA, SOC 2)
  - Access Controls (MFA, SSO, RBAC)
  - Vendor Management (subprocessors, insurance, SLAs)
  - Infrastructure (cloud, data centers, monitoring)
  - Application Security (SAST, DAST, secure SDLC)
  - Data Management (classification, DLP, encryption)
  - Risk Management (risk assessments, frameworks)

- Creates 5 canonical responses for matching
- Tests all 4 steps of processing logic
- Provides detailed performance metrics
- Saves results to JSON file

**Usage:**
```bash
# Default: 1000 questions
./venv/Scripts/python test_batch_endpoint.py

# To test with more questions (edit NUM_QUESTIONS variable)
# 3000+ questions will trigger chunking
```

**Expected Output:**
```
================================================================================
BATCH ENDPOINT TEST SUITE
================================================================================
Testing endpoint: http://localhost:8000/batch-process-questionnaire
Number of questions: 1000
Started at: 2025-01-15 14:30:00

================================================================================
STEP 1: Creating sample canonical responses
================================================================================
✓ Created: CANONICAL-ISO27001
✓ Created: CANONICAL-GDPR
✓ Created: CANONICAL-MFA
✓ Created: CANONICAL-SOC2
✓ Created: CANONICAL-ENCRYPTION

Created 5/5 canonical responses

================================================================================
STEP 2: Testing batch endpoint with 1000 questions
================================================================================

Generating 1000 realistic vendor risk questions...
✓ Generated 1000 questions

Sample questions:
  SEC-1: What encryption standards does your organization use for data at rest?...
  SEC-2: How often do you conduct penetration testing?...
  SEC-3: Do you have an ISO 27001 certification?...

Expected API chunking:
  - Total questions: 1000
  - Chunk size limit: 2048
  - Expected chunks: 1

================================================================================
MAKING BATCH API REQUEST
================================================================================
Endpoint: http://localhost:8000/batch-process-questionnaire
Starting at: 2025-01-15 14:30:05
Completed at: 2025-01-15 14:30:12
Elapsed time: 7.23 seconds
Status code: 200

================================================================================
RESULTS ANALYSIS
================================================================================

Total results: 1000

Breakdown:
  LINKED:                   234 ( 23.4%)
  CONFIRMATION_REQUIRED:    512 ( 51.2%)
  NO_MATCH:                 254 ( 25.4%)

Performance metrics:
  Questions/second:        138.31
  Average time/question:   7.23 ms

Sample results (first 10):
  [1] SEC-1: CONFIRMATION_REQUIRED → What encryption standards should be used?...
  [2] SEC-2: NO_MATCH
  [3] SEC-3: CONFIRMATION_REQUIRED → What is ISO 27001 certification?...
  [4] SEC-4: NO_MATCH
  [5] SEC-5: NO_MATCH

✓ Full results saved to: batch_test_results_1000q_20250115_143012.json

================================================================================
TEST SUMMARY
================================================================================
✓ Batch endpoint test PASSED

Key features tested:
  ✓ Batch processing with 4-step logic
  ✓ Automatic chunking for large batches
  ✓ Performance optimization
  ✓ Realistic vendor risk questions

Completed at: 2025-01-15 14:30:12
```

---

### 2. `test_retry_logic.py` - Chunking & Edge Case Tests

**Purpose:** Test edge cases, boundary conditions, and chunking behavior

**Tests Included:**

| Test | Questions | Expected Behavior |
|------|-----------|-------------------|
| Test 1 | 10 | Small batch - 1 API call |
| Test 2 | 500 | Medium batch - 1 API call |
| Test 3 | 3000 | Large batch - 2 chunks (2048+952) |
| Test 4 | 2048 | Edge case - Exactly at limit, 1 chunk |
| Test 5 | 2049 | Edge case - 1 over limit, 2 chunks |
| Test 6 | 10000 | Massive batch - 5 chunks, may trigger retry |

**Usage:**
```bash
./venv/Scripts/python test_retry_logic.py
```

**Expected Output:**
```
================================================================================
BATCH ENDPOINT - RETRY LOGIC & CHUNKING TEST SUITE
================================================================================
Started: 2025-01-15 14:35:00

Testing: http://localhost:8000/batch-process-questionnaire

================================================================================
RUNNING TESTS
================================================================================

================================================================================
TEST 1: Small Batch (10 questions)
================================================================================
Expected: 1 API call, no chunking
✓ Success: 10 results returned

================================================================================
TEST 2: Medium Batch (500 questions)
================================================================================
Expected: 1 API call, no chunking
✓ Success: 500 results returned

================================================================================
TEST 3: Large Batch (3000 questions) - Chunking Test
================================================================================
Expected: 2 chunks (2048 + 952), 2 API calls
Sending 3000 questions...
Started: 14:35:15
Completed: 14:35:28
✓ Success: 3000 results returned
  Expected 2 chunks of 2048 + 952

================================================================================
TEST 4: Edge Case (Exactly 2048 questions)
================================================================================
Expected: 1 chunk, 1 API call (no splitting)
Sending exactly 2048 questions...
✓ Success: 2048 results returned
  Should be processed in 1 chunk (at limit)

================================================================================
TEST 5: Edge Case (2049 questions - Over Boundary)
================================================================================
Expected: 2 chunks (2048 + 1), 2 API calls
Sending 2049 questions (1 over limit)...
✓ Success: 2049 results returned
  Should be split into 2 chunks (2048 + 1)

================================================================================
TEST 6: Massive Batch (10000 questions)
================================================================================
Expected: 5 chunks, 5 API calls
⚠ This test takes longer and may hit rate limits (tests retry logic)
Sending 10000 questions...
Started: 14:35:45
Watch for retry messages in server logs...
Completed: 14:36:12
✓ Success: 10000 results returned
  Processed in 5 chunks of ~2000 each

  Status breakdown:
    NO_MATCH: 9998
    CONFIRMATION_REQUIRED: 2

================================================================================
TEST SUMMARY
================================================================================

Results: 6/6 tests passed

  ✓ PASS: Small Batch (10)
  ✓ PASS: Medium Batch (500)
  ✓ PASS: Large Batch (3000)
  ✓ PASS: Edge Case (2048)
  ✓ PASS: Edge Case (2049)
  ✓ PASS: Massive Batch (10000)

================================================================================
Completed: 2025-01-15 14:36:12

🎉 All tests passed!

Features verified:
  ✓ Automatic chunking (2048 question limit)
  ✓ Boundary conditions (2048, 2049)
  ✓ Large batch processing (3000+ questions)
  ✓ Massive batch processing (10000 questions)
```

---

## Testing Retry Logic

To specifically test the retry logic with exponential backoff, you can:

### Method 1: Monitor Server Logs

When running the 10000 question test, watch the server console for retry messages:

```
Rate limit hit. Retry 1/3 after 2s...
Rate limit hit. Retry 2/3 after 4s...
Rate limit hit. Retry 3/3 after 8s...
```

### Method 2: Intentionally Trigger Rate Limits

Run multiple large batches simultaneously:

```bash
# Terminal 1
./venv/Scripts/python test_retry_logic.py

# Terminal 2 (immediately after)
./venv/Scripts/python test_retry_logic.py

# Terminal 3 (immediately after)
./venv/Scripts/python test_retry_logic.py
```

This increases the chance of hitting OpenAI's rate limits, triggering the retry logic.

---

## Customizing Tests

### Testing with More Questions

Edit `test_batch_endpoint.py`:

```python
# Line 13
NUM_QUESTIONS = 3000  # Change to 3000, 5000, 10000, etc.
```

### Testing Different Categories

Edit the `question_templates` list in `generate_realistic_questions()` to add your own question categories.

---

## Prerequisites

1. **Server Running:**
   ```bash
   ./venv/Scripts/python main.py
   ```

2. **Database Reset (if needed):**
   ```bash
   ./venv/Scripts/python reset_database.py 1
   ```

3. **Valid OpenAI API Key:**
   - Ensure `.env` has `OPENAI_API_KEY=sk-...`

4. **Install requests library (if needed):**
   ```bash
   ./venv/Scripts/pip install requests
   ```

---

## Interpreting Results

### Status Meanings

- **LINKED:** Question matched via saved link, exact ID, or high confidence (>92%)
- **CONFIRMATION_REQUIRED:** Medium confidence match (80-92%)
- **NO_MATCH:** Low confidence (<80%), no suitable answer found

### Performance Metrics

Good performance benchmarks:
- **Small batches (10-100):** ~100-200 questions/second
- **Medium batches (500-1000):** ~80-150 questions/second
- **Large batches (3000+):** ~50-100 questions/second

Lower speeds for large batches are normal due to:
- Multiple API calls for chunking
- Database query overhead
- Network latency

---

## Troubleshooting

### Error: Connection refused
```
✗ Error: Connection refused
```
**Solution:** Start the server: `./venv/Scripts/python main.py`

### Error: 500 Internal Server Error
```
✗ Failed: Status 500
Response: RateLimitError: Rate limit exceeded after 3 retries
```
**Solution:** This is expected behavior testing retry logic. Wait 60 seconds and retry.

### Error: Database dimension mismatch
```
ValueError: expected 1024 dimensions, not 768
```
**Solution:** Reset database: `./venv/Scripts/python reset_database.py 1`

### Slow Performance
If tests are very slow (>1 second per question):
1. Check database indexes exist
2. Verify OpenAI API is responding quickly
3. Ensure server has adequate resources

---

## Cost Estimates

OpenAI embedding costs (~$0.00002 per 1K tokens):

| Questions | Est. Tokens | Est. Cost |
|-----------|-------------|-----------|
| 1000 | ~20K | $0.0004 |
| 3000 | ~60K | $0.0012 |
| 10000 | ~200K | $0.004 |

**Note:** Costs are negligible for testing. Production use with millions of questions would cost ~$40 per million questions.
