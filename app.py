# app.py

import streamlit as st
from build_rag import build_rag, update_logs, get_impact
from langchain_ollama import ChatOllama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

st.set_page_config(page_title="🧠 Codebase Q&A", layout="wide")
st.title("💬 Chat with Your Codebase")

# Sidebar
with st.sidebar:
    st.header("🔧 Configuration")
    project_dir = st.text_input("📁 Project Directory", value=".")
    ollama_model = st.text_input("🧠 Ollama Model", value="llama3.1")
    ollama_endpoint = st.text_input("🔗 Ollama Endpoint", value="http://127.0.0.1:11434")
    force_rebuild = st.button("🔁 Rebuild Index")

# Session setup
st.session_state.setdefault("retriever", None)
st.session_state.setdefault("project_dir_used", None)
st.session_state.setdefault("thinking_logs", [])
st.session_state.setdefault("qa_chain", None)
st.session_state.setdefault("chat_history", [])
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
    return LLMChain(llm=llm, prompt=prompt)

# Build RAG
if should_rebuild:
    with st.spinner("🔄 Building RAG index..."):
        retriever = build_rag(
            project_dir=project_dir,
            ollama_model=ollama_model,
            ollama_endpoint=ollama_endpoint,
            log_placeholder=log_placeholder
        )
        st.session_state["retriever"] = retriever
        st.session_state["project_dir_used"] = project_dir
        st.session_state["qa_chain"] = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            return_source_documents=True
        )

# Advanced prompt for function/file-aware responses
QA_PROMPT = (
    "Given this code context, answer with references to any relevant files, classes, or functions. "
    "If answering about code impact or changes, mention dependencies and potential breakages explicitly.\n"
    "{context}\n\nUser Question: {question}"
)

# Chat interface
st.subheader("💬 Ask about your codebase")

query = st.text_input("📝 Your question", placeholder="What does this project do?")
rewrite_chain = get_rewrite_chain(llm)

def rerank(source_documents, query):
    # Boost exact term matches in summary and function/class chunks
    def score(doc):
        return (
            (query.lower() in doc.metadata.get("summary", "").lower()) +
            (doc.metadata.get("type") in ["function", "class"]) +
            (1 if doc.metadata.get("name") and doc.metadata.get("name").lower() in query.lower() else 0)
        )
    return sorted(source_documents, key=score, reverse=True)

def is_impact_question(q):
    return (
        "impact" in q.lower() or
        "what if" in q.lower() or
        "break" in q.lower()
    )

if query and st.session_state["qa_chain"]:
    with st.spinner("💭 Thinking..."):
        # Question rewriting
        rewritten = rewrite_chain.run({"original": query}).strip()
        # Impact analysis route:
        impact_files = []
        if is_impact_question(query):
            # Try to extract filename queried about
            import re
            match = re.search(r"[\w\-/\.]+\.kt", query)
            if match:
                target_file = match.group(0)
                impact_files = get_impact(target_file)
                impact_text = (
                    f"Files that may be impacted if `{target_file}` changes: " +
                    (", ".join(impact_files) if impact_files else "None found.")
                )
                # Record in QA chain prompt
                context = f"{impact_text}\n\n"
            else:
                context = ""
        else:
            context = ""

        # Generate answer with context and advanced prompt
        result = st.session_state["qa_chain"](
            {"query": context + rewritten, "prompt": QA_PROMPT}
        )

        answer = result["result"]
        sources = rerank(result.get("source_documents", []), query)
        st.session_state["chat_history"].append((query, answer, sources, impact_files))

# Display chat history
for q, a, srcs, impact_files in reversed(st.session_state["chat_history"][-10:]):
    with st.expander(f"Q: {q}"):
        st.markdown(f"**A:** {a}")
        if impact_files:
            st.markdown(f"**🔍 Impacted files:** {', '.join(impact_files)}")
        if srcs:
            st.markdown("**🔎 Top Chunks/Sources:**")
            for doc in srcs[:5]:
                md = doc.metadata
                st.markdown(f"- `{md.get('source')}` [{md.get('type')}] (chunk {md.get('chunk_index')}) | {md.get('summary')}")

# Logs
with st.expander("🛠️ Debug / Logs", expanded=False):
    update_logs(log_placeholder)
