"""
Chunk analysis tools for debugging semantic chunking and anchor quality.
"""

import os
import sys
import json
import streamlit as st
from typing import List, Dict, Any

# Add parent directory to path to import from codebase-qa root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import log_highlight, log_to_sublog

def analyze_chunks(project_config, retriever=None):
    """Analyze chunk quality and anchor distribution."""
    log_highlight("ChunkAnalyzer.analyze_chunks")
    
    st.subheader("🧩 Chunk Quality Analysis")
    
    # Load hierarchical index for chunk analysis
    hierarchy_file = project_config.get_hierarchy_file()
    
    if not os.path.exists(hierarchy_file):
        st.warning("⚠️ No hierarchical index found for chunk analysis")
        return
    
    try:
        with open(hierarchy_file, 'r') as f:
            hierarchy = json.load(f)
        
        analyze_chunk_distribution(hierarchy)
        analyze_anchor_quality(hierarchy, project_config)
        analyze_file_coverage(hierarchy, project_config)
        
        if retriever:
            analyze_retrieval_patterns(retriever, project_config)
        
    except Exception as e:
        st.error(f"❌ Error analyzing chunks: {e}")

def analyze_file_chunks(project_config, retriever=None, file_path=None):
    """Analyze chunks for a specific file and return chunk data."""
    log_highlight(f"ChunkAnalyzer.analyze_file_chunks for {file_path}")
    
    if not file_path:
        return []
    
    try:
        # Load hierarchical index
        hierarchy_file = project_config.get_hierarchy_file()
        if not os.path.exists(hierarchy_file):
            return []
        
        with open(hierarchy_file, 'r') as f:
            hierarchy = json.load(f)
        
        # Get file-level data
        file_level = hierarchy.get("file_level", {})
        file_data = file_level.get(file_path, {})
        
        if not file_data:
            return []
        
        # Extract chunk information
        chunks = []
        chunk_data = file_data.get("chunks", [])
        
        for i, chunk_info in enumerate(chunk_data):
            chunk = {
                "content": chunk_info.get("content", ""),
                "metadata": {
                    "source": file_path,
                    "chunk_index": i,
                    "start_line": chunk_info.get("start_line", 0),
                    "end_line": chunk_info.get("end_line", 0),
                    "type": chunk_info.get("type", "unknown"),
                    "anchors": chunk_info.get("anchors", [])
                }
            }
            chunks.append(chunk)
        
        return chunks
        
    except Exception as e:
        log_to_sublog(project_config.project_dir, "debug_tools.log", f"Error analyzing file chunks for {file_path}: {e}")
        return []

def analyze_chunk_distribution(hierarchy):
    """Analyze how chunks are distributed across files."""
    st.write("**📊 Chunk Distribution Analysis**")
    
    file_level = hierarchy.get("file_level", {})
    
    if not file_level:
        st.warning("No file-level data found")
        return
    
    chunk_counts = []
    file_types = {}
    
    for file_path, file_data in file_level.items():
        if isinstance(file_data, dict):
            chunk_count = file_data.get("chunk_count", 0)
            chunk_counts.append(chunk_count)
            
            # Categorize by file type
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in file_types:
                file_types[ext] = {"files": 0, "total_chunks": 0}
            file_types[ext]["files"] += 1
            file_types[ext]["total_chunks"] += chunk_count
    
    if chunk_counts:
        total_chunks = sum(chunk_counts)
        avg_chunks = total_chunks / len(chunk_counts)
        max_chunks = max(chunk_counts)
        min_chunks = min(chunk_counts)
        
        st.metric("Total chunks", total_chunks)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Average per file", f"{avg_chunks:.1f}")
        with col2:
            st.metric("Maximum per file", max_chunks)
        with col3:
            st.metric("Minimum per file", min_chunks)
        
        # Show distribution by file type
        st.write("**Chunks by file type:**")
        for ext, data in sorted(file_types.items(), key=lambda x: x[1]["total_chunks"], reverse=True):
            avg_per_file = data["total_chunks"] / data["files"] if data["files"] > 0 else 0
            st.write(f"  • {ext or '[no extension]'}: {data['total_chunks']} chunks in {data['files']} files (avg: {avg_per_file:.1f})")

