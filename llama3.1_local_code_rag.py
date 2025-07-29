# Imports (same as before)
import streamlit as st
import os, json, hashlib, time
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain.docstore.document import Document
import pathspec
from chunker_factory import get_chunker

# Page setup
st.set_page_config(page_title="Codebase Chat", layout="wide")
st.title("💬 Chat with Your Codebase")

# Sidebar settings
with st.sidebar:
    st.header("📁 Project Settings")
    project_dir = st.text_input("Enter path to your project directory", value=".", type="default")
    ollama_model = st.text_input("Ollama Model", value="llama3.1")
    ollama_endpoint = "http://127.0.0.1:11434"

# Constants
VECTOR_DB_DIR = "vector_db"
METADATA_FILE = os.path.join(VECTOR_DB_DIR, "processed_files.json")
EXTENSIONS = (".kt", ".kts", ".gradle", ".gitignore", ".properties", ".xml")

# Session state keys
for key in ["chat_history", "retriever"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "chat_history" else None

# LLM setup
ollama = ChatOllama(model=ollama_model, base_url=ollama_endpoint)

# Logs initializer
user_input = st.chat_input("Type your question here...")
if "thinking_logs" not in st.session_state:
    st.session_state.thinking_logs = []

def update_logs(log_placeholder):
    formatted = "<br>".join(st.session_state.thinking_logs)
    log_placeholder.markdown(
        f"<div style='overflow-y:scroll; background:#f9f9f9; padding:10px; font-family:monospace; font-size:13px;'>{formatted}</div>",
        unsafe_allow_html=True
    )

# Helpers
def load_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_metadata(metadata):
    os.makedirs(VECTOR_DB_DIR, exist_ok=True)
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2)

def get_file_hash(path):
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def load_gitignore_patterns(directory):
    gitignore_path = os.path.join(directory, ".gitignore")
    if not os.path.exists(gitignore_path):
        return None
    with open(gitignore_path, "r") as f:
        return pathspec.PathSpec.from_lines("gitwildmatch", f.readlines())

def reset_metadata_if_extensions_changed(new_extensions):
    metadata = load_metadata()
    known_extensions = {os.path.splitext(p)[1] for p in metadata.keys()}
    if not set(new_extensions).issubset(known_extensions):
        save_metadata({})

def get_files_to_process(directory, extensions=EXTENSIONS):
    metadata = load_metadata()
    new_metadata = {}
    files_to_process = []

    skipped_gitignore, skipped_cached = 0, 0
    spec = load_gitignore_patterns(directory)

    for root, _, files in os.walk(directory):
        for file in files:
            if not file.endswith(extensions):
                continue

            path = os.path.join(root, file)
            rel_path = os.path.relpath(path, directory)

            if spec and spec.match_file(rel_path):
                skipped_gitignore += 1
                continue

            file_hash = get_file_hash(path)
            if not file_hash:
                continue

            stored_hash = metadata.get(rel_path)
            if stored_hash == file_hash:
                skipped_cached += 1
                continue

            files_to_process.append(path)
            new_metadata[rel_path] = file_hash

    save_metadata(new_metadata)
    st.session_state.thinking_logs.append(f"⏭️ Skipped: {skipped_gitignore} via .gitignore, {skipped_cached} unchanged")
    return files_to_process

def summarize_chunk(chunk, path):
    prompt = f"Summarize the following code chunk from {path} in one line:\n\n{chunk}"
    try:
        response = ollama.invoke([("human", prompt)])
        return response.content.strip()
    except Exception as e:
        st.warning(f"Failed to summarize chunk: {e}")
        return "No summary available"

