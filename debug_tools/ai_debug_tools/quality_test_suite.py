#!/usr/bin/env python3
"""
Comprehensive Quality Testing Suite for RAG System
Tests answer quality, embedding compatibility, and logs all details for debugging.
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Add the core directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'core'))

from chat_handler import ChatHandler
from rag_manager import RagManager
from config.config import ProjectConfig
from logger import log_to_sublog, log_highlight

class QualityTestSuite:
    """Comprehensive testing suite for RAG system quality and debugging."""
    
    def __init__(self, project_dir: str, ollama_model: str = "llama3.1", ollama_endpoint: str = "http://127.0.0.1:11434", is_streamlit_context: bool = False):
        self.project_dir = project_dir
        self.ollama_model = ollama_model
        self.ollama_endpoint = ollama_endpoint
        self.project_config = ProjectConfig(project_type="android", project_dir=project_dir)
        self.test_results = []
        self.is_streamlit_context = is_streamlit_context
        
        # Determine log directory based on context
        if is_streamlit_context:
            # When run from Streamlit UI
            self.log_dir = os.path.join(project_dir, "debug_tools", "logs")
        else:
            # When run manually from ai_debug_tools
            self.log_dir = os.path.join(os.path.dirname(__file__), "logs")
        
        os.makedirs(self.log_dir, exist_ok=True)
        
    def test_embedding_compatibility(self) -> Dict[str, Any]:
        """Test embedding model compatibility and dimensions."""
        log_highlight("Testing embedding compatibility")
        log_to_sublog(self.project_dir, "quality_test.log", "=== EMBEDDING COMPATIBILITY TEST ===")
        
        results = {
            "test_name": "embedding_compatibility",
            "timestamp": datetime.now().isoformat(),
            "ollama_model": self.ollama_model,
            "ollama_endpoint": self.ollama_endpoint,
            "status": "unknown",
            "details": {}
        }
        
        try:
            # Test 1: Check if Ollama is running
            log_to_sublog(self.project_dir, "quality_test.log", "Testing Ollama connectivity...")
            response = requests.get(f"{self.ollama_endpoint}/api/tags", timeout=10)
            if response.status_code != 200:
                results["status"] = "failed"
                results["details"]["ollama_connection"] = f"Failed: {response.status_code}"
                log_to_sublog(self.project_dir, "quality_test.log", f"Ollama connection failed: {response.status_code}")
                return results
            
            log_to_sublog(self.project_dir, "quality_test.log", "Ollama is running")
            results["details"]["ollama_connection"] = "success"
            
            # Test 2: Check available models
            models_data = response.json()
            available_models = [model.get("name", "") for model in models_data.get("models", [])]
            log_to_sublog(self.project_dir, "quality_test.log", f"Available models: {available_models}")
            results["details"]["available_models"] = available_models
            
            # Test 3: Check if embedding model exists
            embedding_models = [model for model in available_models if "nomic-embed" in model.lower()]
            if embedding_models:
                embedding_model = embedding_models[0]
                log_to_sublog(self.project_dir, "quality_test.log", f"Embedding model {embedding_model} is available")
                results["details"]["embedding_model"] = "available"
                results["status"] = "success"
            else:
                log_to_sublog(self.project_dir, "quality_test.log", f"Embedding model not found")
                results["details"]["embedding_model"] = "not_found"
                results["status"] = "warning"
                
        except Exception as e:
            results["status"] = "failed"
            results["details"]["error"] = str(e)
            log_to_sublog(self.project_dir, "quality_test.log", f"Embedding compatibility test failed: {e}")
            
        return results
    
    def test_rag_building(self) -> Dict[str, Any]:
        """Test RAG building process and log all details."""
        log_highlight("Testing RAG building process")
        log_to_sublog(self.project_dir, "quality_test.log", "=== RAG BUILDING TEST ===")
        
        results = {
            "test_name": "rag_building",
            "timestamp": datetime.now().isoformat(),
            "status": "unknown",
            "details": {}
        }
        
        try:
            # Initialize session state before RAG building
            if not self.is_streamlit_context:
                import streamlit as st
                if not hasattr(st, 'session_state'):
                    st.session_state = {}
                if 'thinking_logs' not in st.session_state:
                    st.session_state.thinking_logs = []
                if 'qa_chain' not in st.session_state:
                    st.session_state.qa_chain = None
            
            # Initialize RAG manager
            rag_manager = RagManager()
            
            # Test RAG building
            log_to_sublog(self.project_dir, "quality_test.log", "Starting RAG building test...")
            start_time = time.time()
            
            # Create a mock log placeholder for non-streamlit context
            class MockLogPlaceholder:
                def empty(self):
                    pass
                def container(self):
                    return self
                def text_area(self, *args, **kwargs):
                    pass
                def __enter__(self):
                    return self
                def __exit__(self, exc_type, exc_val, exc_tb):
                    pass
            
            # Build RAG index
            retriever, qa_chain = rag_manager.build_rag_index(
                self.project_dir, 
                self.ollama_model, 
                self.ollama_endpoint, 
                "android", 
                MockLogPlaceholder()
            )
            
            build_time = time.time() - start_time
            log_to_sublog(self.project_dir, "quality_test.log", f"RAG building completed in {build_time:.2f}s")
            
            results["status"] = "success"
            results["details"]["build_time"] = build_time
            results["details"]["retriever_created"] = retriever is not None
            results["details"]["qa_chain_created"] = qa_chain is not None
            
            # Store for later use
            self.retriever = retriever
            self.qa_chain = qa_chain
            
        except Exception as e:
            results["status"] = "failed"
            results["details"]["error"] = str(e)
            log_to_sublog(self.project_dir, "quality_test.log", f"RAG building test failed: {e}")
            
        return results
    
    def test_question_quality(self, question: str, expected_rating: int = 4) -> Dict[str, Any]:
        """Test answer quality for a specific question."""
        log_highlight(f"Testing question quality: {question}")
        log_to_sublog(self.project_dir, "quality_test.log", f"=== QUESTION QUALITY TEST: {question} ===")
        
        results = {
            "test_name": "question_quality",
            "question": question,
            "expected_rating": expected_rating,
            "timestamp": datetime.now().isoformat(),
            "status": "unknown",
            "details": {}
        }
        
        try:
            # Initialize chat handler
            chat_handler = ChatHandler(
                llm=RagManager().setup_llm(self.ollama_model, self.ollama_endpoint),
                project_config=self.project_config,
                project_dir=self.project_dir
            )
            
            # Create mock session state for non-streamlit context
            if not self.is_streamlit_context:
                import streamlit as st
                if not hasattr(st, 'session_state'):
                    st.session_state = {}
                if 'thinking_logs' not in st.session_state:
                    st.session_state.thinking_logs = []
                if 'qa_chain' not in st.session_state:
                    st.session_state.qa_chain = None
            
            # Process the question
            log_to_sublog(self.project_dir, "quality_test.log", f"Processing question: {question}")
            start_time = time.time()
            
            # Create mock log placeholder
            class MockLogPlaceholder:
                def empty(self):
                    pass
                def container(self):
                    return self
                def text_area(self, *args, **kwargs):
                    pass
                def __enter__(self):
                    return self
                def __exit__(self, exc_type, exc_val, exc_tb):
                    pass
            
            # Store qa_chain in session state for chat_handler to use
            if not self.is_streamlit_context:
                import streamlit as st
                st.session_state.qa_chain = self.qa_chain
            
            answer, reranked_docs, impact_files, metadata = chat_handler.process_query(
                question, self.qa_chain, MockLogPlaceholder(), debug_mode=True
            )
            
            processing_time = time.time() - start_time
            log_to_sublog(self.project_dir, "quality_test.log", f"Question processed in {processing_time:.2f}s")
            
            # Analyze answer quality
            quality_metrics = self._analyze_answer_quality(answer, metadata, reranked_docs)
            
            results["status"] = "success"
            results["details"]["processing_time"] = processing_time
            results["details"]["answer_length"] = len(answer)
            results["details"]["source_docs_count"] = len(reranked_docs)
            results["details"]["impact_files_count"] = len(impact_files)
            results["details"]["metadata"] = metadata
            results["details"]["quality_metrics"] = quality_metrics
            results["details"]["answer"] = answer
            results["details"]["source_docs"] = [
                {
                    "source": doc.metadata.get("source", "unknown"),
                    "chunk_index": doc.metadata.get("chunk_index", 0),
                    "name": doc.metadata.get("name", ""),
                    "content_preview": doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                }
                for doc in reranked_docs[:5]  # Top 5 sources
            ]
            
            # Calculate satisfaction rating
            satisfaction_rating = self._calculate_satisfaction_rating(quality_metrics, expected_rating)
            results["details"]["satisfaction_rating"] = satisfaction_rating
            
            log_to_sublog(self.project_dir, "quality_test.log", f"Quality analysis completed. Satisfaction rating: {satisfaction_rating}/10")
            
        except Exception as e:
            results["status"] = "failed"
            results["details"]["error"] = str(e)
            log_to_sublog(self.project_dir, "quality_test.log", f"Question quality test failed: {e}")
            
        return results
    
    def _analyze_answer_quality(self, answer: str, metadata: Dict, source_docs: List) -> Dict[str, Any]:
        """Analyze the quality of an answer."""
        metrics = {
            "relevance_score": 0,
            "completeness_score": 0,
            "clarity_score": 0,
            "source_utilization": 0,
            "metadata_completeness": 0
        }
        
        # Relevance score (based on answer content)
        if answer and len(answer) > 50:
            metrics["relevance_score"] = min(10, len(answer) / 20)  # Simple heuristic
        
        # Completeness score
        if metadata.get("intent") and metadata.get("confidence"):
            metrics["completeness_score"] = 8
        elif metadata.get("intent") or metadata.get("confidence"):
            metrics["completeness_score"] = 5
        else:
            metrics["completeness_score"] = 2
        
        # Clarity score (based on answer structure)
        if "•" in answer or "-" in answer or "\n" in answer:
            metrics["clarity_score"] = 8
        elif len(answer) > 100:
            metrics["clarity_score"] = 6
        else:
            metrics["clarity_score"] = 4
        
        # Source utilization
        if source_docs:
            metrics["source_utilization"] = min(10, len(source_docs) * 2)
        
        # Metadata completeness
        metadata_fields = ["intent", "confidence", "rewritten_query"]
        present_fields = sum(1 for field in metadata_fields if metadata.get(field))
        metrics["metadata_completeness"] = (present_fields / len(metadata_fields)) * 10
        
        return metrics
    
    def _calculate_satisfaction_rating(self, quality_metrics: Dict, expected_rating: int) -> int:
        """Calculate satisfaction rating based on quality metrics."""
        avg_score = sum(quality_metrics.values()) / len(quality_metrics)
        
        # Adjust based on expected rating
        if avg_score >= expected_rating:
            return min(10, int(avg_score))
        else:
            return max(1, int(avg_score * 0.8))  # Penalty for not meeting expectations
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test suite."""
        log_highlight("Starting comprehensive quality test suite")
        log_to_sublog(self.project_dir, "quality_test.log", "=== COMPREHENSIVE QUALITY TEST SUITE ===")
        
        test_suite_results = {
            "timestamp": datetime.now().isoformat(),
            "project_dir": self.project_dir,
            "ollama_model": self.ollama_model,
            "tests": []
        }
        
        # Test 1: Embedding compatibility
        embedding_test = self.test_embedding_compatibility()
        test_suite_results["tests"].append(embedding_test)
        
        # Test 2: RAG building
        rag_test = self.test_rag_building()
        test_suite_results["tests"].append(rag_test)
        
        # Test 3: Question quality tests
        test_questions = [
            "What is this codebase about?",
            "What is the impact if I want to change the flow skipping MainActivity and directly go to SettingsFragment?",
            "What is the business logic in SettingsFragment?",
            "What is the validation given to username in LoginScreen?",
            "List down the project directory file structure"
        ]
        
        for question in test_questions:
            question_test = self.test_question_quality(question)
            test_suite_results["tests"].append(question_test)
        
        # Save comprehensive results
        results_file = os.path.join(self.log_dir, "comprehensive_test_results.json")
        with open(results_file, 'w') as f:
            json.dump(test_suite_results, f, indent=2)
        
        log_to_sublog(self.project_dir, "quality_test.log", f"Comprehensive test completed. Results saved to {results_file}")
        
        return test_suite_results

