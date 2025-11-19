-- ============================================================================
-- DATABASE MIGRATION: vendor_id to provider_id + Answer Format
-- ============================================================================
-- This SQL script migrates the database schema from vendor_id to provider_id
-- and converts answer_text to structured JSON answer format.
--
-- IMPORTANT: Backup your database before running this script!
--
-- Usage:
--   mysql -u root -p database_name < migration.sql
-- ============================================================================

-- ============================================================================
-- STEP 1: Add new columns
-- ============================================================================
ALTER TABLE responseentry
ADD COLUMN provider_id VARCHAR(16) NULL AFTER id,
ADD COLUMN answer LONGTEXT NULL AFTER question_text;

ALTER TABLE questionlink
ADD COLUMN provider_id VARCHAR(16) NULL AFTER id;

ALTER TABLE matchlog
ADD COLUMN provider_id VARCHAR(16) NULL AFTER id;

-- ============================================================================
-- STEP 2: Migrate data from vendor_id to provider_id
-- ============================================================================
-- Note: vendor_id is stored as binary, so we cast it to CHAR
UPDATE responseentry
SET provider_id = CAST(vendor_id AS CHAR)
WHERE provider_id IS NULL AND vendor_id IS NOT NULL;

UPDATE questionlink
SET provider_id = CAST(vendor_id AS CHAR)
WHERE provider_id IS NULL AND vendor_id IS NOT NULL;

UPDATE matchlog
SET provider_id = CAST(vendor_id AS CHAR)
WHERE provider_id IS NULL AND vendor_id IS NOT NULL;

-- ============================================================================
-- STEP 3: Migrate answer_text to JSON answer format
-- ============================================================================
-- Convert answer_text to JSON with structure: {type, text, comment}
UPDATE responseentry
SET answer = JSON_OBJECT(
    'type', 'text',
    'text', COALESCE(answer_text, ''),
    'comment', NULL
)
WHERE answer IS NULL AND answer_text IS NOT NULL;

-- ============================================================================
-- STEP 4: Make provider_id NOT NULL
-- ============================================================================
ALTER TABLE responseentry
MODIFY COLUMN provider_id VARCHAR(16) NOT NULL;

ALTER TABLE questionlink
MODIFY COLUMN provider_id VARCHAR(16) NOT NULL;

ALTER TABLE matchlog
MODIFY COLUMN provider_id VARCHAR(16) NOT NULL;

-- ============================================================================
-- STEP 5: Drop old indexes and constraints
-- ============================================================================
-- Drop old vendor_id indexes (if they exist)
DROP INDEX IF EXISTS idx_vendor_id ON responseentry;
DROP INDEX IF EXISTS idx_qlink_vendor ON questionlink;
DROP INDEX IF EXISTS idx_qlink_client_vendor ON questionlink;
DROP INDEX IF EXISTS idx_matchlog_vendor ON matchlog;
DROP INDEX IF EXISTS idx_matchlog_client_vendor ON matchlog;

-- Drop old unique constraints (if they exist)
DROP INDEX IF EXISTS uix_vendor_question ON responseentry;
DROP INDEX IF EXISTS uix_vendor_new_question ON questionlink;
DROP INDEX IF EXISTS uix_clientvendor_question ON responseentry;
DROP INDEX IF EXISTS uix_clientvendor_new_question ON questionlink;

-- ============================================================================
-- STEP 6: Create new indexes on provider_id
-- ============================================================================
CREATE INDEX idx_provider_id ON responseentry(provider_id);
CREATE INDEX idx_qlink_provider ON questionlink(provider_id);
CREATE INDEX idx_matchlog_provider ON matchlog(provider_id);

-- Create unique constraints
CREATE UNIQUE INDEX uix_provider_question
ON responseentry(provider_id, question_id);

CREATE UNIQUE INDEX uix_provider_new_question
ON questionlink(provider_id, new_question_id);

-- ============================================================================
-- STEP 7: Drop old columns
-- ============================================================================
ALTER TABLE responseentry
DROP COLUMN vendor_id,
DROP COLUMN answer_text;

ALTER TABLE questionlink
DROP COLUMN vendor_id;

ALTER TABLE matchlog
DROP COLUMN vendor_id;

-- ============================================================================
-- STEP 8: Verification queries
-- ============================================================================
-- Check for NULL values
SELECT 'responseentry NULL check' as check_name,
       COUNT(*) as null_count
FROM responseentry
WHERE provider_id IS NULL OR answer IS NULL;

SELECT 'questionlink NULL check' as check_name,
       COUNT(*) as null_count
FROM questionlink
WHERE provider_id IS NULL;

SELECT 'matchlog NULL check' as check_name,
       COUNT(*) as null_count
FROM matchlog
WHERE provider_id IS NULL;

-- Row counts
SELECT 'responseentry' as table_name, COUNT(*) as row_count FROM responseentry;
SELECT 'questionlink' as table_name, COUNT(*) as row_count FROM questionlink;
SELECT 'matchlog' as table_name, COUNT(*) as row_count FROM matchlog;

-- Sample data verification
SELECT 'responseentry sample' as sample_name,
       id, provider_id, question_id,
       LEFT(answer, 100) as answer_preview
FROM responseentry
LIMIT 3;

-- ============================================================================
-- Migration Complete!
-- ============================================================================