def build_rag(project_dir, log_placeholder):
    reset_metadata_if_extensions_changed(EXTENSIONS)
    files_to_process = get_files_to_process(project_dir, EXTENSIONS)
    embeddings = OllamaEmbeddings(model=ollama_model, base_url=ollama_endpoint)

    if not files_to_process:
        st.info("✅ All files already processed. Loading existing vector DB...")
        return Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embeddings).as_retriever()

    start_time = time.time()
    st.info(f"📂 Processing {len(files_to_process)} new/updated files...")
    st.session_state.thinking_logs.append(f"🔍 Starting RAG for {len(files_to_process)} files...")
    update_logs(log_placeholder)

    total_chunks, documents = 0, []

    for path in files_to_process:
        ext = os.path.splitext(path)[1]
        chunker = get_chunker(ext)

        t0 = time.time()
        st.session_state.thinking_logs.append(f"📄 Processing file: {path}")
        update_logs(log_placeholder)

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                chunks = chunker(content)
                chunk_count = len(chunks)
                total_chunks += chunk_count

                for i, chunk in enumerate(chunks):
                    summary = summarize_chunk(chunk, path)
                    documents.append(Document(
                        page_content=chunk,
                        metadata={"source": path, "chunk_index": i, "summary": summary}
                    ))

                duration = time.time() - t0
                st.session_state.thinking_logs.append(f"✅ {path}: {chunk_count} chunks in {duration:.2f}s")
                update_logs(log_placeholder)

        except Exception as e:
            st.warning(f"Failed to process {path}: {e}")
            st.session_state.thinking_logs.append(f"❌ Error with {path}: {e}")
            update_logs(log_placeholder)

    db_duration = time.time() - start_time
    vectorstore = Chroma.from_documents(documents, embedding=embeddings, persist_directory=VECTOR_DB_DIR)
    st.success("✅ Vector DB updated")
    st.session_state.thinking_logs.append(f"📦 Indexed {total_chunks} chunks from {len(files_to_process)} files in {db_duration:.2f}s")
    update_logs(log_placeholder)

    return vectorstore.as_retriever()

def ollama_llm(question, context, log_placeholder):
    prompt = f"Question: {question}\n\nContext:\n{context}"
    st.session_state.thinking_logs.append("🧠 Sending prompt to LLM...")
    update_logs(log_placeholder)

    st.session_state.thinking_logs.append(f"📨 Prompt:\n{prompt[:1000]}...")
    update_logs(log_placeholder)

    response = ollama.invoke([("human", prompt)])
    st.session_state.thinking_logs.append("✅ Response received.")
    update_logs(log_placeholder)

    return response.content.strip()

def combine_docs(docs, log_placeholder):
    sources = [doc.metadata.get("source", "unknown") for doc in docs]
    st.session_state.thinking_logs.append(f"📚 Retrieved {len(docs)} docs:\n" + "\n".join(sources))
    update_logs(log_placeholder)
    return "\n\n".join(doc.page_content for doc in docs)

def rag_chain(question, log_placeholder):
    st.session_state.thinking_logs.clear()
    st.session_state.thinking_logs.append("🔍 Retrieving context...")
    update_logs(log_placeholder)

    docs = st.session_state.retriever.invoke(question)
    context = combine_docs(docs, log_placeholder)

    st.session_state.thinking_logs.append("🧠 Generating response...")
    update_logs(log_placeholder)

    return ollama_llm(question, context, log_placeholder)

# Load retriever
if st.session_state.retriever is None and os.path.exists(project_dir):
    log_placeholder = st.empty()
    st.session_state.retriever = build_rag(project_dir, log_placeholder)
    if st.session_state.retriever:
        st.sidebar.success("Codebase loaded!")

# Layout containers
main_container = st.container()
chat_container = main_container.container()
log_container = main_container.container()

st.markdown("""
<style>
    .main-container > div:nth-child(1) { height: 75vh; overflow-y: auto; }
    .main-container > div:nth-child(2) { height: 25vh; overflow-y: auto; border-top: 1px solid #ccc; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-container'>", unsafe_allow_html=True)

with chat_container:
    st.subheader("🧠 Chat History")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    st.subheader("💬 Ask a Question")
    user_input = st.chat_input("Type your question here...")

with log_container:
    st.subheader("🪵 Thinking Mode Logs")
    log_placeholder = st.empty()

    if user_input and st.session_state.retriever:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        response = rag_chain(user_input, log_placeholder)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)