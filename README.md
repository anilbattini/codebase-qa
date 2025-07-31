# Codebase QA: Chat with Your Codebase

![Streamlit App](https://img.shields.io/badge/Streamlit-App-blue) ![License](https://img.shields.io/badge/License-MIT-green) ![Python](https://img.shields.io/badge/Python-3.8%2B-yellow) ![Local LLM](https://img.shields.io/badge/Local%20LLM-Ollama-orange)

## Overview

Codebase QA is an interactive Streamlit-based tool that allows you to chat with your project's codebase using Retrieval-Augmented Generation (RAG) powered by local large language models (LLMs) like those from Ollama. It analyzes your project files, builds a vector database for semantic search, and enables natural language queries about your code—such as understanding business logic, impact analysis, UI flows, or technical details.

The tool supports various project types (e.g., Android, iOS, Python, JavaScript/TypeScript) and intelligently chunks code with meaningful metadata for better context retrieval. It uses Chroma as the vector database and focuses on incremental updates, semantic awareness, and efficient querying.

This architecture reduces custom code by leveraging established libraries, making it maintainable and performant. It evolved from a more complex 15-file system to a streamlined setup with 2-3 core files, while providing advanced features like hierarchical indexing and query intent classification.

A preview shown with android project chosen:
<img width="1906" height="850" alt="Screenshot 2025-07-31 at 2 16 13 PM" src="https://github.com/user-attachments/assets/c9341a02-7e9d-4b13-aaf6-ccfe1c7c4c58" />

## Key Features

- **Project Type Detection**: Automatically detects or lets you select project types (e.g., Android, Python, JavaScript) and processes relevant file extensions.
- **RAG Index Building**: Scans project directories, chunks code semantically (e.g., by classes, functions, imports), adds rich metadata (dependencies, complexity scores, UI elements), and stores in a Chroma vector database.
- **Local LLM Integration**: Uses Ollama for embeddings and query processing, keeping everything local and private.
- **Chat Interface**: Ask questions about your codebase with context-aware responses, including source attribution, impact analysis, and debug tools.
- **Incremental Updates**: Tracks file changes via Git (if available) or custom hashing, reindexing only modified files for efficiency.
- **Advanced Retrieval**: Supports query intent classification (e.g., overview, business logic, UI flow), hierarchical indexing, and relevance scoring.
- **Debugging Tools**: Inspect vector DB, test chunking/embeddings/retrieval, view project structure, and force rebuilds.
- **Metadata-Rich Chunks**: Extracts dependencies, API endpoints, business logic indicators, validations, and more for precise context building.

## Benefits of the New Architecture

- **80% Less Custom Code**: Leverages libraries like LangChain, Chroma, and Ollama for core RAG operations.
- **Language-Aware Chunking**: Automatic splitting with semantic awareness (e.g., functions, classes, imports) and overlap for better context.
- **Metadata Extraction**: Captures imports, functions, classes, dependencies, UI elements, and complexity metrics.
- **Context-Aware Chat**: Intent classification, query rewriting, impact analysis, and reranked sources for relevant answers.
- **Incremental Indexing**: Only processes changed files using Git integration or fallback hashing.
- **Semantic Search**: Relevance scoring and hierarchical indexes for multi-level querying.
- **Source Attribution**: Tracks and displays exact sources in responses.
- **Robust Error Handling**: Graceful management of processing errors.
- **Optimized Performance**: Efficient vector operations and token management.
- **Easy Maintenance**: Built on actively maintained open-source libraries.

## Installation

1. **Prerequisites**:
   - Python 3.8 or higher.
   - Ollama installed and running locally (download from ollama.ai).
   - Git (optional, for advanced file tracking).

2. **Clone the Repository**:
    ```bash 
    git clone https://github.com/your-repo/codebase-qa.git
    cd codebase-qa
    ```


3. **Install Dependencies**:
    ```bash 
    pip install -r requirements.txt
    ```

4. **Run Ollama**:
Start Ollama and pull a model (e.g., `ollama pull llama3`).

## Usage

1. **Launch the App**:
    ```bash 
    streamlit run app.py
    ```

2. **Configure in the Sidebar**:
- Select your project directory.
- Choose the project type (e.g., Python, JavaScript).
- Pick a local Ollama model and endpoint.
- Toggle force rebuild or debug mode if needed.

3. **Build the Index**:
- Click "Rebuild Index" to process files and create the vector database (stored in `./vector_db/`).
- The app logs progress, showing processed files, chunks, and stats.

4. **Chat with Your Codebase**:
- Once ready, enter queries like:
  - "What is the main business logic in this app?"
  - "What happens if I change file X?"
  - "Explain the UI flow for the login screen."
- Responses include generated answers, source documents, and impact analysis.

5. **Debug Mode**:
- Enable to access tools for inspecting the vector DB, testing chunking, embeddings, retrieval, and more.

## Project Structure

```text
codebase-qa/
├── app.py                      # Main Streamlit app orchestrator
├── ui_components.py            # UI rendering components
├── chat_handler.py             # Chat processing with intent classification
├── rag_manager.py              # RAG setup and management
├── build_rag.py                # RAG building, indexing, and dependency extraction
├── chunker_factory.py          # Semantic-aware chunking
├── config.py                   # Project configurations and auto-detection
├── git_hash_tracker.py         # File change tracking (Git or custom)
├── debug_tools.py              # Debugging utilities
├── metadata_extractor.py       # Enhanced metadata extraction
├── query_classifier.py         # Query intent classification
├── context_builder.py          # Advanced context building for queries
├── hierarchical_indexer.py     # Multi-level hierarchical indexing
└── vector_db/                  # Generated vector database (Chroma)
```



Generated files include:
- `code_relationships.json`: Dependency mappings.
- `git_tracking.json`: File change tracking info.

## How It Works

1. **Input Selection**: 
    - User picks project directory, type, and LLM model.

2. **Index Building**:
   - Scans files based on extensions (e.g., `.py` for Python).
   - Chunks content semantically with overlaps and metadata (e.g., dependencies, complexity).
   - Builds hierarchical indexes and stores in Chroma.
3. **Query Processing**:
   - Classifies intent (e.g., overview, impact analysis).
   - Rewrites query, retrieves relevant chunks, builds enhanced context.
   - Passes to local LLM for response generation.
4. **Output**: Displays answer with sources, impacted files, and debug info.

## Contributing

Contributions are welcome! Please submit pull requests for bug fixes, features, or improvements. Follow standard Python best practices.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments

- Built with Streamlit for the UI.
- Powered by LangChain for RAG and Ollama for local LLMs.
- Uses Chroma for vector storage.

