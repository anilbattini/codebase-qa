"""
Interactive retrieval testing tools for debugging search quality using actual core functionality.
"""

import os
import sys
import streamlit as st
from typing import List, Dict, Any

# Add parent directory to path to import from codebase-qa root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import log_highlight, log_to_sublog

def test_retrieval(project_config, retriever, vectorstore=None):
    """Interactive retrieval testing interface using actual core functionality."""
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
        test_single_query(test_query, retriever, k_docs, project_config, vectorstore)
    
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
        run_test_suite(test_suites[selected_suite], retriever, project_config, vectorstore)
    
    # Comparison testing
    st.write("**Query Comparison Testing**")
    
    col1, col2 = st.columns(2)
    with col1:
        query1 = st.text_input("Query 1:", placeholder="MainActivity")
    with col2:
        query2 = st.text_input("Query 2:", placeholder="main activity class")
    
    if query1 and query2 and st.button("⚖️ Compare Queries"):
        compare_queries(query1, query2, retriever, project_config)

def test_single_query(query: str, retriever, k: int, project_config, vectorstore=None):
    """Test a single query and display detailed results using actual retriever."""
    st.write(f"**Testing query: '{query}'**")
    
    try:
        # Check if retriever is available
        if not retriever:
            st.error("❌ No retriever available for testing")
            return
        
        # Use the actual retriever to get documents
        docs = retriever.get_relevant_documents(query, k=k)
        
        if not docs:
            st.error("❌ No documents retrieved")
            return
        
        st.success(f"✅ Retrieved {len(docs)} documents")
        
        # Display results
        for i, doc in enumerate(docs, 1):
            # Safely get metadata
            metadata = getattr(doc, 'metadata', {})
            if not isinstance(metadata, dict):
                metadata = {}
            
            source = metadata.get('source', 'Unknown source') if isinstance(metadata, dict) else 'Unknown source'
            
            with st.expander(f"📄 Result {i}: {source}"):
                st.write("**Metadata:**")
                
                # Show key metadata fields safely
                key_fields = ['source', 'type', 'chunk_index', 'screen_name', 'class_names', 'function_names']
                for field in key_fields:
                    if isinstance(metadata, dict) and field in metadata and metadata[field]:
                        st.write(f"  • **{field}**: {metadata[field]}")
                
                # Show content preview
                st.write("**Content Preview:**")
                content = getattr(doc, 'page_content', '') or getattr(doc, 'content', '')
                if len(content) > 500:
                    st.code(content[:500] + "...")
                    st.write(f"*Content truncated. Full length: {len(content)} characters*")
                else:
                    st.code(content)
                
                # Show relevance indicators
                st.write("**Relevance Indicators:**")
                
                # Check for query terms in content
                query_terms = query.lower().split()
                content_lower = content.lower()
                matching_terms = [term for term in query_terms if term in content_lower]
                
                if matching_terms:
                    st.write(f"  ✅ Query terms found: {', '.join(matching_terms)}")
                else:
                    st.write("  ⚠️ No exact query terms found in content")
                
                # Check for semantic anchors
                anchors = []
                if isinstance(metadata, dict):
                    for anchor_type in ['screen_name', 'class_names', 'function_names', 'component_name']:
                        if metadata.get(anchor_type):
                            anchors.append(f"{anchor_type}: {metadata[anchor_type]}")
                
                if anchors:
                    st.write(f"  🎯 Semantic anchors: {', '.join(anchors)}")
                else:
                    st.write("  ⚠️ No semantic anchors found")
                
    except Exception as e:
        st.error(f"❌ Error testing query: {e}")
        log_to_sublog(project_config.project_dir, "debug_tools.log", f"Error testing query '{query}': {e}")

