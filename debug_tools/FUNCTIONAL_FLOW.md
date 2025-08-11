# FUNCTIONAL FLOW DIRAGRAM

## 🟦 RAG Index Build & Ready Flow

```python
Sidebar: user selects project directory, project type, model, and endpoint       [BLUE]
|  (User input in the sidebar UI initializes project setup parameters)
v
[UIComponents.render_sidebar_config, Line no: 19, core/ui_components.py](https://github.com/anilbattini/codebase-qa/blob/main/core/ui_components.py#L19)
    — Renders sidebar inputs for project directory, project type, Ollama model and endpoint.
    — Handles user changes, validations, and warnings about existing data.

|
v
[RagManager.initialize_session_state, Line no: 14, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L14)
    — Initializes critical Streamlit session state keys like retriever and QA chain for stable app state.
    — Ensures consistent session during build or load operations.

|
v
[ProjectConfig.__init__, Line no: 112, core/config.py](https://github.com/anilbattini/codebase-qa/blob/main/core/config.py#L112)
    — Detects or applies project type (auto/manual).
    — Loads language specific file extensions, chunking rules, ignore patterns, and project indicators.

|
v
[RagManager.should_rebuild_index, Line no: 74, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L74)
    — Checks presence of vector DB SQLite file, git/hash tracking files.
    — Detects if source files have changed or if force rebuild is requested.

|--- If REBUILD is needed (new or changed files, or force rebuild)
|    |
|    v
|    [RagManager.cleanup_existing_files, Line no: 41, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L41)
|        — Deletes existing vector DB directories and clears session state to ensure clean rebuild.
|        — Handles retry logic to overcome file locks during cleanup.

|    |
|    v
|    [RagManager.build_rag_index, Line no: 165, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L165)
|        — Coordinates full RAG build workflow: files scanning, chunking, embedding, indexing.
|        — Sets retriever and QA chain objects into Streamlit session state when done.

|    |
|    v
|    [build_rag, Line no: 19, core/build_rag.py](https://github.com/anilbattini/codebase-qa/blob/main/core/build_rag.py#L19)
|        — Reads files, applies chunking per language, extracts semantic metadata.
|        — Creates output folders and handles incremental file processing via git/hash tracking.
|        — Initializes embedding model and verifies Ollama endpoint responsiveness.
|        — Processes each source file: chunks files, extracts metadata, deduplicates using chunk fingerprints.
|        — Builds code relationships and hierarchical index files.
|        — Sanitizes chunks and sends batches for embedding via Ollama API.
|        — Persists embeddings in Chroma vector database.
|        — Updates file tracking and logs detailed stats on the process.

|    |
|    v
|    [ProjectConfig.create_directories, Line no: 181, core/config.py](https://github.com/anilbattini/codebase-qa/blob/main/core/config.py#L181)
|        — Ensures all database and logs directories exist for current project type.

|    |
|    v
|    [FileHashTracker.get_changed_files, core/git_hash_tracker.py](https://github.com/anilbattini/codebase-qa/blob/main/core/git_hash_tracker.py)
|        — Obtains list of newly changed or added files for incremental processing.

|    |
|    v
|    [ModelConfig.get_embedding_model, Line no: 63, core/model_config.py](https://github.com/anilbattini/codebase-qa/blob/main/core/model_config.py#L63)
|        — Retrieves the embedding model name to ensure consistency in embedding dimensions.

|    |
|    v
|    [ModelConfig.get_ollama_endpoint, core/model_config.py](https://github.com/anilbattini/codebase-qa/blob/main/core/model_config.py)
|        — Retrieves the Ollama server endpoint URL used for embedding and LLM calls.

|    |
|    v
|    [chunker_factory.get_chunker, core/chunker_factory.py](https://github.com/anilbattini/codebase-qa/blob/main/core/chunker_factory.py)
|        — Selects language-specific chunking strategy function per file extension.

|    |
|    v
|    [chunker_factory.chunker, core/chunker_factory.py](https://github.com/anilbattini/codebase-qa/blob/main/core/chunker_factory.py)
|        — Executes semantic chunking, splitting code into meaningful segments for embedding.

|    |
|    v
|    [MetadataExtractor.create_enhanced_metadata, core/metadata_extractor.py](https://github.com/anilbattini/codebase-qa/blob/main/core/metadata_extractor.py)
|        — Extracts detailed chunk meta class names, function names, dependencies, semantic anchors.

|    |
|    v
|    [chunk_fingerprint, Line no: 13, core/build_rag.py](https://github.com/anilbattini/codebase-qa/blob/main/core/build_rag.py#L13)
|        — Generates SHA-256 hash fingerprints for each chunk to eliminate duplicate embeddings.

|    |
|    v
|    [chunker_factory.summarize_chunk, core/chunker_factory.py](https://github.com/anilbattini/codebase-qa/blob/main/core/chunker_factory.py)
|        — Creates concise summary keywords from chunks for retrieval relevance boosts.

|    |
|    v
|    [build_code_relationship_map, core/build_rag.py](https://github.com/anilbattini/codebase-qa/blob/main/core/build_rag.py)
|        — Constructs mappings of code dependencies to understand file impact and relationships.

|    |
|    v
|    [HierarchicalIndexer.create_hierarchical_index, core/hierarchical_indexer.py](https://github.com/anilbattini/codebase-qa/blob/main/core/hierarchical_indexer.py)
|        — Builds layered hierarchical indexes grouping chunks by modules, files, classes.

|    |
|    v
|    (Sanitize chunks for embedding ingestion)
|        — Cleans chunk contents and metadata ensuring compatibility with vector storage.

|    |
|    v
|    (Embed chunks in batches with OllamaEmbeddings via Ollama API)
|        — Sends semantic chunks in batches to generate embeddings with consistent vector dimensions.

|    |
|    v
|    (Store embedded vectors and metadata in persistent Chroma vector database)
|        — Writes the computed embeddings along with metadata for similarity search on queries.

|    |
|    v
|    (Update git or file hash tracking records)
|        — Records processed files for incremental rebuild detection on next run.

|    |
|    v
|    [RagManager.build_rag_index, Line no: 165, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L165)
|        — Finalizes by setting retriever and QA chain in session state for query answering.

|--- If NO rebuild required (No changes detected)
    |
    v
    [RagManager.load_existing_rag_index, Line no: 194, core/rag_manager.py](https://github.com/anilbattini/codebase-qa/blob/main/core/rag_manager.py#L194)
    — Loads existing embeddings, vector DB, retriever, and QA chain from disk.
    — Uses same embedding model as in build step to avoid dimension mismatches.
    — Ensures session state is ready for query processing.

|
v
RAG system is ready for queries with retriever and QA chain available in Streamlit session state.


```

