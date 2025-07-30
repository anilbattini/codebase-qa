# chat_handler.py (Enhanced Complete Version)

import streamlit as st
import re
from langchain.prompts import PromptTemplate
from build_rag import update_logs, get_impact
from query_intent_classifier import QueryIntentClassifier
from context_builder import ContextBuilder

class ChatHandler:
    """Enhanced chat processing with intent classification and better context building."""
    
    def __init__(self, llm, project_config):
        self.llm = llm
        self.project_config = project_config
        self.query_intent_classifier = QueryIntentClassifier(project_config)
        self.context_builder = ContextBuilder(project_config)
        self.rewrite_chain = self._create_rewrite_chain()
    
    def _create_rewrite_chain(self):
        """Create the enhanced query rewriting chain."""
        prompt = PromptTemplate(
            input_variables=["original", "project_type", "intent"],
            template=(
                "You are a codebase analysis assistant. Rephrase the following question to be more specific "
                "and better suited for searching through a {project_type} project codebase.\n\n"
                "Query Intent: {intent}\n"
                "Original Question: {original}\n\n"
                "Improved Question (be specific and include relevant technical terms):"
            )
        )
        return prompt | self.llm
    
    def process_query(self, query, qa_chain, log_placeholder, debug_mode=False):
        """Enhanced query processing with intent classification and better context."""
        
        # Initialize thinking logs
        st.session_state.thinking_logs.append("🧠 Starting enhanced query processing...")
        update_logs(log_placeholder)
        
        # Step 1: Classify query intent
        intent, confidence = self.query_intent_classifier.classify_intent(query)
        
        st.session_state.thinking_logs.append(
            f"🎯 Detected intent: {intent} (confidence: {confidence:.2f})"
        )
        update_logs(log_placeholder)
        
        if debug_mode:
            st.info(f"🎯 **Query Intent**: {intent} (confidence: {confidence:.2f})")
        
        # Get context hints based on intent
        query_hints = self.query_intent_classifier.get_query_context_hints(intent, query)
        
        # Step 2: Enhanced query rewriting
        rewritten = self._rewrite_query_with_intent(query, intent, log_placeholder, debug_mode)
        
        # Step 3: Impact analysis (if applicable)
        impact_files, impact_context = self._analyze_impact_with_intent(
            query, intent, log_placeholder
        )
        
        # Step 4: Enhanced document retrieval
        st.session_state.thinking_logs.append("📖 Performing intelligent document retrieval...")
        update_logs(log_placeholder)
        
        # Get retriever and perform search
        retriever = st.session_state.get("retriever")
        if not retriever:
            st.error("No retriever available. Please rebuild the RAG index.")
            return None, [], []
        
        # Retrieve documents using the rewritten query
        retrieved_docs = retriever.invoke(rewritten)
        
        if debug_mode:
            st.info(f"📊 Retrieved {len(retrieved_docs)} documents")
        
        # Step 5: Build enhanced context
        st.session_state.thinking_logs.append("🏗️ Building enhanced context...")
        update_logs(log_placeholder)
        
        enhanced_context = self.context_builder.build_enhanced_context(
            query, retrieved_docs, intent, query_hints
        )
        
        # Step 6: Generate answer with enhanced context
        st.session_state.thinking_logs.append("🤖 Generating contextual answer...")
        update_logs(log_placeholder)
        
        # Create enhanced prompt
        enhanced_query = self._create_enhanced_query(
            query, rewritten, intent, impact_context, enhanced_context
        )
        
        # Generate answer
        try:
            result = qa_chain.invoke({"query": enhanced_query})
        except Exception as e:
            st.error(f"Error generating answer: {e}")
            return "Sorry, I encountered an error while processing your query.", [], []
        
        st.session_state.thinking_logs.append("✨ Enhanced answer generated successfully!")
        update_logs(log_placeholder)
        
        # Process and store results
        answer = result["result"]
        sources = self._rerank_sources_by_intent(
            result.get("source_documents", []), query, intent
        )
        
        # Store conversation with metadata
        conversation_metadata = {
            "intent": intent,
            "confidence": confidence,
            "rewritten_query": rewritten,
            "context_hints": query_hints
        }
        
        new_qa_key = f"qa_{len(st.session_state['chat_history'])}"
        st.session_state["chat_history"].append((
            query, answer, sources, impact_files, conversation_metadata
        ))
        st.session_state["expand_latest"] = new_qa_key
        
        st.session_state.thinking_logs.append("💾 Enhanced conversation saved to history")
        update_logs(log_placeholder)
        
        if debug_mode:
            st.success(f"✅ **Processing Complete**")
        
        return answer, sources, impact_files
    
    def _rewrite_query_with_intent(self, query, intent, log_placeholder, debug_mode):
        """Enhanced query rewriting with intent awareness."""
        try:
            st.session_state.thinking_logs.append("✏️ Rewriting query with intent awareness...")
            update_logs(log_placeholder)
            
            rewritten = self.rewrite_chain.invoke({
                "original": query,
                "project_type": self.project_config.project_type,
                "intent": intent
            }).content.strip()
            
            if debug_mode:
                st.info(f"🔄 **Rewritten query**: {rewritten}")
            
            st.session_state.thinking_logs.append(f"✅ Query enhanced: {rewritten[:50]}...")
            update_logs(log_placeholder)
            
            return rewritten
            
        except Exception as e:
            if debug_mode:
                st.warning(f"Query rewriting failed: {e}")
            st.session_state.thinking_logs.append("⚠️ Using original query (rewriting failed)")
            update_logs(log_placeholder)
            return query
    
    def _analyze_impact_with_intent(self, query, intent, log_placeholder):
        """Enhanced impact analysis based on intent."""
        impact_files = []
        context = ""
        
        # Enhanced impact analysis for specific intents
        if intent == "impact_analysis" or self._is_impact_question(query):
            st.session_state.thinking_logs.append("🔍 Performing detailed impact analysis...")
            update_logs(log_placeholder)
            
            # Extract file/component mentions from query
            file_mentions = self._extract_file_mentions(query)
            
            for mention in file_mentions:
                related_files = get_impact(mention)
                impact_files.extend(related_files)
            
            if impact_files:
                impact_text = (
                    f"Components that may be impacted: {', '.join(set(impact_files))}\n\n"
                )
                context = impact_text
                
                st.session_state.thinking_logs.append(
                    f"📊 Found {len(set(impact_files))} potentially impacted components"
                )
                update_logs(log_placeholder)
        
        return list(set(impact_files)), context
    
    def _extract_file_mentions(self, query):
        """Extract potential file or component mentions from query."""
        # Look for capitalized words that might be file/class names
        file_mentions = re.findall(r'\b[A-Z][a-zA-Z0-9_]*[a-zA-Z0-9]\b', query)
        
        # Look for words with file extensions
        extensions = self.project_config.get_extensions()
        for ext in extensions:
            pattern = rf'\b\w+{re.escape(ext)}\b'
            file_mentions.extend(re.findall(pattern, query, re.IGNORECASE))
        
        return list(set(file_mentions))
    
    def _create_enhanced_query(self, original_query, rewritten_query, intent, impact_context, enhanced_context):
        """Create enhanced query with all context."""
        parts = []
        
        # Add intent context
        parts.append(f"Query Intent: {intent}")
        
        # Add impact context if available
        if impact_context:
            parts.append(f"Impact Analysis:\n{impact_context}")
        
        # Add enhanced context
        parts.append(enhanced_context)
        
        # Add the actual query
        parts.append(f"User Question: {original_query}")
        parts.append(f"Enhanced Question: {rewritten_query}")
        
        return "\n\n".join(parts)
    
    def _is_impact_question(self, query):
        """Check if the query is about impact analysis."""
        impact_keywords = [
            "impact", "what if", "break", "affect", "change", "modify", 
            "remove", "delete", "consequences", "dependencies"
        ]
        return any(keyword in query.lower() for keyword in impact_keywords)
    
    def _rerank_sources_by_intent(self, source_documents, query, intent):
        """Enhanced source reranking based on intent and project priorities."""
        def calculate_priority_score(doc):
            source = doc.metadata.get("source", "").lower()
            content = doc.page_content.lower()
            metadata = doc.metadata
            
            score = 0
            
            # Base query relevance
            query_terms = query.lower().split()
            for term in query_terms:
                if term in content:
                    score += 1
                if term in source:
                    score += 0.5
            
            # Intent-specific scoring
            if intent == "overview":
                priority_files = self.project_config.get_priority_files()
                if any(pf in source for pf in priority_files):
                    score += 5
                if metadata.get('chunk_hierarchy') in ['module', 'class']:
                    score += 3
                    
            elif intent == "business_logic":
                business_indicators = metadata.get('business_logic_indicators', [])
                score += len(business_indicators) * 2
                if metadata.get('validation_rules'):
                    score += 3
                    
            elif intent == "ui_flow":
                ui_elements = metadata.get('ui_elements', [])
                score += len(ui_elements) * 1.5
                if metadata.get('screen_references'):
                    score += 4
                    
            elif intent == "technical":
                if metadata.get('chunk_hierarchy') == 'function':
                    score += 3
                complexity = metadata.get('complexity_score', 0)
                score += complexity * 0.5
            
            # Project-specific priorities
            priority_extensions = self.project_config.config.get("priority_extensions", [])
            if any(source.endswith(ext) for ext in priority_extensions):
                score += 2
            
            return score
        
        return sorted(source_documents, key=calculate_priority_score, reverse=True)
