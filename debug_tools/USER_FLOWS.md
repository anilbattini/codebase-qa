# MERMAID CHART FLOW DIAGRAM - UPDATED FOR 2025-09-03 ENHANCEMENTS

## 🟦 RAG Index Build & Ready Flow (Enhanced)

```mermaid
flowchart TD
    A[User selects project directory, project type, and provider] --> A1{Choose Provider}
    A1 -->|Ollama Local| A2[Configure Ollama Model & Endpoint]
    A1 -->|Cloud OpenAI| A3[Configure Cloud Endpoint & API Key]
    A2 --> B[Validate Ollama Connection]  
    A3 --> B1[Validate Cloud API Key & Endpoint]
    B --> C[Initialize session state for retriever and QA chain]
    B1 --> C
    C --> D[Apply project type and config Load file extensions and chunking rules]
    D --> E{Should rebuild index? Check DB, tracking, and file changes}
    
    E -->|No Database| F1[Full Rebuild: Clean database directory]
    E -->|No Tracking| F1
    E -->|Files Changed| F2[Incremental Rebuild: Process only changed files]
    E -->|No Changes| F3[No Rebuild: Load existing index]
    
    F1 --> PM1[core/process_manager.py: ProcessManager.start_rag_build]
    F2 --> PM1
    PM1 --> PM2[Disable UI During Build]
    PM2 --> PM3[Show Build Progress with Timeout Protection]
    
    PM3 --> G1[Start Full RAG Build Workflow]
    F2 --> G2[Start Incremental RAG Build Workflow]
    F3 --> S[Load existing RAG index from disk]
    
    G1 --> H1[Clean existing vector DB and clear session state]
    G2 --> H2[Preserve existing database and process changed files]
    
    H1 --> I[core/index_builder.py: Scan ALL files and apply semantic chunking]
    H2 --> I2[core/index_builder.py: Scan CHANGED files and apply semantic chunking]
    
    I --> J[core/context/metadata_extractor.py: Extract semantic metadata including design patterns, call sites, error handling]
    I2 --> J
    
    J --> J1[core/context/cross_reference_builder.py: Build Cross-References: symbols, call graphs, inheritance]
    J1 --> J2[Generate statistics and fingerprint chunks]
    J2 --> J3[core/context/chunker_factory.py: Summarize chunks for relevance]
    J3 --> J4[core/context/hierarchical_indexer.py: Build code relationships and hierarchical index]
    J4 --> N1[Phase 3 Enhanced Context Building]
    N1 --> N2[core/context/context_builder.py: Multi-strategy Context Assembly incorporating impact analysis]
    N2 --> O[Sanitize chunks for embedding]
    O --> P[Embed chunks via Ollama API with Model Consistency]
    P --> Q1[Store embeddings in NEW Chroma DB]
    P --> Q2[Update existing Chroma DB with new documents]
    
    Q1 --> R[Set retriever and QA chain in session state]
    Q2 --> R
    R --> PM4[core/process_manager.py: ProcessManager.finish_rag_build]
    PM4 --> PM5[Re-enable UI Elements]
    PM5 --> Z[RAG system is ready for queries]
    
    S --> T[Ensure embedding model consistency and restore retriever/QA chain]
    T --> Z
    
    %% Force Rebuild Flow
    F3 --> U{User wants Force Rebuild?}
    U -->|Yes| V[Force Rebuild: Clear all data and rebuild]
    U -->|No| T
    V --> G1
    
    %% Enhanced Git Tracking
    E --> W[core/context/git_hash_tracker.py: Enhanced Git Tracking: full git diff + working directory]
    W --> X{Detect changes between commits}
    X -->|Changes found| F2
    X -->|No changes| F3
    
    %% Debug Mode Activation
    Z --> DM1{Debug Mode Enabled?}
    DM1 -->|5-Click Activation| DM2[Show Debug Tools Panel]
    DM2 --> DM3[Vector DB Inspector, Chunk Analyzer, Retrieval Tester]
```

## 🟩 User Query & Answer Flow (Enhanced with Validation & Diagnostics)

