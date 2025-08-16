# FUNCTIONAL FLOW DIAGRAM

## 🟦 RAG Index Build & Ready Flow

Sidebar: user selects project directory, project type, model provider, and endpoint       
↓  
[UIComponents.render_sidebar_config, Line no: 19, core/ui_components.py](https://github.com/anilbattini/codebase-qa/blob/main/core/ui_components.py#L19)  
  └─ **ENHANCED**: Renders sidebar inputs for project directory, project type, model provider selection, and provider-specific configuration.  
  └─ **NEW**: Model Provider dropdown with Ollama and Hugging Face options.  
  └─ **NEW**: Provider-specific configuration (Ollama endpoint vs Hugging Face cache info).  
  └─ Handles user changes, validations, and warnings about existing data.  
↓  
[RagManager.initialize_session_state, Line no: 14, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L14)  
  └─ Initializes critical Streamlit session state keys like retriever and QA chain for stable app state.  
  └─ Ensures consistent session during build or load operations.  
↓  
[ProjectConfig.__init__, Line no: 112, core/config.py](https://github.com/anilbattini/codebase-qa/blob/main/core/config.py#L112)  
  └─ Detects or applies project type (auto/manual).  
  └─ Loads language specific file extensions, chunking rules, ignore patterns, and project indicators.  
↓  
[ModelConfig._initialize_provider, Line no: 63, core/model_config.py](https://github.com/anilbattini/codebase-qa/blob/main/core/model_config.py#L63)  
  └─ **NEW**: Initializes the selected model provider (Ollama or Hugging Face).  
  └─ **NEW**: Sets up provider-specific configuration and availability checks.  
  └─ **NEW**: Handles provider switching with cache management.  
↓  
[RagManager.should_rebuild_index, Line no: 123, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L123)  
  └─ **NEW**: Returns detailed rebuild information: {"rebuild": bool, "reason": str, "files": list}  
  └─ Checks presence of vector DB SQLite file, git/hash tracking files.  
  └─ **ENHANCED**: Detects if source files have changed via Git commit differences or working directory changes.  
  └─ **NEW**: Distinguishes between incremental rebuild (changed files) and full rebuild (no DB, no tracking).  

**REBUILD DECISION LOGIC:**
- **No Database**: `{"rebuild": True, "reason": "no_database", "files": None}` → Full rebuild
- **No Tracking**: `{"rebuild": True, "reason": "no_tracking", "files": None}` → Full rebuild  
- **Files Changed**: `{"rebuild": True, "reason": "files_changed", "files": [file_list]}` → Incremental rebuild
- **No Changes**: `{"rebuild": False, "reason": "no_changes", "files": []}` → Load existing

**FORCE REBUILD HANDLING:**
If user requests force rebuild (via "🔄 Force Rebuild" button)  
↓  
[App.py force rebuild logic, Line no: 54, core/app.py](https://github.com/anilbattini/codebase-qa/blob/main/core/app.py#L54)  
  └─ **NEW**: Clears existing data and performs complete rebuild regardless of file changes.  
  └─ **NEW**: Shows user confirmation: "🔄 Force Rebuild: User requested complete rebuild. Cleaning existing data..."  

**INCREMENTAL REBUILD (Changed Files Detected):**
↓  
[RagManager.build_rag_index with incremental=True, Line no: 162, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L162)  
  └─ **NEW**: Calls build_rag with incremental=True and files_to_process parameter.  
  └─ **NEW**: Shows progress: "🔄 Incremental Build: Processing X changed files..."  
  └─ **NEW**: Preserves existing database and only processes changed files.  

**FULL REBUILD (No DB, No Tracking, or Force Rebuild):**
↓  
[RagManager.cleanup_existing_files, Line no: 41, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L41)  
  └─ Deletes existing vector DB directories and clears session state to ensure clean rebuild.  
  └─ Handles retry logic to overcome file locks during cleanup.  
↓  
[RagManager.build_rag_index with incremental=False, Line no: 162, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L162)  
  └─ **NEW**: Calls build_rag with incremental=False for full rebuild.  
  └─ **NEW**: Shows progress: "🔄 Full Build: Rebuilding entire RAG index..."  

**BUILD PROCESS (build_rag function):**
↓  
[build_rag, Line no: 62, core/build_rag.py](https://github.com/anilbattini/codebase-qa/blob/main/core/build_rag.py#L62)  
  └─ **NEW**: Supports incremental=True/False and files_to_process parameters.  
  └─ **NEW**: For incremental builds: preserves existing database, processes only changed files.  
  └─ **NEW**: For full builds: cleans database directory, processes all files.  
  └─ **ENHANCED**: Shows build mode: "🔄 Incremental build mode - processing only changed files" or "Full build mode".  
  └─ Reads files, applies chunking per language, extracts semantic metadata.  
  └─ Creates output folders and handles incremental file processing via git/hash tracking.  
  └─ **ENHANCED**: Initializes embedding model via ModelProvider interface (Ollama or Hugging Face).  
  └─ **NEW**: Uses in-memory caching to prevent model reloading.  
  └─ Processes each source file: chunks files, extracts metadata, deduplicates using chunk fingerprints.  
  └─ Builds code relationships and hierarchical index files.  
  └─ Sanitizes chunks and sends batches for embedding via selected provider API.  
  └─ **ENHANCED**: Persists embeddings in Chroma vector database with incremental update support.  
  └─ Updates file tracking and logs detailed stats on the process.  
↓  
[ProjectConfig.create_directories, Line no: 181, core/config.py](https://github.com/anilbattini/codebase-qa/blob/main/core/config.py#L181)  
  └─ Ensures all database and logs directories exist for current project type.  
↓  
[FileHashTracker.get_changed_files, core/git_hash_tracker.py](https://github.com/anilbattini/codebase-qa/blob/main/core/git_hash_tracker.py)  
  └─ **ENHANCED**: Now properly detects Git commit differences using `git diff --name-only {last_commit}..{current_commit}`.  
  └─ **NEW**: Combines commit differences + working directory changes for comprehensive change detection.  
  └─ **NEW**: Provides detailed logging: "Git commit diff detected X changed files between {last_commit} and {current_commit}".  
  └─ **NEW**: Falls back to content-hash tracking if Git tracking fails.  
↓  
[ModelProvider.get_embedding_model, Line no: 63, core/model_provider.py](https://github.com/anilbattini/codebase-qa/blob/main/core/model_provider.py#L63)  
  └─ **NEW**: Retrieves embedding model via abstract ModelProvider interface.  
  └─ **NEW**: Supports both Ollama and Hugging Face providers.  
  └─ **NEW**: Implements in-memory caching to prevent model reloading.  
  └─ **NEW**: Uses custom cache directory for Hugging Face models.  
↓  
[ModelConfig.get_current_provider, core/model_config.py](https://github.com/anilbattini/codebase-qa/blob/main/core/model_config.py)  
  └─ **NEW**: Returns the current model provider instance (Ollama or Hugging Face).  
  └─ **NEW**: Handles provider switching with cache management.  
↓  
[chunker_factory.get_chunker, core/chunker_factory.py](https://github.com/anilbattini/codebase-qa/blob/main/core/chunker_factory.py)  
  └─ Selects language-specific chunking strategy function per file extension.  
↓  
[chunker_factory.chunker, core/chunker_factory.py](https://github.com/anilbattini/codebase-qa/blob/main/core/chunker_factory.py)  
  └─ Executes semantic chunking, splitting code into meaningful segments for embedding.  
↓  
[MetadataExtractor.create_enhanced_metadata, core/metadata_extractor.py](https://github.com/anilbattini/codebase-qa/blob/main/core/metadata_extractor.py)  
  └─ Extracts detailed chunk meta class names, function names, dependencies, semantic anchors.  
↓  
[chunk_fingerprint, Line no: 13, core/build_rag.py](https://github.com/anilbattini/codebase-qa/blob/main/core/build_rag.py#L13)  
  └─ Generates SHA-256 hash fingerprints for each chunk to eliminate duplicate embeddings.  
↓  
[chunker_factory.summarize_chunk, core/chunker_factory.py](https://github.com/anilbattini/codebase-qa/blob/main/core/chunker_factory.py)  
  └─ Creates concise summary keywords from chunks for retrieval relevance boosts.  
↓  
[ModelProvider.embed_documents, core/model_provider.py](https://github.com/anilbattini/codebase-qa/blob/main/core/model_provider.py)  
  └─ **NEW**: Embeds chunks using the selected provider (Ollama or Hugging Face).  
  └─ **NEW**: Uses cached model instances to prevent reloading.  
  └─ **NEW**: Handles provider-specific embedding formats and error handling.  
↓  
[Chroma.persist, core/build_rag.py](https://github.com/anilbattini/codebase-qa/blob/main/core/build_rag.py)  
  └─ **ENHANCED**: Persists embeddings in Chroma vector database with incremental update support.  
  └─ **NEW**: Handles both full rebuild and incremental update scenarios.  
↓  
[FileHashTracker.update_tracking, core/git_hash_tracker.py](https://github.com/anilbattini/codebase-qa/blob/main/core/git_hash_tracker.py)  
  └─ **ENHANCED**: Updates file tracking with new commit SHA and file hashes.  
  └─ **NEW**: Supports incremental tracking for changed files only.  
↓  
[ProjectConfig.create_directories, Line no: 181, core/config.py](https://github.com/anilbattini/codebase-qa/blob/main/core/config.py#L181)  
  └─ Ensures all database and logs directories exist for current project type.  
↓  
[RagManager.build_rag_index, Line no: 162, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L162)  
  └─ **ENHANCED**: Stores retriever in session state for later QA chain setup.  
  └─ **NEW**: Supports both incremental and full rebuild modes.  
  └─ **NEW**: Logs detailed build information and performance metrics.  
↓  
[App.py success message, Line no: 150, core/app.py](https://github.com/anilbattini/codebase-qa/blob/main/core/app.py#L150)  
  └─ **ENHANCED**: Shows appropriate success message based on build mode.  
  └─ **NEW**: "✅ RAG index built successfully!" for full builds.  
  └─ **NEW**: "✅ RAG index rebuilt successfully!" for incremental builds.  

**RAG INDEX READY:**
↓  
[App.py chat interface, Line no: 200, core/app.py](https://github.com/anilbattini/codebase-qa/blob/main/core/app.py#L200)  
  └─ **ENHANCED**: Shows chat interface only when RAG is ready.  
  └─ **NEW**: Renders chat history with metadata display.  
  └─ **NEW**: Sets up chat handler with proper error handling.  
  └─ **NEW**: Processes queries using the selected model provider.  

## 🟩 Chat Query Processing Flow

User enters query in chat input form  
↓  
[UIComponents.render_chat_input, Line no: 500, core/ui_components.py](https://github.com/anilbattini/codebase-qa/blob/main/core/ui_components.py#L500)  
  └─ **ENHANCED**: Renders chat input form with proper form submission handling.  
  └─ **NEW**: Always enabled when RAG is ready (no more disabled state).  
↓  
[ChatHandler.process_query, Line no: 43, core/chat_handler.py](https://github.com/anilbattini/codebase-qa/blob/main/core/chat_handler.py#L43)  
  └─ **ENHANCED**: Enhanced query processing with intent classification, rewriting, and RAG support.  
  └─ **NEW**: Supports both RAG-enabled and RAG-disabled modes.  
  └─ **NEW**: Uses in-memory cached models for faster processing.  
↓  
[QueryIntentClassifier.classify_intent, Line no: 36, core/query_intent_classifier.py](https://github.com/anilbattini/codebase-qa/blob/main/core/query_intent_classifier.py#L36)  
  └─ **ENHANCED**: Classifies query intent with confidence scoring.  
  └─ **NEW**: Provides query context hints for better retrieval.  
↓  
[ChatHandler._rewrite_query_with_intent, Line no: 300, core/chat_handler.py](https://github.com/anilbattini/codebase-qa/blob/main/core/chat_handler.py#L43)  
  └─ **ENHANCED**: Rewrites queries based on intent for better retrieval.  
  └─ **NEW**: Uses LLM chain for intelligent query rewriting.  
↓  
[RagManager.get_retriever, Line no: 380, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L380)  
  └─ **NEW**: Lazy loading of retriever - only loads when needed.  
  └─ **NEW**: Prevents unnecessary model loading during RAG loading.  
↓  
[Retriever.invoke, core/chat_handler.py](https://github.com/anilbattini/codebase-qa/blob/main/core/chat_handler.py#L43)  
  └─ **ENHANCED**: Retrieves relevant documents using rewritten query.  
  └─ **NEW**: Falls back to original query if no results.  
  └─ **NEW**: Tries key terms if still no results.  
↓  
[ContextBuilder.build_enhanced_context, core/context_builder.py](https://github.com/anilbattini/codebase-qa/blob/main/core/context_builder.py)  
  └─ **ENHANCED**: Builds enhanced context window using retrieved documents.  
  └─ **NEW**: Incorporates intent-aware context building.  
↓  
[RagManager.lazy_get_qa_chain, Line no: 350, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L350)  
  └─ **NEW**: Lazy loading of QA chain - only created when needed.  
  └─ **NEW**: Uses cached retriever and loads LLM model on demand.  
  └─ **NEW**: Implements in-memory caching for QA chain.  
↓  
[ModelProvider.get_llm_model, Line no: 300, core/model_provider.py](https://github.com/anilbattini/codebase-qa/blob/main/core/model_provider.py#L300)  
  └─ **NEW**: Retrieves LLM model via abstract ModelProvider interface.  
  └─ **NEW**: Supports both Ollama and Hugging Face providers.  
  └─ **NEW**: Implements in-memory caching to prevent model reloading.  
↓  
[QAChain.invoke, core/chat_handler.py](https://github.com/anilbattini/codebase-qa/blob/main/core/chat_handler.py#L43)  
  └─ **ENHANCED**: Generates answer using enhanced context and query.  
  └─ **NEW**: Falls back to direct LLM call if QA chain fails.  
  └─ **NEW**: Handles provider-specific response formats.  
↓  
[App.py chat history update, Line no: 220, core/app.py](https://github.com/anilbattini/codebase-qa/blob/main/core/app.py#L220)  
  └─ **NEW**: Stores chat history with metadata in session state.  
  └─ **NEW**: Forces UI refresh to show new chat history.  
  └─ **NEW**: Handles errors gracefully with user feedback.  

## 🟨 Model Provider Management Flow

User selects model provider in sidebar  
↓  
[UIComponents.render_sidebar_config, Line no: 76, core/ui_components.py](https://github.com/anilbattini/codebase-qa/blob/main/core/ui_components.py#L76)  
  └─ **NEW**: Model Provider dropdown with Ollama and Hugging Face options.  
  └─ **NEW**: Provider-specific configuration display.  
↓  
[ModelConfig.switch_to_ollama/switch_to_huggingface, core/model_config.py](https://github.com/anilbattini/codebase-qa/blob/main/core/model_config.py)  
  └─ **NEW**: Handles provider switching with proper initialization.  
  └─ **NEW**: Sets provider type and initializes provider instance.  
↓  
[set_provider, core/model_provider.py](https://github.com/anilbattini/codebase-qa/blob/main/core/model_provider.py)  
  └─ **NEW**: Global provider management function.  
  └─ **NEW**: Clears previous provider cache to prevent memory issues.  
  └─ **NEW**: Creates new provider instance via factory pattern.  
↓  
[ModelProviderFactory.create_provider, core/model_provider.py](https://github.com/anilbattini/codebase-qa/blob/main/core/model_provider.py)  
  └─ **NEW**: Factory pattern for creating provider instances.  
  └─ **NEW**: Supports both Ollama and Hugging Face providers.  
↓  
[ModelProvider.check_availability, core/model_provider.py](https://github.com/anilbattini/codebase-qa/blob/main/core/model_provider.py)  
  └─ **NEW**: Provider-specific availability checks.  
  └─ **NEW**: Ollama: HTTP endpoint responsiveness.  
  └─ **NEW**: Hugging Face: Local model availability and cache status.  
↓  
[ModelProvider initialization, core/model_provider.py](https://github.com/anilbattini/codebase-qa/blob/main/core/model_provider.py)  
  └─ **NEW**: Provider-specific initialization.  
  └─ **NEW**: Ollama: Sets endpoint URL.  
  └─ **NEW**: Hugging Face: Creates custom cache directory and sets environment variables.  
↓  
[ModelProvider.get_embedding_model/get_llm_model, core/model_provider.py](https://github.com/anilbattini/codebase-qa/blob/main/core/model_provider.py)  
  └─ **NEW**: Provider-specific model loading with in-memory caching.  
  └─ **NEW**: Ollama: Uses langchain_ollama for API calls.  
  └─ **NEW**: Hugging Face: Downloads and caches local models.  
↓  
[Model caching and reuse, core/model_provider.py](https://github.com/anilbattini/codebase-qa/blob/main/core/model_provider.py)  
  └─ **NEW**: In-memory caching prevents model reloading.  
  └─ **NEW**: Cache management with clear_cache method.  
  └─ **NEW**: Custom cache directory for Hugging Face models.  

## 🟪 Error Handling and Fallback Flow

Error occurs during any operation  
↓  
[Logger.log_to_sublog, core/logger.py](https://github.com/anilbattini/codebase-qa/blob/main/core/logger.py)  
  └─ **ENHANCED**: Comprehensive error logging with context.  
  └─ **NEW**: Provider-specific error logging.  
  └─ **NEW**: Cache status and model loading error logging.  
↓  
[Error handling in core functions, various files](https://github.com/anilbattini/codebase-qa/blob/main/core/)  
  └─ **ENHANCED**: Graceful error handling with user feedback.  
  └─ **NEW**: Provider-specific error handling and fallbacks.  
  └─ **NEW**: Cache corruption handling and recovery.  
↓  
[Fallback mechanisms, various files](https://github.com/anilbattini/codebase-qa/blob/main/core/)  
  └─ **NEW**: Fallback to Ollama if Hugging Face fails.  
  └─ **NEW**: Fallback to direct LLM calls if QA chain fails.  
  └─ **NEW**: Fallback to content-hash tracking if Git tracking fails.  
↓  
[User notification, core/app.py](https://github.com/anilbattini/codebase-qa/blob/main/core/app.py)  
  └─ **ENHANCED**: Clear error messages with actionable information.  
  └─ **NEW**: Provider-specific error messages and solutions.  
  └─ **NEW**: Cache status and model availability information.  

## 🔄 Key Improvements Summary

### **Multi-Provider Model System**
- **Abstract Interface**: ModelProvider ABC for consistent provider interface
- **Provider Implementations**: OllamaProvider and HuggingFaceProvider
- **Factory Pattern**: ModelProviderFactory for creating provider instances
- **Global Management**: Centralized provider switching and management

### **Model Caching & Performance**
- **In-Memory Caching**: Prevents model reloading on every access
- **Lazy Loading**: Models loaded only when needed
- **Cache Management**: Automatic cache clearing during provider switching
- **Custom Cache Directory**: Dedicated Hugging Face cache location

### **Enhanced RAG Management**
- **Lazy Loading**: Retriever and QA chain loaded only when needed
- **Incremental Builds**: Smart rebuild detection and processing
- **Git Tracking**: Enhanced change detection with commit differences
- **User Experience**: Clear progress indicators and confirmation flows

### **Improved Error Handling**
- **Provider-Specific Errors**: Tailored error messages and solutions
- **Graceful Fallbacks**: Multiple fallback mechanisms for robustness
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **User Feedback**: Clear error messages with actionable information

This enhanced functional flow provides a comprehensive understanding of the new multi-provider system, model caching, and incremental build capabilities while maintaining backward compatibility with existing Ollama functionality.
