# RAG Codebase QA Tool - Complete AI Technical Guide

## 🎯 System Architecture Overview

This is a **production-ready Retrieval-Augmented Generation (RAG)** system for intelligent codebase analysis and querying. The tool employs semantic chunking, vector embeddings, multi-phase query processing, and LLM integration to provide contextually accurate code insights across multiple programming languages.

### 🗂️ Folder Structure & Deployment

``` python
source-project/                    # User's source code project
├── codebase-qa/                  # Tool installation directory (this repo)
│   ├── core/                     # Core RAG processing modules
│   ├── debug_tools/              # Testing and diagnostic tools  
│   ├── cli.py                    # Command line interface
│   └── requirements.txt          # Dependencies
├── codebase-qa_<project_type>/   # Generated data directory (auto-created)
│   ├── logs/                     # Session logs and diagnostics
│   ├── chroma.sqlite3            # Vector database
│   ├── git_tracking.json         # File change tracking
│   ├── code_relationships.json   # Dependency mappings
│   ├── hierarchical_index.json   # Multi-level code structure
│   ├── cross_references.json     # Symbol usage and definitions
│   └── <uuid>/                   # Chroma vector storage
└── (user's source files)         # Project being analyzed
```

## RAG Tool Structure (codebase-qa/)

``` python
codebase-qa/                          # Core RAG tool directory
├── core/                             # Core RAG functionality
│   ├── app.py                        # Streamlit application entry point
│   ├── build_rag.py                  # Main RAG index builder with semantic chunking
│   ├── chat_handler.py               # Chat interaction logic with intent classification
│   ├── chunker_factory.py            # Code chunking strategies per language
│   ├── config.py                     # Multi-language project configuration
│   ├── context_builder.py            # Enhanced context building (Phase 3)
│   ├── git_hash_tracker.py           # File change tracking (Git + hash fallback)
│   ├── hierarchical_indexer.py       # Multi-level code structure indexing
│   ├── logger.py                     # Centralized logging with session rotation
│   ├── metadata_extractor.py         # Semantic metadata and pattern extraction
│   ├── model_config.py               # Centralized LLM/embedding configuration
│   ├── process_manager.py            # Process state management and UI protection
│   ├── query_intent_classifier.py    # Query intent classification and scoring
│   ├── rag_manager.py                # Session lifecycle and provider management
│   └── ui_components.py              # Streamlit UI components and interactions
├── debug_tools/                      # Debugging and testing infrastructure
│   ├── ai_debug_tools/               # Automated test suites
│   │   ├── developer_test_suite.py   # Primary end-to-end test suite
│   │   ├── developer_ui_test_suite.py # UI automation testing with Selenium
│   │   ├── embedding_dimension_test.py # Embedding compatibility diagnostics
│   │   ├── quality_test_suite.py     # Answer quality and performance testing
│   │   ├── quick_ui_test.py          # Fast UI verification tests
│   │   ├── run_comprehensive_tests.py # Test orchestration and reporting
│   │   ├── test_core_integration.py  # Debug tools integration validation
│   │   ├── test_helpers.py           # Mock objects and test utilities
│   │   ├── test_real_retrieval.py    # Real retrieval system testing
│   │   ├── test_retriever_fix.py     # Retriever configuration validation
│   │   ├── test_runner.py            # Test execution engine and reporting
│   │   ├── test_session_state.py     # Session state management testing
│   │   ├── test_suite.py             # Core RAG functionality tests
│   │   └── ui_tests.py               # UI component functionality testing
│   ├── chunk_analyzer.py             # Chunk quality analysis and distribution
│   ├── db_inspector.py               # SQLite database inspection and queries
│   ├── debug_tools.py                # Main debug interface and tools coordination
│   ├── query_runner.py               # Custom query execution against vector DB
│   ├── rag_debug_queries.sql         # Comprehensive SQL debugging queries
│   ├── retrieval_tester.py           # Retrieval performance and accuracy testing
│   └── vector_db_inspector.py        # Vector database health and statistics
├── cli.py                            # Command line interface entry point
├── requirements.txt                  # Python dependencies specification
├── setup.py                          # Package installation configuration
├── pyproject.toml                    # Modern Python project configuration
├── MANIFEST.in                       # Package manifest for distribution
├── LICENSE                           # Software license
└── README.md                         # Project documentation

```

## Generated Data Structure (codebase-qa_<project_type>/)

