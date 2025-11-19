# Database Refactoring Summary: Client-Vendor Relationship

## Overview

This refactoring replaces the simple `vendor_id` string field with a proper client-vendor relationship model, enabling multiple clients per vendor with isolated question-answer pairs.

## Key Changes

### 1. Database Schema Changes

#### **clientvendor Table** (Already Exists)
```sql
CREATE TABLE clientvendor (
    id INT PRIMARY KEY AUTO_INCREMENT,
    clientid VARCHAR(255) NOT NULL,
    providerid VARCHAR(255) NOT NULL,
    clientnicknameforiendor VARCHAR(255),
    UNIQUE KEY uix_client_provider (clientid, providerid)
);
```

#### **responseentry Table**
**Before:**
```python
vendor_id: str  # Simple string identifier
answer_text: str  # Plain text answer
```

**After:**
```python
client_vendor_id: int  # Foreign key to clientvendor.id
answer: Dict[str, Any]  # JSON object with type, text, comment
```

**Answer Format:**
```json
{
  "type": "text",
  "text": "The actual answer text",
  "comment": "Optional additional notes"
}
```

#### **questionlink Table**
**Before:**
```python
vendor_id: str
```

**After:**
```python
client_vendor_id: int  # Foreign key to clientvendor.id
```

#### **matchlog Table**
**Before:**
```python
vendor_id: str
```

**After:**
```python
client_vendor_id: int  # Foreign key to clientvendor.id
```

### 2. API Changes

#### **Input Format Changes**

**Before:**
```json
{
  "vendor_id": "SkyBlackBox",
  "questions": [...]
}
```

**After:**
```json
{
  "client_id": "84.08",
  "provider_id": "SkyBlackBox",
  "questions": [...]
}
```

#### **Response Format Changes**

**Before:**
```json
{
  "results": [{
    "id": "q1",
    "status": "LINKED",
    "data": {
      "answer_text": "We comply with GDPR...",
      "evidence": "Section 2.3",
      "canonical_question_text": "What are your compliance standards?",
      "similarity_score": 0.95
    }
  }]
}
```

**After:**
```json
{
  "results": [{
    "id": "q1",
    "status": "LINKED",
    "data": {
      "answer": {
        "type": "text",
        "text": "We comply with GDPR...",
        "comment": "Updated Q4 2024"
      },
      "evidence": "Section 2.3",
      "canonical_question_text": "What are your compliance standards?",
      "similarity_score": 0.95
    }
  }]
}
```

### 3. Code Changes

#### **New Models:**
- `app/models/client_vendor.py` - ClientVendor model
- `app/models/types.py` - Added JSONType for answer storage
- `app/schemas/answer.py` - Answer schema with type, text, comment

#### **Updated Models:**
- `app/models/response.py` - ResponseEntry uses client_vendor_id and answer JSON
- `app/models/question_link.py` - QuestionLink uses client_vendor_id
- `app/models/match_log.py` - MatchLog uses client_vendor_id

#### **Updated Services:**
- `app/services/question_processor.py`:
  - Constructor now takes `client_id` and `provider_id`
  - Auto-creates/looks up `client_vendor_id`
  - Uses new Answer format
- `app/services/semantic_search.py` - Uses `client_vendor_id` for filtering

#### **Updated API Routes:**
- `app/api/questionnaire.py`:
  - `/questionnaire/process` - Accepts `client_id` and `provider_id`
  - `/questionnaire/batch-process` - Accepts `client_id` and `provider_id`
- `app/api/responses.py`:
  - `/responses/create` - Accepts `client_id`, `provider_id`, and Answer object
  - `/responses/batch-create` - Accepts `client_id`, `provider_id`
  - `/responses/list` - Filters by `client_id` and `provider_id`

## Migration Process

### Prerequisites
1. **Backup your database** before running migration
2. Ensure `clientvendor` table exists and is populated
3. Update `.env` with correct `DATABASE_URL`

### Running the Migration

```bash
python migrate_to_clientvendor.py
```

The script will:
1. Add new `client_vendor_id` and `answer` columns
2. Migrate existing `vendor_id` data to `client_vendor_id`
3. Convert `answer_text` to JSON `answer` format
4. Drop old columns
5. Add foreign key constraints
6. Update indexes
7. Verify migration success

### Migration Steps in Detail:

**Step 1:** Add new columns
- `client_vendor_id INT` to `responseentry`, `questionlink`, `matchlog`
- `answer LONGTEXT` to `responseentry`

**Step 2:** Migrate vendor_id data
- For each unique `vendor_id`, find or create matching `clientvendor` entry
- Update all references to use `client_vendor_id`

**Step 3:** Migrate answer format
- Convert all `answer_text` values to JSON format:
  ```json
  {"type": "text", "text": "<original_answer_text>", "comment": null}
  ```

**Step 4:** Drop old columns
- Remove `vendor_id` from all tables
- Remove `answer_text` from `responseentry`

**Step 5:** Add constraints
- Set `client_vendor_id` as NOT NULL
- Add foreign key constraints to `clientvendor.id`

