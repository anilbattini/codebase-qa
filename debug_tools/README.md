# RAG Pipeline Debug Tools

Comprehensive debugging tools for analyzing each step of the RAG pipeline, including chunking, metadata extraction, retrieval performance, and ranking.

## 🛠️ Available Tools

### 1. Database Inspector (`db_inspector.py`)
Comprehensive SQLite database analysis for Chroma vector database.

**Features:**
- Database overview and statistics
- Chunking quality analysis
- Metadata completeness analysis
- Retrieval performance analysis
- Semantic analysis
- File processing statistics

**Usage:**
```python
from debug_tools import ChromaDBInspector

# Analyze database
inspector = ChromaDBInspector("path/to/chroma.sqlite3")
report = inspector.generate_debug_report()
print_debug_report(report)
```

### 2. Query Runner (`query_runner.py`)
Executes specific debug queries and provides formatted output.

**Features:**
- Quick analysis for common issues
- Specific debugging for chunking, metadata, retrieval, performance
- Custom query execution
- Formatted output

**Usage:**
```python
from debug_tools import run_debug_analysis, print_quick_analysis

# Quick analysis
results = run_debug_analysis("path/to/chroma.sqlite3", "quick")
print_quick_analysis(results)

# Specific analysis
results = run_debug_analysis("path/to/chroma.sqlite3", "chunking")
```

### 3. SQL Query Collection (`rag_debug_queries.sql`)
Comprehensive collection of SQL queries for debugging each step.

**Categories:**
1. **Database Overview Queries** - Basic database information
2. **Chunking Quality Analysis** - Chunk length distribution, file-level analysis
3. **Metadata Quality Analysis** - Metadata completeness, semantic anchors
4. **Semantic Analysis** - Business logic, UI elements, dependencies
5. **Retrieval Performance Analysis** - Embedding statistics, distance distribution
6. **File Processing Statistics** - File extensions, top files by chunk count
7. **Debugging Specific Issues** - Missing metadata, very short/long chunks
8. **Performance Analysis** - Database size, index analysis
9. **Custom Debug Queries** - Pattern matching, duplicate detection
10. **Export Queries** - For external analysis

## 🔍 Debug Categories

### 1. Chunking Quality Analysis
**Issues to detect:**
- Very short chunks (<50 chars) - may indicate poor chunking
- Very long chunks (>3000 chars) - may be too large for effective retrieval
- Uneven chunk distribution across files
- Missing chunk types

**Key queries:**
```sql
-- Chunk length distribution
SELECT 
    CASE 
        WHEN LENGTH(content) < 100 THEN 'Very Short (<100)'
        WHEN LENGTH(content) < 500 THEN 'Short (100-500)'
        WHEN LENGTH(content) < 1000 THEN 'Medium (500-1000)'
        WHEN LENGTH(content) < 2000 THEN 'Long (1000-2000)'
        ELSE 'Very Long (>2000)'
    END as length_category,
    COUNT(*) as chunk_count
FROM embeddings
GROUP BY length_category
ORDER BY chunk_count DESC;

-- File-level chunk distribution
SELECT 
    metadata->>'$.source' as file_path,
    COUNT(*) as chunk_count,
    AVG(LENGTH(content)) as avg_chunk_length
FROM embeddings
GROUP BY metadata->>'$.source'
ORDER BY chunk_count DESC
LIMIT 10;
```

### 2. Metadata Quality Analysis
**Issues to detect:**
- Missing semantic anchors
- Incomplete metadata fields
- Poor class/function extraction
- Missing business logic indicators

**Key queries:**
```sql
-- Metadata completeness
SELECT 
    COUNT(*) as total_chunks,
    SUM(CASE WHEN metadata->>'$.has_semantic_anchors' = 'true' THEN 1 ELSE 0 END) as chunks_with_anchors,
    SUM(CASE WHEN metadata->>'$.class_names' IS NOT NULL THEN 1 ELSE 0 END) as chunks_with_class_names,
    SUM(CASE WHEN metadata->>'$.function_names' IS NOT NULL THEN 1 ELSE 0 END) as chunks_with_function_names
FROM embeddings;

-- Find chunks without semantic anchors
SELECT 
    id,
    metadata->>'$.source' as source,
    metadata->>'$.type' as chunk_type,
    LENGTH(content) as content_length
FROM embeddings
WHERE metadata->>'$.has_semantic_anchors' = 'false'
ORDER BY LENGTH(content) DESC
LIMIT 10;
```

### 3. Retrieval Performance Analysis
**Issues to detect:**
- Embedding size inconsistencies
- Distance distribution problems
- Poor retrieval quality

