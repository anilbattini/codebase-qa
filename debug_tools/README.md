# Debug Tools

This directory contains comprehensive debugging and testing tools for the RAG system, designed to help developers understand, test, and troubleshoot the codebase QA tool.

## 🎯 Overview

The debug tools provide a complete testing and debugging ecosystem for the RAG codebase QA tool. They include:

- **Core Debug Tools**: UI wrappers around core functionality for inspection
- **Comprehensive Test Suites**: End-to-end testing of all functionality
- **Quality Assurance**: Performance and accuracy testing
- **Real-time Logging**: Detailed logging for troubleshooting
- **🆕 Incremental RAG Build System**: Smart rebuild logic with user confirmation

## 🆕 New Features: Incremental RAG Build System

### **Smart Rebuild Logic**
The system now intelligently determines when and how to rebuild the RAG index:

- **🔄 Incremental Rebuild**: Only processes changed files, preserving existing database
- **🔄 Full Rebuild**: Complete rebuild when no database exists or force rebuild requested
- **✅ Smart Detection**: Uses Git commit differences + working directory changes
- **🔄 User Confirmation**: Asks permission before force rebuilding when no changes detected

### **Rebuild Decision Matrix**
| Scenario | Action | User Experience |
|----------|---------|-----------------|
| No Database | Full Rebuild | Automatic, no user input needed |
| No Tracking File | Full Rebuild | Automatic, no user input needed |
| Files Changed | Incremental Rebuild | Shows "🔄 Incremental Build: Processing X changed files..." |
| No Changes | Load Existing | Shows "✅ No file changes detected" + Force Rebuild button |
| Force Rebuild | Full Rebuild | User clicks button, system confirms and rebuilds |

### **Enhanced Git Tracking**
- **Commit Difference Detection**: Uses `git diff --name-only {last_commit}..{current_commit}`
- **Working Directory Changes**: Detects uncommitted changes
- **Comprehensive Logging**: Detailed logs for debugging change detection
- **Fallback Support**: Falls back to content-hash tracking if Git fails

## 🔧 Core Debug Tools

### `debug_tools.py`
Main debug tools class that provides comprehensive debugging functionality:
- **Vector Database Inspection**: Analyze database statistics and content
- **Chunk Analysis**: Examine chunk quality and distribution
- **Retrieval Testing**: Test retrieval quality and performance
- **Configuration Debugging**: Verify system configuration
- **Session State Management**: Uses actual core methods from session state
- **🆕 Incremental Build Testing**: Test the new incremental rebuild functionality

**Key Principle**: Debug tools are UI wrappers around core functionality, not recreators.

```python
from debug_tools import DebugTools

# Create debug tools instance
debug_tools = DebugTools(project_config, ollama_model, ollama_endpoint, project_dir)

# Use debug tools
files = debug_tools.get_available_files()
results = debug_tools.test_retrieval("MainActivity")

# 🆕 Test incremental rebuild
debug_tools.test_incremental_rebuild()
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
- ✅ **🆕 Incremental RAG Building**: Test incremental vs full rebuild scenarios
- ✅ **🆕 User Confirmation Flow**: Test force rebuild confirmation logic
- ✅ **Query Processing**: Chat functionality with satisfaction scoring
- ✅ **UI Functionality**: Complete UI testing including rebuild index

**🆕 New Test Scenarios**:
- **Incremental Build Testing**: Verify only changed files are processed
- **Force Rebuild Testing**: Test user confirmation and complete rebuild
- **Git Tracking Validation**: Ensure proper change detection between commits
- **Database Preservation**: Verify existing data is preserved during incremental builds

**Features**:
- **Comprehensive Logging**: Detailed logs for all operations
- **Real-world Testing**: Tests actual rebuild scenarios and UI interactions
- **Performance Metrics**: Measures build time, retrieval speed, satisfaction scores
- **Error Handling**: Robust error detection and reporting
- **Detailed Reports**: Generates comprehensive test reports
- **🆕 Incremental Build Metrics**: Tracks incremental vs full build performance

## 🚀 Production Deployment

## 🆕 Incremental Build System Architecture

### **Core Components**

#### **1. Smart Rebuild Decision Engine**
```python
# RagManager.should_rebuild_index() returns detailed information
{
    "rebuild": True/False,
    "reason": "no_database" | "no_tracking" | "files_changed" | "no_changes",
    "files": [list_of_changed_files] | None
}
```

#### **2. Incremental Build Coordinator**
```python
# RagManager.build_rag_index() supports both modes
def build_rag_index(self, project_dir, ollama_model, ollama_endpoint, 
                    project_type, log_placeholder, 
                    incremental=False, files_to_process=None):
    if incremental and files_to_process:
        # Process only changed files, preserve database
        retriever = build_rag(..., incremental=True, files_to_process=files_to_process)
    else:
        # Full rebuild: clean database and process all files
        retriever = build_rag(..., incremental=False)
