# Debug Tools for RAG System

This directory contains comprehensive debugging and diagnostic tools for the RAG (Retrieval-Augmented Generation) system.

## 🛠️ Available Tools

### 1. **Vector Database Inspector** (`vector_db_inspector.py`)
- **Database Structure Analysis**: Shows total size, file count, and file types
- **Critical Files Status**: Checks for essential files like `chroma.sqlite3`, `hierarchical_index.json`
- **Retriever Diagnostics**: Analyzes retriever and vector store configuration
- **Hierarchical Index Analysis**: Quality assessment of the index structure
- **Retrieval Health Check**: Tests sample queries to verify system health

### 2. **Chunk Analyzer** (`chunk_analyzer.py`)
- **Chunk Distribution**: Analysis of how chunks are distributed across files
- **Anchor Quality Assessment**: Checks semantic anchor coverage
- **File Coverage Analysis**: Compares indexed vs expected files
- **Retrieval Pattern Analysis**: Tests different query patterns for effectiveness

### 3. **Retrieval Tester** (`retrieval_tester.py`)
- **Interactive Query Testing**: Test custom queries with detailed results
- **Predefined Test Suites**: Ready-made tests for Android, UI, and Architecture patterns
- **Query Comparison**: Side-by-side comparison of different query formulations
- **Relevance Scoring**: Automatic relevance assessment of retrieved documents

### 4. **Main Debug Interface** (`debug_tools.py`)
- **Tabbed Interface**: Organized debug tools in easy-to-navigate tabs
- **Legacy Tools Support**: Backwards compatibility with existing debug functions
- **Configuration Display**: Complete system configuration overview

## 🚀 How to Use

### In Streamlit Application
1. Enable "Debug Mode" in the sidebar
2. Navigate to the debug section at the bottom of the page
3. Use the tabbed interface to access different tools:
   - **🗄️ Vector DB**: Database inspection and health checks
   - **🧩 Chunks**: Chunk quality and anchor analysis
   - **🔍 Retrieval**: Retriever diagnostics
   - **🧪 Testing**: Interactive testing tools
   - **⚙️ Legacy Tools**: Original debug interface

### Command Line Testing
```bash
cd debug_tools
python test_debug_tools.py
```

## 🔧 Process Protection

The debug tools include process protection to prevent UI interference during critical operations:

- **UI Lock**: Debug mode changes are disabled during RAG building
- **Safe State Management**: Maintains safe UI state during processes
- **Build Status Display**: Real-time build progress monitoring
- **Emergency Stop**: Option to safely halt long-running processes

## 📊 Key Features

### Vector Database Diagnostics
- **Size Analysis**: Total database size and file distribution
- **Quality Metrics**: Anchor coverage, file coverage, retrieval health
- **Performance Insights**: Vector count, collection statistics

### Chunk Quality Assessment
- **Semantic Anchors**: Analysis of class names, function names, screen names
- **Content Distribution**: Chunk counts per file type
- **Missing Anchors**: Identification of files with poor semantic structure

### Retrieval Testing
- **Test Suites**: Predefined tests for different project types
- **Custom Queries**: Interactive testing with detailed feedback
- **Comparison Tools**: Side-by-side query analysis
- **Performance Metrics**: Success rates, relevance scores, anchor coverage

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure you're running from the correct directory
   - Check that all dependencies are installed

2. **Database Not Found**
   - Verify the project directory is correctly set
   - Check if RAG index has been built for the current project type

3. **Poor Retrieval Quality**
   - Use the Chunk Analyzer to check anchor quality
   - Run the Retrieval Health Check to identify issues
   - Consider rebuilding the index if many files lack anchors

### Performance Tips

- Use the Vector DB Inspector to check database size and structure
- Monitor chunk distribution to ensure balanced indexing
- Regular retrieval testing helps maintain quality over time

## 📝 Logging

All debug tools log their activities to project-specific log files:
- `vector_db_inspection.log`: Database analysis results
- `chunk_analysis.log`: Chunk quality assessments
- `retrieval_testing.log`: Query test results
- `process_manager.log`: Process state changes

Logs are stored in `codebase-qa_db_{project_type}/logs/` directory.

## 🔄 Integration

The debug tools are fully integrated with the main RAG system:
- **Project Type Aware**: Automatically adapts to Android, Python, iOS, etc.
- **Session State Integration**: Works with Streamlit session management
- **Process Protection**: Prevents interference with RAG building
- **Real-time Updates**: Live monitoring of system state

## 🎯 Best Practices

1. **Regular Health Checks**: Run diagnostics after major changes
2. **Monitor Anchor Quality**: Maintain >80% anchor coverage for best results
3. **Test Retrieval Patterns**: Verify different query types work well
4. **Process Protection**: Always use debug tools safely during builds
5. **Log Analysis**: Review logs to identify recurring issues