def test_retrieval_results(query: str, retriever, project_config, vectorstore=None):
    """Test a single query and return results as a list of dictionaries using the existing retriever from session state."""
    try:
        log_to_sublog(project_config.project_dir, "debug_tools.log", 
                     f"Testing retrieval results for query: {query}")
        
        # Use the retriever from session state (same as main app)
        if not retriever:
            retriever = st.session_state.get("retriever")
        
        if not retriever:
            log_to_sublog(project_config.project_dir, "debug_tools.log", "No retriever available in session state")
            return []
        
        # Use the actual retriever to get documents
        docs = retriever.get_relevant_documents(query, k=5)
        
        if not docs:
            log_to_sublog(project_config.project_dir, "debug_tools.log", "No documents retrieved")
            return []
        
        log_to_sublog(project_config.project_dir, "debug_tools.log", 
                     f"Retrieved {len(docs)} documents for query: {query}")
        
        # Convert to list of dictionaries
        results = []
        for i, doc in enumerate(docs, 1):
            # Safely get metadata
            metadata = getattr(doc, 'metadata', {})
            if not isinstance(metadata, dict):
                metadata = {}
            
            result = {
                "content": getattr(doc, 'page_content', '') or getattr(doc, 'content', ''),
                "source": metadata.get('source', 'Unknown') if isinstance(metadata, dict) else 'Unknown',
                "score": metadata.get('score', 0.0) if isinstance(metadata, dict) else 0.0,
                "metadata": metadata
            }
            results.append(result)
            
            log_to_sublog(project_config.project_dir, "debug_tools.log", 
                         f"Result {i}: {result['source']} (score: {result['score']})")
        
        log_to_sublog(project_config.project_dir, "debug_tools.log", 
                     f"Retrieval test completed successfully: {len(results)} results")
        return results
        
    except Exception as e:
        log_to_sublog(project_config.project_dir, "debug_tools.log", 
                     f"Error testing retrieval for query '{query}': {e}")
        return []

def run_test_suite(queries: List[str], retriever, project_config, vectorstore=None):
    """Run a test suite with multiple queries and display results."""
    st.write(f"**Running test suite with {len(queries)} queries**")
    
    results = []
    
    for i, query in enumerate(queries, 1):
        st.write(f"**Query {i}/{len(queries)}: {query}**")
        
        try:
            docs = retriever.get_relevant_documents(query, k=3)
            
            if docs:
                # Analyze results
                sources = [doc.metadata.get('source', 'Unknown') for doc in docs]
                unique_sources = len(set(sources))
                
                # Check relevance
                query_terms = query.lower().split()
                relevant_docs = 0
                for doc in docs:
                    content_lower = doc.page_content.lower()
                    if any(term in content_lower for term in query_terms):
                        relevant_docs += 1
                
                result = {
                    "query": query,
                    "retrieved": len(docs),
                    "unique_sources": unique_sources,
                    "relevant_docs": relevant_docs,
                    "relevance_rate": relevant_docs / len(docs) if docs else 0
                }
                results.append(result)
                
                st.success(f"✅ Retrieved {len(docs)} docs from {unique_sources} files")
                st.write(f"  • Relevance: {result['relevance_rate']:.1%} ({relevant_docs}/{len(docs)} docs)")
                
                # Show top result
                if docs:
                    top_doc = docs[0]
                    st.write(f"  • Top result: {top_doc.metadata.get('source', 'Unknown')}")
                    
                    # Show content preview
                    content = top_doc.page_content
                    if len(content) > 200:
                        st.write(f"  • Preview: {content[:200]}...")
                    else:
                        st.write(f"  • Preview: {content}")
            else:
                st.warning(f"⚠️ No results for: {query}")
                results.append({
                    "query": query,
                    "retrieved": 0,
                    "unique_sources": 0,
                    "relevant_docs": 0,
                    "relevance_rate": 0
                })
                
        except Exception as e:
            st.error(f"❌ Error testing '{query}': {e}")
            results.append({
                "query": query,
                "error": str(e)
            })
    
    # Summary
    if results:
        st.write("**📊 Test Suite Summary**")
        
        successful_results = [r for r in results if "error" not in r]
        if successful_results:
            avg_retrieved = sum(r["retrieved"] for r in successful_results) / len(successful_results)
            avg_relevance = sum(r["relevance_rate"] for r in successful_results) / len(successful_results)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Avg documents retrieved", f"{avg_retrieved:.1f}")
            with col2:
                st.metric("Avg relevance rate", f"{avg_relevance:.1%}")
            with col3:
                st.metric("Successful queries", f"{len(successful_results)}/{len(results)}")
            
            # Quality assessment
            if avg_relevance > 0.7:
                st.success("✅ High relevance rate - retrieval working well")
            elif avg_relevance > 0.5:
                st.warning("⚠️ Moderate relevance rate - some improvement needed")
            else:
                st.error("❌ Low relevance rate - retrieval needs improvement")
        
        # Log results
        log_to_sublog(project_config.project_dir, "debug_tools.log", 
                     f"Test suite completed: {len(successful_results)}/{len(results)} successful queries")

