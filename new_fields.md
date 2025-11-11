-- Adds the new column to store the vectors
ALTER TABLE `question`
ADD COLUMN `embedding` BLOB;

-- Creates the high-performance index on the new column
-- This requires MySQL 8.0.34+
CREATE VECTOR INDEX `idx_question_embedding`
ON `question` (`embedding`) USING HNSW;


