# MERMAID CHART FLOW DIAGRAM

## 🟦 RAG Index Build & Ready Flow

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
    
    F1 --> PM1[ProcessManager.start_rag_build]
    F2 --> PM1
    PM1 --> PM2[Disable UI During Build]
    PM2 --> PM3[Show Build Progress with Timeout Protection]
    
    PM3 --> G1[Start Full RAG Build Workflow]
    F2 --> G2[Start Incremental RAG Build Workflow]
    F3 --> S[Load existing RAG index from disk]
    
    G1 --> H1[Clean existing vector DB Clear session state]
    G2 --> H2[Preserve existing database Process changed files only]
    
    H1 --> I[Scan ALL files and apply chunking]
    H2 --> I2[Scan CHANGED files and apply chunking]
    
    I --> J[Extract semantic metadata]
    I2 --> J
    
    J --> J1[Build Cross-References]
    J1 --> J2[Symbol Definitions & Usage Maps]
    J2 --> J3[Inheritance Relationships] 
    J3 --> J4[Design Pattern Detection]
    J4 --> K[Generate chunk fingerprints]
    K --> L[Summarize chunks for relevance]
    L --> M[Build code relationship map]
    M --> N[Create hierarchical index]
    N --> N1[Phase 3 Enhanced Context Building]
    N1 --> N2[Multi-strategy Context Assembly]
    N2 --> O[Sanitize chunks for embedding]
    O --> P[Embed chunks via Ollama API with Model Consistency]
    P --> Q1[Store embeddings in NEW Chroma DB]
    P --> Q2[Update existing Chroma DB with new documents]
    
    Q1 --> R[Set retriever and QA chain in session state]
    Q2 --> R
    R --> PM4[ProcessManager.finish_rag_build]
    PM4 --> PM5[Re-enable UI Elements]
    PM5 --> Z[RAG system is ready for queries]
    
    S --> T[Ensure embedding model consistency Restore retriever and QA chain]
    T --> Z
    
    %% Force Rebuild Flow
    F3 --> U{User wants Force Rebuild?}
    U -->|Yes| V[Force Rebuild: Clear all data and rebuild]
    U -->|No| T
    V --> G1
    
    %% Enhanced Git Tracking
    E --> W[Enhanced Git Tracking: git diff + working directory changes]
    W --> X{Detect changes between commits}
    X -->|Changes found| F2
    X -->|No changes| F3
    
    %% Debug Mode Activation
    Z --> DM1{Debug Mode Enabled?}
    DM1 -->|5-Click Activation| DM2[Show Debug Tools Panel]
    DM2 --> DM3[Vector DB Inspector, Chunk Analyzer, Retrieval Tester]
