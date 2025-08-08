# RAG Codebase QA Tool - Technical AI Guide

## 🎯 Project Overview

This is a **Retrieval Augmented Generation (RAG)** tool for analyzing and querying codebases. It uses semantic chunking, vector embeddings, and LLM integration to provide intelligent code analysis and Q&A capabilities.

### Core Architecture
- **Semantic Chunking**: Breaks code into meaningful chunks with metadata
- **Vector Database (Chroma)**: Stores embeddings for similarity search
- **Ollama Integration**: Uses local LLM models for embeddings and chat
- **Streamlit UI**: Interactive web interface for queries and debugging
- **Git Tracking**: Incremental processing based on file changes

## 📁 Project Structure

```
codebase-qa/
├── core/                          # Core RAG functionality
│   ├── build_rag.py              # Main RAG index builder
│   ├── rag_manager.py            # Session lifecycle management
│   ├── config.py                 # Project configuration
│   ├── model_config.py           # Centralized model configuration
│   ├── chunker_factory.py        # Code chunking strategies
│   ├── metadata_extractor.py     # Metadata extraction
│   ├── git_hash_tracker.py       # File change tracking
│   ├── logger.py                 # Centralized logging
│   ├── chat_handler.py           # Chat interaction logic
│   ├── ui_components.py          # Streamlit UI components
│   ├── process_manager.py        # Process management
│   ├── query_intent_classifier.py # Query classification
│   ├── context_builder.py        # Context building
│   ├── hierarchical_indexer.py   # Hierarchical indexing
│   └── app.py                    # Application entry point
├── debug_tools/                  # Debugging and testing tools
│   ├── debug_tools.py           # Main debug interface
│   ├── chunk_analyzer.py        # Chunk analysis tools
│   ├── retrieval_tester.py      # Retrieval testing
│   ├── db_inspector.py          # Database inspection
│   ├── query_runner.py          # Query execution
│   ├── vector_db_inspector.py   # Vector DB analysis
│   └── ai_debug_tools/          # Test suites
│       ├── developer_test_suite.py      # Main test suite
│       ├── quality_test_suite.py        # Quality tests
│       ├── test_helpers.py              # Test utilities
│       ├── test_runner.py               # Test execution
│       ├── test_suite.py                # Core test suite
│       └── ui_tests.py                  # UI tests
├── cli.py                        # Command line interface
└── requirements.txt              # Dependencies
```

## 🔧 Core Components Deep Dive

### 1. RAG Index Building (`core/build_rag.py`)

**Purpose**: Creates the vector database from source code files.

**Key Features**:
- **Embedding Model Selection**: Uses `nomic-embed-text:latest` for 768-dimensional embeddings
- **Semantic Chunking**: Breaks code into meaningful chunks with metadata
- **Git Tracking**: Only processes changed files for efficiency
- **Metadata Extraction**: Extracts class names, function names, dependencies

**Critical Implementation Details**:
```python
# Embedding model selection (CRITICAL for dimension consistency)
embedding_model = "nomic-embed-text:latest"  # 768 dimensions
embeddings = OllamaEmbeddings(model=embedding_model, base_url=ollama_endpoint)
vectorstore = Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embeddings)
```

**AI Tool Lesson**: Always use the same embedding model for building and loading. Dimension mismatches (768 vs 4096) cause fatal errors.

### 2. Session Management (`core/rag_manager.py`)

**Purpose**: Manages RAG session lifecycle and ensures consistency.

**Key Methods**:
- `build_rag_index()`: Creates new RAG index
- `load_existing_rag_index()`: Loads existing index (CRITICAL FIX)
- `should_rebuild_index()`: Determines if rebuild is needed

**Critical Fix Applied**:
```python
# OLD (caused dimension mismatch):
embeddings = OllamaEmbeddings(model=ollama_model, base_url=ollama_endpoint)

# NEW (uses same model as build_rag.py):
embedding_model = "nomic-embed-text:latest"  # Same as build_rag.py
embeddings = OllamaEmbeddings(model=embedding_model, base_url=ollama_endpoint)
```

**AI Tool Lesson**: When loading existing data, use the same configuration that was used to create it.

### 3. Centralized Model Configuration (`core/model_config.py`)

**Purpose**: Single source of truth for all model settings.

