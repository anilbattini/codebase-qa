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
        """Enhanced query processing with intent classification, rewriting, hierarchy-aware context, and RAG support."""

        # Step 0: Initialize logs
        st.session_state.thinking_logs.append("🧠 Starting enhanced query processing...")
        update_logs(log_placeholder)

        # Step 1: Classify intent
        intent, confidence = self.query_intent_classifier.classify_intent(query)
        st.session_state.thinking_logs.append(f"🎯 Detected intent: {intent} (confidence: {confidence:.2f})")
        update_logs(log_placeholder)

        if debug_mode:
            st.info(f"🎯 **Query Intent**: {intent} (confidence: {confidence:.2f})")

        disable_rag = st.session_state.get("disable_rag", False)

        if disable_rag:
            st.session_state.thinking_logs.append("⚙️ RAG is disabled – sending query directly to LLM.")
            update_logs(log_placeholder)

            # Minimal context path: skip rewriting, retrieval, context building
            rewritten = query
            impact_files, impact_context = [], ""
            enhanced_context = ""
        else:
            # Step 2: Enhanced query rewriting
            rewritten = self._rewrite_query_with_intent(query, intent, log_placeholder, debug_mode)

            # Step 3: Impact analysis (if applicable)
            impact_files, impact_context = self._analyze_impact_with_intent(query, intent, log_placeholder)

            # Step 4: Prepare retrieval hints
            query_hints = self.query_intent_classifier.get_query_context_hints(intent, query)

            # Step 5: Retrieve documents
            st.session_state.thinking_logs.append("📖 Performing intelligent document retrieval...")
            update_logs(log_placeholder)
            retriever = st.session_state.get("retriever")

            if not retriever:
                st.error("❌ No retriever found. Please rebuild the RAG index before querying.")
                return None, [], []

            try:
                retrieved_docs = retriever.invoke(rewritten)
            except Exception as e:
                st.error(f"❌ Retrieval failed: {e}")
                return "Sorry, I couldn't retrieve supporting documents.", [], []

            if debug_mode:
                st.info(f"📊 Retrieved {len(retrieved_docs)} chunks")

            # Step 6: Build final context
            st.session_state.thinking_logs.append("🏗️ Building enhanced context window...")
            update_logs(log_placeholder)

            try:
                enhanced_context = self.context_builder.build_enhanced_context(
                    query=query,
                    retrieved_docs=retrieved_docs,
                    intent=intent,
                    query_hints=query_hints
                )
            except Exception as e:
                st.error(f"❌ Context building failed: {e}")
                enhanced_context = ""

        # Step 7: Generate prompt and invoke LLM
        st.session_state.thinking_logs.append("🤖 Generating final contextual answer...")
        update_logs(log_placeholder)

        enhanced_query = self._create_enhanced_query(
            query, rewritten, intent, impact_context, enhanced_context
        )

        try:
            result = qa_chain.invoke({"query": enhanced_query})
            answer = result.get("result", "ℹ️ No answer was generated.")
            source_docs = result.get("source_documents", [])
        except Exception as e:
            st.error(f"❌ LLM failed: {e}")
            return "Sorry, something went wrong while generating the answer.", [], []

        st.session_state.thinking_logs.append("✨ Answer generated successfully!")
        update_logs(log_placeholder)

        # Step 8: Prioritize & Store in chat history
        reranked_docs = self._rerank_docs_by_intent(source_docs, query, intent)

        conversation_metadata = {
            "intent": intent,
            "confidence": confidence,
            "rewritten_query": rewritten,
            "context_hints": self.query_intent_classifier.get_query_context_hints(intent, query),
            "rag_used": not disable_rag
        }

        new_qa_key = f"qa_{len(st.session_state['chat_history'])}"
        st.session_state["chat_history"].append(
            (query, answer, reranked_docs, impact_files, conversation_metadata)
        )
        st.session_state["expand_latest"] = new_qa_key

        st.session_state.thinking_logs.append("💾 Saved to session history")
        update_logs(log_placeholder)

        if debug_mode:
            st.success("✅ Processing complete")

        return answer, reranked_docs, impact_files

    # ------------------ Helper Methods ------------------

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
            rewritten = self.rewrite_chain.invoke({
                "original": query,
                "project_type": self.project_config.project_type,
                "intent": intent
            }).content.strip()
            if debug_mode:
                st.info(f"🔄 Rewritten query: {rewritten}")
            st.session_state.thinking_logs.append(f"✅ Query rewritten")
            update_logs(log_placeholder)
            return rewritten
        except Exception as e:
            if debug_mode:
                st.warning(f"Query rewriting failed: {e}")
            st.session_state.thinking_logs.append("⚠️ Query rewriting failed, using original")
            update_logs(log_placeholder)
            return query

    def _analyze_impact_with_intent(self, query, intent, log_placeholder):
        """Perform impact analysis if applicable to intent."""
        impact_files = []
        context = ""
        if intent == "impact_analysis" or self._is_impact_question(query):
            st.session_state.thinking_logs.append("🔍 Performing impact analysis...")
            update_logs(log_placeholder)
            file_mentions = self._extract_file_mentions(query)
            for mention in file_mentions:
                related_files = get_impact(mention)
                impact_files.extend(related_files)
            if impact_files:
                context = f"Components impacted: {', '.join(set(impact_files))}"
                st.session_state.thinking_logs.append(f"📊 {len(set(impact_files))} impacted files identified")
                update_logs(log_placeholder)
        return list(set(impact_files)), context

    def _extract_file_mentions(self, query):
        file_mentions = re.findall(r'\b[A-Z][a-zA-Z0-9_]*[a-zA-Z0-9]\b', query)
        extensions = self.project_config.get_extensions()
        for ext in extensions:
            pattern = rf'\b\w+{re.escape(ext)}\b'
            file_mentions.extend(re.findall(pattern, query, re.IGNORECASE))
        return list(set(file_mentions))

    def _create_enhanced_query(self, original_query, rewritten_query, intent, impact_context, enhanced_context):
        parts = []
        parts.append(f"🧠 Intent: {intent}")
        if impact_context:
            parts.append(f"📎 Impact:\n{impact_context}")
        if enhanced_context:
            parts.append(f"📚 Context:\n{enhanced_context}")
        parts.append(f"💬 Rewritten Query:\n{rewritten_query}")
        parts.append(f"User asked:\n{original_query}")
        return "\n\n".join(parts)

    def _is_impact_question(self, query):
        impact_keywords = [
            "impact", "what if", "break", "affect", "change", "modify",
            "remove", "delete", "consequences", "dependencies"
        ]
        return any(k in query.lower() for k in impact_keywords)

    def _rerank_sources_by_intent(self, source_documents, query, intent):
        def score(doc):
            source = doc.metadata.get("source", "").lower()
            content = doc.page_content.lower()
            meta = doc.metadata
            score = 0
            for term in query.lower().split():
                if term in content:
                    score += 1
                if term in source:
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
                comp = meta.get("complexity_score", 0)
                score += comp * 0.3
            return score

        sorted_docs = sorted(source_documents, key=score, reverse=True)
        return [doc.metadata.get("source", "unknown") for doc in sorted_docs[:5]]