def analyze_anchor_quality(hierarchy, project_config):
    """Analyze semantic anchor quality across chunks."""
    st.write("**🔗 Semantic Anchor Quality Analysis**")
    
    file_level = hierarchy.get("file_level", {})
    
    anchor_stats = {
        "files_with_classes": 0,
        "files_with_functions": 0,
        "files_with_screens": 0,
        "files_with_components": 0,
        "files_without_anchors": 0,
        "total_files": 0
    }
    
    problematic_files = []
    
    for file_path, file_data in file_level.items():
        if isinstance(file_data, dict):
            anchor_stats["total_files"] += 1
            
            has_anchor = False
            if file_data.get("class_names"):
                anchor_stats["files_with_classes"] += 1
                has_anchor = True
            if file_data.get("function_names"):
                anchor_stats["files_with_functions"] += 1
                has_anchor = True
            if file_data.get("screen_names"):
                anchor_stats["files_with_screens"] += 1
                has_anchor = True
            if file_data.get("component_names"):
                anchor_stats["files_with_components"] += 1
                has_anchor = True
            
            if not has_anchor:
                anchor_stats["files_without_anchors"] += 1
                problematic_files.append({
                    "file": file_path,
                    "chunks": file_data.get("chunk_count", 0),
                    "type": os.path.splitext(file_path)[1]
                })
    
    total_files = anchor_stats["total_files"]
    if total_files > 0:
        # Display anchor statistics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Files with classes", f"{anchor_stats['files_with_classes']} ({anchor_stats['files_with_classes']/total_files*100:.1f}%)")
            st.metric("Files with functions", f"{anchor_stats['files_with_functions']} ({anchor_stats['files_with_functions']/total_files*100:.1f}%)")
        with col2:
            st.metric("Files with screens", f"{anchor_stats['files_with_screens']} ({anchor_stats['files_with_screens']/total_files*100:.1f}%)")
            st.metric("Files without anchors", f"{anchor_stats['files_without_anchors']} ({anchor_stats['files_without_anchors']/total_files*100:.1f}%)")
        
        # Show problematic files
        if problematic_files:
            st.write("**🚨 Files without semantic anchors:**")
            st.write(f"These {len(problematic_files)} files may have poor retrieval quality:")
            
            for file_info in problematic_files[:10]:  # Show top 10
                st.write(f"  • {file_info['file']} ({file_info['chunks']} chunks, {file_info['type']})")
            
            if len(problematic_files) > 10:
                st.write(f"  ... and {len(problematic_files) - 10} more files")
    
    # Log anchor quality results
    anchor_quality_pct = (total_files - anchor_stats['files_without_anchors']) / total_files * 100 if total_files > 0 else 0
    log_to_sublog(project_config.get_project_dir(), "chunk_analysis.log", 
                  f"Anchor quality: {anchor_quality_pct:.1f}% ({anchor_stats['files_without_anchors']}/{total_files} files without anchors)")

def analyze_file_coverage(hierarchy, project_config):
    """Analyze which files are covered vs missing from the index."""
    st.write("**📁 File Coverage Analysis**")
    
    file_level = hierarchy.get("file_level", {})
    indexed_files = set(file_level.keys())
    
    # Get all project files that should be indexed
    project_dir = project_config.get_project_dir()
    extensions = project_config.get_extensions()
    
    all_project_files = set()
    for root, dirs, files in os.walk(project_dir):
        # Skip the database directories
        dirs[:] = [d for d in dirs if not d.startswith("codebase-qa_db")]
        
        for file in files:
            if file.endswith(extensions):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_dir)
                all_project_files.add(rel_path)
    
    # Convert indexed files to relative paths for comparison
    indexed_rel_files = set()
    for file_path in indexed_files:
        if os.path.isabs(file_path):
            indexed_rel_files.add(os.path.relpath(file_path, project_dir))
        else:
            indexed_rel_files.add(file_path)
    
    # Calculate coverage
    missing_files = all_project_files - indexed_rel_files
    extra_files = indexed_rel_files - all_project_files
    
    total_expected = len(all_project_files)
    total_indexed = len(indexed_rel_files)
    coverage_pct = (total_indexed / total_expected * 100) if total_expected > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Expected files", total_expected)
    with col2:
        st.metric("Indexed files", total_indexed)
    with col3:
        st.metric("Coverage", f"{coverage_pct:.1f}%")
    
    if missing_files:
        st.warning(f"⚠️ {len(missing_files)} files not indexed:")
        for file in sorted(list(missing_files)[:5]):
            st.write(f"  • Missing: {file}")
        if len(missing_files) > 5:
            st.write(f"  ... and {len(missing_files) - 5} more")
    
    if extra_files:
        st.info(f"ℹ️ {len(extra_files)} extra files in index (possibly moved/deleted):")
        for file in sorted(list(extra_files)[:5]):
            st.write(f"  • Extra: {file}")
        if len(extra_files) > 5:
            st.write(f"  ... and {len(extra_files) - 5} more")
    
    if coverage_pct < 90:
        st.error("❌ Low file coverage detected. Consider rebuilding the index.")
    elif coverage_pct < 95:
        st.warning("⚠️ Some files missing from index. Partial rebuild may be needed.")
    else:
        st.success("✅ Good file coverage.")

