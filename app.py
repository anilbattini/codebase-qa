# app.py

import streamlit as st
from build_rag import build_rag, update_logs, get_impact
from langchain_ollama import ChatOllama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from config import ProjectConfig

st.set_page_config(page_title="🧠 Codebase Q&A", layout="wide")
st.title("💬 Chat with Your Codebase")

# Sidebar Configuration
with st.sidebar:
    st.header("🔧 Configuration")
    project_dir = st.text_input("📁 Project Directory", value=".")

    # Project type selection
    project_types = ["auto-detect"] + list(ProjectConfig.LANGUAGE_CONFIGS.keys())
    selected_type = st.selectbox("🎯 Project Type", project_types, index=0)
    project_type = None if selected_type == "auto-detect" else selected_type

    ollama_model = st.text_input("🧠 Ollama Model", value="llama3.1")
    ollama_endpoint = st.text_input("🔗 Ollama Endpoint", value="http://127.0.0.1:11434")
    force_rebuild = st.button("🔁 Rebuild Index")

    # Debug mode toggle
    st.divider()
    debug_mode = st.checkbox("🔧 Enable Debug Mode", help="Show debugging tools and detailed logs")

# Session state initialization
st.session_state.setdefault("retriever", None)
st.session_state.setdefault("project_dir_used", None)
st.session_state.setdefault("thinking_logs", [])
st.session_state.setdefault("qa_chain", None)
st.session_state.setdefault("chat_history", [])

# Initialize project config
project_config = ProjectConfig(project_type) if project_type else ProjectConfig()

log_placeholder = st.empty()
should_rebuild = (
        st.session_state["retriever"] is None or
        st.session_state["project_dir_used"] != project_dir or
        force_rebuild
)

# Model & chain setup
llm = ChatOllama(model=ollama_model, base_url=ollama_endpoint)

def get_rewrite_chain(llm):
    prompt = PromptTemplate(
        input_variables=["original"],
        template=(
            "Rephrase or clarify the following software engineering question so it's best suited "
            "for a codebase-aware assistant:\n\nUser Query: {original}\n\nBetter:"
        )
    )
    return prompt | llm

# Build RAG
if should_rebuild:
    with st.spinner("🔄 Building RAG index..."):
        retriever = build_rag(
            project_dir=project_dir,
            ollama_model=ollama_model,
            ollama_endpoint=ollama_endpoint,
            log_placeholder=log_placeholder,
            project_type=project_type
        )
        st.session_state["retriever"] = retriever
        st.session_state["project_dir_used"] = project_dir
        st.session_state["qa_chain"] = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            return_source_documents=True
        )

# Initialize rewrite chain
rewrite_chain = get_rewrite_chain(llm)

# Language-agnostic reranking function
def smart_rerank(source_documents, query):
    def priority_score(doc):
        source = doc.metadata.get("source", "").lower()
        content = doc.page_content.lower()

        # Priority based on project configuration
        priority_bonus = 0
        priority_files = project_config.get_priority_files()
        priority_extensions = project_config.config.get("priority_extensions", [])

        # Boost files that match priority patterns
        if any(pf in source for pf in priority_files):
            priority_bonus = 3
        elif any(source.endswith(ext) for ext in priority_extensions):
            priority_bonus = 2

        # Penalize utility files for project questions
        if source.endswith(".py") and project_config.project_type != "python" and any(word in query.lower() for word in ["project", "app", "what"]):
            priority_bonus = -2

        # Query relevance
        query_match = sum(1 for word in query.lower().split() if word in content)

        return priority_bonus + query_match

    return sorted(source_documents, key=priority_score, reverse=True)

def is_impact_question(q):
    return (
            "impact" in q.lower() or
            "what if" in q.lower() or
            "break" in q.lower()
    )

# Main Chat Interface
st.subheader("💬 Ask about your codebase")
query = st.text_input(
    "📝 Your question",
    placeholder=f"What does this {project_config.project_type} project do?"
)

if query and st.session_state["qa_chain"]:
    with st.spinner("💭 Thinking..."):
        # Question rewriting
        try:
            rewritten = rewrite_chain.invoke({"original": query}).content.strip()
            if debug_mode:
                st.info(f"🔄 Rewritten query: {rewritten}")
        except Exception as e:
            if debug_mode:
                st.warning(f"Query rewriting failed: {e}")
            rewritten = query  # Fallback to original

        # Impact analysis route
        impact_files = []
        if is_impact_question(query):
            import re
            # Look for file patterns based on project type
            priority_extensions = project_config.config.get("priority_extensions", [])
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
            else:
                context = ""
        else:
            context = ""

        # Generate answer
        result = st.session_state["qa_chain"](
            {"query": context + rewritten}
        )

        answer = result["result"]
        sources = smart_rerank(result.get("source_documents", []), query)
        st.session_state["chat_history"].append((query, answer, sources, impact_files))

# Display chat history
for q, a, srcs, impact_files in reversed(st.session_state["chat_history"][-10:]):
    with st.expander(f"Q: {q}"):
        st.markdown(f"**A:** {a}")
        if impact_files:
            st.markdown(f"**🔍 Impacted files:** {', '.join(impact_files)}")
        if srcs:
            st.markdown("**🔎 Top Sources:**")
            for doc in srcs[:5]:
                md = doc.metadata
                source_name = md.get('source', 'Unknown')
                chunk_type = md.get('type', 'text')
                chunk_index = md.get('chunk_index', 0)
                summary = md.get('summary', '')
                st.markdown(f"- `{source_name}` [{chunk_type}] (chunk {chunk_index}) | {summary}")

# Conditional Debug Section
if debug_mode:
    st.divider()
    st.subheader("🔧 Debug Tools")

    # Import debug tools only when needed
    try:
        from debug_tools import DebugTools
        debug_tools = DebugTools(
            project_config=project_config,
            ollama_model=ollama_model,
            ollama_endpoint=ollama_endpoint,
            project_dir=project_dir
        )
        debug_tools.render_debug_interface(st.session_state.get("retriever"))
    except ImportError:
        st.error("Debug tools not available. Make sure debug_tools.py is in your project directory.")

# Processing Logs (always available but collapsible)
with st.expander("🛠️ Processing Logs", expanded=debug_mode):
    update_logs(log_placeholder)
