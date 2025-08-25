import streamlit as st
import re
import os
from langchain.prompts import PromptTemplate
from build_rag import update_logs, get_impact
from context_builder import ContextBuilder
from query_intent_classifier import QueryIntentClassifier
from logger import log_highlight, log_to_sublog

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
        
        # # 🔧 FIX: Validate LLM connectivity
        # try:
        #     test_response = self.llm.invoke("Test connection")
        #     log_to_sublog(project_dir, "chat_handler.log", f"Main LLM test: {type(test_response)}")
        # except Exception as e:
        #     log_to_sublog(project_dir, "chat_handler.log", f"Main LLM connection failed: {e}")
        #     raise ValueError(f"Main LLM not responsive: {e}")
        
        # Always use local Ollama for rewriting
        self.rewrite_llm = rewrite_llm if rewrite_llm is not None else llm
        
        # 🔧 FIX: Test rewrite LLM
        # try:
        #     test_rewrite = self.rewrite_llm.invoke("Test rewrite")
        #     log_to_sublog(project_dir, "chat_handler.log", f"Rewrite LLM test: {type(test_rewrite)}")
        # except Exception as e:
        #     log_to_sublog(project_dir, "chat_handler.log", f"Rewrite LLM connection failed: {e}")
            
        self.rewrite_chain = self._create_rewrite_chain()
        
        self.context_builder = ContextBuilder(project_config, project_dir=project_dir)
        self.query_intent_classifier = QueryIntentClassifier(project_config)


    def _create_rewrite_chain(self):
        """Create a chain for rewriting queries to be more searchable using the dedicated rewrite LLM."""
        prompt = PromptTemplate(
            input_variables=["original", "project_type", "intent"],
            template=(
                "You are a codebase search assistant. Convert the following question into a simple, searchable query "
                "for searching a {project_type} project codebase.\n\n"
                "Intent: {intent}\nOriginal: {original}\n\n"
                "Return ONLY a concise search query (no explanations, no alternatives, no markdown). "
                "Focus on key terms that would appear in the codebase.\n\n"
                "IMPORTANT: For questions about 'what does this project do', 'project overview', or 'main purpose', "
                "include terms like: main activity, MainActivity, application, app purpose, project structure, "
                "manifest, build.gradle, README, documentation.\n\n"
                "Search Query:"
            ),
        )
        return prompt | self.rewrite_llm


    def process_query(self, query, qa_chain, log_placeholder, debug_mode=False):
        """
        Enhanced query processing with Phase 3 context.
        Returns: (answer, reranked_docs, impact_files, metadata)
        """
        log_highlight("ChatHandler.process_query")
        st.session_state.setdefault("thinking_logs", [])
        st.session_state.thinking_logs.append("🧠 Starting enhanced query processing...")
        update_logs(log_placeholder)
        log_to_sublog(self.project_dir, "chat_handler.log", f"Starting query processing: {query}")

        try:
            # Phase 1: Intent
            intent, confidence = self.query_intent_classifier.classify_intent(query)
            st.session_state.thinking_logs.append(f"🎯 Detected intent: {intent} (confidence: {confidence:.2f})")
            update_logs(log_placeholder)
            log_to_sublog(self.project_dir, "chat_handler.log", f"Intent classification: {intent} (confidence: {confidence:.2f})")
            if debug_mode:
                st.info(f"🎯 **Query Intent**: {intent} (confidence: {confidence:.2f})")

            # Optional bypass
            disable_rag = st.session_state.get("disable_rag", False)
            if disable_rag:
                st.session_state.thinking_logs.append("⚙️ RAG is disabled – sending query directly to LLM.")
                update_logs(log_placeholder)
                log_to_sublog(self.project_dir, "chat_handler.log", "RAG disabled - sending query directly to LLM")
                result = self.llm.invoke(f"User question: {query}")
                answer = getattr(result, "content", str(result))
                return answer, [], [], {"intent": intent, "confidence": confidence}

            # Phase 2: Rewriting (local Ollama)
            rewritten = self._rewrite_query_with_intent(query, intent, log_placeholder, debug_mode)
            log_to_sublog(self.project_dir, "chat_handler.log", f"Query rewritten: '{query}' -> '{rewritten}'")

            # Phase 3: Impact analysis
            impact_files, impact_context = self._analyze_impact_with_intent(query, intent, log_placeholder)
            if impact_files:
                log_to_sublog(self.project_dir, "chat_handler.log", f"Impact analysis: {len(impact_files)} files affected")

            # Phase 4: Retrieval (existing retriever)
            st.session_state.thinking_logs.append("📖 Performing intelligent document retrieval...")
            update_logs(log_placeholder)
            log_to_sublog(self.project_dir, "chat_handler.log", "Starting document retrieval...")

            retriever = st.session_state.get("retriever")
            if not retriever:
                st.error("❌ No retriever found. Please rebuild the RAG index before querying.")
                log_to_sublog(self.project_dir, "chat_handler.log", "ERROR: No retriever found")
                return "Please rebuild the RAG index before querying.", [], [], {}

            retrieved_docs = self._retrieve_with_fallback(retriever, query, rewritten, log_placeholder)
            if debug_mode:
                st.info(f"📊 Retrieved {len(retrieved_docs)} chunks")

            # Phase 5: Build Phase 3 enhanced context
            st.session_state.thinking_logs.append("🏗️ Building enhanced context window...")
            update_logs(log_placeholder)
            log_to_sublog(self.project_dir, "chat_handler.log", "Building enhanced context window...")
            
             # Rerank and metadata
            source_documents = retrieved_docs
            if source_documents:
                reranked_docs = self._rerank_docs_by_intent(source_documents, query, intent)
                log_to_sublog(self.project_dir, "chat_handler.log", f"Documents reranked by intent: {len(reranked_docs)} documents")
            else:
                reranked_docs = []
                log_to_sublog(self.project_dir, "chat_handler.log", "No source documents to rerank")

            try:
                enhanced_context = self.context_builder.build_enhanced_context(reranked_docs, query, intent)
                formatted_context = self.context_builder.format_context_for_llm(enhanced_context)
                log_to_sublog(self.project_dir, "chat_handler.log", f"Phase 3 enhanced context built: {len(formatted_context)} characters")
            except Exception as e:
                log_to_sublog(self.project_dir, "chat_handler.log", f"Phase 3 context building failed, using fallback: {e}")
                formatted_context = ""

            # Phase 6: Generate final answer with provider-specific prompt handling
            st.session_state.thinking_logs.append("🤖 Generating answer...")
            update_logs(log_placeholder)
            log_to_sublog(self.project_dir, "chat_handler.log", "Generating final answer...")

            
            if self.provider == 'cloud' and hasattr(self.llm, 'invoke_with_system_user'):
                # 🎯 CLOUD: Direct system/user separation with crystal clear task definition
                system_prompt = (
                    "You are a senior codebase analyst. Your task is to answer questions about software projects using only the provided code context.\n\n"
                    "IMPORTANT RULES:\n"
                    "- Answer the user's question directly and specifically\n"
                    "- Use ONLY the code context provided - do not invent or assume information\n" 
                    "- Cite specific files or code snippets when explaining\n"
                    "- If insufficient context is provided, state this clearly\n"
                    "- Focus on answering the actual question, not analyzing the prompt structure\n"
                    "- Be concise and practical in your response"
                )
                
                user_prompt = (
                    f"QUESTION: {query}\n\n"
                    f"CONTEXT TO USE:\n{formatted_context}\n\n"
                    f"Based on the code context above, please answer the question: {query}"
                )
                
                result = self.llm.invoke_with_system_user(system_prompt, user_prompt)
                answer = getattr(result, "content", str(result))
            
            else:
                # 🎯 OLLAMA + CLOUD FALLBACK: Clearer single prompt structure
                final_prompt = PromptTemplate(
                    input_variables=["context", "query"],
                    template=(
                        "You are a senior codebase analyst answering questions about software projects.\n\n"
                        "QUESTION: {query}\n\n"
                        "CODE CONTEXT:\n{context}\n\n"
                        "INSTRUCTIONS:\n"
                        "- Answer the question directly using the code context provided\n"
                        "- Cite specific files or code when explaining\n"
                        "- If context is insufficient, say so clearly\n"
                        "- Be practical and concise\n\n"
                        "ANSWER:"
                    ),
                )
                
                final_chain = final_prompt | self.llm
                result = final_chain.invoke({
                    "context": formatted_context,
                    "query": query,
                })
                answer = getattr(result, "content", str(result))

            st.session_state.thinking_logs.append("✅ Answer generated successfully!")
            update_logs(log_placeholder)
            log_to_sublog(self.project_dir, "chat_handler.log", "Query processing completed successfully")

            metadata = {
                "intent": intent,
                "confidence": confidence,
                "rewritten_query": rewritten,
                "enhanced_query": None,  # superseded by structured prompt
                "phase_3_enabled": True,
            }
            return answer, reranked_docs, impact_files, metadata

        except Exception as e:
            st.error(f"❌ Error processing query: {e}")
            log_to_sublog(self.project_dir, "chat_handler.log", f"Error processing query: {e}")
            return f"Sorry, I encountered an error while processing your query: {e}", [], [], {}


    def _retrieve_with_fallback(self, retriever, query, rewritten, log_placeholder):
        """Retrieve documents with multiple fallback strategies."""
        try:
            # Try with rewritten query first
            retrieved_docs = retriever.invoke(rewritten)
            log_to_sublog(self.project_dir, "chat_handler.log", f"Retrieved {len(retrieved_docs)} documents with rewritten query")
            
            # If no results, try with original query as fallback
            if not retrieved_docs:
                st.session_state.thinking_logs.append("⚠️ No results with rewritten query, trying original...")
                update_logs(log_placeholder)
                retrieved_docs = retriever.invoke(query)
                log_to_sublog(self.project_dir, "chat_handler.log", f"Retrieved {len(retrieved_docs)} documents with original query")
            
            # If still no results, try with key terms
            if not retrieved_docs:
                st.session_state.thinking_logs.append("⚠️ No results, trying with key terms...")
                update_logs(log_placeholder)
                key_terms = self._extract_key_terms(query)
                if key_terms:
                    key_query = " ".join(key_terms)
                    retrieved_docs = retriever.invoke(key_query)
                    log_to_sublog(self.project_dir, "chat_handler.log", f"Retrieved {len(retrieved_docs)} documents with key terms: {key_terms}")
            
            return retrieved_docs
            
        except Exception as e:
            st.error(f"❌ Retrieval failed: {e}")
            log_to_sublog(self.project_dir, "chat_handler.log", f"Retrieval failed: {e}")
            return []

    def _create_enhanced_query_v2(self, original_query, rewritten_query, intent, impact_context, phase3_context):
        """Create final-answer prompt content with Phase 3 context."""
        return f"""You are a senior codebase analyst. Answer ONLY using the Context below.

    === Context ===
    {phase3_context if phase3_context else "(no additional context)"}

    === Original Query ===
    {original_query}

    === Rewritten Query ===
    {rewritten_query}

    === Intent ===
    {intent}

    {("=== Impact ===\n" + impact_context) if impact_context else ""}

    Instructions:
    - Use the Context strictly; do not invent facts or generalities.
    - Cite specific files/chunks from the Context when explaining.
    - If the Context lacks enough information, say: "Insufficient context to answer precisely."
    - Provide a concise, definitive answer tailored to the intent.

    Now provide the answer:"""
    
    def _rerank_docs_by_intent(self, source_documents, query, intent):
        """Rerank and return actual Document objects (not file name strings)."""
        def score(doc):
            source = doc.metadata.get("source", "").lower()
            content = doc.page_content.lower()
            meta = doc.metadata
            score = 0
            
            for token in query.lower().split():
                if token in content:
                    score += 1
                if token in source:
                    score += 0.5
            
            if intent == "overview":
                if any(pf in source for pf in self.project_config.get_priority_files()):
                    score += 5
            elif intent == "business_logic":
                score += len(meta.get("business_logic_indicators", [])) * 2
                if meta.get("validation_rules"):
                    score += 3
            elif intent == "ui_flow":
                score += len(meta.get("ui_elements", [])) * 2
            elif intent == "technical":
                if meta.get("chunk_hierarchy") == "function":
                    score += 4
                score += meta.get("complexity_score", 0) * 0.3
            
            return score
        
        sorted_docs = sorted(source_documents, key=score, reverse=True)
        return sorted_docs[:5]

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
        """Extract key terms from a query using a simple tokenizer."""
        tokens = re.findall(r'\b\w+\b', query.lower())
        return [t for t in tokens if len(t) > 3 and not t.isdigit()]

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