```

#### **3. Enhanced Git Tracking System**
```python
# FileHashTracker._get_git_changed_files() now detects:
# 1. Commit differences: git diff --name-only {last_commit}..{current_commit}
# 2. Working directory changes: git ls-files --others --modified --exclude-standard
# 3. Combines both for comprehensive change detection
```

#### **4. User Confirmation Interface**
```python
# App.py shows appropriate UI based on rebuild decision
if rebuild_info["reason"] == "no_changes":
    st.success("✅ No file changes detected. RAG index is up to date.")
    # Show Force Rebuild button for manual override
    if st.button("🔄 Force Rebuild"):
        st.session_state["force_rebuild"] = True
        st.rerun()
```

### **Build Modes Comparison**

| Aspect | Full Build | Incremental Build |
|--------|------------|-------------------|
| **Database Handling** | Clean and recreate | Preserve existing |
| **File Processing** | All files | Changed files only |
| **Processing Time** | Longer | Faster |
| **Resource Usage** | Higher | Lower |
| **Use Case** | Fresh setup, major changes | Regular updates, small changes |
| **User Experience** | Automatic | Shows progress with file count |

### **Performance Benefits**

- **🔄 Incremental Builds**: 3-10x faster than full rebuilds
- **💾 Database Preservation**: Maintains existing embeddings and metadata
- **📊 Smart Change Detection**: Only processes what's necessary
- **🔄 User Control**: Manual force rebuild when needed

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

### 🆕 Incremental Build Testing
```python
# Test incremental rebuild functionality
def test_incremental_build():
    # Simulate file changes
    changed_files = ["file1.kt", "file2.xml"]
    
    # Test incremental mode
    rebuild_info = rag_manager.should_rebuild_index(project_dir, False, "android")
    if rebuild_info["reason"] == "files_changed":
        print(f"Incremental rebuild: {len(rebuild_info['files'])} files")
    
    # Test force rebuild
    if st.button("🔄 Force Rebuild"):
        st.session_state["force_rebuild"] = True
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
├── FUNCTIONAL_FLOW.md     # Functional flow documentation
├── MERMAID_CHART.md       # Mermaid chart documentation
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
- `st.session_state.get("vectorstore")` exists
- No embedding dimension errors

✅ **Debug Tools Working**:
- Chunk analyzer shows processed files
- Retrieval tester returns results
- No `'str' object has no attribute 'get'` errors

✅ **Performance Good**:
- Fast query responses
- Accurate retrieval results
- No dimension mismatches

✅ **🆕 Incremental Build System Working**:
- Properly detects changed files via Git tracking
- Shows appropriate rebuild messages (incremental vs full)
- User confirmation flow works for force rebuild
- Database preservation during incremental builds

### 🆕 New Success Indicators for Incremental Builds
✅ **Smart Rebuild Detection**:
- Shows "🔄 Incremental Build: Processing X changed files..." for file changes
- Shows "🔄 Full Build: Rebuilding entire RAG index..." for full rebuilds
- Shows "✅ No file changes detected" when everything is up to date

✅ **User Experience**:
- Force Rebuild button appears when no changes detected
- Clear progress indicators for both build modes
- Proper error handling and fallbacks

✅ **Performance Improvements**:
- Incremental builds complete 3-10x faster than full rebuilds
- Existing database and embeddings are preserved
- Only necessary files are processed

## 🚀 Quick Start Guide

### Testing the New Incremental Build System

1. **Enable Debug Mode**: Click the app title 5 times or check "Debug Mode" in sidebar
2. **Test File Change Detection**: Make changes to some files and refresh the app
3. **Verify Incremental Build**: Should show "🔄 Incremental Build: Processing X changed files..."
4. **Test No Changes Scenario**: When no files changed, should show "✅ No file changes detected"
5. **Test Force Rebuild**: Click "🔄 Force Rebuild" button to trigger complete rebuild

### Debug Tools Usage

#### In the UI
1. **Enable Debug Mode**: Click the app title 5 times or check "Debug Mode" in sidebar
2. **Access Debug Tools**: Use the debug tabs in the UI
3. **Inspect Results**: View detailed analysis and logs

#### Programmatically
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

### 🆕 4. Incremental Build Issues
**Error**: `UnboundLocalError: cannot access local variable 'time' where it is not associated with a value`

**Solution**: Fixed in latest version - ensure no duplicate `import time` statements in `build_rag.py`

**Error**: Incremental builds not detecting changed files

**Solution**: Check Git tracking logs, ensure `git diff` command works, verify commit SHAs in `last_commit.json`

This comprehensive debug tools documentation should enable developers to effectively test, debug, and improve the RAG codebase QA tool, including the new incremental build system.