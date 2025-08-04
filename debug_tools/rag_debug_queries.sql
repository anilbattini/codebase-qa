-- =============================================================================
-- RAG PIPELINE DEBUG QUERIES
-- =============================================================================
-- This file contains comprehensive SQL queries to debug each step of the RAG pipeline
-- Usage: Run these queries against the Chroma SQLite database (chroma.sqlite3)

-- =============================================================================
-- 1. DATABASE OVERVIEW QUERIES
-- =============================================================================

-- Basic database information
SELECT 
    COUNT(*) as total_embeddings,
    COUNT(DISTINCT metadata->>'$.source') as unique_files,
    AVG(LENGTH(content)) as avg_chunk_length,
    MIN(LENGTH(content)) as min_chunk_length,
    MAX(LENGTH(content)) as max_chunk_length
FROM embeddings;

-- Database size and table information
SELECT 
    name as table_name,
    sql as table_schema
FROM sqlite_master 
WHERE type='table';

-- =============================================================================
-- 2. CHUNKING QUALITY ANALYSIS
-- =============================================================================

-- Chunk length distribution analysis
SELECT 
    CASE 
        WHEN LENGTH(content) < 100 THEN 'Very Short (<100)'
        WHEN LENGTH(content) < 500 THEN 'Short (100-500)'
        WHEN LENGTH(content) < 1000 THEN 'Medium (500-1000)'
        WHEN LENGTH(content) < 2000 THEN 'Long (1000-2000)'
        ELSE 'Very Long (>2000)'
    END as length_category,
    COUNT(*) as chunk_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM embeddings), 2) as percentage
FROM embeddings
GROUP BY length_category
ORDER BY chunk_count DESC;

-- File-level chunk distribution
SELECT 
    metadata->>'$.source' as file_path,
    COUNT(*) as chunk_count,
    AVG(LENGTH(content)) as avg_chunk_length,
    MIN(LENGTH(content)) as min_chunk_length,
    MAX(LENGTH(content)) as max_chunk_length,
    COUNT(DISTINCT metadata->>'$.type') as chunk_type_count
FROM embeddings
WHERE metadata->>'$.source' IS NOT NULL
GROUP BY metadata->>'$.source'
ORDER BY chunk_count DESC
LIMIT 20;

-- Chunk type analysis
SELECT 
    metadata->>'$.type' as chunk_type,
    COUNT(*) as count,
    AVG(LENGTH(content)) as avg_length,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM embeddings), 2) as percentage
FROM embeddings
WHERE metadata->>'$.type' IS NOT NULL
GROUP BY metadata->>'$.type'
ORDER BY count DESC;

-- =============================================================================
-- 3. METADATA QUALITY ANALYSIS
-- =============================================================================

-- Metadata completeness analysis
SELECT 
    COUNT(*) as total_chunks,
    SUM(CASE WHEN metadata->>'$.source' IS NOT NULL THEN 1 ELSE 0 END) as has_source,
    SUM(CASE WHEN metadata->>'$.class_names' IS NOT NULL THEN 1 ELSE 0 END) as has_class_names,
    SUM(CASE WHEN metadata->>'$.function_names' IS NOT NULL THEN 1 ELSE 0 END) as has_function_names,
    SUM(CASE WHEN metadata->>'$.screen_name' IS NOT NULL THEN 1 ELSE 0 END) as has_screen_name,
    SUM(CASE WHEN metadata->>'$.business_logic_indicators' IS NOT NULL THEN 1 ELSE 0 END) as has_business_logic,
    SUM(CASE WHEN metadata->>'$.ui_elements' IS NOT NULL THEN 1 ELSE 0 END) as has_ui_elements,
    SUM(CASE WHEN metadata->>'$.dependencies' IS NOT NULL THEN 1 ELSE 0 END) as has_dependencies,
    SUM(CASE WHEN metadata->>'$.api_endpoints' IS NOT NULL THEN 1 ELSE 0 END) as has_api_endpoints,
    SUM(CASE WHEN metadata->>'$.has_semantic_anchors' = 'true' THEN 1 ELSE 0 END) as has_semantic_anchors
FROM embeddings;

-- Sample metadata for inspection
SELECT 
    id,
    metadata->>'$.source' as source,
    metadata->>'$.class_names' as class_names,
    metadata->>'$.function_names' as function_names,
    metadata->>'$.screen_name' as screen_name,
    metadata->>'$.type' as chunk_type,
    metadata->>'$.has_semantic_anchors' as has_anchors,
    LENGTH(content) as content_length
FROM embeddings
WHERE metadata->>'$.source' IS NOT NULL
ORDER BY RANDOM()
LIMIT 10;

-- Class and function distribution
SELECT 
    metadata->>'$.class_names' as class_names,
    COUNT(*) as count
