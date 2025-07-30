# debug_tools.py

import streamlit as st
import os
import shutil
import numpy as np
from typing import Optional
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from config import ProjectConfig

class DebugTools:
    """Comprehensive debugging tools for the RAG system."""

    def __init__(self, project_config: ProjectConfig, ollama_model: str, ollama_endpoint: str, project_dir: str):
        self.project_config = project_config
        self.ollama_model = ollama_model
        self.ollama_endpoint = ollama_endpoint
        self.project_dir = project_dir
        self.vector_db_dir = "./vector_db"

    def render_debug_interface(self, retriever=None):
        """Render all debug tools in the Streamlit interface."""

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔍 Inspect Vector DB"):
                self.inspect_vector_db()

            if st.button("🧪 Test Chunking"):
                self.test_chunking()

            if st.button("📁 Show Project Structure"):
                self.show_project_structure()

        with col2:
            if st.button("🧮 Test Embeddings"):
                self.test_embeddings()

            if st.button("🎯 Test Retrieval"):
                self.test_retrieval(retriever)

            if st.button("🔄 Force Clean Rebuild"):
                self.force_clean_rebuild()

    def inspect_vector_db(self):
        """Inspect the contents of the vector database."""
        try:
            embeddings = OllamaEmbeddings(model=self.ollama_model, base_url=self.ollama_endpoint)
            vectorstore = Chroma(persist_directory=self.vector_db_dir, embedding_function=embeddings)

            all_docs = vectorstore.get()
            st.write(f"**Total chunks in vector DB:** {len(all_docs['ids'])}")

            # Group by file type and source
            file_types = {}
            source_files = {}

            for metadata in all_docs['metadatas']:
                source = metadata.get('source', 'Unknown')
                ext = source.split('.')[-1] if '.' in source else 'no_ext'

                file_types[ext] = file_types.get(ext, 0) + 1
                source_files[source] = source_files.get(source, 0) + 1

            # Display file type statistics
            st.write("**File types indexed:**")
            for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
                st.write(f"- `.{ext}`: {count} chunks")

            # Display top source files
            st.write("**Top source files by chunk count:**")
            top_files = sorted(source_files.items(), key=lambda x: x[1], reverse=True)[:15]
            for source, count in top_files:
                st.write(f"- `{source}`: {count} chunks")

            # Test project-specific queries
            self._test_vector_queries(vectorstore)

        except Exception as e:
            st.error(f"Error inspecting vector DB: {e}")

    def _test_vector_queries(self, vectorstore):
        """Test vector search with project-specific queries."""
        st.write("**Testing project-specific queries:**")

        # Generate test queries based on project type
        base_queries = [
            f"{self.project_config.project_type} project",
            "main application file",
            "what does this app do"
        ]

        # Add project-specific queries
        priority_files = self.project_config.get_priority_files()
        if priority_files:
            base_queries.extend([f"{pf} file" for pf in priority_files[:2]])

        for test_query in base_queries:
            docs = vectorstore.similarity_search(test_query, k=5)
            st.write(f"\n**Query: '{test_query}'**")
            for j, doc in enumerate(docs):
                source = doc.metadata.get('source', 'Unknown')
                chunk_type = doc.metadata.get('type', 'unknown')
                st.write(f"  {j+1}. `{source}` [{chunk_type}] - {doc.page_content[:100]}...")

    def test_chunking(self):
        """Test chunking functionality on project files."""
        try:
            from chunker_factory import get_chunker

            # Find a sample file to test
            extensions = self.project_config.get_extensions()
            priority_files = self.project_config.get_priority_files()

            sample_file = None
            for root, dirs, files in os.walk(self.project_dir):
                for file in files:
                    if any(file.lower().startswith(pf) for pf in priority_files) and any(file.endswith(ext) for ext in extensions):
                        sample_file = os.path.join(root, file)
                        break
                if sample_file:
                    break

            if not sample_file:
                # Fallback to any file with correct extension
                for root, dirs, files in os.walk(self.project_dir):
                    for file in files:
                        if any(file.endswith(ext) for ext in extensions):
                            sample_file = os.path.join(root, file)
                            break
                    if sample_file:
                        break

            if sample_file:
                with open(sample_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                st.write(f"**Testing file:** `{sample_file}`")
                st.write(f"**File content preview:**")
                st.code(content[:500] + "..." if len(content) > 500 else content)

                ext = os.path.splitext(sample_file)[1]
                chunker = get_chunker(ext, self.project_config)
                chunks = chunker(content)

                st.write(f"**Chunking result:** {len(chunks)} chunks")
                for i, chunk in enumerate(chunks[:3]):
                    if isinstance(chunk, dict):
                        st.write(f"**Chunk {i+1}:**")
                        st.write(f"- Type: {chunk.get('type', 'unknown')}")
                        st.write(f"- Name: {chunk.get('name', 'unknown')}")
                        chunk_content = chunk.get('content', '')
                        st.code(chunk_content[:300] + "..." if len(chunk_content) > 300 else chunk_content)
                    else:
                        st.write(f"**Chunk {i+1}:** {str(chunk)[:200]}...")
            else:
                st.error(f"No sample files found with extensions: {extensions}")

        except Exception as e:
            st.error(f"Chunking test failed: {e}")
            st.exception(e)

    def test_embeddings(self):
        """Test embedding functionality."""
        try:
            embeddings = OllamaEmbeddings(model=self.ollama_model, base_url=self.ollama_endpoint)

            # Create project-specific test texts
            summary_keywords = self.project_config.get_summary_keywords()
            test_texts = [
                f"{self.project_config.project_type} application code",
                f"main {summary_keywords[0] if summary_keywords else 'application'} component",
                "configuration file content",
                f"what does this {self.project_config.project_type} project do"
            ]

            embedded = embeddings.embed_documents(test_texts)
            query_embed = embeddings.embed_query(f"what does this {self.project_config.project_type} project do")

            st.write("**Embedding test successful**")
            st.write(f"Embedded {len(test_texts)} texts, query embedding dimension: {len(query_embed)}")

            # Calculate similarities
            similarities = []
            for i, doc_embed in enumerate(embedded):
                similarity = np.dot(query_embed, doc_embed) / (np.linalg.norm(query_embed) * np.linalg.norm(doc_embed))
                similarities.append((test_texts[i], similarity))

            st.write(f"**Similarities to 'what does this {self.project_config.project_type} project do':**")
            for text, sim in sorted(similarities, key=lambda x: x[1], reverse=True):
                st.write(f"- {sim:.3f}: {text}")

        except Exception as e:
            st.error(f"Embedding test failed: {e}")
            st.exception(e)

    def test_retrieval(self, retriever):
        """Test direct retrieval functionality."""
        if not retriever:
            st.error("No retriever available. Please build the RAG index first.")
            return

        # Generate project-specific test queries
        priority_files = self.project_config.get_priority_files()
        test_queries = [
            f"{self.project_config.project_type} app",
            f"what does this {self.project_config.project_type} project do",
            "main application logic"
        ]

        if priority_files:
            test_queries.append(f"{priority_files[0]} file")

        for test_query in test_queries:
            st.write(f"\n**Testing query: '{test_query}'**")
            test_docs = retriever.get_relevant_documents(test_query)
            st.write(f"Retrieved {len(test_docs)} documents:")
            for i, doc in enumerate(test_docs[:5]):
                source = doc.metadata.get('source', 'Unknown')
                chunk_type = doc.metadata.get('type', 'unknown')
                st.write(f"  {i+1}. `{source}` [{chunk_type}]")
                st.code(doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content)

    def show_project_structure(self):
        """Display project file structure."""
        st.write("**Project file structure:**")

        extensions = self.project_config.get_extensions()
        file_count = {}

        for root, dirs, files in os.walk(self.project_dir):
            # Skip hidden and build directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['build', '__pycache__', 'node_modules', 'dist']]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in extensions:
                    rel_path = os.path.relpath(os.path.join(root, file), self.project_dir)
                    file_count[ext] = file_count.get(ext, 0) + 1
                    if file_count[ext] <= 10:  # Show first 10 files of each type
                        st.write(f"- `{rel_path}`")

        st.write(f"\n**File count by extension:**")
        for ext, count in sorted(file_count.items()):
            st.write(f"- `{ext}`: {count} files")

        st.write(f"\n**Project type detected:** {self.project_config.project_type}")
        st.write(f"**Priority files:** {', '.join(self.project_config.get_priority_files())}")

    def force_clean_rebuild(self):
        """Force a complete rebuild of the vector database."""
        try:
            if os.path.exists(self.vector_db_dir):
                shutil.rmtree(self.vector_db_dir)
                st.success("✅ Deleted existing vector DB")

            # Clear session state
            for key in ['retriever', 'qa_chain', 'project_dir_used']:
                if key in st.session_state:
                    del st.session_state[key]

            st.info("🔄 Cleared session state. Click 'Rebuild Index' to create fresh vector DB")

        except Exception as e:
            st.error(f"Error during clean rebuild: {e}")
