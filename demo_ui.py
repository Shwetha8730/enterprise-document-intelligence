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

tab1, tab2, tab3 , tab4 = st.tabs(["📤 Upload & Analyze", "🔍 Semantic Search", "🧾 Audit Log","📊 Analytics",])

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
                "filepath": tmp_path,
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
        pdf_path = doc["filepath"]

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
                  st.markdown(
                f"**{key.replace('_', ' ').title()}:** "
                f"{', '.join(val) if isinstance(val, list) else val}"
            )

            st.subheader("📄Original Document")

            with open(pdf_path, "rb") as pdf_file:
                st.download_button(
                 label="📥 Download Original Document",
                 data=pdf_file,
                 file_name=doc["filename"],
                 mime="application/pdf",
)
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

# ------------------------------------------------------------ TAB 4

with tab4:

    st.subheader("📊 Analytics Dashboard")

    stats = database.get_dashboard_stats()

    confidence_percent = {}

    if stats["confidence_by_type"]:
       confidence_percent = {
          k: v * 100
          for k, v in stats["confidence_by_type"].items()
    }

    col1, col2 = st.columns(2)

    with col1:
      st.subheader("📂 Document Distribution")
      st.bar_chart(stats["document_types"])

    with col2:
       st.subheader("📈 Classification Confidence (%)")

       if confidence_percent:
           st.bar_chart(confidence_percent)
       else:
           st.info("No confidence data available.")

    st.markdown("### 📂 Document Types")

    counts = stats["document_types"]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("🧾 Invoice", counts.get("Invoice", 0))
    c2.metric("📄 Resume", counts.get("Resume", 0))
    c3.metric("📜 Contract", counts.get("Contract", 0))
    c4.metric("📧 Email", counts.get("Email", 0))

    st.markdown("---")

    st.subheader("📅 Upload Activity")

    if len(stats["uploads_per_day"]) > 1:
       st.line_chart(stats["uploads_per_day"])
    elif stats["uploads_per_day"]:
       st.metric(
         "Today's Uploads",
          list(stats["uploads_per_day"].values())[0]
    )
    else:
       st.info("No upload activity yet.")
    
st.markdown("---")

st.caption(
    "Developed using Python • FastAPI • Streamlit • spaCy • FAISS • Sentence Transformers • SQLite"
)