```python
codebase-qa_<project_type>/           # Generated data directory (auto-created)
├── logs/                             # Session logs and component diagnostics
│   ├── rag_session_YYYYMMDD_HHMMSS.log # Timestamped session logs with rotation
│   ├── chat_handler.log              # Query processing and intent classification logs
│   ├── chunking_metadata.log         # Semantic chunking and anchor validation logs
│   ├── file_tracking.log             # Git tracking and hash comparison logs  
│   ├── hierarchy_status.log          # Hierarchical indexing status and errors
│   ├── intent_classification.log     # Query intent analysis and confidence scores
│   ├── process_manager.log           # Build process state and UI protection logs
│   ├── rag_manager.log               # Session lifecycle and provider setup logs
│   ├── rewriting_queries.log         # Query rewriting and enhancement logs
│   └── ui_components.log             # UI interactions and configuration changes
├── <uuid>/                           # Chroma vector storage directory
│   └── index_metadata.pickle         # Vector index metadata and configuration
├── chroma.sqlite3                    # Main vector database (SQLite backend)
├── git_tracking.json                 # File processing status and change tracking
├── last_commit.json                  # Git commit tracking for incremental builds
├── code_relationships.json           # Dependency maps and file relationships
├── hierarchical_index.json           # Multi-level code structure (component/file/logic/UI/API)
├── cross_references.json             # Symbol definitions, usage maps, inheritance
├── call_graph_index.json             # Function call relationships and flow analysis
├── inheritance_index.json            # Class hierarchy and interface implementations  
├── symbol_usage_index.json           # Symbol usage patterns and design patterns
└── .codelens/                        # IDE integration metadata
    └── menu_state.json               # CodeLens menu state persistence

```

**Key Principle**: Tool stays in `codebase-qa/`, generated data in `codebase-qa_<project_type>/`

## 🏗️ Core Architecture Components

### 1. **Multi-Phase RAG Pipeline**
```python
Query Input → Intent Classification → Query Rewriting → Document Retrieval → 
Context Assembly → Answer Generation → Document Re-ranking → Impact Analysis → Response
```

### 2. **Semantic Processing Layers**
- **Chunking**: Config-driven semantic chunking with anchor validation
- **Metadata Extraction**: Class/function/dependency extraction with design pattern detection  
- **Cross-referencing**: Symbol usage maps and inheritance relationships
- **Hierarchical Indexing**: Multi-level code structure analysis

### 3. **Provider Abstraction**
- **Local**: Ollama models (llama3.1, nomic-embed-text)
- **Cloud**: OpenAI-compatible APIs with environment variable configuration
- **Centralized**: Single configuration point via `model_config.py`

## 📁 Core Module Deep Dive

### `core/app.py` - Application Orchestrator
- **Streamlit UI initialization** and session management
- **RAG lifecycle coordination** (build/load/query cycles)
- **Provider configuration** and debug mode integration
- **Error handling** and process protection during builds

### `core/build_rag.py` - Vector Database Builder  
- **Incremental processing** using Git tracking or hash comparison
- **Semantic chunking** with anchor validation (768-dim embeddings)
- **Cross-reference building** for enhanced context assembly
- **Metadata sanitization** and document preparation for Chroma

**Critical Implementation**:
```python
embedding_model = "nomic-embed-text:latest"  # Always 768 dimensions
embeddings = OllamaEmbeddings(model=embedding_model, base_url=ollama_endpoint)
vectorstore = Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embeddings)
```

### `core/rag_manager.py` - Session Lifecycle Manager
- **Build/load decision logic** with incremental vs full rebuild detection
- **Provider-agnostic LLM setup** with fallback strategies  
- **Session state management** for Streamlit integration
- **Cleanup and recovery** operations for failed builds

**Embedding Consistency Fix**:
```python
# CRITICAL: Use same embedding model as build_rag.py
embedding_model = "nomic-embed-text:latest"  
embeddings = OllamaEmbeddings(model=embedding_model, base_url=ollama_endpoint)
```

### `core/chat_handler.py` - Query Processing Engine
- **Intent classification** with confidence scoring
- **Multi-fallback retrieval** (rewritten → original → key terms)
- **Phase 3 enhanced context** building with cross-references
- **Impact analysis** for dependency chain queries

### `core/config.py` - Multi-Language Configuration
- **Project type auto-detection** with extensible patterns
- **Language-specific chunking rules** and entity patterns
- **Path normalization** (relative/absolute conversion)
- **Database backup/restore** for project type switching

