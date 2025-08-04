"""
Interactive retrieval testing tools for debugging search quality.
"""

import os
import sys
import streamlit as st
from typing import List, Dict, Any

# Add parent directory to path to import from codebase-qa root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import log_highlight, log_to_sublog

def test_retrieval(project_config, retriever, qa_chain=None):
    """Interactive retrieval testing interface."""
    log_highlight("RetrievalTester.test_retrieval")
    
    st.subheader("🧪 Interactive Retrieval Tester")
    
    if not retriever:
        st.error("❌ No retriever available for testing")
        return
    
    # Custom query testing
    st.write("**Custom Query Testing**")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        test_query = st.text_input("Enter test query:", placeholder="e.g., MainActivity onCreate method")
    with col2:
        k_docs = st.number_input("Documents to retrieve:", min_value=1, max_value=20, value=5)
    
    if test_query and st.button("🔍 Test Retrieval"):
        test_single_query(test_query, retriever, k_docs, project_config, qa_chain)
    
    # Predefined test suites
    st.write("**Predefined Test Suites**")
    
    test_suites = {
        "Android Basics": [
            "MainActivity class",
            "onCreate method",
            "Fragment navigation",
            "Button click listener",
            "RecyclerView setup"
        ],
        "UI Components": [
            "layout files",
            "drawable resources",
            "string values",
            "theme configuration",
            "menu items"
        ],
        "Architecture": [
            "ViewModel pattern",
            "Repository pattern",
            "dependency injection",
            "data binding",
            "lifecycle methods"
        ]
    }
    
    selected_suite = st.selectbox("Select test suite:", list(test_suites.keys()))
    
    if st.button(f"🚀 Run {selected_suite} Test Suite"):
        run_test_suite(test_suites[selected_suite], retriever, project_config, qa_chain)
    
    # Comparison testing
    st.write("**Query Comparison Testing**")
    
    col1, col2 = st.columns(2)
    with col1:
        query1 = st.text_input("Query 1:", placeholder="MainActivity")
    with col2:
        query2 = st.text_input("Query 2:", placeholder="main activity class")
    
    if query1 and query2 and st.button("⚖️ Compare Queries"):
        compare_queries(query1, query2, retriever, project_config)

def test_single_query(query: str, retriever, k: int, project_config, qa_chain=None):
    """Test a single query and display detailed results."""
    st.write(f"**Testing query: '{query}'**")
    
    try:
        # Retrieve documents
        docs = retriever.get_relevant_documents(query, k=k)
        
        if not docs:
            st.error("❌ No documents retrieved")
            return
        
        st.success(f"✅ Retrieved {len(docs)} documents")
        
        # Display results
        for i, doc in enumerate(docs, 1):
            with st.expander(f"📄 Result {i}: {doc.metadata.get('source', 'Unknown source')}"):
                # Metadata analysis
                metadata = doc.metadata
                st.write("**Metadata:**")
                
                # Show important metadata fields
                important_fields = [
                    ("source", "Source file"),
                    ("chunk_index", "Chunk index"),
                    ("class_names", "Classes"),
                    ("function_names", "Functions"),
                    ("screen_name", "Screen"),
                    ("component_name", "Component"),
                    ("file_type", "File type")
                ]
                
                for field, label in important_fields:
                    value = metadata.get(field)
                    if value:
                        if isinstance(value, list):
                            st.write(f"  • {label}: {', '.join(value)}")
                        else:
                            st.write(f"  • {label}: {value}")
                
                # Content analysis
                content = doc.page_content
                st.write("**Content:**")
                st.code(content[:500] + ("..." if len(content) > 500 else ""), language="text")
                
                # Query relevance analysis
                query_terms = query.lower().split()
                content_lower = content.lower()
                
                matching_terms = []
                for term in query_terms:
                    if term in content_lower:
                        matching_terms.append(term)
                
                relevance_score = len(matching_terms) / len(query_terms) if query_terms else 0
                
                if relevance_score > 0.7:
                    st.success(f"✅ High relevance: {relevance_score:.0%} ({len(matching_terms)}/{len(query_terms)} terms match)")
                elif relevance_score > 0.4:
                    st.warning(f"⚠️ Medium relevance: {relevance_score:.0%} ({len(matching_terms)}/{len(query_terms)} terms match)")
                else:
                    st.error(f"❌ Low relevance: {relevance_score:.0%} ({len(matching_terms)}/{len(query_terms)} terms match)")
                
                if matching_terms:
                    st.write(f"Matching terms: {', '.join(matching_terms)}")
        
        # Test with QA chain if available
        if qa_chain:
            st.write("**QA Chain Test:**")
            try:
                with st.spinner("Generating answer..."):
                    answer = qa_chain.invoke({"query": query})
                    if isinstance(answer, dict):
                        answer_text = answer.get("result", answer.get("answer", str(answer)))
                    else:
                        answer_text = str(answer)
                    
                    st.write("**Generated Answer:**")
                    st.write(answer_text)
                    
            except Exception as e:
                st.error(f"❌ QA chain error: {e}")
        
        # Log the test
        log_to_sublog(project_config.project_dir, "retrieval_testing.log", 
                      f"Query tested: '{query}' -> {len(docs)} docs retrieved")
        
    except Exception as e:
        st.error(f"❌ Error testing query: {e}")
        log_to_sublog(project_config.project_dir, "retrieval_testing.log", f"Error testing query '{query}': {e}")