**Key Features**:
- **Centralized Configuration**: All model settings in one place
- **Getter/Setter Methods**: Clean interface for accessing settings
- **Default Values**: Consistent defaults across the application
- **Easy Updates**: Change settings in one place, affects entire app

**Usage**:
```python
from model_config import model_config

# Get settings
ollama_model = model_config.get_ollama_model()
embedding_model = model_config.get_embedding_model()

# Set settings
model_config.set_ollama_model("llama3.1:latest")
model_config.set_embedding_model("nomic-embed-text:latest")
```

**AI Tool Lesson**: Use centralized configuration to avoid inconsistencies across files.

### 4. Debug Tools (`debug_tools/`)

**Purpose**: Comprehensive debugging and testing tools.

**Key Principle**: Debug tools should be **UI wrappers** around core functionality, not recreators.

#### Debug Tools Architecture

**✅ CORRECT APPROACH**:
```python
def _get_retriever(self):
    """Get retriever from session state - use same one as main app."""
    return st.session_state.get("retriever")

def test_retrieval(self, query):
    """Test retrieval using existing retriever."""
    retriever = self._get_retriever()
    if not retriever:
        return {"error": "No retriever available - RAG system not ready"}
    docs = retriever.get_relevant_documents(query, k=5)
    # Process results...
```

**❌ WRONG APPROACH** (causes dimension mismatches):
```python
def _load_vectorstore(self):
    """DON'T DO THIS - creates new embeddings"""
    embeddings = OllamaEmbeddings(model=self.embedding_model, base_url=self.ollama_endpoint)
    vectorstore = Chroma(persist_directory=self.vector_db_dir, embedding_function=embeddings)
    return vectorstore
```

**AI Tool Lesson**: Debug tools should use existing session state, not create new instances.

## 🧪 Testing Strategy

### Test File Organization

**Consolidated Approach** (Recommended):
- `developer_test_suite.py`: Complete end-to-end testing
- `quality_test_suite.py`: Quality and performance tests
- `test_helpers.py`: Common test utilities and mocks

**❌ Avoid**: Creating separate test files for every small fix. Consolidate related tests.

### Production Testing Requirements

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

### Test Files Internal Coverage

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

### One-liner Coverage Summary
```
test_runner.py              # Test execution engine and reporting system
test_suite.py               # Core RAG functionality tests (setup, connectivity, embedding, building, query)
ui_tests.py                 # UI component testing (rebuild index, debug tools, chat functionality)
test_helpers.py             # Mock objects and utility functions for testing
embedding_dimension_test.py # Embedding model compatibility diagnostics and fixes
quality_test_suite.py       # Quality assurance and performance testing with specific questions
test_core_integration.py    # Debug tools integration validation with core modules
```

## 🐛 Common Issues and Solutions

### 1. Embedding Dimension Mismatch

**Error**: `Collection expecting embedding with dimension of 768, got 4096`

**Root Cause**: Different embedding models used for building vs loading.

**Solution**: Ensure `load_existing_rag_index()` uses same embedding model as `build_rag()`.

### 2. Session State Issues

**Error**: `No retriever available - RAG system not ready`

**Root Cause**: RAG system not initialized or session state cleared.

**Solution**: Check if `st.session_state.get("retriever")` exists before using.

### 3. Metadata Access Errors

**Error**: `'str' object has no attribute 'get'`

**Root Cause**: Document metadata is string instead of dict.

**Solution**: Use safe metadata access:
```python
metadata = getattr(doc, 'metadata', {})
if not isinstance(metadata, dict):
    metadata = {}
```

## 📊 File Processing and Tracking

### Git Tracking System

**Purpose**: Tracks which files have been processed to avoid reprocessing.

**Key Files**:
- `git_tracking.json`: Maps file paths to their processing status
- `last_commit.json`: Tracks current git commit for change detection

**Usage in Debug Tools**:
```python
def get_available_files(self):
    """Get list of processed files from git_tracking.json."""
    git_tracking_file = os.path.join(self.vector_db_dir, "git_tracking.json")
    with open(git_tracking_file, 'r') as f:
        git_data = json.load(f)
    processed_files = list(git_data.keys())  # Files are keys, not in "files" subobject
    return [os.path.relpath(abs_path, self.project_dir) for abs_path in processed_files]
```

