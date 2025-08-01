"""
Vector database inspection tools for debugging RAG retrieval issues.
"""

import os
import sys
import json
import streamlit as st
from typing import List, Dict, Any

# Add parent directory to path to import from codebase-qa root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import log_highlight, log_to_sublog

def inspect_vector_db(project_config, retriever=None):
    """Comprehensive vector database inspection."""
    log_highlight("VectorDBInspector.inspect_vector_db")
    
    st.subheader("🗄️ Vector Database Inspector")
    
    db_dir = project_config.get_db_dir()
    
    if not os.path.exists(db_dir):
        st.error(f"❌ Database directory not found: {db_dir}")
        return
    
    # Database structure analysis
    st.write("**Database Structure:**")
    db_files = []
    total_size = 0
    
    for root, dirs, files in os.walk(db_dir):
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            total_size += file_size
            db_files.append({
                "path": os.path.relpath(file_path, db_dir),
                "size_mb": file_size / (1024 * 1024),
                "type": get_file_type(file)
            })
    
    st.write(f"Total database size: {total_size / (1024 * 1024):.2f} MB")
    st.write(f"Total files: {len(db_files)}")
    
    # Group files by type
    file_types = {}
    for file_info in db_files:
        file_type = file_info["type"]
        if file_type not in file_types:
            file_types[file_type] = {"count": 0, "size_mb": 0}
        file_types[file_type]["count"] += 1
        file_types[file_type]["size_mb"] += file_info["size_mb"]
    
    st.write("**Files by type:**")
    for file_type, info in file_types.items():
        st.write(f"  • {file_type}: {info['count']} files ({info['size_mb']:.2f} MB)")
    
    # Check critical files
    critical_files = {
        "chroma.sqlite3": "Vector embeddings database",
        "hierarchical_index.json": "Hierarchical index for enhanced retrieval",
        "code_relationships.json": "Code relationship mapping",
        "file_hashes.json": "File change tracking",
        "last_commit.json": "Git commit tracking"
    }
    
    st.write("**Critical files status:**")
    for file_name, description in critical_files.items():
        file_path = os.path.join(db_dir, file_name)
        if os.path.exists(file_path):
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            st.success(f"✅ {file_name}: {size_mb:.2f} MB - {description}")
        else:
            st.warning(f"⚠️ {file_name}: Missing - {description}")
    
    # Retriever diagnostics
    if retriever:
        st.write("**Retriever Diagnostics:**")
        retriever_type = type(retriever).__name__
        st.info(f"Retriever type: {retriever_type}")
        
        if hasattr(retriever, 'vectorstore'):
            vectorstore = retriever.vectorstore
            vectorstore_type = type(vectorstore).__name__
            st.info(f"Vector store type: {vectorstore_type}")
            
            # Try to get collection info
            try:
                if hasattr(vectorstore, '_collection'):
                    collection = vectorstore._collection
                    if hasattr(collection, 'count'):
                        count = collection.count()
                        st.info(f"Total vectors in collection: {count}")
                elif hasattr(vectorstore, 'index'):
                    # FAISS-style
                    if hasattr(vectorstore.index, 'ntotal'):
                        st.info(f"Total vectors in index: {vectorstore.index.ntotal}")
            except Exception as e:
                st.warning(f"Could not get vector count: {e}")
    
    # Log inspection results
    log_to_sublog(project_config.get_project_dir(), "vector_db_inspection.log", 
                  f"Vector DB inspection completed. Size: {total_size / (1024 * 1024):.2f} MB, Files: {len(db_files)}")

def get_file_type(filename):
    """Determine file type for categorization."""
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == '.sqlite3' or 'chroma' in filename:
        return "Vector Database"
    elif ext == '.json':
        return "JSON Metadata"
    elif ext == '.log':
        return "Log File"
    elif ext in ['.pkl', '.pickle']:
        return "Pickled Data"
    else:
        return "Other"

def analyze_hierarchical_index(project_config):
    """Analyze the hierarchical index for quality issues."""
    st.subheader("📊 Hierarchical Index Analysis")
    
    hierarchy_file = project_config.get_hierarchy_file()
    
    if not os.path.exists(hierarchy_file):
        st.warning("⚠️ No hierarchical index found. Rebuild recommended.")
        return
    
    try:
        with open(hierarchy_file, 'r') as f:
            hierarchy = json.load(f)
        
        # Analyze different levels
        levels = ["file_level", "component_level", "business_level", "ui_level", "dependency_level", "api_level"]
        
        st.write("**Index levels analysis:**")
        for level in levels:
            if level in hierarchy:
                level_data = hierarchy[level]
                if isinstance(level_data, dict):
                    count = len(level_data)
                    st.success(f"✅ {level}: {count} entries")
                else:
                    st.info(f"ℹ️ {level}: Non-dict structure")
            else:
                st.warning(f"⚠️ {level}: Missing")
        
        # Check for quality issues
        file_level = hierarchy.get("file_level", {})
        missing_anchors = 0
        total_files = len(file_level)
        
        for file_path, file_data in file_level.items():
            if isinstance(file_data, dict):
                chunk_count = file_data.get("chunk_count", 0)
                if chunk_count == 0:
                    missing_anchors += 1
        
        if total_files > 0:
            anchor_quality = ((total_files - missing_anchors) / total_files) * 100
            if anchor_quality > 80:
                st.success(f"✅ Anchor quality: {anchor_quality:.1f}% ({total_files - missing_anchors}/{total_files} files have anchors)")
            elif anchor_quality > 60:
                st.warning(f"⚠️ Anchor quality: {anchor_quality:.1f}% ({total_files - missing_anchors}/{total_files} files have anchors)")
            else:
                st.error(f"❌ Poor anchor quality: {anchor_quality:.1f}% ({total_files - missing_anchors}/{total_files} files have anchors)")
        
    except Exception as e:
        st.error(f"❌ Error analyzing hierarchical index: {e}")

def check_retrieval_health(project_config, retriever):
    """Check retrieval system health."""
    st.subheader("🩺 Retrieval Health Check")
    
    if not retriever:
        st.error("❌ No retriever available for health check")
        return
    
    # Test queries for different types
    test_queries = [
        ("class MainActivity", "Class-based query"),
        ("button click", "UI interaction query"),
        ("navigation", "Navigation query"),
        ("Fragment", "Component query")
    ]
    
    st.write("**Testing retrieval with sample queries:**")
    
    for query, description in test_queries:
        try:
            with st.expander(f"🔍 {description}: '{query}'"):
                docs = retriever.get_relevant_documents(query)
                
                if docs:
                    st.success(f"✅ Retrieved {len(docs)} documents")
                    
                    # Show top result details
                    top_doc = docs[0]
                    st.write("**Top result:**")
                    st.write(f"Source: {top_doc.metadata.get('source', 'Unknown')}")
                    st.write(f"Content preview: {top_doc.page_content[:200]}...")
                    
                    # Check for anchor quality
                    metadata = top_doc.metadata
                    anchors = []
                    for anchor_type in ["class_names", "function_names", "screen_name", "component_name"]:
                        if metadata.get(anchor_type):
                            anchors.append(anchor_type)
                    
                    if anchors:
                        st.info(f"Anchors present: {', '.join(anchors)}")
                    else:
                        st.warning("⚠️ No semantic anchors found in top result")
                else:
                    st.warning(f"⚠️ No documents retrieved for '{query}'")
                    
        except Exception as e:
            st.error(f"❌ Error testing '{query}': {e}")
    
    log_to_sublog(project_config.get_project_dir(), "retrieval_health.log", 
                  f"Retrieval health check completed for {len(test_queries)} test queries")