def test_retrieval_results(query: str, retriever, project_config, qa_chain=None):
    """Test a single query and return results as a list of dictionaries."""
    try:
        if not retriever:
            return []
        
        # Retrieve documents
        docs = retriever.get_relevant_documents(query, k=5)
        
        if not docs:
            return []
        
        # Convert to list of dictionaries
        results = []
        for doc in docs:
            result = {
                "content": doc.page_content,
                "source": doc.metadata.get('source', 'Unknown'),
                "score": doc.metadata.get('score', 0.0),
                "metadata": doc.metadata
            }
            results.append(result)
        
        return results
        
    except Exception as e:
        log_to_sublog(project_config.project_dir, "debug_tools.log", f"Error testing retrieval for query '{query}': {e}")
        return []

# --------------- CODE CHANGE SUMMARY ---------------
# ADDED
# - test_retrieval_results(): New function that returns results as list of dictionaries.
# - Structured return format with content, source, score, and metadata.
# - Proper error handling and logging for retrieval testing.
# - Integration with UI components for result display.

def run_test_suite(queries: List[str], retriever, project_config, qa_chain=None):
    """Run a predefined test suite and show summary results."""
    st.write(f"**Running test suite with {len(queries)} queries...**")
    
    results = []
    
    for query in queries:
        try:
            docs = retriever.get_relevant_documents(query, k=3)
            
            result = {
                "query": query,
                "retrieved_count": len(docs),
                "has_results": len(docs) > 0,
                "has_anchors": False,
                "top_relevance": 0
            }
            
            if docs:
                # Check top result for anchors
                top_doc = docs[0]
                metadata = top_doc.metadata
                anchors = []
                for anchor_type in ["class_names", "function_names", "screen_name", "component_name"]:
                    if metadata.get(anchor_type):
                        anchors.append(anchor_type)
                
                result["has_anchors"] = len(anchors) > 0
                
                # Calculate relevance
                query_terms = query.lower().split()
                content = top_doc.page_content.lower()
                matching_terms = sum(1 for term in query_terms if term in content)
                result["top_relevance"] = matching_terms / len(query_terms) if query_terms else 0
            
            results.append(result)
            
        except Exception as e:
            st.error(f"Error testing '{query}': {e}")
            results.append({
                "query": query,
                "retrieved_count": 0,
                "has_results": False,
                "has_anchors": False,
                "top_relevance": 0,
                "error": str(e)
            })
    
    # Display summary
    st.write("**Test Suite Results:**")
    
    # Calculate metrics
    total_queries = len(results)
    successful_queries = sum(1 for r in results if r["has_results"])
    queries_with_anchors = sum(1 for r in results if r["has_anchors"])
    avg_relevance = sum(r["top_relevance"] for r in results) / total_queries if total_queries > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total queries", total_queries)
    with col2:
        st.metric("Successful", f"{successful_queries} ({successful_queries/total_queries*100:.0f}%)")
    with col3:
        st.metric("With anchors", f"{queries_with_anchors} ({queries_with_anchors/total_queries*100:.0f}%)")
    with col4:
        st.metric("Avg relevance", f"{avg_relevance:.0%}")
    
    # Detailed results
    with st.expander("📊 Detailed Results"):
        for result in results:
            status_icon = "✅" if result["has_results"] else "❌"
            anchor_icon = "🔗" if result["has_anchors"] else "⚪"
            relevance_pct = f"{result['top_relevance']:.0%}"
            
            st.write(f"{status_icon} {anchor_icon} **{result['query']}** - {result['retrieved_count']} docs, {relevance_pct} relevance")
            
            if result.get("error"):
                st.error(f"Error: {result['error']}")
    
    # Overall assessment
    if successful_queries / total_queries > 0.8 and avg_relevance > 0.6:
        st.success("🎉 Test suite passed! Good retrieval quality.")
    elif successful_queries / total_queries > 0.6:
        st.warning("⚠️ Test suite partially passed. Some issues detected.")
    else:
        st.error("❌ Test suite failed. Significant retrieval issues detected.")
    
    # Log results
    log_to_sublog(project_config.get_project_dir(), "test_suite_results.log", 
                  f"Test suite completed: {successful_queries}/{total_queries} successful, {avg_relevance:.0%} avg relevance")

