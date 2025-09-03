# chat_handler.py

from datetime import datetime
import streamlit as st

from index_builder import update_logs
from context.context_builder import ContextBuilder
from query.prompt_router import PromptRouter
from query.query_intent_classifier import QueryIntentClassifier
from logger import log_highlight, log_to_sublog
from config.feature_toggle_manager import FeatureToggleManager
from query.retrieval_logic import RetrievalLogic
from query.answer_validation_handler import AnswerValidationHandler

class ChatHandler:
    """
    Main chat handler for processing user queries.
    Delegates validation to AnswerValidationHandler for better separation of concerns.
    """

    def __init__(self, llm, provider, project_config, project_dir=".", rewrite_llm=None):
        self.project_dir = project_dir
        self.llm = llm
        self.project_config = project_config
        self.provider = provider
        self.rewrite_llm = rewrite_llm if rewrite_llm is not None else llm
        self.context_builder = ContextBuilder(project_config, project_dir=project_dir)
        self.query_intent_classifier = QueryIntentClassifier(project_config)
        self.retrieval_logic = RetrievalLogic(self.rewrite_llm, self.project_dir, self.project_config)
        self.validation_handler = AnswerValidationHandler(self.project_dir)

    def process_query(self, query, vectorstore, log_placeholder, debug_mode=False):
        """Enhanced query processing with comprehensive logging."""
        log_highlight("ChatHandler.process_query")
        query_start_time = datetime.now()
        st.session_state.setdefault("thinking_logs", [])

        log_to_sublog(self.project_dir, "preparing_full_context.log",
            f"\n{'='*80}\n🚀 QUERY PROCESSING START: {query_start_time.isoformat()}\n" +
            f"Query: {query}\nDebug Mode: {debug_mode}\n{'='*80}")

        st.session_state.thinking_logs.append("🧠 Starting enhanced query processing...")
        update_logs(log_placeholder)

        try:
            # Phase 1: Intent Classification
            intent, confidence = self.query_intent_classifier.classify_intent(query)
            log_to_sublog(self.project_dir, "preparing_full_context.log",
                f"🎯 PHASE 1: Intent Classification\n Intent: {intent}\n Confidence: {confidence:.2f}")
            st.session_state.thinking_logs.append(f"🎯 Detected intent: {intent} (confidence: {confidence:.2f})")
            update_logs(log_placeholder)
            
            if debug_mode:
                st.info(f"🎯 **Query Intent**: {intent} (confidence: {confidence:.2f})")

            # Check for RAG bypass
            disable_rag = st.session_state.get("disable_rag", False)
            if disable_rag:
                log_to_sublog(self.project_dir, "preparing_full_context.log",
                    "⚙️ RAG BYPASS: Sending query directly to LLM")
                st.session_state.thinking_logs.append("⚙️ RAG is disabled – sending query directly to LLM.")
                update_logs(log_placeholder)
                result = self.llm.invoke(f"User question: {query}")
                answer = getattr(result, "content", str(result))
                return answer, [], [], {"intent": intent, "confidence": confidence}

            # Phase 2: Query Processing Setup
            vectorstore = st.session_state.get("vectorstore")
            project_type = self.project_config.project_type.upper()
            from config.model_config import model_config

            rewrite_chain = model_config.create_rewrite_chain(self.rewrite_llm, intent, project_type)
            retriever = self.retrieval_logic.get_retriever(vectorstore, rewrite_chain)

            if retriever:
                st.session_state["retriever"] = retriever

            retriever_type = type(retriever).__name__
            if retriever_type == "MultiQueryRetriever":
                rewritten = query
                log_to_sublog(self.project_dir, "preparing_full_context.log",
                    "📝 PHASE 2: Skipping rewriting (Enhanced retriever will handle)")
            else:
                rewritten = self.retrieval_logic.rewrite_query(query, intent, rewrite_chain, log_placeholder, debug_mode)
                log_to_sublog(self.project_dir, "preparing_full_context.log",
                    f"📝 PHASE 2: Query Rewriting\n Original: {query}\n Rewritten: {rewritten}")

            # Phase 3: Impact Analysis
            impact_files, impact_context = self.retrieval_logic.analyze_impact(query, intent, log_placeholder)
            log_to_sublog(self.project_dir, "preparing_full_context.log",
                f"🔍 PHASE 3: Impact Analysis\n Impact Files: {len(impact_files)}\n Files: {impact_files[:5]}")

            # Phase 4: Document Retrieval
            st.session_state.thinking_logs.append("📖 Performing intelligent document retrieval...")
            update_logs(log_placeholder)
            log_to_sublog(self.project_dir, "preparing_full_context.log",
                "📖 PHASE 4: Document Retrieval\n Starting retrieval process...")

            if not retriever:
                error_msg = "No retriever found. Please rebuild the RAG index before querying."
                log_to_sublog(self.project_dir, "preparing_full_context.log", f"❌ ERROR: {error_msg}")
                st.error(f"❌ {error_msg}")
                return error_msg, [], [], {}

            log_to_sublog(self.project_dir, "preparing_full_context.log",
                f"🔍 Using Retriever Type: {retriever_type}")

            retrieved_docs = self.retrieval_logic.retrieve_with_fallback(retriever, query, rewritten, log_placeholder)
            log_to_sublog(self.project_dir, "preparing_full_context.log",
                f"✅ Retrieved {len(retrieved_docs)} documents")

            if debug_mode:
                st.info(f"📊 Retrieved {len(retrieved_docs)} chunks")

            # Phase 5: Context Building
            source_documents = retrieved_docs
            if source_documents:
                reranked_docs = self.query_intent_classifier.rerank_docs_by_intent(source_documents, query, intent)
                log_to_sublog(self.project_dir, "preparing_full_context.log",
                    f"📊 PHASE 5: Context Building\n Original docs: {len(source_documents)}\n Reranked docs: {len(reranked_docs)}")
                
                formatted_context = self.context_builder.create_full_context(reranked_docs)

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
                f"🤖 PHASE 6: Answer Generation\n Using provider: {self.provider}")

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

            if user_part:
                result = self.llm.invoke_with_system_user(sys_or_single, user_part)
            else:
                result = self.llm.invoke(sys_or_single)

            answer = getattr(result, "content", str(result))
            answer_metadata = {
                "intent": intent,
                "confidence": confidence,
                "rewritten_query": rewritten,
                "enhanced_query": None,
                "phase_3_enabled": True,
            }

            # Pipeline Diagnostics using AnswerValidationHandler
            if FeatureToggleManager.is_enabled("pipeline_diagnostics", self.project_dir):
                log_to_sublog(self.project_dir, "preparing_full_context.log",
                    "🔍 Running comprehensive pipeline diagnostics...")
                diagnosis = self.validation_handler.diagnose_quality_issue(query, rewritten, reranked_docs, answer)
                self.validation_handler.log_pipeline_diagnosis(diagnosis, query)
                
                answer_metadata["pipeline_diagnosis"] = {
                    "rewriting_issues": diagnosis["rewriting_quality"].get("rewriting_issue", False),
                    "retrieval_issues": diagnosis["retrieval_quality"].get("retrieval_issue", False),
                    "answer_quality_flag": diagnosis["answer_quality"].get("quality_flag", "unknown"),
                    "critical_fixes_count": len([f for f in diagnosis["recommended_fixes"]
                                               if isinstance(f, dict) and f.get("severity") == "critical"]),
                }

                critical_fixes = [f for f in diagnosis["recommended_fixes"]
                                if isinstance(f, dict) and f.get("severity") == "critical"]
                if critical_fixes and debug_mode:
                    st.warning("🚨 **Critical Quality Issues Detected:**")
                    for fix in critical_fixes:
                        st.write(f"- **{fix['action']}**: {fix['details']}")
                        st.caption(f"💡 **Fix**: {fix['implementation']}")

            # Answer Validation using AnswerValidationHandler
            if FeatureToggleManager.is_enabled("deepeval_validator", self.project_dir):
                log_to_sublog(self.project_dir, "preparing_full_context.log",
                    "🔍 Running answer validation...")
                validation_results = self.validation_handler.validate_answer_quality(query, answer, reranked_docs)

                if validation_results:
                    self.validation_handler.log_quality_metrics(validation_results)
                    answer_metadata.update({
                        "deepeval_validation": validation_results,
                        "deepeval_score": validation_results.get("overall_score", 0.0),
                        "quality_flag": validation_results.get("quality_flag", "unknown"),
                    })

                    overall_score = validation_results.get("overall_score", 0.0)
                    if overall_score < 0.6 and debug_mode:
                        st.warning(f"⚠️ **Answer Quality Alert**: Validation score {overall_score:.3f} below threshold.")

            # Final Logging
            query_end_time = datetime.now()
            processing_duration = (query_end_time - query_start_time).total_seconds()

            log_to_sublog(self.project_dir, "preparing_full_context.log",
                f"\n🏁 QUERY PROCESSING COMPLETE: {query_end_time.isoformat()}\n" +
                f"Total Duration: {processing_duration:.2f}s\n" +
                f"Answer Length: {len(answer)} characters\n" +
                f"Documents Used: {len(reranked_docs)}\n" +
                f"{'='*80}\n")

            st.session_state.thinking_logs.append("✅ Answer generated successfully!")
            update_logs(log_placeholder)

            return answer, reranked_docs, impact_files, answer_metadata

        except Exception as e:
            error_time = datetime.now()
            log_to_sublog(self.project_dir, "preparing_full_context.log",
                f"\n❌ QUERY PROCESSING ERROR: {error_time.isoformat()}\n" +
                f"Error: {str(e)}\nQuery: {query}\n{'='*80}\n")
            st.error(f"❌ Error processing query: {e}")
            return f"Sorry, I encountered an error while processing your query: {e}", [], [], {}