def compare_queries(query1: str, query2: str, retriever, project_config):
    """Compare two queries and analyze differences in results."""
    st.write(f"**Comparing queries: '{query1}' vs '{query2}'**")
    
    try:
        # Get results for both queries
        docs1 = retriever.get_relevant_documents(query1, k=5)
        docs2 = retriever.get_relevant_documents(query2, k=5)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Results for '{query1}':**")
            st.write(f"Retrieved: {len(docs1)} documents")
            
            if docs1:
                sources1 = [doc.metadata.get('source', 'Unknown') for doc in docs1]
                st.write(f"Files: {', '.join(set(sources1))}")
                
                # Show top result
                top_doc1 = docs1[0]
                st.write(f"**Top result:** {top_doc1.metadata.get('source', 'Unknown')}")
                content1 = top_doc1.page_content[:150] + "..." if len(top_doc1.page_content) > 150 else top_doc1.page_content
                st.write(f"Preview: {content1}")
        
        with col2:
            st.write(f"**Results for '{query2}':**")
            st.write(f"Retrieved: {len(docs2)} documents")
            
            if docs2:
                sources2 = [doc.metadata.get('source', 'Unknown') for doc in docs2]
                st.write(f"Files: {', '.join(set(sources2))}")
                
                # Show top result
                top_doc2 = docs2[0]
                st.write(f"**Top result:** {top_doc2.metadata.get('source', 'Unknown')}")
                content2 = top_doc2.page_content[:150] + "..." if len(top_doc2.page_content) > 150 else top_doc2.page_content
                st.write(f"Preview: {content2}")
        
        # Analyze overlap
        if docs1 and docs2:
            sources1 = set(doc.metadata.get('source', 'Unknown') for doc in docs1)
            sources2 = set(doc.metadata.get('source', 'Unknown') for doc in docs2)
            
            overlap = sources1.intersection(sources2)
            unique1 = sources1 - sources2
            unique2 = sources2 - sources1
            
            st.write("**📊 Overlap Analysis:**")
            st.write(f"  • Common files: {len(overlap)}")
            st.write(f"  • Unique to query 1: {len(unique1)}")
            st.write(f"  • Unique to query 2: {len(unique2)}")
            
            if overlap:
                st.write(f"  • Common files: {', '.join(overlap)}")
            
            # Quality comparison
            def calculate_relevance(docs, query):
                query_terms = query.lower().split()
                relevant = 0
                for doc in docs:
                    content_lower = doc.page_content.lower()
                    if any(term in content_lower for term in query_terms):
                        relevant += 1
                return relevant / len(docs) if docs else 0
            
            relevance1 = calculate_relevance(docs1, query1)
            relevance2 = calculate_relevance(docs2, query2)
            
            st.write("**🎯 Relevance Comparison:**")
            st.write(f"  • Query 1 relevance: {relevance1:.1%}")
            st.write(f"  • Query 2 relevance: {relevance2:.1%}")
            
            if abs(relevance1 - relevance2) < 0.1:
                st.info("ℹ️ Similar relevance scores")
            elif relevance1 > relevance2:
                st.success(f"✅ Query 1 has better relevance")
            else:
                st.success(f"✅ Query 2 has better relevance")
        
    except Exception as e:
        st.error(f"❌ Error comparing queries: {e}")
        log_to_sublog(project_config.project_dir, "debug_tools.log", f"Error comparing queries: {e}")