def compare_queries(query1: str, query2: str, retriever, project_config):
    """Compare retrieval results between two queries."""
    st.write(f"**Comparing: '{query1}' vs '{query2}'**")
    
    try:
        docs1 = retriever.get_relevant_documents(query1, k=5)
        docs2 = retriever.get_relevant_documents(query2, k=5)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Query 1: '{query1}'**")
            st.write(f"Retrieved: {len(docs1)} documents")
            
            if docs1:
                for i, doc in enumerate(docs1[:3], 1):
                    st.write(f"{i}. {doc.metadata.get('source', 'Unknown')}")
                    st.caption(doc.page_content[:100] + "...")
        
        with col2:
            st.write(f"**Query 2: '{query2}'**")
            st.write(f"Retrieved: {len(docs2)} documents")
            
            if docs2:
                for i, doc in enumerate(docs2[:3], 1):
                    st.write(f"{i}. {doc.metadata.get('source', 'Unknown')}")
                    st.caption(doc.page_content[:100] + "...")
        
        # Find overlapping results
        sources1 = {doc.metadata.get('source') for doc in docs1}
        sources2 = {doc.metadata.get('source') for doc in docs2}
        
        overlap = sources1.intersection(sources2)
        
        st.write("**Comparison Analysis:**")
        st.write(f"• Overlap: {len(overlap)} files appear in both results")
        st.write(f"• Unique to query 1: {len(sources1 - sources2)} files")
        st.write(f"• Unique to query 2: {len(sources2 - sources1)} files")
        
        if overlap:
            st.write("**Overlapping files:**")
            for source in list(overlap)[:5]:
                st.write(f"  • {source}")
        
        # Log comparison
        log_to_sublog(project_config.get_project_dir(), "query_comparison.log", 
                      f"Compared '{query1}' ({len(docs1)} docs) vs '{query2}' ({len(docs2)} docs), {len(overlap)} overlap")
        
    except Exception as e:
        st.error(f"❌ Error comparing queries: {e}")