```mermaid
flowchart TD
    A[User submits question in chat input box] --> A1{RAG Disabled?}
    A1 -->|Yes| A2[Direct LLM Query Without RAG]
    A1 -->|No| B[core/ui_components.py: Chat UI captures input and triggers processing]
    A2 --> I[Chat UI renders response]
    B --> C[System checks if RAG pipeline is ready]
    C --> D[core/query/query_intent_classifier.py: Intent classifier analyzes user's query with confidence scoring]
    D --> D1[Extract query context hints based on intent]
    D1 --> E[core/query/retrieval_logic.py: Enhanced contamination-free query rewriting with intent awareness]
    E --> F[Multi-fallback retrieval strategy]
    
    F --> F1[Try rewritten query]
    F1 --> F2{Results found?}
    F2 -->|No| F3[Try original query]
    F3 --> F4{Results found?}
    F4 -->|No| F5[Try key terms extraction]
    F5 --> G[Retrieve relevant documents]
    F2 -->|Yes| G
    F4 -->|Yes| G
    
    G --> G1[Phase 3 Enhanced Context Assembly with multi-layer layers]
    G1 --> G2[core/context/context_builder.py: Multi-layered Context Building: hierarchical, call flow, inheritance, impact]
    G2 --> G3[Context Ranking by Intent Relevance]
    G3 --> H[core/query/chat_handler.py: Chat handler uses RetrievalQA with enhanced context]
    H --> H1[core/query/prompt_router.py: Document re-ranking by intent]
    H1 --> H2[core/query/retrieval_logic.py: Impact analysis if applicable]
    H2 --> H3[Answer generation]
    H3 --> H4[core/query/answer_validation_handler.py: Answer validation & pipeline diagnostics via AnswerValidationHandler]
    H4 --> I[Chat UI renders response with metadata, sources, and quality feedback]
```

## 🟨 Enhanced Provider Selection Flow

```mermaid
flowchart TD
    A[User opens application] --> B[core/ui_components.py: Sidebar Configuration Panel]
    B --> C{Provider Selected?}
    C -->|No| D[Show Provider Selection: Choose Provider...]
    D --> E[User selects Ollama Local or Cloud OpenAI]
    
    E --> F{Provider Type?}
    F -->|Ollama| G[Configure Ollama Settings]
    F -->|Cloud| H[Configure Cloud Settings]
    
    G --> G1[core/config/model_config.py: Set Ollama Model: llama3.1:latest]
    G1 --> G2[Set Ollama Endpoint: http://localhost:11434]
    G2 --> G3[Set Embedding Model: nomic-embed-text:latest]
    G3 --> I[Validate Ollama Connection]
    
    H --> H1[Set Cloud Endpoint from ENV or Custom]
    H1 --> H2[Validate CLOUD_API_KEY environment variable]
    H2 --> H3[Set Cloud Model: gpt-4.1]
    H3 --> H4[Set Local Ollama for Embeddings]
    H4 --> J[core/config/custom_llm_client.py: Validate Cloud API Connection]
    
    I --> K{Connection Valid?}
    J --> K
    K -->|Yes| L[core/config/model_config.py: ModelConfig.set_provider configured]
    K -->|No| M[Show Connection Error & Retry Options]
    M --> D
    L --> N[Provider Ready for RAG Operations]
```

## 🟪 Process Management & UI Protection Flow

```mermaid
flowchart TD
    A[RAG Build Process Started] --> B[core/process_manager.py: ProcessManager.start_rag_build]
    B --> C[Record build start time and process ID]
    C --> D[Disable UI elements that could interfere]
    D --> E[Set building flag in session state]
    E --> F[Show build progress with real-time updates]
    
    F --> G[Monitor build timeout 10 minutes]
    G --> H{Build timeout exceeded?}
    H -->|Yes| I[Show timeout warning and force stop option]
    H -->|No| J{Build completed?}
    J -->|No| K[Continue monitoring and show progress]
    K --> G
    J -->|Yes| L[core/process_manager.py: ProcessManager.finish_rag_build]
    
    I --> M[User can force stop or continue waiting]
    M --> N{User choice?}
    N -->|Force Stop| L
    N -->|Continue| G
    
    L --> O[Clear building flag from session state]
    O --> P[Re-enable all UI elements]
    P --> Q[Clean up process resources]
    Q --> R[RAG system ready for use]
```

## 🟫 Debug Mode Activation & Tools Flow

```mermaid
flowchart TD
    A[User in main application] --> B{Debug Mode Enabled?}
    B -->|No| C[core/ui_components.py: User clicks title button]
    C --> D[Increment click counter]
    D --> E{Click count >= 5?}
    E -->|No| F[Show current click count]
    E -->|Yes| G[Enable Debug Mode]
    G --> H[Show success message: Debug mode enabled]
    H --> I[Reset click counter]
    
    B -->|Yes| J[core/ui_components.py: Show Debug Tools in Sidebar]
    J --> K[Render Debug Section with Tabs]
    K --> L[Vector DB Inspector Tab]
    K --> M[Chunk Analyzer Tab]
    K --> N[Retrieval Tester Tab]
    K --> O[Build Status Tab]
    K --> P[Logs Viewer Tab]
    
    L --> L1[Inspect Vector DB Statistics]
    L1 --> L2[Show total documents, files, chunk sizes]
    L2 --> L3[Display file breakdown and clear DB option]
    
    M --> M1[Select file for chunk analysis]
    M1 --> M2[Analyze chunks using existing retriever]
    M2 --> M3[Display chunk content and metadata]
    
    N --> N1[Enter test query for retrieval]
    N1 --> N2[Test using session state retriever]
    N2 --> N3[Display relevance scores and results]
    
    O --> O1[Show database existence and size]
    O1 --> O2[Display tracking files and git status]
    
    P --> P1[core/logger.py: List available log files]
    P1 --> P2[Display selected log content with download]
```

