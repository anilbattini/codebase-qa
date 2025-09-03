# FUNCTIONAL_FLOW DIAGRAM - UPDATED for 2025-09-03 ENHANCEMENTS

---

## 🟦 RAG Index Build & Ready Flow

**Provider Selection & Configuration:**  
User opens application and configures provider settings  
↓  
[UIComponents.render_sidebar_config – Provider Selection, Line 72, core/ui_components.py](https://github.com/anilbattini/codebase-qa/blob/main/core/ui_components.py#L72)  
	└─ **NEW**: Renders provider selection: "Choose Provider...", "Ollama (Local)", "Cloud (OpenAI Compatible)"  
	└─ **NEW**: For Ollama: Shows locked model and endpoint fields for consistency  
	└─ **NEW**: For Cloud: Shows endpoint selection (Environment/Custom) and API key validation  
	└─ **NEW**: Validates provider settings and shows connection status  
	└─ **NEW**: Displays embedding model configuration (always local Ollama for embeddings)  
↓  
[ModelConfig.set_provider, Line 214, core/model_config.py](https://github.com/anilbattini/codebase-qa/blob/main/core/model_config.py#L214)  
	└─ **NEW**: Sets active provider (ollama or cloud) in centralized configuration  
	└─ **NEW**: Validates provider choice and updates all related settings  
↓  
[ModelConfig.get_llm, Line 70, core/model_config.py](https://github.com/anilbattini/codebase-qa/blob/main/core/model_config.py#L70)  
	└─ **NEW**: Factory method returns appropriate LLM instance (ChatOllama or CustomLLMClient for cloud)  
	└─ **NEW**: Handles provider-specific parameter mapping and configuration  
	└─ **NEW**: Includes fallback logic and error handling for provider switching  
	└─ **NEW**: Ensures consistent parameter handling across different providers  

---

**Project Configuration:**  
Sidebar: user selects project directory, project type, model, and endpoint  
↓  
[UIComponents.render_sidebar_config, Line 72, core/ui_components.py](https://github.com/anilbattini/codebase-qa/blob/main/core/ui_components.py#L72)  
	└─ Renders sidebar inputs for project directory, project type, provider configuration  
	└─ Handles user changes, validations, and warnings about existing data  
	└─ **NEW**: Includes provider selection and configuration validation  
	└─ **NEW**: Shows "Disable RAG (query LLM directly)" toggle for LLM-only mode  
↓  
[RagManager.initialize_session_state, Line 23, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L23)  
	└─ Initializes critical Streamlit session state keys like retriever and QA chain for stable app state  
	└─ Ensures consistent session during build or load operations  
	└─ **NEW**: Initializes provider-specific session state variables  
↓  
[ProjectConfig.__init__, Line 262, core/config.py](https://github.com/anilbattini/codebase-qa/blob/main/core/config.py#L262)  
	└─ Detects or applies project type (auto/manual detection)  
	└─ Loads language specific file extensions, chunking rules, ignore patterns, and project indicators  
	└─ **NEW**: Supports project type-specific database directories (codebase-qa_<project_type>/)  
	└─ **NEW**: Handles project type switching with database backup and restore  
↓  
[RagManager.should_rebuild_index, Line 174, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L174)  
	└─ **NEW**: Returns detailed rebuild information: {"rebuild": bool, "reason": str, "files": list}  
	└─ Checks presence of vector DB SQLite file, git/hash tracking files  
	└─ **ENHANCED**: Detects if source files have changed via Git commit differences or working directory changes  
	└─ **NEW**: Distinguishes between incremental rebuild (changed files) and full rebuild (no DB, no tracking)  

---

**REBUILD DECISION LOGIC:**  
- **No Database**: `{"rebuild": True, "reason": "no_database", "files": None}` → Full rebuild  
- **No Tracking**: `{"rebuild": True, "reason": "no_tracking", "files": None}` → Full rebuild  
- **Files Changed**: `{"rebuild": True, "reason": "files_changed", "files": [file_list]}` → Incremental rebuild  
- **No Changes**: `{"rebuild": False, "reason": "no_changes", "files": []}` → Load existing  

---

**PROCESS MANAGEMENT & UI PROTECTION (NEW SECTION):**  
If rebuild is required, protect the build process from UI interference  
↓  
[ProcessManager.start_rag_build, Line 18, core/process_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/process_manager.py#L18)  
	└─ **NEW**: Marks RAG building as started with timestamp for timeout detection  
	└─ **NEW**: Sets building flag in session state to prevent concurrent operations  
	└─ **NEW**: Disables UI elements that could interfere with build process  
	└─ **NEW**: Provides build timeout detection (10 minutes) and recovery mechanisms  
↓  
[ProcessManager.disable_ui_during_build, Line 70, core/process_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/process_manager.py#L70)  
	└─ **NEW**: Returns safe UI state during build to prevent user interference  
	└─ **NEW**: Blocks force rebuild, debug mode, and project type changes during build  
	└─ **NEW**: Shows build status with progress and timeout warnings  

---

**FORCE REBUILD HANDLING:**  
If user requests force rebuild (via "🔄 Force Rebuild" button)  
↓  
[App.py force rebuild logic, Line 54, core/app.py](https://github.com/anilbattini/codebase-qa/blob/main/core/app.py#L54)  
	└─ **NEW**: Clears existing data and performs complete rebuild regardless of file changes  
	└─ **NEW**: Shows user confirmation: "🔄 Force Rebuild: User requested complete rebuild. Cleaning existing data..."  
	└─ **NEW**: Uses ProcessManager to protect the force rebuild process  

---

**INCREMENTAL REBUILD (Changed Files Detected):**  
↓  
[RagManager.build_rag_index with incremental=True, Line 206, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L206)  
	└─ **NEW**: Calls build_rag with incremental=True and files_to_process parameter  
	└─ **NEW**: Shows progress: "🔄 Incremental Build: Processing X changed files..."  
	└─ **NEW**: Preserves existing database and only processes changed files  

---

**FULL REBUILD (No DB, No Tracking, or Force Rebuild):**  
↓  
[RagManager.cleanup_existing_files, Line 91, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L91)  
	└─ Deletes existing vector DB directories and clears session state to ensure clean rebuild  
	└─ Handles retry logic with timeout to overcome file locks during cleanup  
	└─ **NEW**: Includes Chroma connection cleanup to prevent database locking issues  
↓  
[RagManager.build_rag_index with incremental=False, Line 206, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L206)  
	└─ **NEW**: Calls build_rag with incremental=False for full rebuild  
	└─ **NEW**: Shows progress: "🔄 Full Build: Rebuilding entire RAG index..."  

---

**BUILD PROCESS (build_rag function):**  
↓  
[build_rag, Line 64, core/build_rag.py](https://github.com/anilbattini/codebase-qa/blob/main/core/build_rag.py#L64)  
	└─ **NEW**: Supports incremental=True/False and files_to_process parameters  
		└─ **NEW**: For incremental builds: preserves existing database, processes only changed files  
		└─ **NEW**: For full builds: cleans database directory, processes all files  
	└─ **ENHANCED**: Shows build mode: "🔄 Incremental build mode - processing only changed files" or "Full build mode"  
	└─ Reads files, applies chunking per language, extracts semantic metadata  
	└─ Creates output folders and handles incremental file processing via git/hash tracking  
	└─ **NEW**: Uses ModelConfig.get_embedding_model() for consistent embedding model selection  
	└─ Initializes embedding model and verifies Ollama endpoint responsiveness  
	└─ Processes each source file: chunks files, extracts metadata, deduplicates using chunk fingerprints  
	└─ **NEW**: Builds cross-references for enhanced context capabilities  
	└─ Builds code relationships and hierarchical index files  
	└─ Sanitizes chunks and sends batches for embedding via Ollama API  
	└─ **ENHANCED**: Persists embeddings in Chroma vector database with incremental update support  
	└─ Updates file tracking and logs detailed stats on the process  
↓  
[ProjectConfig.create_directories, Line 342, core/config.py](https://github.com/anilbattini/codebase-qa/blob/main/core/config.py#L342)  
	└─ Ensures all database and logs directories exist for current project type  
	└─ **NEW**: Creates project-type-specific directories (codebase-qa_<project_type>/)  
↓  
[FileHashTracker.get_changed_files, Line 22, core/git_hash_tracker.py](https://github.com/anilbattini/codebase-qa/blob/main/core/git_hash_tracker.py#L22)  
	└─ **ENHANCED**: Now properly detects Git commit differences using `git diff --name-only {last_commit}..{current_commit}`  
	└─ **NEW**: Combines commit differences + working directory changes for comprehensive change detection  
	└─ **NEW**: Provides detailed logging: "Git commit diff detected X changed files between {last_commit} and {current_commit}"  
	└─ **NEW**: Falls back to content-hash tracking if Git tracking fails  
	└─ **NEW**: Handles gitignore patterns and hierarchical ignore rules  

---

**Cross-Reference Building (NEW STEP):**  
↓  
[CrossReferenceBuilder.build_cross_references, Line 54, core/cross_reference_builder.py](https://github.com/anilbattini/codebase-qa/blob/main/core/cross_reference_builder.py#L54)  
	└─ **NEW**: Extracts symbol definitions from method signatures and metadata  
	└─ **NEW**: Builds comprehensive usage maps and call relationships  
	└─ **NEW**: Builds inheritance and interface implementation relationships  
	└─ **NEW**: Detects design pattern instances (Factory, Singleton, Observer, Strategy, etc.)  
	└─ **NEW**: Generates statistics about cross-references and code complexity  
↓  
[CrossReferenceBuilder.save_cross_references, Line 382, core/cross_reference_builder.py](https://github.com/anilbattini/codebase-qa/blob/main/core/cross_reference_builder.py#L382)  
	└─ **NEW**: Saves cross-reference data to structured files:  
		└─ cross_references.json (main cross-reference data)  
		└─ call_graph_index.json (function call relationships)  
		└─ inheritance_index.json (class hierarchy mappings)  
		└─ symbol_usage_index.json (symbol usage patterns)  
	└─ **NEW**: Creates quick-lookup files for common queries  

---

**Enhanced Context Building (Phase 3 - NEW STEP):**  
↓  
[ContextBuilder.load_context_data, Line 34, core/context_builder.py](https://github.com/anilbattini/codebase-qa/blob/main/core/context_builder.py#L34)  
	└─ **NEW**: Loads cross-reference and hierarchical data for context assembly  
	└─ **NEW**: Initializes multi-strategy context building capabilities  
	└─ **NEW**: Prepares enhanced context layers for query processing  
↓  
[ModelConfig.get_embedding_model, Line 186, core/model_config.py](https://github.com/anilbattini/codebase-qa/blob/main/core/model_config.py#L186)  
	└─ Retrieves the embedding model name to ensure consistency in embedding dimensions  
	└─ **NEW**: Centralized embedding model configuration prevents dimension mismatches  
↓  
[ModelConfig.get_ollama_endpoint, Line 202, core/model_config.py](https://github.com/anilbattini/codebase-qa/blob/main/core/model_config.py#L202)  
	└─ Retrieves the Ollama server endpoint URL used for embedding and LLM calls  
	└─ **NEW**: Supports both local Ollama and cloud provider endpoints  
↓  
[chunker_factory.get_chunker, Line 164, core/chunker_factory.py](https://github.com/anilbattini/codebase-qa/blob/main/core/chunker_factory.py#L164)  
	└─ Selects language-specific chunking strategy function per file extension  
	└─ **NEW**: Enhanced semantic chunking with context hierarchy and improved overlap  
↓  
[SemanticChunker.create_semantic_chunker, Line 16, core/chunker_factory.py](https://github.com/anilbattini/codebase-qa/blob/main/core/chunker_factory.py#L16)  
	└─ Executes semantic chunking, splitting code into meaningful segments for embedding  
	└─ **NEW**: Config-driven, semantic-aware chunking with context hierarchy  
	└─ **NEW**: Calculates semantic richness scores and detects chunk types  
↓  
[MetadataExtractor.create_enhanced_metadata, Line 21, core/metadata_extractor.py](https://github.com/anilbattini/codebase-qa/blob/main/core/metadata_extractor.py#L21)  
	└─ Extracts detailed chunk meta class names, function names, dependencies, semantic anchors  
	└─ **NEW**: Enhanced method signature extraction for multiple languages  
	└─ **NEW**: Design pattern detection and error handling pattern extraction  
	└─ **NEW**: API usage pattern extraction for external service detection  
↓  
[chunk_fingerprint, Line 24, core/build_rag.py](https://github.com/anilbattini/codebase-qa/blob/main/core/build_rag.py#L24)  
	└─ Generates SHA-256 hash fingerprints for each chunk to eliminate duplicate embeddings  
↓  
[chunker_factory.summarize_chunk, Line 176, core/chunker_factory.py](https://github.com/anilbattini/codebase-qa/blob/main/core/chunker_factory.py#L176)  
	└─ Creates concise summary keywords from chunks for retrieval relevance boosts  
↓  
[build_code_relationship_map, Line 52, core/build_rag.py](https://github.com/anilbattini/codebase-qa/blob/main/core/build_rag.py#L52)  
	└─ Constructs mappings of code dependencies to understand file impact and relationships  
	└─ **NEW**: Uses normalized paths for cross-platform compatibility  
↓  
[HierarchicalIndexer.create_hierarchical_index, Line 21, core/hierarchical_indexer.py](https://github.com/anilbattini/codebase-qa/blob/main/core/hierarchical_indexer.py#L21)  
	└─ Builds layered hierarchical indexes grouping chunks by modules, files, classes  
	└─ **NEW**: Multi-level indices for component, file, business logic, UI flow, and API levels  
	└─ **NEW**: Surfaces missing anchors/attributes for RAG pipeline health monitoring  
↓  
(Sanitize chunks for embedding ingestion)  
	└─ Cleans chunk contents and metadata ensuring compatibility with vector storage  
	└─ **NEW**: Enhanced sanitization handles complex metadata structures  
↓  
(Embed chunks in batches with OllamaEmbeddings via Ollama API)  
	└─ Sends semantic chunks in batches to generate embeddings with consistent vector dimensions  
	└─ **NEW**: Batch processing with progress tracking and timeout protection  
	└─ **NEW**: Retry logic for embedding computation failures  
↓  
(Store embedded vectors and metadata in persistent Chroma vector database)  
	└─ **ENHANCED**: For incremental builds: updates existing database with new documents  
	└─ **ENHANCED**: For full builds: creates new database from scratch  
	└─ **NEW**: Handles incremental vs full database creation with proper error handling and fallbacks  
	└─ **NEW**: Database lock prevention with connection cleanup  
↓  
(Update git or file hash tracking records)  
	└─ Records processed files for incremental rebuild detection on next run  
	└─ **NEW**: Enhanced tracking with both Git commit and working directory changes  
↓  
[ProcessManager.finish_rag_build, Line 33, core/process_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/process_manager.py#L33)  
	└─ **NEW**: Marks RAG building as finished and clears build state  
	└─ **NEW**: Re-enables all UI elements that were disabled during build  
	└─ **NEW**: Cleans up process resources and logs build completion  
↓  
[RagManager.build_rag_index completion, Line 206, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L206)  
	└─ Finalizes by setting retriever and QA chain in session state for query answering  
	└─ **NEW**: Uses provider-specific LLM configuration for QA chain setup  

---

**NO REBUILD REQUIRED (No changes detected):**  
↓  
[App.py no changes handling, Line 89, core/app.py](https://github.com/anilbattini/codebase-qa/blob/main/core/app.py#L89)  
	└─ **NEW**: Shows success message: "✅ No file changes detected. RAG index is up to date."  
	└─ **NEW**: Displays info box: "💡 No new files to process. The RAG index is already up to date with the latest changes."  
	└─ **NEW**: Provides "🔄 Force Rebuild" button for manual rebuild option  
	└─ **NEW**: Similar to project type change logic: asks user permission before major operations  
↓  
[RagManager.load_existing_rag_index, Line 251, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L251)  
	└─ Loads existing embeddings, vector DB, retriever, and QA chain from disk  
	└─ **CRITICAL FIX**: Uses same embedding model as in build step to avoid dimension mismatches  
	└─ **NEW**: Embedding model consistency check: `embedding_model = "nomic-embed-text:latest"`  
	└─ **NEW**: Provider-specific LLM setup with fallback logic  
	└─ Ensures session state is ready for query processing  
↓  
RAG system is ready for queries with retriever and QA chain available in Streamlit session state  

---

**Debug Mode Activation (NEW SECTION):**  
If user wants to access debug tools  
↓  
[UIComponents.render_welcome_screen – 5-click debug, Line 288, core/ui_components.py](https://github.com/anilbattini/codebase-qa/blob/main/core/ui_components.py#L288)  
	└─ **NEW**: Tracks title button clicks (5 clicks to enable debug mode)  
	└─ **NEW**: Shows debug click counter and enables debug mode after 5 clicks  
	└─ **NEW**: Displays success message: "🔧 Debug mode enabled! Check the sidebar for debug options."  
↓  
[UIComponents.render_debug_section, Line 388, core/ui_components.py](https://github.com/anilbattini/codebase-qa/blob/main/core/ui_components.py#L388)  
	└─ **NEW**: Renders comprehensive debug tools and inspection section  
	└─ **NEW**: Creates tabs for Vector DB Inspector, Chunk Analyzer, Retrieval Tester, Build Status, Logs  
	└─ **NEW**: Integrates with actual core functionality (not mock implementations)  

---

## 🟩 User Query & Answer Flow

**Query Input and RAG Mode Check:**  
User enters a question in the chat UI input box  
↓  
[UIComponents.render_chat_input, Line 347, core/ui_components.py](https://github.com/anilbattini/codebase-qa/blob/main/core/ui_components.py#L347)  
	└─ Captures user's natural language question input  
	└─ Disables input if RAG system is not fully ready  
	└─ **NEW**: Supports form-based input with proper submission handling  
↓  
[App.py RAG disable check, Line 40, core/app.py](https://github.com/anilbattini/codebase-qa/blob/main/core/app.py#L40)  
	└─ **NEW**: Checks "Disable RAG (query LLM directly)" toggle in sidebar  
	└─ **NEW**: If RAG disabled: sends query directly to LLM without retrieval  
	└─ **NEW**: If RAG enabled: proceeds with full RAG pipeline processing  
↓  
[RagManager.is_ready, Line 328, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L328)  
	└─ Checks session state to ensure retriever and QA chain objects are initialized  
	└─ Prevents query submission if system isn't ready  
	└─ **NEW**: Validates both retriever and provider-specific QA chain readiness  

---

**Enhanced Query Processing Pipeline:**  
↓  
[ChatHandler.process_query, Line 43, core/chat_handler.py](https://github.com/anilbattini/codebase-qa/blob/main/core/chat_handler.py#L43)  
	└─ **NEW**: Enhanced query processing with Phase 3 context + full backward compatibility  
	└─ **NEW**: Multi-phase processing: Intent → Rewriting → Retrieval → Context → Generation → Ranking  
↓  
[QueryIntentClassifier.classify_intent, Line 34, core/query_intent_classifier.py](https://github.com/anilbattini/codebase-qa/blob/main/core/query_intent_classifier.py#L34)  
	└─ Applies pattern-based matching on user query to classify intent (overview, technical, business_logic, ui_flow, impact_analysis)  
	└─ Returns intent label and confidence score to inform retrieval strategy  
	└─ **NEW**: Enhanced intent classification with confidence scoring  
↓  
[ChatHandler._rewrite_query_with_intent, Line 263, core/chat_handler.py](https://github.com/anilbattini/codebase-qa/blob/main/core/chat_handler.py#L263)  
	└─ **NEW**: Enhanced query rewriting with intent awareness  
	└─ **NEW**: Uses centralized rewrite chain with project type and intent context  
	└─ **NEW**: Includes fallback logic if rewriting fails  
↓  
[RetrievalLogic.retrieve_with_fallback, Line 176, core/retrieval_logic.py](https://github.com/anilbattini/codebase-qa/blob/main/core/retrieval_logic.py#L176)  
	└─ **NEW**: Multi-fallback retrieval strategy for robust document finding  
	└─ **NEW**: Strategy 1: Try rewritten query first  
	└─ **NEW**: Strategy 2: Fall back to original query if no results  
	└─ **NEW**: Strategy 3: Extract key terms and search with those  
	└─ **NEW**: Comprehensive logging of each retrieval attempt  
↓  
[QueryIntentClassifier.get_query_context_hints, Line 64, core/query_intent_classifier.py](https://github.com/anilbattini/codebase-qa/blob/main/core/query_intent_classifier.py#L64)  
	└─ Extracts relevant keywords or anchors based on classified intent  
	└─ These hints boost relevant context retrieval and improve accuracy  
↓  
[Retriever.invoke via session state, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py)  
	└─ Performs vector similarity search in Chroma vector store  
	└─ Retrieves top-k most semantically relevant code chunks for user query  
	└─ **NEW**: Uses consistent embedding model to prevent dimension mismatches  

---

**Phase 3 Enhanced Context Assembly:**  
↓  
[ContextBuilder.build_enhanced_context, Line 75, core/context_builder.py](https://github.com/anilbattini/codebase-qa/blob/main/core/context_builder.py#L75)  
	└─ **NEW**: Multi-strategy context assembly using cross-references  
	└─ **NEW**: Supports both original hierarchical context and enhanced layered context  
	└─ **NEW**: Selects appropriate context strategies based on query intent  
↓  
[ContextBuilder._select_strategies, Line 197, core/context_builder.py](https://github.com/anilbattini/codebase-qa/blob/main/core/context_builder.py#L197)  
	└─ **NEW**: Selects context building strategies based on intent:  
		└─ Overview: Hierarchical + Project Structure  
		└─ Technical: Call Flow + Implementation Details  
		└─ Business Logic: Inheritance + Validation Rules  
		└─ Impact Analysis: Impact + Dependency Chains  
↓  
[ContextBuilder._build_hierarchical_context, Line 222, core/context_builder.py](https://github.com/anilbattini/codebase-qa/blob/main/core/context_builder.py#L222)  
	└─ **NEW**: Builds hierarchical context layer using project structure  
↓  
[ContextBuilder._build_call_flow_context, Line 242, core/context_builder.py](https://github.com/anilbattini/codebase-qa/blob/main/core/context_builder.py#L242)  
	└─ **NEW**: Builds call flow context layer using function relationships  
↓  
[ContextBuilder._build_inheritance_context, Line 268, core/context_builder.py](https://github.com/anilbattini/codebase-qa/blob/main/core/context_builder.py#L268)  
	└─ **NEW**: Builds inheritance context layer using class hierarchies  
↓  
[ContextBuilder._build_impact_context, Line 294, core/context_builder.py](https://github.com/anilbattini/codebase-qa/blob/main/core/context_builder.py#L294)  
	└─ **NEW**: Builds impact analysis context layer using dependency chains  
↓  
[ContextBuilder._rank_context_layers, Line 332, core/context_builder.py](https://github.com/anilbattini/codebase-qa/blob/main/core/context_builder.py#L332)  
	└─ **NEW**: Ranks context layers by relevance to query intent  
↓  
[ContextBuilder.format_context_for_llm, Line 355, core/context_builder.py](https://github.com/anilbattini/codebase-qa/blob/main/core/context_builder.py#L355)  
	└─ **NEW**: Formats enhanced multi-layered context for LLM consumption  

---

**Enhanced Query Generation and Processing:**  
↓  
[PromptRouter.build_enhanced_query, Line 47, core/prompt_router.py](https://github.com/anilbattini/codebase-qa/blob/main/core/prompt_router.py#L47)  
	└─ **NEW**: Intent-driven prompt routing with specialized templates for RAG Codebase QA  
	└─ **NEW**: Provider-adaptive templates (Ollama vs Cloud)  
	└─ **NEW**: Original question preservation with enhanced context  
↓  
[ChatHandler._analyze_impact_with_intent, Line 295, core/chat_handler.py](https://github.com/anilbattini/codebase-qa/blob/main/core/chat_handler.py#L295)  
	└─ **NEW**: Performs impact analysis if applicable to intent (impact_analysis queries)  
	└─ **NEW**: Extracts file mentions and traces dependency chains  
↓  
[RetrievalQA chain via provider-specific LLM, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py)  
	└─ Constructs prompt consisting of user query plus retrieved code chunks with enhanced context  
	└─ **NEW**: Uses ModelConfig.get_llm() factory for provider-agnostic LLM access  
		└─ Sends prompt to configured LLM (Ollama or Cloud) for natural language generation  
↓  
[ChatHandler._rerank_docs_by_intent, Line 230, core/chat_handler.py](https://github.com/anilbattini/codebase-qa/blob/main/core/chat_handler.py#L230)  
	└─ **NEW**: Document re-ranking based on intent and relevance scoring  
	└─ **NEW**: Intent-aware scoring that prioritizes relevant document types  
	└─ **NEW**: Returns actual Document objects (not just file name strings)  
↓  
[build_rag.get_impact, Line 589, core/build_rag.py](https://github.com/anilbattini/codebase-qa/blob/main/core/build_rag.py#L589)  
	└─ Performs impact analysis tracing file dependencies for related/affected code  
	└─ Returns list of impacted files to augment response metadata  
	└─ **NEW**: Uses normalized path handling for cross-platform compatibility  

---

**Answer Validation & Pipeline Diagnostics (NEW SECTION):**  
↓  
[AnswerValidationHandler.validate_answer_quality, Line 33, core/answer_validation_handler.py](https://github.com/anilbattini/codebase-qa/blob/main/core/answer_validation_handler.py#L33)  
	└─ **NEW**: Enhanced local validation building on existing quality analysis  
	└─ **NEW**: Multi-metric scoring (relevancy, completeness, accuracy, code-specific quality)  
	└─ **NEW**: Overall score calculation with weighted components  
↓  
[AnswerValidationHandler.diagnose_quality_issue, Line 118, core/answer_validation_handler.py](https://github.com/anilbattini/codebase-qa/blob/main/core/answer_validation_handler.py#L118)  
	└─ **NEW**: Comprehensive pipeline diagnostics to identify quality bottlenecks  
	└─ **NEW**: Analyzes rewriting quality, retrieval coverage, and answer quality  
	└─ **NEW**: Generates actionable fix recommendations with priority levels  
↓  
[UIComponents.render_chat_history, Line 359, core/ui_components.py](https://github.com/anilbattini/codebase-qa/blob/main/core/ui_components.py#L359)  
	└─ Renders generated answer, source chunk attributions, and impact metadata in UI  
	└─ Supports expansion, chat context, and debug information display  
	└─ **NEW**: Enhanced metadata display with intent, confidence, rewritten query  
	└─ **NEW**: Handles both old (4 items) and new (5 items) chat history formats for backward compatibility  
	└─ **NEW**: Shows top 5 sources with detailed metadata and chunk information  

---

**Debug Tools Integration (When Debug Mode Enabled):**  
↓  
[UIComponents.render_debug_section, Line 388, core/ui_components.py](https://github.com/anilbattini/codebase-qa/blob/main/core/ui_components.py#L388)  
	└─ **NEW**: Shows comprehensive debug tools in expandable section  
	└─ **NEW**: Vector DB Inspector: Database statistics and health checking  
	└─ **NEW**: Chunk Analyzer: File-specific chunk analysis with metadata  
	└─ **NEW**: Retrieval Tester: Query performance testing with relevance scores  
	└─ **NEW**: Build Status: Database file analysis and tracking status  
	└─ **NEW**: Logs Viewer: Real-time log file access with download capability  
	└─ **NEW**: All tools use existing session state retriever (no recreation)  

---

**Processing Logs and Monitoring:**  
↓  
[UIComponents.render_processing_logs, Line 646, core/ui_components.py](https://github.com/anilbattini/codebase-qa/blob/main/core/ui_components.py#L646)  
	└─ **NEW**: Renders processing logs section with scrollable display  
	└─ **NEW**: Shows last 50 logs to prevent overwhelming display  
	└─ **NEW**: Provides clear and copy actions for log management  
	└─ **NEW**: Only visible when debug mode is enabled

---

## 🟨 Enhanced Provider Selection Flow

**Provider Configuration:**  
User opens application and needs to configure LLM provider  
↓  
[UIComponents.render_sidebar_config, Line 72, core/ui_components.py](https://github.com/anilbattini/codebase-qa/blob/main/core/ui_components.py#L72)  
	└─ Shows provider selection dropdown: "Choose Provider...", "Ollama (Local)", "Cloud (OpenAI Compatible)"  
↓  
**If Ollama Selected:**  
[ModelConfig.set_provider("ollama"), Line 214, core/model_config.py](https://github.com/anilbattini/codebase-qa/blob/main/core/model_config.py#L214)  
	└─ Sets provider to "ollama" in centralized configuration  
	└─ Shows locked/disabled model and endpoint fields for consistency  
	└─ Uses default values: model="llama3.1:latest", endpoint="http://localhost:11434"  
↓  
**If Cloud Selected:**  
[ModelConfig.set_provider("cloud"), Line 214, core/model_config.py](https://github.com/anilbattini/codebase-qa/blob/main/core/model_config.py#L214)  
	└─ Sets provider to "cloud" in centralized configuration  
	└─ Shows endpoint options: "From Environment" or "Custom Endpoint"  
	└─ Validates CLOUD_API_KEY environment variable  
	└─ Uses hardcoded model: "gpt-4.1"  
	└─ Still requires local Ollama for embeddings (editable settings)  
↓  
[ModelConfig.get_llm, Line 70, core/model_config.py](https://github.com/anilbattini/codebase-qa/blob/main/core/model_config.py#L70)  
	└─ Factory method returns appropriate LLM client:  
		└─ For Ollama: ChatOllama instance  
		└─ For Cloud: CustomLLMClient instance with Runnable compatibility  
↓  
[CustomLLMClient.invoke_with_system_user, Line 59, core/custom_llm_client.py](https://github.com/anilbattini/codebase-qa/blob/main/core/custom_llm_client.py#L59)  
	└─ **NEW**: Direct method for system/user prompt separation  
	└─ **NEW**: Handles OpenAI-compatible API calls with proper message formatting  
	└─ **NEW**: Called directly from query.chat_handler.py for cloud provider queries  

---

## 🟪 Process Management & UI Protection Flow

**Build Process Protection:**  
When RAG building starts, protect the process from UI interference  
↓  
[ProcessManager.start_rag_build, Line 18, core/process_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/process_manager.py#L18)  
	└─ Records build start time and process ID for timeout detection  
	└─ Sets building flag in session state to prevent concurrent operations  
	└─ Logs build start with project details  
↓  
[ProcessManager.disable_ui_during_build, Line 70, core/process_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/process_manager.py#L70)  
	└─ Returns safe UI state during build to prevent user interference  
	└─ Blocks force rebuild, debug mode, and project type changes  
	└─ Shows build status with progress information  
↓  
[ProcessManager.check_rag_build_timeout, Line 50, core/process_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/process_manager.py#L50)  
	└─ Monitors build timeout (15 minutes) and provides recovery options  
	└─ Shows timeout warning and force stop option if exceeded  
↓  
[ProcessManager.finish_rag_build, Line 33, core/process_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/process_manager.py#L33)  
	└─ Clears building flag and re-enables all UI elements  
	└─ Cleans up process resources and logs completion  

---

This comprehensive update ensures all recent improvements and architectural changes from 2025-09-03 are accurately represented with proper GitHub links, exact line numbers, and detailed flow descriptions for all major user interactions and internal processing pipelines.
