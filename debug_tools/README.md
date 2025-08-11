# Debug Tools

This directory contains comprehensive debugging and testing tools for the RAG system, designed to help developers understand, test, and troubleshoot the codebase QA tool.

## 🎯 Overview

The debug tools provide a complete testing and debugging ecosystem for the RAG codebase QA tool. They include:

- **Core Debug Tools**: UI wrappers around core functionality for inspection
- **Comprehensive Test Suites**: End-to-end testing of all functionality
- **Quality Assurance**: Performance and accuracy testing
- **Real-time Logging**: Detailed logging for troubleshooting

## 🔧 Core Debug Tools

### `debug_tools.py`
Main debug tools class that provides comprehensive debugging functionality:
- **Vector Database Inspection**: Analyze database statistics and content
- **Chunk Analysis**: Examine chunk quality and distribution
- **Retrieval Testing**: Test retrieval quality and performance
- **Configuration Debugging**: Verify system configuration
- **Session State Management**: Uses actual core methods from session state

**Key Principle**: Debug tools are UI wrappers around core functionality, not recreators.

```python
from debug_tools import DebugTools

# Create debug tools instance
debug_tools = DebugTools(project_config, ollama_model, ollama_endpoint, project_dir)

# Use debug tools
files = debug_tools.get_available_files()
results = debug_tools.test_retrieval("MainActivity")
```

### `chunk_analyzer.py`
Chunk analysis tools for debugging semantic chunking:
- **Analyze Chunk Quality**: Examine chunk distribution and metadata
- **File-Specific Analysis**: Analyze chunks for specific files
- **Metadata Inspection**: Review extracted metadata quality
- **Uses Actual Retriever**: Uses retriever from session state

### `retrieval_tester.py`
Interactive retrieval testing tools:
- **Single Query Testing**: Test individual queries
- **Multiple Query Testing**: Test multiple queries simultaneously
- **Query Comparison**: Compare different query results
- **Performance Metrics**: Measure retrieval speed and accuracy

### `db_inspector.py`
Database inspection and analysis tools:
- **Vector Database Statistics**: Comprehensive database analysis
- **File Distribution Analysis**: Analyze file processing patterns
- **Database Health Checks**: Verify database integrity
- **Performance Metrics**: Database performance analysis

### `query_runner.py`
Query execution and analysis tools:
- **Predefined Queries**: Execute common debug queries
- **Query Analysis**: Analyze query results and performance
- **Custom Queries**: Run custom debug queries
- **Performance Metrics**: Query execution metrics

### `vector_db_inspector.py`
Vector database specific inspection tools:
- **Chroma Database Analysis**: Detailed Chroma database inspection
- **Embedding Model Compatibility**: Check embedding model compatibility
- **Database Structure Inspection**: Analyze database structure
- **Collection Analysis**: Examine database collections

## 🧪 Test Suites

### `ai_debug_tools/developer_test_suite.py`
**Complete End-to-End Testing Suite**

This is the main test suite that developers should run to verify all functionalities:

```bash
cd debug_tools/ai_debug_tools
python developer_test_suite.py
```

**Test Coverage**:
- ✅ **Project Setup**: Configuration and validation
- ✅ **Ollama Connectivity**: Model availability and connection
- ✅ **Embedding Dimension Fix**: Consistent embedding models (768 vs 4096 dimensions)
- ✅ **RAG Building**: Index creation and management
- ✅ **Query Processing**: Chat functionality with satisfaction scoring
- ✅ **UI Functionality**: Complete UI testing including rebuild index

**Features**:
- **Comprehensive Logging**: Detailed logs for all operations
- **Real-world Testing**: Tests actual rebuild scenarios and UI interactions
- **Performance Metrics**: Measures build time, retrieval speed, satisfaction scores
- **Error Handling**: Robust error detection and reporting
- **Detailed Reports**: Generates comprehensive test reports

## 🚀 Production Deployment

**⚠️ CRITICAL: Before shipping to production, always run both test suites:**

```bash
# 1. Run comprehensive test suite
python developer_test_suite.py

# 2. Run quality assurance tests  
python quality_test_suite.py

# 3. Verify all tests pass (100% success rate required)
```

**Why this is essential:**
- ✅ Catches breaking changes before they reach production
- ✅ Validates model compatibility (embedding dimensions, Ollama connectivity)
- ✅ Tests UI functionality (rebuild, debug tools, chat)
- ✅ Ensures quality (query processing, context building)
- ✅ Validates centralized configuration (model settings)