## 🟦 Cross-Reference Building & Enhanced Context Flow (Updated)

```mermaid
flowchart TD
    A[Documents with Enhanced Metadata] --> B[core/context/cross_reference_builder.py: CrossReferenceBuilder.build_cross_references]
    B --> C[Extract Symbol Definitions]
    C --> C1[core/context/metadata_extractor.py: Method signatures with parameters and return types]
    C1 --> C2[Class definitions and interfaces]
    C2 --> C3[Variable and constant definitions]
    
    C3 --> D[Build Usage Maps]
    D --> D1[Function call relationships]
    D1 --> D2[Class instantiation patterns]
    D2 --> D3[Variable usage tracking]
    
    D3 --> E[Build Inheritance Relationships]
    E --> E1[Class hierarchy mapping]
    E1 --> E2[Interface implementation tracking]
    E2 --> E3[Abstract class relationships]
    
    E3 --> F[Detect Design Patterns]
    F --> F1[Factory Pattern Detection]
    F1 --> F2[Singleton Pattern Detection]
    F2 --> F3[Observer Pattern Detection]
    F3 --> F4[Strategy Pattern Detection]
    
    F4 --> G[Generate Statistics]
    G --> G1[Symbol count and distribution]
    G1 --> G2[Usage frequency analysis]
    G2 --> G3[Complexity metrics]
    
    G3 --> H[Save Cross-References to Files]
    H --> H1[cross_references.json - Main data]
    H1 --> H2[call_graph_index.json - Call relationships]
    H2 --> H3[inheritance_index.json - Class hierarchies]
    H3 --> H4[symbol_usage_index.json - Usage patterns]
    
    H4 --> I[core/context/context_builder.py: Context Builder Loads Cross-Reference Data]
    I --> J[core/context/cross_reference_query.py: Multi-Strategy Context Assembly Available]
```

## 🟩 Enhanced Query Processing with Fallback Strategies (Updated)

```mermaid
flowchart TD
    A[User Query Received] --> B[core/query/query_intent_classifier.py: QueryIntentClassifier.classify_intent]
    B --> C[Intent Classification with Confidence Score]
    C --> D[core/query/retrieval_logic.py: Query Rewriting with Intent Awareness]
    D --> E[Multi-Fallback Retrieval Strategy]
    
    E --> F[Strategy 1: Rewritten Query]
    F --> G{Documents Retrieved?}
    G -->|Yes| M[Sufficient Results Found]
    G -->|No| H[Strategy 2: Original Query]
    
    H --> I{Documents Retrieved?}
    I -->|Yes| M
    I -->|No| J[Strategy 3: Key Terms Extraction]
    
    J --> K[core/query/retrieval_logic.py: Extract Key Terms from Query]
    K --> L[Search with Key Terms Only]
    L --> M
    
    M --> N[Phase 3 Enhanced Context Building]
    N --> N1[core/context/context_builder.py: Select Context Strategies Based on Intent]
    N1 --> N2{Intent Type?}
    
    N2 -->|Overview| O1[Hierarchical Context + Project Structure]
    N2 -->|Technical| O2[Call Flow Context + Implementation Details]
    N2 -->|Business Logic| O3[Inheritance Context + Validation Rules]
    N2 -->|Impact Analysis| O4[Impact Context + Dependency Chains]
    
    O1 --> P[Rank Context Layers by Relevance]
    O2 --> P
    O3 --> P
    O4 --> P
    
    P --> Q[Format Multi-Layered Context for LLM]
    Q --> R[core/query/prompt_router.py: Generate Enhanced Query with Context]
    R --> S[core/config/model_config.py: Send to LLM via Provider Factory]
    S --> T[core/query/query_intent_classifier.py: Document Re-ranking by Intent]
    T --> U[Return Answer with Metadata and Sources]
```

## 🆕 **New Addition: Answer Validation & Quality Monitoring Flow (2025-09-03)**