**Supported Languages**: Android (Kotlin/Java), iOS (Swift/Obj-C), Java, JavaScript/TypeScript, Python, Web

### `core/model_config.py` - Centralized Model Management
- **Provider factory pattern** with consistent parameter handling
- **Environment variable integration** for cloud APIs
- **Live configuration updates** with proper logging
- **Embedding model consistency** enforcement

### `core/ui_components.py` - Streamlit Interface
- **Project type selection** with change confirmation dialogs
- **Provider configuration** (Ollama vs Cloud) with validation
- **Chat interface** with metadata display and history
- **Debug tools integration** (5-click debug mode activation)

### `core/logger.py` - Centralized Logging
- **Project-specific log directories** with session rotation
- **Multi-level logging** (console INFO+, file DEBUG+) 
- **Sublog utilities** for component-specific diagnostics
- **Highlight logging** for major processing milestones

## 🧪 Testing & Debug Architecture

### Primary Test Suites (Run Before Production)

#### 1. `debug_tools/ai_debug_tools/developer_test_suite.py`
**Complete end-to-end validation**:
- Project setup and configuration
- Ollama connectivity and model availability  
- Embedding dimension compatibility
- RAG index building and loading
- Query processing and answer quality
- UI functionality testing

#### 2. `debug_tools/ai_debug_tools/quality_test_suite.py` 
**Performance and quality assurance**:
- Embedding model compatibility testing
- RAG building process validation  
- Answer quality analysis with satisfaction scoring
- Comprehensive test reporting

#### 3. `debug_tools/ai_debug_tools/test_core_integration.py`
**Debug tools integration validation**:
- Core module import testing
- Git tracking functionality
- Chunk analyzer integration
- Retrieval tester validation

### Debug Tools Principles

**✅ CORRECT APPROACH - Reuse Core Instances**:
```python
def test_retrieval(self, query):
    retriever = st.session_state.get("retriever")  # Use existing
    if not retriever:
        return {"error": "No retriever available"}
    return retriever.get_relevant_documents(query)
```

**❌ WRONG APPROACH - Create New Instances**:
```python
def test_retrieval(self, query):  
    embeddings = OllamaEmbeddings(...)  # DON'T DO THIS
    vectorstore = Chroma(...)           # Creates dimension mismatches
```

### Debug Tool Components

- **Vector DB Inspector**: Database statistics and health checking
- **Chunk Analyzer**: Chunk quality and distribution analysis  
- **Retrieval Tester**: Query performance and relevance testing
- **Database Inspector**: SQLite-level database analysis with custom queries

## ⚠️ Critical Issues & Solutions

### 1. **Embedding Dimension Mismatch**
**Error**: `Collection expecting embedding with dimension of 768, got 4096`
**Solution**: Ensure consistent embedding model across build/load operations
**Fix**: Always use `nomic-embed-text:latest` (768D) not LLM model (4096D)

### 2. **Session State Corruption**
**Error**: `No retriever available - RAG system not ready`
**Solution**: Proper session state initialization and validation
**Fix**: Check `st.session_state.get("retriever")` before use

### 3. **Metadata Access Errors**  
**Error**: `'str' object has no attribute 'get'`
**Solution**: Safe metadata access with type checking
**Fix**: `metadata = getattr(doc, 'metadata', {}) if hasattr(doc, 'metadata') else {}`

### 4. **Database Lock Issues**
**Error**: `database is locked` during rebuild
**Solution**: Proper cleanup with retry logic and connection management
**Fix**: Force close Chroma connections before deletion

## 🚀 Performance Optimizations

### **Embedding Strategy**
- **Dedicated Model**: `nomic-embed-text:latest` (768D) for embeddings
- **Fallback Logic**: Use LLM model if dedicated model unavailable
- **Consistency Check**: Validate model availability before processing

### **Processing Efficiency**  
- **Incremental Builds**: Git/hash-based change detection
- **Batch Processing**: Process documents in configurable batches
- **Timeout Protection**: 10-minute timeout for embedding computation
- **Progress Tracking**: Real-time progress updates in UI

### **Memory Management**
- **Chunk Deduplication**: SHA256 fingerprinting prevents duplicates
- **Metadata Sanitization**: Clean metadata before vectorstore storage
- **Session Cleanup**: Proper resource cleanup on rebuild

## 📊 Operational Excellence

