# MERMAID CHART FLOW DIAGRAM

## 🟦 RAG Index Build & Ready Flow
```mermaid
flowchart TD
    A[User selects project directory, project type, model provider, and endpoint] --> B[Sidebar renders inputs Handles validation and warnings]
    B --> C[Initialize session state for retriever and QA chain]
    C --> D[Apply project type and config Load file extensions and chunking rules]
    D --> E[Initialize Model Provider Ollama or Hugging Face]
    E --> F{Should rebuild index? Check DB, tracking, and file changes}
    
    F -->|No Database| G1[Full Rebuild: Clean database directory]
    F -->|No Tracking| G1
    F -->|Files Changed| G2[Incremental Rebuild: Process only changed files]
    F -->|No Changes| G3[No Rebuild: Load existing index]
    
    G1 --> H1[Start Full RAG Build Workflow]
    G2 --> H2[Start Incremental RAG Build Workflow]
    G3 --> S[Load existing RAG index from disk]
    
    H1 --> I1[Clean existing vector DB Clear session state]
    H2 --> I2[Preserve existing database Process changed files only]
    
    I1 --> J[Scan ALL files and apply chunking]
    I2 --> J2[Scan CHANGED files and apply chunking]
    
    J --> K[Extract semantic metadata]
    J2 --> K
    
    K --> L[Generate chunk fingerprints]
    L --> M[Summarize chunks for relevance]
    M --> N[Build code relationship map]
    N --> O[Create hierarchical index]
    O --> P[Sanitize chunks for embedding]
    P --> Q[Embed chunks via Model Provider API]
    Q --> R1[Store embeddings in NEW Chroma DB]
    Q --> R2[Update existing Chroma DB with new documents]
    
    R1 --> S1[Set retriever and QA chain in session state]
    R2 --> S1
    S1 --> Z[RAG system is ready for queries]
    
    S --> T[Ensure embedding model consistency Restore retriever and QA chain]
    T --> Z
    
    %% Force Rebuild Flow
    G3 --> U{User wants Force Rebuild?}
    U -->|Yes| V[Force Rebuild: Clear all data and rebuild]
    U -->|No| T
    V --> H1
    
    %% Enhanced Git Tracking
    F --> W[Enhanced Git Tracking: git diff + working directory changes]
    W --> X{Detect changes between commits}
    X -->|Changes found| G2
    X -->|No changes| G3
    
    %% Model Provider Integration
    E --> Y[Model Provider Selection]
    Y --> Y1[Ollama Provider: Local LLM server]
    Y --> Y2[Hugging Face Provider: Local open-source models]
    Y1 --> Z1[Initialize Ollama endpoint and models]
    Y2 --> Z2[Initialize Hugging Face cache and models]
    Z1 --> Q
    Z2 --> Q
```

## 🟩 User Query & Answer Flow

```mermaid
flowchart TD
    A[User submits question in chat input box] --> B[Chat UI captures input and triggers processing]
    B --> C[System checks if RAG pipeline is ready]
    C --> D[Intent classifier analyzes user's query]
    D --> E[Classifier extracts context hints from query]
    E --> F[Lazy load retriever if needed]
    F --> G[Retriever fetches relevant documents based on query and hints]
    G --> H[Chat handler combines query and documents using RetrievalQA]
    H --> I[Lazy load QA chain and LLM model if needed]
    I --> J[RAG pipeline processes and generates final response]
    J --> K[Chat UI renders response in conversation history]
    K --> L[Store chat history with metadata in session state]
```

## 🟨 Model Provider Management Flow

```mermaid
flowchart TD
    A[User selects model provider in sidebar] --> B[Model Provider dropdown: Ollama or Hugging Face]
    B --> C{Provider type selected?}
    
    C -->|Ollama| D[Initialize Ollama Provider]
    C -->|Hugging Face| E[Initialize Hugging Face Provider]
    
    D --> F[Set Ollama endpoint and model configuration]
    E --> G[Create custom cache directory Set environment variables]
    
    F --> H[Check Ollama availability via HTTP endpoint]
    G --> I[Check Hugging Face model availability and cache status]
    
    H --> J{Ollama available?}
    I --> K{Hugging Face models available?}
    
    J -->|Yes| L[Set Ollama as current provider]
    J -->|No| M[Fallback to Hugging Face or show error]
    
    K -->|Yes| N[Set Hugging Face as current provider]
    K -->|No| O[Download models to custom cache]
    
    L --> P[Provider ready for use]
    N --> P
    O --> P
    
    %% Provider Switching
    P --> Q{User wants to switch provider?}
    Q -->|Yes| R[Clear previous provider cache]
    R --> S[Initialize new provider]
    S --> P
    
    Q -->|No| T[Continue with current provider]
```