## 🟩 User Query & Answer Flow

```python
User enters a question in the chat UI input box            [GREEN]
|
v
[UIComponents.render_chat_input, Line no: 161, core/ui_components.py](https://github.com/kumarb/codebase-qa/blob/main/core/ui_components.py#L161)
    — Captures user’s natural language question input.
    — Disables input if RAG system is not fully ready.

|
v
[RagManager.is_ready, Line no: 195, core/rag_manager.py](https://github.com/kumarb/codebase-qa/blob/main/core/rag_manager.py#L195)
    — Checks session state to ensure retriever and QA chain objects are initialized.
    — Prevents query submission if system isn’t ready.

|
v
[QueryIntentClassifier.classify_intent, Line no: 29, core/query_intent_classifier.py](https://github.com/kumarb/codebase-qa/blob/main/core/query_intent_classifier.py#L29)
    — Applies pattern-based matching on user query to classify intent (e.g., overview, validation).
    — Returns intent label and confidence score to inform retrieval strategy.

|
v
[QueryIntentClassifier.get_query_context_hints, Line no: 56, core/query_intent_classifier.py](https://github.com/kumarb/codebase-qa/blob/main/core/query_intent_classifier.py#L56)
    — Optionally extracts relevant keywords or anchors based on classified intent.
    — These hints boost relevant context retrieval.

|
v
[Retriever.get_relevant_documents, core/rag_manager.py]
    — Performs vector similarity search in Chroma vector store.
    — Retrieves top-k most semantically relevant code chunks for user query.

|
v
[ChatHandler & RetrievalQA (combined with LangChain library), core/chat_handler.py](https://github.com/kumarb/codebase-qa/blob/main/core/chat_handler.py)
    — Constructs prompt consisting of user query plus retrieved code chunks with metadata.
    — Sends prompt to Ollama LLM for natural language generation of the answer.

|
v
[build_rag.get_impact, Line no: 379, core/build_rag.py](https://github.com/kumarb/codebase-qa/blob/main/core/build_rag.py#L379)
    — Optionally performs impact analysis tracing file dependencies for related/affected code.
    — Returns list of impacted files to augment response metadata.

|
v
[UIComponents.render_chat_history, Line no: 282, core/ui_components.py](https://github.com/kumarb/codebase-qa/blob/main/core/ui_components.py#L282)
    — Renders generated answer, source chunk attributions, and impact metadata in UI.
    — Supports expansion, chat context, and debug information display.

```