```mermaid
flowchart TD
    A[Answer Generated by LLM] --> B[core/query/answer_validation_handler.py: AnswerValidationHandler.validate_answer_quality]
    B --> C[Multi-Metric Quality Assessment]
    
    C --> C1[Calculate Relevancy Score - Query/Answer Alignment]
    C1 --> C2[Calculate Completeness Score - Context Utilization]
    C2 --> C3[Calculate Accuracy Score - Technical Reference Validation]
    C3 --> C4[Calculate Code Quality Score - File References, Methods, Patterns]
    
    C4 --> D[Overall Quality Score Calculation]
    D --> E{Quality Score >= 0.8?}
    E -->|Yes| F[Mark as HIGH QUALITY]
    E -->|No| G{Quality Score >= 0.6?}
    G -->|Yes| H[Mark as ACCEPTABLE]
    G -->|No| I[Mark as NEEDS IMPROVEMENT]
    
    F --> J[core/logger.py: Log Quality Metrics]
    H --> J
    I --> J
    
    J --> K[Pipeline Diagnostics Analysis]
    K --> K1[Entity Preservation Check in Rewriting]
    K1 --> K2[Retrieval Coverage Analysis]
    K2 --> K3[Context Utilization Assessment]
    
    K3 --> L{Critical Issues Found?}
    L -->|Yes| M[Generate Quality Alert]
    L -->|No| N[Log Normal Metrics]
    
    M --> M1[core/logger.py: Log to quality_alerts.log]
    M1 --> O[Generate Fix Recommendations]
    N --> N1[core/logger.py: Log to quality_metrics.log]
    
    O --> O1[Entity Preservation Fixes if needed]
    O1 --> O2[Retrieval Scope Improvements if needed]
    O2 --> O3[Context Enhancement Suggestions if needed]
    
    O3 --> P[Pipeline Diagnosis Complete]
    N1 --> P
    P --> Q[Return Quality Assessment to Chat Handler]
```

## 🟨 Feature Toggle Management Flow (Updated)

```mermaid
flowchart TD
    A[Application Startup] --> B[core/config/feature_toggle_manager.py: FeatureToggleManager initialization]
    B --> C[Load core/config/featureToggle.json configuration]
    C --> D[Parse feature definitions and version requirements]
    D --> E[Get current application version from pyproject.toml]
    
    E --> F[Feature Request: is_enabled check]
    F --> G{Feature exists in config?}
    G -->|No| H[Return False - Feature not defined]
    G -->|Yes| I[Check enabled flag]
    
    I --> J{Feature enabled in config?}
    J -->|No| K[Return False - Feature disabled]
    J -->|Yes| L[Check version requirement]
    
    L --> M{App version >= min version?}
    M -->|No| N[Return False - Version too low]
    M -->|Yes| O[Return True - Feature enabled]
    
    H --> P[core/logger.py: Log toggle decision with reason]
    K --> P
    N --> P
    O --> P
    
    P --> Q[Feature toggle decision complete]
```

## **Key Enhancements Reflected in Updated Charts:**

### **🔄 Updated File Paths:**
1. **Context Processing**: All context-related files now in `core/context/` folder
2. **Query Processing**: All query-related files now in `core/query/` folder
3. **Configuration**: All config files now in `core/config/` folder
4. **Renamed Files**: `build_rag.py` → `core/index_builder.py`

### **🆕 New Components Added:**
1. **core/config/custom_llm_client.py**: Cloud provider LLM client with system/user prompt support
2. **core/context/cross_reference_builder.py**: Cross-reference mapping and call graph generation
3. **core/context/cross_reference_query.py**: Fast cross-reference querying interface
4. **core/query/answer_validation_handler.py**: Complete quality assessment pipeline
5. **core/query/retrieval_logic.py**: Modular retrieval operations with intelligent fallbacks
6. **core/query/prompt_router.py**: Intent-specific prompt templates

### **🏗️ Architectural Improvements:**
1. **Modular Organization**: Clean separation of concerns across specialized folders
2. **Enhanced Maintainability**: Easier navigation and component isolation
3. **Clear Dependencies**: Well-defined interfaces between modules
4. **Scalable Structure**: Easy to add new features and components

### **🔧 Enhanced Features:**
1. **Quality Monitoring**: Real-time validation and pipeline diagnostics
2. **Multi-Provider Support**: Seamless switching between Ollama and cloud providers
3. **Advanced Context Assembly**: Multi-layered context building with cross-references
4. **Feature Toggle System**: Runtime control over advanced capabilities

These updated Mermaid charts now accurately reflect the refactored file structure and enhanced capabilities of the RAG Codebase QA Tool, maintaining all functionality while improving organization and maintainability.

Sources
[1] MERMAID_CHART.md https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/82676895/00d9aa19-2970-4026-9618-689627857795/MERMAID_CHART.md