def analyze_retrieval_patterns(retriever, project_config):
    """Analyze retrieval patterns with sample queries."""
    st.write("**🎯 Retrieval Pattern Analysis**")
    
    # Test different query patterns
    query_patterns = [
        ("MainActivity", "Direct class name"),
        ("button click handler", "Behavioral description"),
        ("navigation between screens", "Process description"),
        ("RecyclerView adapter", "Component + pattern"),
        ("Fragment lifecycle", "Lifecycle concept")
    ]
    
    pattern_results = []
    
    for query, pattern_type in query_patterns:
        try:
            docs = retriever.get_relevant_documents(query, k=3)
            
            result = {
                "query": query,
                "type": pattern_type,
                "retrieved_count": len(docs),
                "has_anchors": False,
                "relevance_score": 0
            }
            
            if docs:
                # Check if top result has anchors
                top_doc = docs[0]
                metadata = top_doc.metadata
                anchors = []
                for anchor_type in ["class_names", "function_names", "screen_name", "component_name"]:
                    if metadata.get(anchor_type):
                        anchors.append(anchor_type)
                
                result["has_anchors"] = len(anchors) > 0
                result["anchor_types"] = anchors
                
                # Simple relevance check (query terms in content)
                query_terms = query.lower().split()
                content = top_doc.page_content.lower()
                matching_terms = sum(1 for term in query_terms if term in content)
                result["relevance_score"] = matching_terms / len(query_terms)
            
            pattern_results.append(result)
            
        except Exception as e:
            st.error(f"Error testing '{query}': {e}")
    
    # Display results
    if pattern_results:
        st.write("**Query pattern performance:**")
        
        for result in pattern_results:
            with st.expander(f"🔍 {result['query']} ({result['type']})"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Documents", result['retrieved_count'])
                with col2:
                    st.metric("Has anchors", "✅" if result['has_anchors'] else "❌")
                with col3:
                    st.metric("Relevance", f"{result['relevance_score']:.0%}")
                
                if result.get('anchor_types'):
                    st.write(f"Anchor types: {', '.join(result['anchor_types'])}")
        
        # Summary
        avg_retrieval = sum(r['retrieved_count'] for r in pattern_results) / len(pattern_results)
        anchor_rate = sum(1 for r in pattern_results if r['has_anchors']) / len(pattern_results)
        avg_relevance = sum(r['relevance_score'] for r in pattern_results) / len(pattern_results)
        
        st.write("**Overall retrieval performance:**")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Avg documents retrieved", f"{avg_retrieval:.1f}")
        with col2:
            st.metric("Queries with anchors", f"{anchor_rate:.0%}")
        with col3:
            st.metric("Avg relevance score", f"{avg_relevance:.0%}")
        
        if anchor_rate < 0.7:
            st.warning("⚠️ Low anchor coverage in retrieval results")
        if avg_relevance < 0.5:
            st.warning("⚠️ Low relevance scores detected")
    
    log_to_sublog(project_config.get_project_dir(), "retrieval_patterns.log", 
                  f"Retrieval pattern analysis completed for {len(query_patterns)} patterns")

# --------------- CODE CHANGE SUMMARY ---------------
# ADDED
# - analyze_file_chunks(): New function for analyzing chunks of a specific file.
# - Returns structured chunk data with content and metadata for UI display.
# - Proper error handling and logging for file-specific chunk analysis.
# - Integration with hierarchical index for detailed chunk information.