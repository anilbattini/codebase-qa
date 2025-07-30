# chat_handler.py

import streamlit as st
import re
from langchain.prompts import PromptTemplate
from build_rag import update_logs, get_impact

class ChatHandler:
    """Handles chat processing logic including query rewriting and answer generation."""
    
    def __init__(self, llm, project_config):
        self.llm = llm
        self.project_config = project_config
        self.rewrite_chain = self._create_rewrite_chain()
    
    def _create_rewrite_chain(self):
        """Create the query rewriting chain."""
        prompt = PromptTemplate(
            input_variables=["original"],
            template=(
                "Rephrase or clarify the following software engineering question so it's best suited "
                "for a codebase-aware assistant:\n\nUser Query: {original}\n\nBetter:"
            )
        )
        return prompt | self.llm
    
    def process_query(self, query, qa_chain, log_placeholder, debug_mode=False):
        """Process a user query and return the response."""
        # Real-time thinking logs
        st.session_state.thinking_logs.append("🧠 Starting to process your question...")
        update_logs(log_placeholder)
        
        # Question rewriting
        rewritten = self._rewrite_query(query, log_placeholder, debug_mode)
        
        # Impact analysis
        impact_files, context = self._analyze_impact(query, log_placeholder)
        
        # Document retrieval
        st.session_state.thinking_logs.append("📖 Searching through your codebase...")
        update_logs(log_placeholder)
        
        # Generate answer
        st.session_state.thinking_logs.append("🤖 Generating answer using AI...")
        update_logs(log_placeholder)
        
        result = qa_chain.invoke({"query": context + rewritten})
        
        st.session_state.thinking_logs.append("✨ Answer generated successfully!")
        update_logs(log_placeholder)
        
        # Process and store results
        answer = result["result"]
        sources = self._rerank_sources(result.get("source_documents", []), query)
        
        # Store conversation
        new_qa_key = f"qa_{len(st.session_state['chat_history'])}"
        st.session_state["chat_history"].append((query, answer, sources, impact_files))
        st.session_state["expand_latest"] = new_qa_key
        
        st.session_state.thinking_logs.append("💾 Conversation saved to history")
        update_logs(log_placeholder)
        
        return answer, sources, impact_files
    
    def _rewrite_query(self, query, log_placeholder, debug_mode):
        """Rewrite the query for better understanding."""
        try:
            st.session_state.thinking_logs.append("✏️ Rewriting query for better understanding...")
            update_logs(log_placeholder)
            
            rewritten = self.rewrite_chain.invoke({"original": query}).content.strip()
            if debug_mode:
                st.info(f"🔄 Rewritten query: {rewritten}")
            
            st.session_state.thinking_logs.append(f"✅ Query rewritten: {rewritten[:50]}...")
            update_logs(log_placeholder)
            
            return rewritten
            
        except Exception as e:
            if debug_mode:
                st.warning(f"Query rewriting failed: {e}")
            st.session_state.thinking_logs.append("⚠️ Using original query (rewriting failed)")
            update_logs(log_placeholder)
            return query
    
    def _analyze_impact(self, query, log_placeholder):
        """Analyze potential file impacts."""
        impact_files = []
        context = ""
        
        if self._is_impact_question(query):
            st.session_state.thinking_logs.append("🔍 Analyzing potential file impacts...")
            update_logs(log_placeholder)
            
            priority_extensions = self.project_config.config.get("priority_extensions", [])
            pattern = r"[\w\-/\.]+(?:" + "|".join(priority_extensions).replace(".", r"\.") + ")"
            match = re.search(pattern, query)
            
            if match:
                target_file = match.group(0)
                impact_files = get_impact(target_file)
                impact_text = (
                    f"Files that may be impacted if `{target_file}` changes: " +
                    (", ".join(impact_files) if impact_files else "None found.")
                )
                context = f"{impact_text}\n\n"
                st.session_state.thinking_logs.append(f"📊 Found {len(impact_files)} potentially impacted files")
                update_logs(log_placeholder)
        
        return impact_files, context
    
    def _is_impact_question(self, query):
        """Check if the query is about impact analysis."""
        return any(keyword in query.lower() for keyword in ["impact", "what if", "break"])
    
    def _rerank_sources(self, source_documents, query):
        """Rerank source documents based on relevance and project priorities."""
        def priority_score(doc):
            source = doc.metadata.get("source", "").lower()
            content = doc.page_content.lower()
            
            priority_bonus = 0
            priority_files = self.project_config.get_priority_files()
            priority_extensions = self.project_config.config.get("priority_extensions", [])
            
            # Boost files that match priority patterns
            if any(pf in source for pf in priority_files):
                priority_bonus = 3
            elif any(source.endswith(ext) for ext in priority_extensions):
                priority_bonus = 2
                
            # Penalize utility files for project questions
            if source.endswith(".py") and self.project_config.project_type != "python" and any(word in query.lower() for word in ["project", "app", "what"]):
                priority_bonus = -2
                
            # Query relevance
            query_match = sum(1 for word in query.lower().split() if word in content)
            
            return priority_bonus + query_match
        
        return sorted(source_documents, key=priority_score, reverse=True)
