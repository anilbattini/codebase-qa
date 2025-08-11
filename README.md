# Codebase QA: Chat with Your Codebase

![Streamlit App](https://img.shields.io/badge/Streamlit-App-blue) ![License](https://img.shields.io/badge/License-MIT-green) ![Python](https://img.shields.io/badge/Python-3.8%2B-yellow) ![Local LLM](https://img.shields.io/badge/Local%20LLM-Ollama-orange)

## Overview

Codebase QA is an interactive Streamlit-based tool that allows you to chat with your project's codebase using Retrieval-Augmented Generation (RAG) powered by local large language models (LLMs) like those from Ollama. It analyzes your project files, builds a vector database for semantic search, and enables natural language queries about your code—such as understanding business logic, impact analysis, UI flows, or technical details.

The tool supports various project types (e.g., Android, iOS, Python, JavaScript/TypeScript) and intelligently chunks code with meaningful metadata for better context retrieval. It uses Chroma as the vector database and focuses on incremental updates, semantic awareness, and efficient querying.

This architecture reduces custom code by leveraging established libraries, making it maintainable and performant. It evolved from a more complex 15-file system to a streamlined setup with 2-3 core files, while providing advanced features like hierarchical indexing and query intent classification.

A preview shown with android project chosen:
<img width="1906" height="850" alt="Screenshot 2025-07-31 at 2 16 13 PM" src="https://github.com/user-attachments/assets/c9341a02-7e9d-4b13-aaf6-ccfe1c7c4c58" />

## Key Features

- **Project Type Detection**: Automatically detects or lets you select project types (e.g., Android, Python, JavaScript) and processes relevant file extensions.
- **RAG Index Building**: Scans project directories, chunks code semantically (e.g., by classes, functions, imports), adds rich metadata (dependencies, complexity scores, UI elements), and stores in a Chroma vector database.
- **Local LLM Integration**: Uses Ollama for embeddings and query processing, keeping everything local and private.
- **Chat Interface**: Ask questions about your codebase with context-aware responses, including source attribution, impact analysis, and debug tools.
- **Incremental Updates**: Tracks file changes via Git (if available) or custom hashing, reindexing only modified files for efficiency.
- **Advanced Retrieval**: Supports query intent classification (e.g., overview, business logic, UI flow), hierarchical indexing, and relevance scoring.
- **Comprehensive Debug Tools**: Inspect vector DB, test chunking/embeddings/retrieval, view project structure, and force rebuilds with detailed logging.
- **Metadata-Rich Chunks**: Extracts dependencies, API endpoints, business logic indicators, validations, and more for precise context building.
- **Robust Testing Suite**: Complete end-to-end testing including UI functionality, rebuild index, and debug tools validation.

## Benefits of the New Architecture

- **80% Less Custom Code**: Leverages libraries like LangChain, Chroma, and Ollama for core RAG operations.
- **Language-Aware Chunking**: Automatic splitting with semantic awareness (e.g., functions, classes, imports) and overlap for better context.
- **Metadata Extraction**: Captures imports, functions, classes, dependencies, UI elements, and complexity metrics.
- **Context-Aware Chat**: Intent classification, query rewriting, impact analysis, and reranked sources for relevant answers.
- **Incremental Indexing**: Only processes changed files using Git integration or fallback hashing.
- **Semantic Search**: Relevance scoring and hierarchical indexes for multi-level querying.
- **Source Attribution**: Tracks and displays exact sources in responses.
- **Robust Error Handling**: Graceful management of processing errors with comprehensive logging.
- **Optimized Performance**: Efficient vector operations and token management.
- **Easy Maintenance**: Built on actively maintained open-source libraries.
- **Comprehensive Testing**: Full test suite covering core functionality and UI features.

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
    streamlit run core/app.py
    ```

2. **Configure in the Sidebar**:
- Select your project directory.
- Choose the project type (e.g., Python, JavaScript).
- Pick a local Ollama model and endpoint.
- Toggle force rebuild or debug mode if needed.

3. **Build the Index**:
- Index gets built automatically when you choose the project type.
- For example, if your project type is `android` then all the generated files will be stored under `./codebase-qa_android/`
- Click "Rebuild Index" to rebuild the whole RAG deleting all the existing files and logs.
- The app logs progress, showing processed files, chunks, and stats.

4. **Chat with Your Codebase**:
- Once ready, enter queries like:
  - "What is the main business logic in this app?"
  - "What happens if I change file X?"
  - "Explain the UI flow for the X screen."
- Responses include generated answers, source documents, and impact analysis.

5. **Debug Mode**:
- Enable to access tools for inspecting the vector DB, testing chunking, embeddings, retrieval, and more.
- See [Debug Tools Documentation](debug_tools/README.md) for detailed usage.

## Testing

### Quick Test
Run the comprehensive test suite to verify all functionality:
```bash
cd debug_tools/ai_debug_tools
python developer_test_suite.py
```

### Individual Tests
- **Core Integration**: `python test_core_integration.py`
- **Quality Tests**: `python quality_test_suite.py`
- **Embedding Tests**: `python embedding_dimension_test.py`

### Test Coverage
The test suite covers:
- ✅ Project setup and validation
- ✅ Embedding model compatibility
- ✅ RAG index building
- ✅ Query processing and answer quality
- ✅ UI functionality (rebuild index, debug tools, chat)
- ✅ Comprehensive logging and reporting

## Project Structure

```text
codebase-qa/
├── core/                         # Core RAG functionality
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
├── requirements.txt              # Dependencies
└── README.md                     # This file

```

Generated files include:
- `code_relationships.json`: Dependency mappings.
- `git_tracking.json`: File change tracking info.
- `logs/`: Comprehensive logging for debugging.

## How It Works

1. **Input Selection**: 
    - User picks project directory, type, and LLM model.

2. **Index Building**:
   - Scans files based on extensions (e.g., `.py` for Python).
   - Chunks content semantically with overlaps and metadata (e.g., dependencies, complexity).
   - Builds hierarchical indexes and stores in Chroma.
   - Uses consistent embedding models (nomic-embed-text:latest) for dimension compatibility.

3. **Query Processing**:
   - Classifies intent (e.g., overview, impact analysis).
   - Rewrites query, retrieves relevant chunks, builds enhanced context.
   - Passes to local LLM for response generation.

4. **Output**: Displays answer with sources, impacted files, and debug info.

## Debug Tools

The debug tools provide comprehensive inspection and testing capabilities:

- **Chunk Analyzer**: Analyze chunk quality and distribution
- **Retrieval Tester**: Test retrieval quality and performance
- **Database Inspector**: Inspect vector database statistics
- **Query Runner**: Execute predefined debug queries
- **Vector DB Inspector**: Analyze Chroma database structure

For detailed debug tools usage, see [Debug Tools Documentation](debug_tools/README.md).

## Troubleshooting

### Common Issues

1. **Embedding Dimension Mismatch**: Ensure using same embedding model for building and loading
2. **Session State Issues**: Check if RAG system is properly initialized
3. **File Processing Errors**: Verify project directory and file permissions

### Debug Mode
Enable debug mode in the sidebar to access:
- Vector database inspection
- Chunk analysis tools
- Retrieval testing
- Build status monitoring
- Real-time logs

## Contributing

Contributions are welcome! Please submit pull requests for bug fixes, features, or improvements. Follow standard Python best practices.

### Development Guidelines
- Use existing core methods from session state
- Add comprehensive logging to all operations
- Test thoroughly using the provided test suites
- Follow the consolidated testing approach

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments

- Built with Streamlit for the UI.
- Powered by LangChain for RAG and Ollama for local LLMs.
- Uses Chroma for vector storage.
- Comprehensive testing and debugging tools included.

---

> _Note: The system includes comprehensive testing and debugging tools. For detailed testing instructions, see the debug_tools documentation._


