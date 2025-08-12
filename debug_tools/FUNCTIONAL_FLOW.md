# FUNCTIONAL FLOW DIAGRAM

## 🟦 RAG Index Build & Ready Flow

Sidebar: user selects project directory, project type, model, and endpoint       
↓  
[UIComponents.render_sidebar_config, Line no: 19, core/ui_components.py](https://github.com/anilbattini/codebase-qa/blob/main/core/ui_components.py#L19)  
  └─ Renders sidebar inputs for project directory, project type, Ollama model and endpoint.  
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
  └─ Initializes embedding model and verifies Ollama endpoint responsiveness.  
  └─ Processes each source file: chunks files, extracts metadata, deduplicates using chunk fingerprints.  
  └─ Builds code relationships and hierarchical index files.  
  └─ Sanitizes chunks and sends batches for embedding via Ollama API.  
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
[ModelConfig.get_embedding_model, Line no: 63, core/model_config.py](https://github.com/anilbattini/codebase-qa/blob/main/core/model_config.py#L63)  
  └─ Retrieves the embedding model name to ensure consistency in embedding dimensions.  
↓  
[ModelConfig.get_ollama_endpoint, core/model_config.py](https://github.com/anilbattini/codebase-qa/blob/main/core/model_config.py)  
  └─ Retrieves the Ollama server endpoint URL used for embedding and LLM calls.  
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
[build_code_relationship_map, core/build_rag.py](https://github.com/anilbattini/codebase-qa/blob/main/core/build_rag.py)  
  └─ Constructs mappings of code dependencies to understand file impact and relationships.  
↓  
[HierarchicalIndexer.create_hierarchical_index, core/hierarchical_indexer.py](https://github.com/anilbattini/codebase-qa/blob/main/core/hierarchical_indexer.py)  
  └─ Builds layered hierarchical indexes grouping chunks by modules, files, classes.  
↓  
(Sanitize chunks for embedding ingestion)  
  └─ Cleans chunk contents and metadata ensuring compatibility with vector storage.  
↓  
(Embed chunks in batches with OllamaEmbeddings via Ollama API)  
  └─ Sends semantic chunks in batches to generate embeddings with consistent vector dimensions.  
↓  
(Store embedded vectors and metadata in persistent Chroma vector database)  
  └─ **ENHANCED**: For incremental builds: updates existing database with new documents.  
  └─ **ENHANCED**: For full builds: creates new database from scratch.  
  └─ **NEW**: Handles incremental vs full database creation with proper error handling and fallbacks.  
↓  
(Update git or file hash tracking records)  
  └─ Records processed files for incremental rebuild detection on next run.  
↓  
[RagManager.build_rag_index, Line no: 162, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L162)  
  └─ Finalizes by setting retriever and QA chain in session state for query answering.  

**NO REBUILD REQUIRED (No changes detected):**
↓  
[App.py no changes handling, Line no: 89, core/app.py](https://github.com/anilbattini/codebase-qa/blob/main/core/app.py#L89)  
  └─ **NEW**: Shows success message: "✅ No file changes detected. RAG index is up to date."  
  └─ **NEW**: Displays info box: "💡 No new files to process. The RAG index is already up to date with the latest changes."  
  └─ **NEW**: Provides "🔄 Force Rebuild" button for manual rebuild option.  
  └─ **NEW**: Similar to project type change logic: asks user permission before major operations.  
↓  
[RagManager.load_existing_rag_index, Line no: 194, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L194)  
  └─ Loads existing embeddings, vector DB, retriever, and QA chain from disk.  
  └─ Uses same embedding model as in build step to avoid dimension mismatches.  
  └─ Ensures session state is ready for query processing.  
↓  
RAG system is ready for queries with retriever and QA chain available in Streamlit session state.


## 🟩 User Query & Answer Flow

User enters a question in the chat UI input box           
↓  
[UIComponents.render_chat_input, Line no: 161, core/ui_components.py](https://github.com/kumarb/codebase-qa/blob/main/core/ui_components.py#L161)  
  └─ Captures user's natural language question input.  
  └─ Disables input if RAG system is not fully ready.  
↓  
[RagManager.is_ready, Line no: 195, core/rag_manager.py](https://github.com/kumarb/codebase-qa/blob/main/core/rag_manager.py#L195)  
  └─ Checks session state to ensure retriever and QA chain objects are initialized.  
  └─ Prevents query submission if system isn't ready.  
↓  
[QueryIntentClassifier.classify_intent, Line no: 29, core/query_intent_classifier.py](https://github.com/kumarb/codebase-qa/blob/main/core/query_intent_classifier.py#L29)  
  └─ Applies pattern-based matching on user query to classify intent (e.g., overview, validation).  
  └─ Returns intent label and confidence score to inform retrieval strategy.  
↓  
[QueryIntentClassifier.get_query_context_hints, Line no: 56, core/query_intent_classifier.py](https://github.com/kumarb/codebase-qa/blob/main/core/query_intent_classifier.py#L56)  
  └─ Optionally extracts relevant keywords or anchors based on classified intent.  
  └─ These hints boost relevant context retrieval.  
↓  
[Retriever.get_relevant_documents, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py)  
  └─ Performs vector similarity search in Chroma vector store.  
  └─ Retrieves top-k most semantically relevant code chunks for user query.  
↓  
[ChatHandler & RetrievalQA (combined with LangChain library), core/chat_handler.py](https://github.com/anilbattini/codebase-qa/blob/main/core/chat_handler.py)  
  └─ Constructs prompt consisting of user query plus retrieved code chunks with metadata.  
  └─ Sends prompt to Ollama LLM for natural language generation of the answer.  
↓  
[build_rag.get_impact, Line no: 379, core/build_rag.py](https://github.com/anilbattini/codebase-qa/blob/main/core/build_rag.py#L379)  
  └─ Optionally performs impact analysis tracing file dependencies for related/affected code.  
  └─ Returns list of impacted files to augment response metadata.  
↓  
[UIComponents.render_chat_history, Line no: 282, core/ui_components.py](https://github.com/kumarb/codebase-qa/blob/main/core/ui_components.py#L282)  
  └─ Renders generated answer, source chunk attributions, and impact metadata in UI.  
  └─ Supports expansion, chat context, and debug information display.