**Key queries:**
```sql
-- Embedding statistics
SELECT 
    COUNT(*) as total_embeddings,
    AVG(LENGTH(embedding)) as avg_embedding_size,
    MIN(LENGTH(embedding)) as min_embedding_size,
    MAX(LENGTH(embedding)) as max_embedding_size
FROM embeddings;

-- Sample embeddings for analysis
SELECT 
    id,
    metadata->>'$.source' as source,
    LENGTH(embedding) as embedding_size,
    metadata->>'$.type' as chunk_type
FROM embeddings
ORDER BY RANDOM()
LIMIT 10;
```

### 4. File Processing Statistics
**Issues to detect:**
- Uneven file processing
- Missing file types
- Processing errors

**Key queries:**
```sql
-- File extension distribution
SELECT 
    SUBSTR(metadata->>'$.source', -4) as file_extension,
    COUNT(*) as chunk_count,
    COUNT(DISTINCT metadata->>'$.source') as file_count
FROM embeddings
WHERE metadata->>'$.source' IS NOT NULL
GROUP BY SUBSTR(metadata->>'$.source', -4)
ORDER BY chunk_count DESC;

-- Top files by chunk count
SELECT 
    metadata->>'$.source' as file_path,
    COUNT(*) as chunk_count,
    AVG(LENGTH(content)) as avg_chunk_length
FROM embeddings
WHERE metadata->>'$.source' IS NOT NULL
GROUP BY metadata->>'$.source'
ORDER BY chunk_count DESC
LIMIT 15;
```

## 🚀 Usage Examples

### Quick Analysis
```bash
# Run quick analysis
python debug_tools/query_runner.py path/to/chroma.sqlite3 quick

# Run specific analysis
python debug_tools/query_runner.py path/to/chroma.sqlite3 chunking
python debug_tools/query_runner.py path/to/chroma.sqlite3 metadata
python debug_tools/query_runner.py path/to/chroma.sqlite3 retrieval
python debug_tools/query_runner.py path/to/chroma.sqlite3 performance
```

### Database Inspector
```bash
# Run comprehensive analysis
python debug_tools/db_inspector.py path/to/chroma.sqlite3
```

### Custom Queries
```python
from debug_tools import QueryRunner

runner = QueryRunner("path/to/chroma.sqlite3")
results = runner.run_custom_query("""
    SELECT 
        metadata->>'$.source' as file,
        COUNT(*) as chunks,
        AVG(LENGTH(content)) as avg_length
    FROM embeddings
    WHERE metadata->>'$.source' LIKE '%.kt'
    GROUP BY metadata->>'$.source'
    ORDER BY chunks DESC
    LIMIT 10;
""")
print(results)
```

## 🔧 Integration with UI

The debug tools are integrated into the Streamlit UI when debug mode is enabled:

1. **Enable debug mode**: Click the app title 5 times
2. **Access debug tools**: Check "Debug Mode" in the sidebar
3. **Use debug tabs**: 
   - Vector DB Inspector
   - Chunk Analyzer
   - Retrieval Tester
   - Build Status
   - Logs Viewer

## 📊 Expected Results

### Good Chunking Quality
- **Chunk lengths**: Most chunks between 100-2000 characters
- **Distribution**: Even distribution across files
- **Types**: Mix of class, function, import, and other chunks

### Good Metadata Quality
- **Semantic anchors**: >80% of chunks have semantic anchors
- **Class names**: >70% of chunks have class names
- **Function names**: >60% of chunks have function names
- **Business logic**: >50% of chunks have business logic indicators

### Good Retrieval Performance
- **Embedding consistency**: All embeddings have similar sizes
- **Distance distribution**: Reasonable distance spread
- **File coverage**: All relevant files processed

## 🐛 Common Issues and Solutions

### Issue: Very Short Chunks
**Cause**: Poor chunking configuration
**Solution**: Adjust chunk size parameters in chunker configuration

### Issue: Missing Semantic Anchors
**Cause**: Poor metadata extraction
**Solution**: Improve regex patterns for class/function detection

### Issue: Uneven File Processing
**Cause**: Gitignore not working properly
**Solution**: Check gitignore patterns and file filtering

### Issue: Poor Retrieval Quality
**Cause**: Embedding issues or poor chunking
**Solution**: Check embedding model and chunk quality

## 📝 Logging

All debug operations are logged to `debug_tools.log` in the project logs directory for troubleshooting.

## 🔗 Related Files

- `rag_debug_queries.sql` - Complete SQL query collection
- `db_inspector.py` - Database analysis tools
- `query_runner.py` - Query execution tools
- `debug_tools.py` - Main debug interface
- `vector_db_inspector.py` - Vector database inspection
- `chunk_analyzer.py` - Chunk analysis tools
- `retrieval_tester.py` - Retrieval testing tools