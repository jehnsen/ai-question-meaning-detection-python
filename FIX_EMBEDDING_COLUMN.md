# Fix: "Data too long for column 'embedding'" Error

## Problem

When creating responses, you may encounter:
```
sqlalchemy.exc.DataError: (pymysql.err.DataError) (1406, "Data too long for column 'embedding' at row 1")
```

This happens because the embedding column was initially created as VARBINARY (limited size) instead of LONGBLOB (up to 4GB).

---

## Solution

You have two options:

### Option 1: Migrate Existing Database (Preserves Data)

If you have existing data you want to keep:

```bash
python migrate_to_longblob.py
```

This will:
- ✅ Alter the `embedding` column to LONGBLOB
- ✅ Preserve all existing data
- ✅ Fix the error

**Output:**
```
Starting migration: embedding column to LONGBLOB...
Table 'responseentry' found. Altering embedding column...
✓ Successfully altered embedding column to LONGBLOB
Migration completed successfully!
```

---

### Option 2: Reset Database (Fresh Start)

If you don't have data to preserve:

```bash
python reset_and_init_db.py
```

**⚠️ WARNING:** This will delete all existing data!

This will:
- ❌ Drop all tables (responseentry, questionlink, matchlog)
- ✅ Recreate tables with correct schema
- ✅ Use LONGBLOB for embeddings

**Confirmation Required:**
```
⚠️  WARNING: This will delete all existing data!
Tables to be dropped: responseentry, questionlink, matchlog
Type 'YES' to continue: YES
```

**Output:**
```
Dropping tables...
✓ Dropped questionlink
✓ Dropped matchlog
✓ Dropped responseentry

✓ All tables dropped successfully

Recreating tables with correct schema...
✓ Database initialized successfully!

Tables created:
  - responseentry (with LONGBLOB for embeddings)
  - questionlink (with foreign key to responseentry)
  - matchlog (for analytics)
```

---

## Verification

After running either migration, test the fix:

```bash
# Start the server
uvicorn main:app --reload

# Test creating a response (use Postman or curl)
curl -X POST http://localhost:8000/responses/batch-create \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_id": "test_vendor",
    "responses": [{
      "question_id": "test_q1",
      "question_text": "What is your refund policy?",
      "answer_text": "Our refund policy allows returns...",
      "evidence": "Section 3.2"
    }]
  }'
```

**Expected Response:**
```json
{
  "message": "Successfully created 1 responses",
  "count": 1,
  "responses": [...]
}
```

If you get this response, the fix worked! ✅

---

## Technical Details

### What Changed

**Before (VARBINARY):**
- Default size: ~65,535 bytes
- Embedding JSON: ~23,000 characters
- **Result:** Data too long error ❌

**After (LONGBLOB):**
- Max size: 4GB
- Embedding JSON: ~23,000 characters
- **Result:** Fits easily ✅

### File Modified

[app/models/types.py](app/models/types.py):
```python
# Before
from sqlalchemy import TypeDecorator, LargeBinary

class VectorType(TypeDecorator):
    impl = LargeBinary  # Limited size

# After
from sqlalchemy.dialects.mysql import LONGBLOB

class VectorType(TypeDecorator):
    impl = LONGBLOB  # Up to 4GB
```

---

## Prevention

For future projects, always use LONGBLOB for embedding vectors in MySQL:

```sql
CREATE TABLE responseentry (
    ...
    embedding LONGBLOB  -- ✅ Correct
    -- NOT VARBINARY     -- ❌ Too small
);
```

---

## Need Help?

If you encounter issues:

1. **Check MySQL version:** `mysql --version`
   - Requires MySQL 5.7+ for LONGBLOB support

2. **Check table structure:**
   ```sql
   DESCRIBE responseentry;
   ```
   - `embedding` column should show `longblob`

3. **Check existing data:**
   ```sql
   SELECT COUNT(*) FROM responseentry;
   ```
   - If you have data, use Option 1 (migrate)
   - If empty, use Option 2 (reset)

4. **Still stuck?** Check the error logs for details