**Never deploy with failing tests!**

### `ai_debug_tools/test_core_integration.py`
**Debug Tools Integration Testing**

Tests that debug tools work correctly with core functionality:

```bash
python test_core_integration.py
```

**Test Coverage**:
- ✅ **Core Integration**: Imports and configuration
- ✅ **Git Tracking**: File reading from git_tracking.json
- ✅ **Chunk Analyzer**: Chunk analysis functionality
- ✅ **Retrieval Tester**: Retrieval testing functionality
- ✅ **DebugTools Class**: DebugTools class functionality
- ✅ **Error Handling**: Edge cases and error scenarios

### `ai_debug_tools/quality_test_suite.py`
**Quality and Performance Testing**

Tests RAG system quality and performance:

```bash
python quality_test_suite.py
```

**Test Coverage**:
- ✅ **Answer Relevance**: Tests answer quality and relevance
- ✅ **Query Processing**: Tests query processing quality
- ✅ **Response Accuracy**: Measures response accuracy
- ✅ **Performance Metrics**: Tests system performance

### `ai_debug_tools/embedding_dimension_test.py`
**Embedding Model Testing**

Tests embedding model compatibility and dimension consistency:

```bash
python embedding_dimension_test.py
```

**Test Coverage**:
- ✅ **Dimension Compatibility**: Tests embedding dimension consistency
- ✅ **Model Switching**: Tests model switching functionality
- ✅ **Embedding Quality**: Tests embedding quality analysis

## 🧪 Testing

### 🚀 Production Testing (Before Shipping)

**⚠️ CRITICAL: Run these 3 test files before any production deployment:**

#### 1. Primary Test Suite
```bash
cd debug_tools/ai_debug_tools
python developer_test_suite.py
```
**Covers:** Complete end-to-end testing (Project Setup, Ollama, Embedding, RAG, Query, UI)

#### 2. Quality Assurance Test
```bash
python quality_test_suite.py
```
**Covers:** Quality assurance and performance testing with specific questions

#### 3. Debug Tools Integration Test
```bash
python test_core_integration.py
```
**Covers:** Debug tools integration validation with core modules

### 📊 Test Files Internal Coverage

#### `developer_test_suite.py` (Primary Umbrella)
**Internal calls:**
```
├── test_runner.py          # Test execution, reporting, result management
├── test_suite.py           # Core test implementations (5 tests: setup, ollama, embedding, rag, query)
├── ui_tests.py             # UI functionality tests (rebuild, debug tools, chat, session)
├── test_helpers.py         # Common utilities (TestConfig, MockSessionState, MockLogPlaceholder)
├── embedding_dimension_test.py  # Embedding dimension diagnostics and fixes
└── quality_test_suite.py   # Quality testing (embedding, rag, question quality)
```

#### `quality_test_suite.py` (Secondary Umbrella)
**Internal calls:**
```
├── quality_test_suite.py   # Self-contained (embedding compatibility, rag building, question quality)
└── embedding_dimension_test.py  # Can be called independently for embedding fixes
```

#### `test_core_integration.py` (Tertiary Standalone)
**Internal calls:**
```
└── test_core_integration.py  # Self-contained (core imports, git tracking, chunk analyzer, retrieval tester, debug tools)
```

### 🔍 Additional Testing
```bash
# Check logs for debugging
tail -50 logs/debug_tools.log
```

## 🚀 Quick Start Guide

## 🔍 Debug Tools Usage

### In the UI
1. **Enable Debug Mode**: Click the app title 5 times or check "Debug Mode" in sidebar
2. **Access Debug Tools**: Use the debug tabs in the UI
3. **Inspect Results**: View detailed analysis and logs

### Programmatically
```python
from debug_tools import DebugTools
from core.config import ProjectConfig

# Create debug tools
project_config = ProjectConfig(project_type="android", project_dir="/path/to/project")
debug_tools = DebugTools(project_config, model_config.get_ollama_model(), model_config.get_ollama_endpoint(), "/path/to/project")

# Test functionality
files = debug_tools.get_available_files()
results = debug_tools.test_retrieval("MainActivity")
inspection = debug_tools.inspect_vector_db()
```

## 📊 Logging and Monitoring

### Log Files
- `logs/debug_tools.log`: Debug tool operations
- `logs/rag_manager.log`: RAG operations
- `logs/build_rag.log`: Index building
- `logs/git_tracking.log`: File tracking

