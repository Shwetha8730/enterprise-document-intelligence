import hashlib
import tempfile
from pathlib import Path
import streamlit as st

from app.extractor import extract_text
from app.orchestrator import DocumentOrchestrator
from app import database

st.set_page_config(page_title="Enterprise AI Document Intelligence Platform", page_icon="📄", layout="wide")

st.title("📄 Enterprise AI Document Intelligence Platform")
st.subheader("AI-Powered Multi-Agent Document Processing System")
st.markdown("---")
st.caption("Multi-agent document classification, metadata extraction, RAG-based semantic search, and Q&A — built as a project inspired by OpenText's Enterprise Information Management / AI Engineering internship role.")

@st.cache_resource
def get_orchestrator():
    return DocumentOrchestrator()

orchestrator = get_orchestrator()

st.caption(f"🔌 Embedding mode: `{orchestrator.embedding_model.mode}`")

if "docs" not in st.session_state:
    st.session_state.docs = {}

col1, col2 = st.columns(2)

with col1:
    st.metric("📄 Processed Documents", len(st.session_state.docs))

with col2:
    st.metric("🤖 Embedding Model", "Sentence-Transformers" if "sentence-transformers" in orchestrator.embedding_model.mode else "TF-IDF Fallback")
    st.caption(orchestrator.embedding_model.mode)

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📤 Upload & Analyze", "🔍 Semantic Search", "🧾 Audit Log"])

# ------------------------------------------------------------ TAB 1

with tab1:

    uploaded_files = st.file_uploader(
        "Upload document(s) (.pdf or .txt)",
        type=["pdf", "txt"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:

            # Generate a unique ID based on file content
            uploaded_file.seek(0)
            file_bytes = uploaded_file.read()
            doc_id = hashlib.sha256(file_bytes).hexdigest()[:8]
            uploaded_file.seek(0)

            # Skip duplicate uploads
            if doc_id in st.session_state.docs:
                st.info(f"{uploaded_file.name} has already been processed.")
                continue

            suffix = Path(uploaded_file.name).suffix

            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            uploaded_file.seek(0)

            text = extract_text(tmp_path)

            with st.spinner(
                f"Processing '{uploaded_file.name}' using the AI multi-agent pipeline..."
            ):
                result = orchestrator.process(
                    doc_id=doc_id,
                    filename=uploaded_file.name,
                    text=text,
                )

            st.session_state.docs[doc_id] = {
                "text": text,
                "result": result,
                "filename": uploaded_file.name,
            }

            st.session_state.current_doc_id = doc_id
            st.success(f"Processed: {uploaded_file.name}")

    if st.session_state.docs:

        doc_id = st.selectbox(
            "Select a processed document",
            options=list(st.session_state.docs.keys()),
            format_func=lambda d: st.session_state.docs[d]["filename"],
            index=list(st.session_state.docs.keys()).index(
                st.session_state.get(
                    "current_doc_id",
                    list(st.session_state.docs.keys())[0],
                )
            ),
        )

        doc = st.session_state.docs[doc_id]
        result = doc["result"]

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🏷️ Classification")
            cls = result["classification"]
            st.metric("Predicted Type", cls["predicted_type"].upper(), f"{cls['confidence']*100:.1f}% confidence")
            st.bar_chart(cls["all_scores"])
            st.subheader("✅ Completeness Check")
            comp = result["completeness_check"]
            (st.success if comp["is_complete"] else st.warning)(comp["recommendation"])

        with col2:
            st.subheader("🔎 Extracted Metadata")
            for key, val in result["metadata"].items():
                if val and key != "missing_fields":
                    st.markdown(f"**{key.replace('_', ' ').title()}:** {', '.join(val) if isinstance(val, list) else val}")

        st.subheader("📝 Auto-Generated Summary")
        st.info(result["summary"])

        st.subheader("💬 Ask a question about this document")

        question = st.text_input("Your question", placeholder="e.g. What is the total amount due?")

        if question:
            answer = orchestrator.answer_question(doc_id, doc["text"], question)
            st.write(f"**Answer:** {answer['answer']}")
            st.caption(f"Confidence: {answer['confidence']} | Agent: {answer['agent']}")

        with st.expander("🔍 View raw extracted text"):
            st.text(doc["text"])

    else:
        st.info("Upload one or more documents above to see the multi-agent pipeline in action. Try the sample invoice or resume in app/sample_docs/ if you don't have one handy.")

# ------------------------------------------------------------ TAB 2

with tab2:
    st.subheader("Semantic Search Across All Processed Documents")
    st.caption("Matches on meaning, not just exact keywords — e.g. searching 'invoices from Microsoft' can surface a document that says 'Redmond-based software vendor' instead of the literal word.")

    query = st.text_input("Search query", placeholder="e.g. invoices from technology vendors")

    if query:

        if not st.session_state.docs:
            st.warning("Upload and process at least one document first (see the Upload tab).")

        else:

            search_result = orchestrator.semantic_search(query, top_k=3)

            if not search_result["results"]:
                st.info("No matching documents found.")

            else:

                for r in search_result["results"]:

                    doc_meta = database.get_document(r["doc_id"])

                    if doc_meta:
                        st.markdown(f"### 📄 {doc_meta['filename']}")
                        st.write(f"**Document Type:** {doc_meta['doc_type'].upper()}")
                        st.write(f"**Similarity Score:** {r['score']:.3f}")
                        if "snippet" in r:
                            st.info(r["snippet"])
                        st.markdown("---")


# ------------------------------------------------------------ TAB 3

with tab3:

    st.subheader("Audit Trail")

    st.caption("Every action taken on every document, with timestamps — mirrors the compliance and traceability requirements of a real enterprise content platform.")

    logs = database.get_audit_log(limit=200)

    if logs:
        st.table(logs)

    else:
        st.info("No actions logged yet. Process a document to populate the audit trail.")


st.markdown("---")

st.caption(
    "Developed using Python • FastAPI • Streamlit • spaCy • FAISS • Sentence Transformers • SQLite"
)