```

## 🟩 User Query & Answer Flow

```mermaid
flowchart TD
    A[User submits question in chat input box] --> A1{RAG Disabled?}
    A1 -->|Yes| A2[Direct LLM Query Without RAG]
    A1 -->|No| B[Chat UI captures input and triggers processing]
    A2 --> I[Chat UI renders response]
    B --> C[System checks if RAG pipeline is ready]
    C --> D[Intent classifier analyzes user's query with confidence scoring]
    D --> D1[Extract query context hints based on intent]
    D1 --> E[Enhanced query rewriting with intent awareness]
    E --> F[Multi-fallback retrieval strategy]
    F --> F1[Try rewritten query]
    F1 --> F2{Results found?}
    F2 -->|No| F3[Try original query]
    F3 --> F4{Results found?}
    F4 -->|No| F5[Try key terms extraction]
    F5 --> G[Retrieve relevant documents]
    F2 -->|Yes| G
    F4 -->|Yes| G
    
    G --> G1[Phase 3 Enhanced Context Assembly]
    G1 --> G2[Multi-layered Context Building]
    G2 --> G3[Hierarchical + Call Flow + Inheritance + Impact Context]
    G3 --> G4[Context Ranking by Intent Relevance]
    G4 --> H[Chat handler processes with RetrievalQA and enhanced context]
    H --> H1[Document re-ranking by intent]
    H1 --> H2[Impact analysis if applicable]
    H2 --> I[Chat UI renders response with metadata and sources]
```

## 🟨 Enhanced Provider Selection Flow

```mermaid
flowchart TD
    A[User opens application] --> B[Sidebar Configuration Panel]
    B --> C{Provider Selected?}
    C -->|No| D[Show Provider Selection: Choose Provider...]
    D --> E[User selects Ollama Local or Cloud OpenAI]
    
    E --> F{Provider Type?}
    F -->|Ollama| G[Configure Ollama Settings]
    F -->|Cloud| H[Configure Cloud Settings]
    
    G --> G1[Set Ollama Model: llama3.1:latest]
    G1 --> G2[Set Ollama Endpoint: http://localhost:11434]
    G2 --> G3[Set Embedding Model: nomic-embed-text:latest]
    G3 --> I[Validate Ollama Connection]
    
    H --> H1[Set Cloud Endpoint from ENV or Custom]
    H1 --> H2[Validate CLOUD_API_KEY environment variable]
    H2 --> H3[Set Cloud Model: gpt-4.1]
    H3 --> H4[Set Local Ollama for Embeddings]
    H4 --> J[Validate Cloud API Connection]
    
    I --> K{Connection Valid?}
    J --> K
    K -->|Yes| L[ModelConfig.set_provider configured]
    K -->|No| M[Show Connection Error & Retry Options]
    M --> D
    L --> N[Provider Ready for RAG Operations]
```

## 🟪 Process Management & UI Protection Flow

```mermaid
flowchart TD
    A[RAG Build Process Started] --> B[ProcessManager.start_rag_build]
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
    J -->|Yes| L[ProcessManager.finish_rag_build]
    
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
    B -->|No| C[User clicks title button]
    C --> D[Increment click counter]
    D --> E{Click count >= 5?}
    E -->|No| F[Show current click count]
    E -->|Yes| G[Enable Debug Mode]
    G --> H[Show success message: Debug mode enabled]
    H --> I[Reset click counter]
    
    B -->|Yes| J[Show Debug Tools in Sidebar]
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
    
    P --> P1[List available log files]
    P1 --> P2[Display selected log content with download]
```

## 🟦 Cross-Reference Building & Enhanced Context Flow

```mermaid
flowchart TD
    A[Documents with Enhanced Metadata] --> B[CrossReferenceBuilder.build_cross_references]
    B --> C[Extract Symbol Definitions]
    C --> C1[Method signatures with parameters and return types]
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
    
    H4 --> I[Context Builder Loads Cross-Reference Data]
    I --> J[Multi-Strategy Context Assembly Available]
```

## 🟩 Enhanced Query Processing with Fallback Strategies

```mermaid
flowchart TD
    A[User Query Received] --> B[QueryIntentClassifier.classify_intent]
    B --> C[Intent Classification with Confidence Score]
    C --> D[Query Rewriting with Intent Awareness]
    D --> E[Multi-Fallback Retrieval Strategy]
    
    E --> F[Strategy 1: Rewritten Query]
    F --> G{Documents Retrieved?}
    G -->|Yes| M[Sufficient Results Found]
    G -->|No| H[Strategy 2: Original Query]
    
    H --> I{Documents Retrieved?}
    I -->|Yes| M
    I -->|No| J[Strategy 3: Key Terms Extraction]
    
    J --> K[Extract Key Terms from Query]
    K --> L[Search with Key Terms Only]
    L --> M
    
    M --> N[Phase 3 Enhanced Context Building]
    N --> N1[Select Context Strategies Based on Intent]
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
    Q --> R[Generate Enhanced Query with Context]
    R --> S[Send to LLM via Provider Factory]
    S --> T[Document Re-ranking by Intent]
    T --> U[Return Answer with Metadata and Sources]
```