**Step 6:** Update indexes
- Drop old `vendor_id` indexes
- Create new `client_vendor_id` indexes
- Update unique constraints

**Step 7:** Verify
- Check for NULL values
- Verify row counts
- Confirm data integrity

## Benefits

### 1. **Proper Multi-Tenancy**
- Same vendor can serve multiple clients
- Each client-vendor pair has isolated questions/answers
- Prevents conflicts when multiple clients ask similar questions

### 2. **Structured Answer Format**
- Answers include type classification
- Support for additional comments/notes
- Extensible for future answer types

### 3. **Better Data Integrity**
- Foreign key constraints ensure referential integrity
- Prevents orphaned records
- Enforces proper relationships

### 4. **Query Optimization**
- Indexed client-vendor relationships
- More efficient filtering
- Better query performance

## Example Use Cases

### Use Case 1: Multiple Clients for Same Vendor

**Scenario:** Vendor "SkyBlackBox" serves two clients: "84.08" and "MegaCorp"

**Before Refactor:**
- Problem: If both clients ask "What is your SLA?", one answer overwrites the other
- vendor_id: "SkyBlackBox"
- All questions compete for the same question_id

**After Refactor:**
- Solution: Each client-vendor pair has isolated Q&A
- Client-Vendor pairs:
  - (client_id: "84.08", provider_id: "SkyBlackBox") → client_vendor_id: 1
  - (client_id: "MegaCorp", provider_id: "SkyBlackBox") → client_vendor_id: 2
- Question "What is your SLA?" can have different answers for each client

### Use Case 2: Structured Answers

**Before:**
```json
{
  "answer_text": "Yes, we support multi-factor authentication"
}
```

**After:**
```json
{
  "answer": {
    "type": "boolean",
    "text": "Yes",
    "comment": "We support TOTP, SMS, and hardware keys as MFA options"
  }
}
```

## Testing the Refactor

### 1. Create Canonical Responses

**Endpoint:** `POST /responses/batch-create`

```json
{
  "client_id": "84.08",
  "provider_id": "SkyBlackBox",
  "responses": [
    {
      "question_id": "q1",
      "question_text": "What is your SLA?",
      "answer": {
        "type": "text",
        "text": "We guarantee 99.9% uptime",
        "comment": "Measured monthly"
      },
      "evidence": "Service Agreement Section 3.2"
    }
  ]
}
```

### 2. Process Questionnaire

**Endpoint:** `POST /questionnaire/batch-process`

```json
{
  "client_id": "84.08",
  "provider_id": "SkyBlackBox",
  "questions": [
    {
      "id": "new_q1",
      "text": "What is your uptime guarantee?"
    }
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "new_q1",
      "status": "LINKED",
      "data": {
        "answer": {
          "type": "text",
          "text": "We guarantee 99.9% uptime",
          "comment": "Measured monthly"
        },
        "evidence": "Service Agreement Section 3.2",
        "canonical_question_text": "What is your SLA?",
        "similarity_score": 0.94
      }
    }
  ]
}
```

### 3. List Responses

**Endpoint:** `GET /responses/list?client_id=84.08&provider_id=SkyBlackBox`

Returns all responses for the specified client-vendor pair.

## Rollback Plan

If you need to rollback:

1. Keep a backup of the database before migration
2. Restore from backup
3. Revert code changes using git:
   ```bash
   git checkout <previous-commit-hash>
   ```

## Important Notes

### ⚠️ Breaking Changes

This is a **BREAKING CHANGE** that affects:
- All API endpoints
- Database schema
- Data format

**You must:**
1. Update all client applications to use new API format
2. Run the migration script on production database
3. Update any external integrations

### Data Mapping Strategy

The migration script assumes:
- Existing `vendor_id` maps to both `clientid` and `providerid`
- If your data structure is different, modify `migrate_vendor_ids()` function

Example custom mapping:
```python
# If vendor_id should map to provider_id with a default client
client_id = "default_client"
provider_id = vendor_id  # Use vendor_id as provider_id
```

### Performance Considerations

- Migration time depends on database size
- Indexes are rebuilt during migration
- Recommend running during low-traffic period
- Monitor foreign key constraint creation (can be slow on large tables)

## Files Modified

### New Files:
- `app/models/client_vendor.py`
- `app/schemas/answer.py`
- `migrate_to_clientvendor.py`
- `REFACTOR_CLIENTVENDOR_SUMMARY.md`

### Modified Files:
- `app/models/response.py`
- `app/models/question_link.py`
- `app/models/match_log.py`
- `app/models/types.py`
- `app/schemas/question.py`
- `app/schemas/response.py`
- `app/schemas/__init__.py`
- `app/services/question_processor.py`
- `app/services/semantic_search.py`
- `app/api/questionnaire.py`
- `app/api/responses.py`

## Support

For questions or issues:
1. Check this document first
2. Review migration script logs
3. Verify database schema matches expected structure
4. Check API request/response formats

## Next Steps

After migration:
1. ✅ Test all API endpoints with new format
2. ✅ Verify data integrity in database
3. ✅ Update client applications
4. ✅ Update API documentation
5. ✅ Update example data files
6. ✅ Monitor for any issues