def main():
    """Main function to run the quality test suite."""
    print("🚀 Starting Quality Test Suite")
    print("=" * 50)
    
    # Configuration
    project_dir = "../"  # Adjust as needed
    ollama_model = "llama3.1"
    ollama_endpoint = "http://127.0.0.1:11434"
    
    # Initialize test suite (manual run, not from Streamlit)
    test_suite = QualityTestSuite(project_dir, ollama_model, ollama_endpoint, is_streamlit_context=False)
    
    # Run comprehensive test
    results = test_suite.run_comprehensive_test()
    
    # Print summary
    print("\n📊 Test Results Summary:")
    print("=" * 50)
    
    for test in results["tests"]:
        status = test.get("status", "unknown")
        test_name = test.get("test_name", "unknown")
        print(f"✅ {test_name}: {status}")
        
        if test_name == "question_quality":
            question = test.get("question", "")
            satisfaction = test.get("details", {}).get("satisfaction_rating", 0)
            print(f"   Question: {question}")
            print(f"   Satisfaction Rating: {satisfaction}/10")
    
    print(f"\n📁 Detailed results saved to: {test_suite.log_dir}/comprehensive_test_results.json")
    print(f"📝 Logs saved to: {test_suite.log_dir}/quality_test.log")

if __name__ == "__main__":
    main() 