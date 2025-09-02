from datetime import datetime
import json
from typing import List
import streamlit as st
import re
import os
from build_rag import update_logs, get_impact
from context_builder import ContextBuilder
from prompt_router import PromptRouter
from query_intent_classifier import QueryIntentClassifier
from logger import log_highlight, log_to_sublog
from config.feature_toggle_manager import FeatureToggleManager

class ChatHandler:
    """
    Main user-question handler: intent classification, query rewriting, impact analysis,
    retrieve/rerank by semantic anchors, hierarchy-aware context build, answer aggregation.
    🆕 Now with Phase 3 enhanced context capabilities.
    """

    def __init__(self, llm, provider, project_config, project_dir=".", rewrite_llm=None):
        self.project_dir = project_dir
        self.llm = llm
        self.project_config = project_config
        self.provider = provider
        self.rewrite_llm = rewrite_llm if rewrite_llm is not None else llm
        self.context_builder = ContextBuilder(project_config, project_dir=project_dir)
        self.query_intent_classifier = QueryIntentClassifier(project_config)

    def _create_enhanced_retriever(self, base_retriever, project_dir, rewrite_chain):
        """Fixed MultiQueryRetriever - access LLM correctly from RunnableSequence."""
        try:
            from langchain.retrievers.multi_query import MultiQueryRetriever
            from langchain.prompts import PromptTemplate
            from langchain.schema import BaseOutputParser
            from langchain.chains import LLMChain
            
            
            # # Extract LLM from RunnableSequence correctly
            # if hasattr(rewrite_chain, 'last'):
            #     # RunnableSequence: get the LLM from the chain
            #     llm = rewrite_chain.last
            #     prompt = rewrite_chain.first
            #     log_to_sublog(project_dir, "preparing_full_context.log",
            #     f"✅ hasattr rewrite_chain last")
            # elif hasattr(rewrite_chain, 'steps') and len(rewrite_chain.steps) > 0:
            #     # Alternative: get from steps
            #     llm = rewrite_chain.steps[-1]
            #     prompt = rewrite_chain.steps[-0]
            #     log_to_sublog(project_dir, "preparing_full_context.log",
            #     f"✅ hasattr rewrite_chain steps")
            # else:
            #     # Fallback: use rewrite_llm directly
            #     llm = self.rewrite_llm
            #     log_to_sublog(project_dir, "preparing_full_context.log",
            #     f"✅ default rewrit_llm for MultiQueryRetriever")
            
            # Create output parser
            class QueryListParser(BaseOutputParser):
                def parse(self, text: str) -> list:
                    if isinstance(text, str):
                        content = text.strip()
                    elif hasattr(text, 'content'):
                        content = text.content.strip()
                    else:
                        content = str(text).strip()
                    
                    # Split and clean
                    lines = [line.strip().strip("'\"") for line in content.split('\n') if line.strip()]
                    queries = []
                    for line in lines:
                        clean_line = re.sub(r'^[\d\.\-\*\+:\s]+', '', line).strip()
                        if len(clean_line) > 3:
                            queries.append(clean_line)
                    
                    return queries[:2] if queries else ["search terms"]
            
             # Simple prompt for MultiQueryRetriever
            multi_qa_prompt = PromptTemplate(
                input_variables=["question"],
                template="Generate 2 search variations for: {question}\nEach on new line:"
            )
            
            # Create LLM chain with parser
            llm_chain = LLMChain(
                prompt=rewrite_chain.first,
                llm=rewrite_chain.last,  # Use extracted LLM
                output_parser=QueryListParser()
            )
            
            # Create MultiQueryRetriever
            enhanced_retriever = MultiQueryRetriever(
                retriever=base_retriever,
                llm_chain=llm_chain,
                max_queries=2
            )
            
            # Test it
            test_docs = enhanced_retriever.get_relevant_documents("test query")
            log_to_sublog(project_dir, "preparing_full_context.log",
                f"✅ Enhanced retriever working: {len(test_docs)} docs")
            
            return enhanced_retriever
            
        except Exception as e:
            log_to_sublog(project_dir, "preparing_full_context.log", 
                f"❌ Enhanced retriever failed: {e}")
            return None

    
    def _get_retriever(self, vectorstore, project_dir, rewrite_chain):
            # 🎛️ FEATURE TOGGLE: Enhanced Retriever Creation
        project_dir_for_toggle = project_dir if project_dir else "."
        base_retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 15})
        
        if FeatureToggleManager.is_enabled("langchain_retriever", project_dir_for_toggle):
            enhanced_retriever = self._create_enhanced_retriever(base_retriever, project_dir, rewrite_chain)
            if enhanced_retriever:
                return enhanced_retriever
            else:
                log_to_sublog(project_dir, "preparing_full_context.log",
                    "🏠 Falling back to legacy retriever due to enhanced failure")

        # Legacy fallback
        log_to_sublog(project_dir, "preparing_full_context.log",
            "🏠 Using legacy Chroma retriever")
        return base_retriever

    def process_query(self, query, vectorstore, log_placeholder, debug_mode=False):
        """
        Enhanced query processing with comprehensive feature toggle logging.
        Tracks every decision and feature usage throughout the pipeline.
        """
        log_highlight("ChatHandler.process_query")
        
        # Initialize comprehensive query tracking
        query_start_time = datetime.now()
        st.session_state.setdefault("thinking_logs", [])
        
        # 📊 QUERY START LOGGING
        log_to_sublog(self.project_dir, "preparing_full_context.log",
            f"\n{'='*80}\n🚀 QUERY PROCESSING START: {query_start_time.isoformat()}\n"
            f"Query: {query}\nDebug Mode: {debug_mode}\n{'='*80}")
        
        log_to_sublog(self.project_dir, "toggle_info.log",
            f"QUERY_START: {query_start_time.isoformat()} - Query: '{query[:100]}...' "
            f"Debug: {debug_mode}")
        
        st.session_state.thinking_logs.append("🧠 Starting enhanced query processing...")
        update_logs(log_placeholder)

        try:
            # Phase 1: Intent Classification
            intent, confidence = self.query_intent_classifier.classify_intent(query)
            
            log_to_sublog(self.project_dir, "preparing_full_context.log",
                f"🎯 PHASE 1: Intent Classification\n"
                f"   Intent: {intent}\n   Confidence: {confidence:.2f}")
            
            st.session_state.thinking_logs.append(f"🎯 Detected intent: {intent} (confidence: {confidence:.2f})")
            update_logs(log_placeholder)
            
            if debug_mode:
                st.info(f"🎯 **Query Intent**: {intent} (confidence: {confidence:.2f})")

            # 🎛️ FEATURE TOGGLE: RAG Bypass Check
            disable_rag = st.session_state.get("disable_rag", False)
            if disable_rag:
                log_to_sublog(self.project_dir, "preparing_full_context.log",
                    "⚙️ RAG BYPASS: Sending query directly to LLM")
                log_to_sublog(self.project_dir, "toggle_info.log",
                    "FEATURE_BYPASS: rag_disabled - Direct LLM query")
                
                st.session_state.thinking_logs.append("⚙️ RAG is disabled – sending query directly to LLM.")
                update_logs(log_placeholder)
                
                result = self.llm.invoke(f"User question: {query}")
                answer = getattr(result, "content", str(result))
                return answer, [], [], {"intent": intent, "confidence": confidence}

            # Phase 2: Query Rewriting  
            vectorstore = st.session_state.get("vectorstore")
            project_type = self.project_config.project_type.upper()
            
            from config.model_config import model_config
            rewrite_chain = model_config.create_rewrite_chain(self.rewrite_llm, intent, project_type)
            retriever = self._get_retriever(vectorstore, self.project_dir, rewrite_chain)
            if retriever:
                st.session_state["retriever"] = retriever
                
            retriever_type = type(retriever).__name__
            
            if retriever_type == "MultiQueryRetriever":
                # Enhanced retriever handles rewriting internally
                rewritten = query  # No additional rewriting needed
                log_to_sublog(self.project_dir, "preparing_full_context.log",
                    f"📝 PHASE 2: Skipping rewriting (Enhanced retriever will handle)")
            else:
                # Legacy retriever needs explicit rewriting
                rewritten = self._rewrite_query_with_intent(query, intent, rewrite_chain, log_placeholder, debug_mode)
                log_to_sublog(self.project_dir, "preparing_full_context.log",
                    f"📝 PHASE 2: Query Rewriting\n"
                    f"   Original: {query}\n   Rewritten: {rewritten}")
            
            # Phase 3: Impact Analysis
            impact_files, impact_context = self._analyze_impact_with_intent(query, intent, log_placeholder)
            
            log_to_sublog(self.project_dir, "preparing_full_context.log",
                f"🔍 PHASE 3: Impact Analysis\n"
                f"   Impact Files: {len(impact_files)}\n   Files: {impact_files[:5]}")

            # Phase 4: Document Retrieval
            st.session_state.thinking_logs.append("📖 Performing intelligent document retrieval...")
            update_logs(log_placeholder)
            
            log_to_sublog(self.project_dir, "preparing_full_context.log",
                f"📖 PHASE 4: Document Retrieval\n   Starting retrieval process...")

            retriever = st.session_state.get("retriever")
            if not retriever:
                error_msg = "No retriever found. Please rebuild the RAG index before querying."
                log_to_sublog(self.project_dir, "preparing_full_context.log", f"❌ ERROR: {error_msg}")
                st.error(f"❌ {error_msg}")
                return error_msg, [], [], {}

            # 🎛️ FEATURE TOGGLE: Enhanced Retrieval Logging
            retriever_type = type(retriever).__name__
            log_to_sublog(self.project_dir, "preparing_full_context.log",
                f"🔍 Using Retriever Type: {retriever_type}")
            log_to_sublog(self.project_dir, "toggle_info.log",
                f"RETRIEVAL_METHOD: {retriever_type} - Processing query: '{query[:50]}...'")

            retrieved_docs = self._retrieve_with_fallback(retriever, query, rewritten, log_placeholder)
            
            log_to_sublog(self.project_dir, "preparing_full_context.log",
                f"✅ Retrieved {len(retrieved_docs)} documents")

            if debug_mode:
                st.info(f"📊 Retrieved {len(retrieved_docs)} chunks")

            # Phase 5: Context Building and Answer Generation
            source_documents = retrieved_docs
            
            if source_documents:
                # Document reranking
                reranked_docs = self.query_intent_classifier.rerank_docs_by_intent(source_documents, query, intent)
                
                log_to_sublog(self.project_dir, "preparing_full_context.log",
                    f"📊 PHASE 5: Context Building\n"
                    f"   Original docs: {len(source_documents)}\n"
                    f"   Reranked docs: {len(reranked_docs)}")

                # Enhanced context creation
                formatted_context = self.context_builder.create_full_context(reranked_docs)
                
                # Try enhanced context building if available
                if hasattr(self, 'context_builder') and self.context_builder:
                    try:
                        enhanced_context = self.context_builder.build_enhanced_context(reranked_docs, query, intent)
                        if enhanced_context and len(enhanced_context) > len(formatted_context):
                            formatted_context = enhanced_context
                            log_to_sublog(self.project_dir, "preparing_full_context.log",
                                "✨ Using enhanced context builder")
                    except Exception as e:
                        log_to_sublog(self.project_dir, "preparing_full_context.log", 
                            f"⚠️ Enhanced context failed: {e}")
            else:
                reranked_docs = []
                formatted_context = "No relevant documentation found for this query."
                
            log_to_sublog(self.project_dir, "preparing_full_context.log",
                f"📄 Final context length: {len(formatted_context)} characters")

            # Phase 6: Answer Generation
            st.session_state.thinking_logs.append("🤖 Generating answer...")
            update_logs(log_placeholder)
            
            log_to_sublog(self.project_dir, "preparing_full_context.log",
                f"🤖 PHASE 6: Answer Generation\n   Using provider: {self.provider}")

            router = PromptRouter()
            detail_level = st.session_state.get("detail_level", "moderate")
            
            sys_or_single, user_part = router.build_enhanced_query(
                query=query,
                rewritten=rewritten, 
                intent=intent,
                context=formatted_context,
                detail_level=detail_level,
                provider=self.provider,
                llm=self.llm,
            )

            if user_part:  # Cloud provider
                result = self.llm.invoke_with_system_user(sys_or_single, user_part)
            else:  # Local provider
                result = self.llm.invoke(sys_or_single)

            # Get final answer
            answer = getattr(result, "content", str(result))

            answer_metadata = {
                "intent": intent,
                "confidence": confidence,
                "rewritten_query": rewritten,
                "enhanced_query": None,
                "phase_3_enabled": True,
            }
            

        except Exception as e:
            error_time = datetime.now()
            log_to_sublog(self.project_dir, "preparing_full_context.log",
                f"\n❌ QUERY PROCESSING ERROR: {error_time.isoformat()}\n"
                f"Error: {str(e)}\nQuery: {query}\n{'='*80}\n")
            log_to_sublog(self.project_dir, "toggle_info.log", 
                f"QUERY_ERROR: {str(e)}")
                
            st.error(f"❌ Error processing query: {e}")
            return f"Sorry, I encountered an error while processing your query: {e}", [], [], {}


    def _retrieve_with_fallback(self, retriever, query, rewritten, log_placeholder):
        """Retrieve documents with multiple separate fallback strategies."""
        
        # Strategy 1: Try rewritten query first (most focused)
        try:
            log_to_sublog(self.project_dir, "preparing_full_context.log",
                        f"Strategy 1: Trying rewritten query: '{rewritten}'")
            
            retrieved_docs = retriever.invoke(rewritten)
            
            if retrieved_docs and len(retrieved_docs) >= 2:  # Good results threshold
                log_to_sublog(self.project_dir, "chat_handler.log", 
                            f"Strategy 1 SUCCESS: Retrieved {len(retrieved_docs)} documents with rewritten query")
                return retrieved_docs
                
            log_to_sublog(self.project_dir, "chat_handler.log", 
                        f"Strategy 1: Insufficient results ({len(retrieved_docs)}) with rewritten query")
            
        except Exception as e:
            log_to_sublog(self.project_dir, "chat_handler.log", f"Strategy 1 failed: {e}")
            retrieved_docs = []

        # Strategy 2: Try original query if rewritten didn't work well
        try:
            st.session_state.thinking_logs.append("⚠️ Trying original query...")
            update_logs(log_placeholder)
            
            log_to_sublog(self.project_dir, "preparing_full_context.log",
                        f"Strategy 2: Trying original query: '{query}'")
            
            original_docs = retriever.invoke(query)
            
            if original_docs and len(original_docs) >= 2:
                log_to_sublog(self.project_dir, "chat_handler.log", 
                            f"Strategy 2 SUCCESS: Retrieved {len(original_docs)} documents with original query")
                return original_docs
                
            # Combine results if both had some results but neither was great
            if retrieved_docs and original_docs:
                combined_docs = retrieved_docs + [doc for doc in original_docs if doc not in retrieved_docs]
                log_to_sublog(self.project_dir, "chat_handler.log", 
                            f"Strategy 2: Combined results - {len(combined_docs)} total documents")
                return combined_docs[:10]  # Limit to top 10
                
            log_to_sublog(self.project_dir, "chat_handler.log", 
                        f"Strategy 2: Insufficient results ({len(original_docs)}) with original query")
            
        except Exception as e:
            log_to_sublog(self.project_dir, "chat_handler.log", f"Strategy 2 failed: {e}")
            original_docs = []

        # Strategy 3: Extract key terms and search (last resort)
        try:
            st.session_state.thinking_logs.append("⚠️ Trying key terms extraction...")
            update_logs(log_placeholder)
            
            # Extract key terms from ORIGINAL query (not rewritten)
            key_terms = self._extract_key_terms(query)
            
            if key_terms:
                # Create focused key term query (max 3-4 terms)
                key_query = " ".join(key_terms[:4])
                
                log_to_sublog(self.project_dir, "preparing_full_context.log",
                            f"Strategy 3: Trying key terms: '{key_query}' from terms: {key_terms}")
                
                key_docs = retriever.invoke(key_query)
                
                log_to_sublog(self.project_dir, "chat_handler.log", 
                            f"Strategy 3: Retrieved {len(key_docs)} documents with key terms: {key_terms}")
                
                return key_docs
                
        except Exception as e:
            log_to_sublog(self.project_dir, "chat_handler.log", f"Strategy 3 failed: {e}")

        # Return whatever we have, even if it's not ideal
        all_docs = retrieved_docs + original_docs if retrieved_docs or original_docs else []
        final_count = len(all_docs)
        
        log_to_sublog(self.project_dir, "chat_handler.log", 
                    f"Final fallback: Returning {final_count} documents from all strategies")
        
        return all_docs[:5] if all_docs else []

    
    def _rewrite_query_with_intent(self, query, intent, log_placeholder, debug_mode):
        """Enhanced query rewriting with intent awareness."""
        try:
            st.session_state.thinking_logs.append("✏️ Rewriting query based on intent...")
            update_logs(log_placeholder)
            log_to_sublog(self.project_dir, "rewriting_queries.log",
                         f"\nOriginal: {query}\nIntent: {intent}")

            rewritten = self.rewrite_chain.invoke({
                "original": query,
                "project_type": self.project_config.project_type,
                "intent": intent
            }).content.strip()

            log_to_sublog(self.project_dir, "rewriting_queries.log",
                         f"Rewritten: {rewritten}\n")

            if debug_mode: 
                st.info(f"🔄 Rewritten query: {rewritten}")
            st.session_state.thinking_logs.append(f"✅ Query rewritten")
            update_logs(log_placeholder)
            return rewritten

        except Exception as e:
            if debug_mode:
                st.warning(f"Query rewriting failed: {e}")
            st.session_state.thinking_logs.append("⚠️ Query rewriting failed, using original")
            log_to_sublog(self.project_dir, "rewriting_queries.log",
                         f"Rewriting failed for: {query} (intent={intent}). Error: {e}\n")
            update_logs(log_placeholder)
            return query

    def _analyze_impact_with_intent(self, query, intent, log_placeholder):
        """Perform impact analysis if applicable to intent."""
        impact_files, context = [], ""
        if intent == "impact_analysis" or self._is_impact_question(query):
            st.session_state.thinking_logs.append("🔍 Performing impact analysis...")
            update_logs(log_placeholder)
            file_mentions = self._extract_file_mentions(query)
            for mention in file_mentions:
                related_files = get_impact(mention, self.project_dir)
                impact_files.extend(related_files)
            if impact_files:
                context = f"Components impacted: {', '.join(set(impact_files))}"
                st.session_state.thinking_logs.append(f"📊 {len(set(impact_files))} impacted files identified")
                update_logs(log_placeholder)
        return list(set(impact_files)), context

    def _extract_file_mentions(self, query):
        # Simple heuristic for file/class/component mentions
        exts = self.project_config.get_extensions()
        file_mentions = re.findall(r'\b[A-Z][a-zA-Z0-9_]*[a-zA-Z0-9]\b', query)
        for ext in exts:
            pat = rf'\b\w+{re.escape(ext)}\b'
            file_mentions.extend(re.findall(pat, query, re.IGNORECASE))
        return list(set(file_mentions))

    def _extract_key_terms(self, query):
        """Extract key terms from a query with better filtering for code search."""
        import re
        
        # Remove common question words and focus on content
        stop_words = {'what', 'where', 'how', 'when', 'why', 'which', 'who', 'does', 'should', 'can', 'will', 
                    'the', 'this', 'that', 'and', 'or', 'but', 'for', 'with', 'from', 'about', 'into'}
        
        # Extract potential code/file terms (preserve quotes content, camelCase, etc.)
        tokens = re.findall(r'"[^"]+"|[A-Z][a-z]+(?:[A-Z][a-z]*)*|\b\w+\b', query)
        
        key_terms = []
        for token in tokens:
            # Remove quotes but keep the content
            clean_token = token.strip('"').lower()
            
            # Keep terms that are likely code-related or important
            if (len(clean_token) > 3 and 
                clean_token not in stop_words and 
                not clean_token.isdigit()):
                key_terms.append(clean_token)
        
        # Prioritize quoted terms and camelCase terms
        quoted_terms = [t.strip('"') for t in tokens if t.startswith('"')]
        camel_case_terms = [t for t in tokens if re.match(r'^[A-Z][a-z]+(?:[A-Z][a-z]*)*$', t)]
        
        # Combine prioritized terms first
        prioritized = quoted_terms + camel_case_terms
        final_terms = prioritized + [t for t in key_terms if t not in prioritized]
    
        return final_terms[:6]  # Return top 6 terms max


    def _create_enhanced_query(self, original_query, rewritten_query, intent, impact_context, enhanced_context):
        """Original enhanced query creation method."""
        # Keep the original logic from old_chat_handler.py
        if enhanced_context:
            if intent == "overview":
                return f"""Based on this comprehensive codebase context:

{enhanced_context}

Answer this question directly and confidently: {rewritten_query}

IMPORTANT INSTRUCTIONS:
- Provide a clear, direct answer about what this project does
- Focus on the main purpose, key components, and functionality
- Use specific details from the code context provided
- Avoid phrases like "I don't know", "it appears", or "based on the provided context"
- Give a definitive answer based on the actual code structure
- If you see MainActivity, manifest files, or build configurations, use those to explain the app's purpose
- Be confident and specific about the project's functionality"""
            else:
                return f"""Based on this detailed codebase context:

{enhanced_context}

Answer this question: {rewritten_query}

Provide a clear, specific answer based on the code context. Use concrete details from the code to support your response."""
        else:
            return rewritten_query

    def _is_impact_question(self, query):
        impact_keywords = [
            "impact", "what if", "break", "affect", "change", "modify",
            "remove", "delete", "consequences", "dependencies"
        ]
        return any(k in query.lower() for k in impact_keywords)