### **File Tracking System**
```json
// git_tracking.json structure
{
  "/absolute/path/to/file.py": {
    "status": "processed",
    "hash": "sha256_hash",
    "timestamp": "2025-08-22T15:00:00Z"
  }
}
```

### **Cross-Reference Data**
```json
// cross_references.json structure  
{
  "symbol_definitions": {...},
  "usage_maps": {...},
  "inheritance_relationships": {...},
  "design_patterns": {...},
  "statistics": {...}
}
```

### **Hierarchical Index**
```json
// hierarchical_index.json structure
{
  "component_level": {...},
  "file_level": {...}, 
  "business_logic_level": {...},
  "ui_flow_level": {...},
  "api_level": {...}
}
```

## 📝 Usage Commands

### **Start Application**
```bash
cd source-project/codebase-qa
streamlit run core/app.py
```

### **Run Comprehensive Tests**  
```bash
cd debug_tools/ai_debug_tools
python developer_test_suite.py
python quality_test_suite.py  
python test_core_integration.py
```

### **Debug Commands**
```bash
# View logs
tail -50 codebase-qa_android/logs/rag_manager.log

# Check database
sqlite3 codebase-qa_android/chroma.sqlite3 ".tables"

# Test specific query
python debug_tools/retrieval_tester.py
```

## 🎯 Success Indicators

### **System Health Checks**
✅ **RAG Ready**: `st.session_state["retriever"]` and `st.session_state["qa_chain"]` exist
✅ **No Dimension Errors**: Same embedding model (768D) used throughout  
✅ **Fast Queries**: Sub-second response times for typical queries
✅ **Accurate Results**: Relevant documents returned with proper metadata
✅ **Clean Logs**: No error messages in session logs

### **Performance Metrics**
✅ **Build Time**: <2 minutes for typical codebases (1000-5000 files)
✅ **Query Time**: <3 seconds for complex queries with context assembly
✅ **Memory Usage**: <2GB peak during processing
✅ **Storage**: Vector DB typically 10-50MB per 1000 code files

## 🔧 Configuration Examples

### **Ollama Provider Setup**
```python
model_config.set_provider("ollama")
model_config.set_ollama_model("llama3.1:latest") 
model_config.set_embedding_model("nomic-embed-text:latest")
model_config.set_ollama_endpoint("http://localhost:11434")
```

### **Cloud Provider Setup**
```python
export CLOUD_API_KEY="sk-..."
export CLOUD_ENDPOINT="https://api.openai.com/v1"
```
```python
model_config.set_provider("cloud")
model_config.set_cloud_endpoint("https://api.openai.com/v1")  
# API key loaded from environment
```

## 🎉 Advanced Features

### **Intent-Based Processing**
- **Overview**: Project structure and main functionality queries
- **Technical**: Specific implementation and architectural questions  
- **Business Logic**: Validation rules and business process queries
- **UI Flow**: User interface and interaction pattern queries
- **Impact Analysis**: Dependency and change impact assessment

### **Context Assembly Strategies**
- **Hierarchical**: Multi-level project structure context
- **Call Flow**: Function call relationship context
- **Inheritance**: Class hierarchy and interface implementation context  
- **Impact**: Dependency chain and change propagation context

### **Provider Abstraction Benefits**
- **Development**: Use local Ollama for development and testing
- **Production**: Switch to cloud APIs for production deployments
- **Hybrid**: Use local for embeddings, cloud for chat completions
- **Failover**: Automatic fallback between providers

## 📚 Integration Guidelines

### **For AI Assistants Working on This Tool**

1. **Always maintain embedding model consistency** (768D nomic-embed-text)
2. **Use debug tools to validate changes** before implementation  
3. **Follow centralized configuration patterns** via model_config.py
4. **Preserve session state management** for Streamlit compatibility
5. **Implement comprehensive logging** for troubleshooting
6. **Test with multiple project types** to ensure compatibility
7. **Validate file tracking** continues working after changes
8. **Ensure clean resource cleanup** in error scenarios

### **Extension Points**
- **New Languages**: Add to `LANGUAGE_CONFIGS` in config.py
- **New Providers**: Extend provider factory in model_config.py  
- **New Chunkers**: Add to chunker_factory.py with config integration
- **New Metadata**: Extend metadata_extractor.py patterns
- **New Debug Tools**: Follow existing pattern of core instance reuse

This comprehensive guide ensures any AI assistant can immediately understand and work effectively with the RAG Codebase QA Tool without requiring additional context or introductions.
```