FROM embeddings
WHERE metadata->>'$.class_names' IS NOT NULL
GROUP BY metadata->>'$.class_names'
ORDER BY count DESC
LIMIT 20;

SELECT 
    metadata->>'$.function_names' as function_names,
    COUNT(*) as count
FROM embeddings
WHERE metadata->>'$.function_names' IS NOT NULL
GROUP BY metadata->>'$.function_names'
ORDER BY count DESC
LIMIT 20;

-- =============================================================================
-- 4. SEMANTIC ANALYSIS
-- =============================================================================

-- Semantic anchors analysis
SELECT 
    SUM(CASE WHEN metadata->>'$.has_semantic_anchors' = 'true' THEN 1 ELSE 0 END) as chunks_with_anchors,
    SUM(CASE WHEN metadata->>'$.has_semantic_anchors' = 'false' THEN 1 ELSE 0 END) as chunks_without_anchors,
    COUNT(*) as total_chunks,
    ROUND(SUM(CASE WHEN metadata->>'$.has_semantic_anchors' = 'true' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as anchor_percentage
FROM embeddings;

-- Business logic indicators
SELECT 
    metadata->>'$.business_logic_indicators' as business_logic,
    COUNT(*) as count
FROM embeddings
WHERE metadata->>'$.business_logic_indicators' IS NOT NULL
GROUP BY metadata->>'$.business_logic_indicators'
ORDER BY count DESC
LIMIT 15;

-- UI elements analysis
SELECT 
    metadata->>'$.ui_elements' as ui_elements,
    COUNT(*) as count
FROM embeddings
WHERE metadata->>'$.ui_elements' IS NOT NULL
GROUP BY metadata->>'$.ui_elements'
ORDER BY count DESC
LIMIT 15;

-- =============================================================================
-- 5. RETRIEVAL PERFORMANCE ANALYSIS
-- =============================================================================

-- Embedding statistics
SELECT 
    COUNT(*) as total_embeddings,
    AVG(LENGTH(embedding)) as avg_embedding_size,
    MIN(LENGTH(embedding)) as min_embedding_size,
    MAX(LENGTH(embedding)) as max_embedding_size
FROM embeddings;

-- Distance distribution (if available)
SELECT 
    distance,
    COUNT(*) as count
FROM embeddings
WHERE distance IS NOT NULL
GROUP BY distance
ORDER BY distance;

-- Sample embeddings for analysis
SELECT 
    id,
    metadata->>'$.source' as source,
    LENGTH(embedding) as embedding_size,
    distance,
    metadata->>'$.type' as chunk_type
FROM embeddings
ORDER BY RANDOM()
LIMIT 10;

-- =============================================================================
-- 6. FILE PROCESSING STATISTICS
-- =============================================================================

-- File extension distribution
SELECT 
    SUBSTR(metadata->>'$.source', -4) as file_extension,
    COUNT(*) as chunk_count,
    COUNT(DISTINCT metadata->>'$.source') as file_count,
    AVG(LENGTH(content)) as avg_chunk_length
FROM embeddings
WHERE metadata->>'$.source' IS NOT NULL
GROUP BY SUBSTR(metadata->>'$.source', -4)
ORDER BY chunk_count DESC;

-- Top files by chunk count
SELECT 
    metadata->>'$.source' as file_path,
    COUNT(*) as chunk_count,
    AVG(LENGTH(content)) as avg_chunk_length,
    COUNT(DISTINCT metadata->>'$.type') as chunk_type_count
FROM embeddings
WHERE metadata->>'$.source' IS NOT NULL
GROUP BY metadata->>'$.source'
ORDER BY chunk_count DESC
LIMIT 15;

-- =============================================================================
-- 7. DEBUGGING SPECIFIC ISSUES
-- =============================================================================

-- Find chunks without semantic anchors
SELECT 
    id,
    metadata->>'$.source' as source,
    metadata->>'$.type' as chunk_type,
    LENGTH(content) as content_length,
    SUBSTR(content, 1, 100) as content_preview
FROM embeddings
WHERE metadata->>'$.has_semantic_anchors' = 'false'
ORDER BY LENGTH(content) DESC
LIMIT 10;

-- Find very short chunks (potential issues)
SELECT 
    id,
    metadata->>'$.source' as source,
    metadata->>'$.type' as chunk_type,
    LENGTH(content) as content_length,
    content
FROM embeddings
WHERE LENGTH(content) < 50
ORDER BY LENGTH(content);

-- Find very long chunks (potential issues)
SELECT 
    id,
    metadata->>'$.source' as source,
    metadata->>'$.type' as chunk_type,
    LENGTH(content) as content_length,
    SUBSTR(content, 1, 200) as content_preview
FROM embeddings
WHERE LENGTH(content) > 3000
ORDER BY LENGTH(content) DESC
LIMIT 10;

-- Find chunks with missing metadata
SELECT 
    id,
    metadata->>'$.source' as source,
    metadata->>'$.type' as chunk_type,
    CASE 
        WHEN metadata->>'$.class_names' IS NULL THEN 'Missing class names'
        WHEN metadata->>'$.function_names' IS NULL THEN 'Missing function names'
        WHEN metadata->>'$.screen_name' IS NULL THEN 'Missing screen name'
        ELSE 'Other missing metadata'
    END as missing_field
FROM embeddings
WHERE metadata->>'$.class_names' IS NULL 
   OR metadata->>'$.function_names' IS NULL
   OR metadata->>'$.screen_name' IS NULL
ORDER BY metadata->>'$.source'
LIMIT 20;

-- =============================================================================
-- 8. PERFORMANCE ANALYSIS
-- =============================================================================

-- Database size analysis
SELECT 
    'embeddings' as table_name,
    COUNT(*) as row_count,
    SUM(LENGTH(content)) as total_content_size,
    SUM(LENGTH(embedding)) as total_embedding_size
FROM embeddings
UNION ALL
SELECT 
    'collections' as table_name,
    COUNT(*) as row_count,
    0 as total_content_size,
    0 as total_embedding_size
FROM collections;

-- Index analysis (if available)
SELECT 
    name as index_name,
    sql as index_schema
FROM sqlite_master 
WHERE type='index';

-- =============================================================================
-- 9. CUSTOM DEBUG QUERIES
-- =============================================================================

-- Query to find specific patterns in content
SELECT 
    id,
    metadata->>'$.source' as source,
    metadata->>'$.type' as chunk_type,
    SUBSTR(content, 1, 150) as content_preview
FROM embeddings
WHERE content LIKE '%error%' OR content LIKE '%exception%' OR content LIKE '%null%'
ORDER BY metadata->>'$.source'
LIMIT 10;

-- Query to analyze specific file types
SELECT 
    metadata->>'$.source' as file_path,
    COUNT(*) as chunk_count,
    GROUP_CONCAT(DISTINCT metadata->>'$.type') as chunk_types
FROM embeddings
WHERE metadata->>'$.source' LIKE '%.kt'
GROUP BY metadata->>'$.source'
ORDER BY chunk_count DESC
LIMIT 10;

-- Query to find duplicate content (potential issues)
SELECT 
    content_hash,
    COUNT(*) as duplicate_count,
    GROUP_CONCAT(metadata->>'$.source') as sources
FROM (
    SELECT 
        content,
        LOWER(REPLACE(REPLACE(content, ' ', ''), '\n', '')) as content_hash,
        metadata->>'$.source' as source
    FROM embeddings
)
GROUP BY content_hash
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC
LIMIT 10;

-- =============================================================================
-- 10. EXPORT QUERIES FOR EXTERNAL ANALYSIS
-- =============================================================================

-- Export chunk statistics for external analysis
SELECT 
    id,
    metadata->>'$.source' as source,
    metadata->>'$.type' as chunk_type,
    LENGTH(content) as content_length,
    metadata->>'$.has_semantic_anchors' as has_anchors,
    metadata->>'$.class_names' as class_names,
    metadata->>'$.function_names' as function_names,
    metadata->>'$.screen_name' as screen_name,
    metadata->>'$.business_logic_indicators' as business_logic,
    metadata->>'$.ui_elements' as ui_elements,
    metadata->>'$.dependencies' as dependencies,
    metadata->>'$.api_endpoints' as api_endpoints,
    LENGTH(embedding) as embedding_size,
    distance
FROM embeddings
ORDER BY metadata->>'$.source', id;

-- Export file-level statistics
SELECT 
    metadata->>'$.source' as file_path,
    COUNT(*) as total_chunks,
    AVG(LENGTH(content)) as avg_chunk_length,
    MIN(LENGTH(content)) as min_chunk_length,
    MAX(LENGTH(content)) as max_chunk_length,
    COUNT(DISTINCT metadata->>'$.type') as chunk_type_count,
    SUM(CASE WHEN metadata->>'$.has_semantic_anchors' = 'true' THEN 1 ELSE 0 END) as chunks_with_anchors,
    SUM(CASE WHEN metadata->>'$.class_names' IS NOT NULL THEN 1 ELSE 0 END) as chunks_with_class_names,
    SUM(CASE WHEN metadata->>'$.function_names' IS NOT NULL THEN 1 ELSE 0 END) as chunks_with_function_names
FROM embeddings
WHERE metadata->>'$.source' IS NOT NULL
GROUP BY metadata->>'$.source'
ORDER BY total_chunks DESC; 