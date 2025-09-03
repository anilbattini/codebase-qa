# retrieval_logic.py

import json
import os
import streamlit as st
import re
from typing import List

from index_builder import update_logs
from logger import log_highlight, log_to_sublog
from config.feature_toggle_manager import FeatureToggleManager

class RetrievalLogic:
    """
    Handles all retrieval-related operations including query rewriting,
    document retrieval, impact analysis, and retriever setup.
    """
    
    def __init__(self, rewrite_llm, project_dir, project_config):
        self.rewrite_llm = rewrite_llm
        self.project_dir = project_dir
        self.project_config = project_config

    def create_enhanced_retriever(self, base_retriever, rewrite_chain):
        """Fixed MultiQueryRetriever - access LLM correctly from RunnableSequence."""
        try:
            from langchain.retrievers.multi_query import MultiQueryRetriever
            from langchain.prompts import PromptTemplate
            from langchain.schema import BaseOutputParser
            from langchain.chains import LLMChain

            class QueryListParser(BaseOutputParser):
                def parse(self, text: str) -> list:
                    if isinstance(text, str):
                        content = text.strip()
                    elif hasattr(text, 'content'):
                        content = text.content.strip()
                    else:
                        content = str(text).strip()

                    lines = [line.strip().strip("'\"") for line in content.split('\n') if line.strip()]
                    queries = []
                    for line in lines:
                        clean_line = re.sub(r'^[\d\.\-\*\+:\s]+', '', line).strip()
                        if len(clean_line) > 3:
                            queries.append(clean_line)
                    return queries[:2] if queries else ["search terms"]

            multi_qa_prompt = PromptTemplate(
                input_variables=["question"],
                template="Generate 2 search variations for: {question}\nEach on new line:"
            )

            llm_chain = LLMChain(
                prompt=rewrite_chain.first,
                llm=rewrite_chain.last,
                output_parser=QueryListParser()
            )

            enhanced_retriever = MultiQueryRetriever(
                retriever=base_retriever,
                llm_chain=llm_chain,
                max_queries=2
            )

            test_docs = enhanced_retriever.get_relevant_documents("test query")
            log_to_sublog(self.project_dir, "preparing_full_context.log",
                f"✅ Enhanced retriever working: {len(test_docs)} docs")
            
            return enhanced_retriever

        except Exception as e:
            log_to_sublog(self.project_dir, "preparing_full_context.log",
                f"❌ Enhanced retriever failed: {e}")
            return None

    def get_retriever(self, vectorstore, rewrite_chain):
        """Get retriever with enhanced features if enabled."""
        project_dir_for_toggle = self.project_dir if self.project_dir else "."
        base_retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 15})

        if FeatureToggleManager.is_enabled("langchain_retriever", project_dir_for_toggle):
            enhanced_retriever = self.create_enhanced_retriever(base_retriever, rewrite_chain)
            if enhanced_retriever:
                return enhanced_retriever
            else:
                log_to_sublog(self.project_dir, "preparing_full_context.log",
                    "🏠 Falling back to legacy retriever due to enhanced failure")

        log_to_sublog(self.project_dir, "preparing_full_context.log",
            "🏠 Using legacy Chroma retriever")
        return base_retriever

    def retrieve_with_fallback(self, retriever, query, rewritten, log_placeholder):
        """Retrieve documents with multiple fallback strategies."""
        try:
            log_to_sublog(self.project_dir, "preparing_full_context.log",
                f"Strategy 1: Trying rewritten query: '{rewritten}'")
            retrieved_docs = retriever.invoke(rewritten)
            
            if retrieved_docs and len(retrieved_docs) >= 2:
                log_to_sublog(self.project_dir, "chat_handler.log",
                    f"Strategy 1 SUCCESS: Retrieved {len(retrieved_docs)} documents with rewritten query")
                return retrieved_docs
                
            log_to_sublog(self.project_dir, "chat_handler.log",
                f"Strategy 1: Insufficient results ({len(retrieved_docs)}) with rewritten query")
        except Exception as e:
            log_to_sublog(self.project_dir, "chat_handler.log", f"Strategy 1 failed: {e}")
            retrieved_docs = []

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

            if retrieved_docs and original_docs:
                combined_docs = retrieved_docs + [doc for doc in original_docs if doc not in retrieved_docs]
                log_to_sublog(self.project_dir, "chat_handler.log",
                    f"Strategy 2: Combined results - {len(combined_docs)} total documents")
                return combined_docs[:10]

            log_to_sublog(self.project_dir, "chat_handler.log",
                f"Strategy 2: Insufficient results ({len(original_docs)}) with original query")
        except Exception as e:
            log_to_sublog(self.project_dir, "chat_handler.log", f"Strategy 2 failed: {e}")
            original_docs = []

        try:
            st.session_state.thinking_logs.append("⚠️ Trying key terms extraction...")
            update_logs(log_placeholder)
            key_terms = self.extract_key_terms(query)
            if key_terms:
                key_query = " ".join(key_terms[:4])
                log_to_sublog(self.project_dir, "preparing_full_context.log",
                    f"Strategy 3: Trying key terms: '{key_query}' from terms: {key_terms}")
                key_docs = retriever.invoke(key_query)
                log_to_sublog(self.project_dir, "chat_handler.log",
                    f"Strategy 3: Retrieved {len(key_docs)} documents with key terms: {key_terms}")
                return key_docs
        except Exception as e:
            log_to_sublog(self.project_dir, "chat_handler.log", f"Strategy 3 failed: {e}")

        all_docs = retrieved_docs + original_docs if retrieved_docs or original_docs else []
        final_count = len(all_docs)
        log_to_sublog(self.project_dir, "chat_handler.log",
            f"Final fallback: Returning {final_count} documents from all strategies")
        return all_docs[:5] if all_docs else []

    def rewrite_query(self, query, intent, rewrite_chain, log_placeholder, debug_mode):
        """Enhanced query rewriting with intent awareness."""
        try:
            st.session_state.thinking_logs.append("✏️ Rewriting query based on intent...")
            update_logs(log_placeholder)
            log_to_sublog(self.project_dir, "rewriting_queries.log",
                f"\nOriginal: {query}\nIntent: {intent}")

            rewritten = rewrite_chain.invoke({
                "question": query,
            }).content.strip()

            log_to_sublog(self.project_dir, "rewriting_queries.log",
                f"Rewritten: {rewritten}\n")

            if debug_mode:
                st.info(f"🔄 Rewritten query: {rewritten}")
            
            st.session_state.thinking_logs.append("✅ Query rewritten")
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
        
    def get_impact(self, file_name: str, project_config) -> List[str]:
        """Get impact analysis for a file."""
        relationship_file = project_config.get_metadata_file()
        if not os.path.exists(relationship_file):
            return []

        try:
            with open(relationship_file) as f:
                code_map = json.load(f)
            normalized_file_name = project_config.normalize_path_for_storage(file_name)
            impacted = set()
            todo = {normalized_file_name}
            while todo:
                current_file = todo.pop()
                for dependant, deps in code_map.items():
                    if current_file in deps and dependant not in impacted:
                        impacted.add(dependant)
                        todo.add(dependant)
            return list(impacted)
        except Exception as e:
            log_highlight(f"Error in impact analysis: {e}")
            return []

    def analyze_impact(self, query, intent, log_placeholder):
        """Perform impact analysis if applicable to intent."""
        impact_files, context = [], ""
        if intent == "impact_analysis" or self.is_impact_question(query):
            st.session_state.thinking_logs.append("🔍 Performing impact analysis...")
            update_logs(log_placeholder)
            
            file_mentions = self.extract_file_mentions(query)
            for mention in file_mentions:
                related_files = self.get_impact(mention, self.project_config)
                impact_files.extend(related_files)
            
            if impact_files:
                context = f"Components impacted: {', '.join(set(impact_files))}"
                st.session_state.thinking_logs.append(f"📊 {len(set(impact_files))} impacted files identified")
                update_logs(log_placeholder)
        
        return list(set(impact_files)), context

    def extract_file_mentions(self, query):
        """Extract file/class/component mentions from query."""
        exts = self.project_config.get_extensions()
        file_mentions = re.findall(r'\b[A-Z][a-zA-Z0-9_]*[a-zA-Z0-9]\b', query)
        
        for ext in exts:
            pat = rf'\b\w+{re.escape(ext)}\b'
            file_mentions.extend(re.findall(pat, query, re.IGNORECASE))
        
        return list(set(file_mentions))

    def extract_key_terms(self, query):
        """Extract key terms from a query with better filtering for code search."""
        stop_words = {'what', 'where', 'how', 'when', 'why', 'which', 'who', 'does', 'should', 'can', 'will',
                     'the', 'this', 'that', 'and', 'or', 'but', 'for', 'with', 'from', 'about', 'into'}

        tokens = re.findall(r'"[^"]+"|[A-Z][a-z]+(?:[A-Z][a-z]*)*|\b\w+\b', query)
        key_terms = []
        
        for token in tokens:
            clean_token = token.strip('"').lower()
            if (len(clean_token) > 3 and
                clean_token not in stop_words and
                not clean_token.isdigit()):
                key_terms.append(clean_token)

        quoted_terms = [t.strip('"') for t in tokens if t.startswith('"')]
        camel_case_terms = [t for t in tokens if re.match(r'^[A-Z][a-z]+(?:[A-Z][a-z]*)*$', t)]
        
        prioritized = quoted_terms + camel_case_terms
        final_terms = prioritized + [t for t in key_terms if t not in prioritized]
        
        return final_terms[:6]

    def is_impact_question(self, query):
        """Check if query is asking about impact analysis."""
        impact_keywords = [
            "impact", "what if", "break", "affect", "change", "modify",
            "remove", "delete", "consequences", "dependencies"
        ]
        return any(k in query.lower() for k in impact_keywords)