### Logging Best Practices
```python
from logger import log_to_sublog

# Comprehensive logging with clear markers
log_to_sublog(project_dir, "debug_tools.log", f"=== OPERATION STARTED ===")
log_to_sublog(project_dir, "debug_tools.log", f"Session state keys: {list(st.session_state.keys())}")

# Error logging with full context
log_to_sublog(project_dir, "debug_tools.log", f"=== OPERATION FAILED ===")
log_to_sublog(project_dir, "debug_tools.log", f"Error type: {type(e)}")
log_to_sublog(project_dir, "debug_tools.log", f"Error message: {str(e)}")
```

## 🐛 Common Issues and Solutions

### 1. Embedding Dimension Mismatch
**Error**: `Collection expecting embedding with dimension of 768, got 4096`

**Solution**: Ensure `load_existing_rag_index()` uses same embedding model as `build_rag()`

### 2. Session State Issues
**Error**: `No retriever available - RAG system not ready`

**Solution**: Check if `st.session_state.get("retriever")` exists before using

### 3. Metadata Access Errors
**Error**: `'str' object has no attribute 'get'`

**Solution**: Use safe metadata access:
```python
metadata = getattr(doc, 'metadata', {})
if not isinstance(metadata, dict):
    metadata = {}
```

## 🎯 Best Practices

### For Developers
1. **Use Session State**: Access existing objects, don't recreate
2. **Add Comprehensive Logging**: Log every step for debugging
3. **Test Incrementally**: Make small changes and test immediately
4. **Check Logs First**: Always examine logs before making changes
5. **Use Existing Methods**: Leverage core functionality, don't duplicate

### For Testing
1. **Run Full Test Suite**: Use `developer_test_suite.py` for comprehensive testing
2. **Check Logs**: Always examine relevant log files
3. **Test UI Functionality**: Verify all UI features work correctly
4. **Validate Rebuild**: Test rebuild index functionality thoroughly
5. **Monitor Performance**: Track build time and retrieval speed

## 📈 Performance Metrics

### Test Results Example
```
📊 FINAL SUMMARY:
   Total Tests: 6
   Successful: 6
   Warnings: 0
   Failed: 0
   Success Rate: 100.0%
   Average Satisfaction: 8.6/10
   Overall Status: SUCCESS
```

### Key Metrics
- **Build Time**: Time to build RAG index
- **Retrieval Speed**: Time to retrieve relevant documents
- **Satisfaction Score**: User satisfaction with responses (1-10)
- **Success Rate**: Percentage of successful operations
- **Error Rate**: Percentage of failed operations

## 🔧 Advanced Usage

### Custom Debug Queries
```python
# Test specific functionality
results = debug_tools.test_retrieval("MainActivity")
chunks = debug_tools.analyze_file_chunks("app/src/main/java/com/example/MainActivity.kt")
inspection = debug_tools.inspect_vector_db()
```

### Performance Testing
```python
# Test retrieval performance
import time
start_time = time.time()
results = debug_tools.test_retrieval("MainActivity")
end_time = time.time()
print(f"Retrieval time: {end_time - start_time:.2f}s")
```

### Error Debugging
```python
# Check logs for errors
import os
log_file = os.path.join(project_dir, "logs", "debug_tools.log")
with open(log_file, 'r') as f:
    logs = f.read()
    print(logs)
```

## 📝 File Structure

```
debug_tools/
├── debug_tools.py          # Main debug tools class
├── chunk_analyzer.py       # Chunk analysis tools
├── retrieval_tester.py     # Retrieval testing tools
├── db_inspector.py         # Database inspection
├── query_runner.py         # Query execution
├── vector_db_inspector.py  # Vector DB inspection
├── __init__.py            # Package initialization
├── README.md              # This file
└── ai_debug_tools/       # Test files
    ├── developer_test_suite.py      # Main test suite
    ├── quality_test_suite.py        # Quality tests
    ├── embedding_dimension_test.py  # Embedding tests
    ├── run_comprehensive_tests.py   # Test runner
    └── test_core_integration.py    # Debug tools tests
```

## 🎉 Success Indicators

### Working System Indicators
✅ **RAG System Ready**:
- `st.session_state.get("retriever")` exists
- `st.session_state.get("qa_chain")` exists
- No embedding dimension errors

✅ **Debug Tools Working**:
- Chunk analyzer shows processed files
- Retrieval tester returns results
- No `'str' object has no attribute 'get'` errors

✅ **Performance Good**:
- Fast query responses
- Accurate retrieval results
- No dimension mismatches

This comprehensive debug tools documentation should enable developers to effectively test, debug, and improve the RAG codebase QA tool.