# Installation & Testing Guide - Effortless-Respond API v5.0

## Prerequisites

- Python 3.10 or higher
- MySQL 8.0.40+ (for native VECTOR support)
- OpenAI API key

---

## Step 1: Install Dependencies

### Option A: Using Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Option B: System-wide Installation

```bash
pip install -r requirements.txt
```

---

## Step 2: Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# MySQL Database Configuration
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/effortless_respond

# OpenAI API Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### Database URL Format
```
mysql+pymysql://[username]:[password]@[host]:[port]/[database_name]
```

**Examples:**
- Local: `mysql+pymysql://root:@localhost:3306/effortless_respond`
- Remote: `mysql+pymysql://admin:mypassword@db.example.com:3306/production_db`

---

## Step 3: Create MySQL Database

### Option A: Using MySQL CLI

```bash
mysql -u root -p

# In MySQL prompt:
CREATE DATABASE effortless_respond CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### Option B: Using MySQL Workbench or phpMyAdmin
1. Open your MySQL GUI
2. Create new database: `effortless_respond`
3. Character set: `utf8mb4`
4. Collation: `utf8mb4_unicode_ci`

---

## Step 4: Initialize Database Tables

```bash
# Run this from the project root directory
python3 -c "from app.services import init_db; init_db()"
```

This will create the following tables:
- `responseentry` - Canonical Q&A pairs with embeddings
- `questionlink` - Saved question-answer mappings
- `matchlog` - Analytics logging (NEW in v5.0)

**Expected Output:**
```
CREATE TABLE responseentry ...
CREATE TABLE questionlink ...
CREATE TABLE matchlog ...
```

---

## Step 5: Start the API Server

### Development Mode (with auto-reload)

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Expected Output:**
```
Starting application...
Initializing OpenAI client...
OpenAI client initialized successfully!
Application ready!
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## Step 6: Verify Installation

### Test 1: Health Check

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{"status": "healthy", "version": "5.0.0"}
```

### Test 2: API Information

```bash
curl http://localhost:8000/
```

**Expected Response:**
```json
{
  "message": "Welcome to Effortless-Respond API v5.0 - Intelligent Fallback Chain",
  "version": "5.0.0",
  "database": "MySQL 8+ with native VECTOR support",
  "features": [...],
  "fallback_chain": [...]
}
```

### Test 3: Swagger Documentation

Open in browser:
```
http://localhost:8000/docs
```

You should see the interactive API documentation with all endpoints.

---

## Step 7: Test with Sample Data

### Create Test Canonical Responses

```bash
curl -X POST http://localhost:8000/responses/batch-create \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_id": "test_vendor",
    "responses": [
      {
        "question_id": "q1",
        "question_text": "What is your refund policy?",
        "answer_text": "Our refund policy allows returns within 30 days of purchase with original receipt.",
        "evidence": "Section 3.2 of Terms of Service"
      },
      {
        "question_id": "q2",
        "question_text": "How do I cancel my order?",
        "answer_text": "To cancel your order, log into your account and go to Order History. Click the Cancel button next to the order.",
        "evidence": null
      },
      {
        "question_id": "q3",
        "question_text": "What payment methods do you accept?",
        "answer_text": "We accept Visa, MasterCard, American Express, PayPal, and Apple Pay.",
        "evidence": "Payment Options page"
      }
    ]
  }'
```

**Expected Response:**
```json
{
  "message": "Successfully created 3 responses",
  "count": 3,
  "responses": [...]
}
```

### Test the Intelligent Fallback Chain

#### Test Case 1: Exact ID Match (Step 1)

```bash
curl -X POST http://localhost:8000/questionnaire/batch-process \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_id": "test_vendor",
    "questions": [
      {"id": "q1", "text": "Different question but same ID"}
    ]
  }'
```

**Expected:** `status: "LINKED"`, `match_method: "ID"` in logs

#### Test Case 2: Fuzzy Match (Step 2)

```bash
curl -X POST http://localhost:8000/questionnaire/batch-process \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_id": "test_vendor",
    "questions": [
      {"id": 999, "text": "Whats your refund pollicy?"}
    ]
  }'