## 🟪 Enhanced Decision Flow for Rebuild Logic

```mermaid
flowchart TD
    A[Check RAG Index Status] --> B{SQLite database exists?}
    B -->|No| C[Full Rebuild: No Database]
    B -->|Yes| D{Git tracking file exists?}
    
    D -->|No| E[Full Rebuild: No Tracking]
    D -->|Yes| F[Check for file changes]
    
    F --> G{Any files changed?}
    G -->|Yes| H[Incremental Rebuild: Changed Files]
    G -->|No| I[No Rebuild: Everything Up to Date]
    
    I --> J{User wants Force Rebuild?}
    J -->|Yes| K[Force Rebuild: User Requested]
    J -->|No| L[Load Existing Index]
    
    C --> M[Clean Database Directory]
    E --> M
    K --> M
    
    M --> N[Process All Files]
    H --> O[Process Only Changed Files]
    L --> P[Load from Disk]
    
    N --> Q[Create New Vector Database]
    O --> R[Update Existing Vector Database]
    
    %% Model Provider Integration
    Q --> S[Initialize Model Provider for embedding]
    R --> S
    P --> S
    
    S --> T{Provider type?}
    T -->|Ollama| U[Use Ollama API for embeddings]
    T -->|Hugging Face| V[Use cached Hugging Face models]
    
    U --> W[Store embeddings in Chroma DB]
    V --> W
    W --> X[RAG system ready]
```

## 🟦 Model Caching and Performance Flow

```mermaid
flowchart TD
    A[Model Provider Request] --> B{Model cached in memory?}
    
    B -->|Yes| C[Return cached model instance]
    B -->|No| D[Load model from disk or download]
    
    D --> E{Provider type?}
    E -->|Ollama| F[Initialize Ollama embeddings/LLM]
    E -->|Hugging Face| G[Initialize Hugging Face models]
    
    F --> H[Cache Ollama model instance]
    G --> I[Cache Hugging Face model instance]
    
    H --> J[Return model for use]
    I --> J
    
    %% Cache Management
    J --> K{Provider switching requested?}
    K -->|Yes| L[Clear all cached models]
    L --> M[Free memory and resources]
    M --> N[Initialize new provider]
    
    K -->|No| O[Continue using cached models]
    
    %% Performance Benefits
    C --> P[Fast response: No model loading]
    J --> Q[First use: Model loaded and cached]
    O --> R[Subsequent uses: Fast cached access]
```

## 🔄 Key System Improvements

### **Multi-Provider Architecture**
- **Abstract Interface**: ModelProvider ABC for consistent provider interface
- **Provider Implementations**: OllamaProvider and HuggingFaceProvider
- **Factory Pattern**: ModelProviderFactory for creating provider instances
- **Global Management**: Centralized provider switching and management

### **Model Caching System**
- **In-Memory Caching**: Prevents model reloading on every access
- **Lazy Loading**: Models loaded only when actually needed
- **Cache Management**: Automatic cache clearing during provider switching
- **Custom Cache Directory**: Dedicated Hugging Face cache location

### **Enhanced RAG Management**
- **Lazy Loading**: Retriever and QA chain loaded only when needed
- **Incremental Builds**: Smart rebuild detection and processing
- **Git Tracking**: Enhanced change detection with commit differences
- **User Experience**: Clear progress indicators and confirmation flows

### **Performance Optimizations**
- **Model Caching**: Prevents "Loading checkpoint shards" messages
- **Lazy Initialization**: Components initialized only when needed
- **Memory Management**: Automatic cache clearing to prevent memory issues
- **Provider Switching**: Seamless switching without conflicts

This enhanced Mermaid chart flow provides a comprehensive visual representation of the new multi-provider system, model caching, and incremental build capabilities while maintaining backward compatibility with existing Ollama functionality.