**AI Tool Lesson**: Files are stored as absolute paths in git_tracking.json, convert to relative paths for display.

## 🔍 Debug Tools Deep Dive

### Chunk Analyzer (`chunk_analyzer.py`)

**Purpose**: Analyze chunk quality and distribution.

**Key Methods**:
- `analyze_chunks()`: Overall chunk analysis
- `analyze_file_chunks()`: File-specific analysis
- `get_available_files()`: Get processed files list

**Implementation**:
```python
def analyze_chunks(project_config, retriever=None):
    """Analyze chunks using actual retriever from session state."""
    if not retriever:
        retriever = st.session_state.get("retriever")
    if not retriever:
        st.error("❌ No retriever available - RAG system not ready")
        return
    vectorstore = retriever.vectorstore
    # Analyze chunks...
```

### Retrieval Tester (`retrieval_tester.py`)

**Purpose**: Test retrieval quality and performance.

**Key Methods**:
- `test_retrieval_results()`: Test single query
- `test_multiple_queries()`: Test multiple queries
- `compare_queries()`: Compare different queries

**Safe Implementation**:
```python
def test_retrieval_results(query: str, retriever, project_config, qa_chain=None):
    """Test retrieval with safe metadata access."""
    if not retriever:
        retriever = st.session_state.get("retriever")
    if not retriever:
        return []
    
    docs = retriever.get_relevant_documents(query, k=5)
    results = []
    for doc in docs:
        metadata = getattr(doc, 'metadata', {})
        if not isinstance(metadata, dict):
            metadata = {}
        # Process results safely...
```

## 🚀 Performance and Optimization

### Embedding Model Selection

**Optimal Setup**:
- **Dedicated Embedding Model**: `nomic-embed-text:latest` (768 dimensions)
- **Fallback**: Use LLM model if dedicated model unavailable
- **Consistency**: Same model for building and loading

### Database Optimization

**Chroma Configuration**:
- **Persist Directory**: Project-specific database location
- **Search Type**: Similarity search with configurable k
- **Metadata**: Rich metadata for better retrieval

## 📝 Logging and Monitoring

### Log File Structure

**Centralized Logging**:
```python
from logger import log_to_sublog

# Log to project-specific log file
log_to_sublog(project_dir, "debug_tools.log", "Operation started")
```

**Log Categories**:
- `rag_manager.log`: RAG operations
- `debug_tools.log`: Debug tool operations
- `build_rag.log`: Index building
- `file_tracking.log`: File tracking

### Debug Information

**Session State Monitoring**:
```python
session_keys = list(st.session_state.keys())
log_to_sublog(project_dir, "debug_tools.log", 
             f"Session state keys: {session_keys}")
```

**Retriever Information**:
```python
log_to_sublog(project_dir, "debug_tools.log", 
             f"Retriever found: {type(retriever)}")
log_to_sublog(project_dir, "debug_tools.log", 
             f"Retriever id: {id(retriever)}")
```

## 🔧 Quick Reference

### Common Commands

```bash
# Run comprehensive tests
python ai_debug_tools/developer_test_suite.py

# Run debug tools tests
python ai_debug_tools/test_core_integration.py

# Check logs
tail -50 logs/debug_tools.log

# Start application
streamlit run core/app.py
```

### Key File Locations

- **Logs**: `logs/debug_tools.log`
- **Vector Database**: `codebase-qa_android/`
- **Git Tracking**: `git_tracking.json`
- **Last Commit**: `last_commit.json`
- **Configuration**: `core/config.py`
- **Model Config**: `core/model_config.py`

### Critical Constants

- **Embedding Model**: `nomic-embed-text:latest` (768 dimensions)
- **Search k**: 5-10 documents
- **Chunk Size**: Configurable per file type
- **Database**: Chroma with SQLite backend

## 🎉 Success Metrics

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

✅ **Clean Code**:
- Files under 250 lines (target: 150 lines)
- Single responsibility principle
- Comprehensive logging
- Centralized configuration

This technical guide focuses on the specific implementation details of the RAG codebase QA tool. For general AI behavior and best practices, see `GENERAL_INSTRUCTIONS_for_AI_TOOL.md`. 