```

**Expected:** `status: "LINKED"` (if >90% similar), `match_method: "FUZZY"` in logs

#### Test Case 3: Semantic Search (Step 3)

```bash
curl -X POST http://localhost:8000/questionnaire/batch-process \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_id": "test_vendor",
    "questions": [
      {"id": 1000, "text": "Can I get my money back?"}
    ]
  }'
```

**Expected:** `status: "LINKED"` or `"CONFIRMATION_REQUIRED"`, `match_method: "SEMANTIC"` in logs

---

## Troubleshooting

### Issue 1: ModuleNotFoundError

**Error:** `ModuleNotFoundError: No module named 'sqlmodel'`

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue 2: MySQL Connection Error

**Error:** `Can't connect to MySQL server`

**Solutions:**
1. Verify MySQL is running:
   ```bash
   # macOS
   brew services list | grep mysql

   # Linux
   systemctl status mysql
   ```

2. Check DATABASE_URL in `.env`
3. Test connection manually:
   ```bash
   mysql -u username -p -h localhost
   ```

### Issue 3: OpenAI API Key Error

**Error:** `OPENAI_API_KEY environment variable is required`

**Solution:**
1. Check `.env` file exists
2. Verify `OPENAI_API_KEY` is set correctly
3. Restart the server after updating `.env`

### Issue 4: MySQL VECTOR not supported

**Error:** Message about VECTOR_COSINE_DISTANCE not found

**Solution:**
- The system will automatically fall back to Python-based cosine similarity
- For full performance, upgrade to MySQL 8.0.40+
- Check MySQL version:
  ```bash
  mysql --version
  ```

### Issue 5: Permission Denied on Database

**Error:** `Access denied for user`

**Solution:**
```bash
# Grant necessary permissions
mysql -u root -p

GRANT ALL PRIVILEGES ON effortless_respond.* TO 'username'@'localhost';
FLUSH PRIVILEGES;
```

---

## Verifying the Refactor

### Check All Features Work

1. **ID Match:** ✅ Create response, then query with same question_id
2. **Fuzzy Match:** ✅ Query with typo in question text
3. **Semantic Search:** ✅ Query with semantically similar question
4. **Match Logging:** ✅ Check `matchlog` table has entries
5. **Batch Processing:** ✅ Send 10+ questions at once

### Query Match Logs

```bash
mysql -u username -p effortless_respond

SELECT
  question_id,
  match_method,
  confidence_score,
  final_status,
  timestamp
FROM matchlog
ORDER BY timestamp DESC
LIMIT 10;
```

**Expected Output:**
```
+-------------+--------------+------------------+--------------+---------------------+
| question_id | match_method | confidence_score | final_status | timestamp           |
+-------------+--------------+------------------+--------------+---------------------+
|        1000 | SEMANTIC     |             0.89 | CONFIRMATION | 2025-01-10 10:30:00 |
|         999 | FUZZY        |             0.92 | LINKED       | 2025-01-10 10:29:00 |
|          q1 | ID           |             1.00 | LINKED       | 2025-01-10 10:28:00 |
+-------------+--------------+------------------+--------------+---------------------+
```

---

## Performance Monitoring

### Check Cost Savings

After processing 100 questions:

```bash
mysql -u username -p effortless_respond

SELECT
  match_method,
  COUNT(*) as count,
  ROUND(AVG(confidence_score), 3) as avg_confidence
FROM matchlog
GROUP BY match_method;
```

**Expected Distribution (70-80% cost savings):**
```
+--------------+-------+-----------------+
| match_method | count | avg_confidence  |
+--------------+-------+-----------------+
| ID           |    60 |           1.000 |
| FUZZY        |    20 |           0.925 |
| SEMANTIC     |    18 |           0.870 |
| NONE         |     2 |           0.000 |
+--------------+-------+-----------------+
```

**Cost Analysis:**
- Old approach: 100 questions × $0.002 = **$0.20**
- New approach: 18 questions × $0.002 = **$0.036** (82% savings!)

---

## Next Steps

1. **Load Production Data:** Import your canonical Q&A pairs
2. **Configure Thresholds:** Adjust in `app/services/question_processor.py`
3. **Monitor Performance:** Use match logs to optimize thresholds
4. **Scale Up:** Add more workers for production load

For detailed API usage, see [API_GUIDE_V5.md](API_GUIDE_V5.md)

For architecture details, see [REFACTOR_V5_SUMMARY.md](REFACTOR_V5_SUMMARY.md)
