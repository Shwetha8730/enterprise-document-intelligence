import hashlib
import tempfile
import os
from pathlib import Path
from mimetypes import guess_type

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.extractor import extract_text
from app.orchestrator import DocumentOrchestrator
from app import database
from app.report_generator import generate_pdf_report

app = FastAPI(title="Document Intelligence Platform API")

orchestrator = DocumentOrchestrator()

DOCS: dict[str, dict] = {}
DOC_ORDER: list[str] = []


class QuestionRequest(BaseModel):
    question: str


@app.get("/api/meta")
def get_meta():
    print("DOCS COUNT:", len(DOCS))
    print("DOCS:", DOCS.keys())
    return {
        "embedding_mode": orchestrator.embedding_model.mode,
        "is_sentence_transformers": "sentence-transformers" in orchestrator.embedding_model.mode,
        "processed_count": len(DOCS),
    }


@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    file_bytes = await file.read()
    doc_id = hashlib.sha256(file_bytes).hexdigest()[:8]

    if doc_id in DOCS:
        return {"doc_id": doc_id, "already_processed": True, **_doc_summary(doc_id)}

    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    text = extract_text(tmp_path)
    result = orchestrator.process(doc_id=doc_id, filename=file.filename, text=text)

    DOCS[doc_id] = {
        "text": text,
        "result": result,
        "filename": file.filename,
        "filepath": tmp_path,
    }
    DOC_ORDER.append(doc_id)

    return {"doc_id": doc_id, "already_processed": False, **_doc_summary(doc_id)}


def _doc_summary(doc_id: str) -> dict:
    doc = DOCS[doc_id]
    return {
        "filename": doc["filename"],
        "result": doc["result"],
    }


@app.get("/api/documents")
def list_documents():
    return {
        "documents": [
            {
                "doc_id": doc_id,
                "filename": DOCS[doc_id]["filename"],
                "predicted_type": DOCS[doc_id]["result"]["classification"]["predicted_type"],
                "confidence": DOCS[doc_id]["result"]["classification"]["confidence"],
            }
            for doc_id in DOC_ORDER
        ]
    }


@app.get("/api/documents/{doc_id}")
def get_document_detail(doc_id: str):
    doc = _require_doc(doc_id)
    return {
        "doc_id": doc_id,
        "filename": doc["filename"],
        "text": doc["text"],
        "result": doc["result"],
    }


@app.get("/api/documents/{doc_id}/file")
def download_original(doc_id: str):
    doc = _require_doc(doc_id)
    mime_type, _ = guess_type(doc["filepath"])
    return FileResponse(
        doc["filepath"],
        media_type=mime_type or "application/octet-stream",
        filename=doc["filename"],
    )


@app.get("/api/documents/{doc_id}/report")
def download_report(doc_id: str):
    doc = _require_doc(doc_id)
    report_path = generate_pdf_report(doc["filename"], doc["result"])
    return FileResponse(
        report_path,
        media_type="application/pdf",
        filename=f"{doc['filename']}_analysis_report.pdf",
    )


@app.post("/api/documents/{doc_id}/ask")
def ask_question(doc_id: str, payload: QuestionRequest):
    doc = _require_doc(doc_id)
    answer = orchestrator.answer_question(doc_id, doc["text"], payload.question)
    return answer


def _require_doc(doc_id: str) -> dict:
    doc = DOCS.get(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found. It may not have been uploaded yet.")
    return doc


@app.get("/api/search")
def semantic_search(q: str = Query(..., min_length=1), top_k: int = 3):
    if not DOCS:
        return {"results": []}
    search_result = orchestrator.semantic_search(q, top_k=top_k)
    enriched = []
    SIMILARITY_THRESHOLD = 0.40 
    for r in search_result.get("results", []):
        if r["score"] < SIMILARITY_THRESHOLD:
           continue
        doc_meta = database.get_document(r["doc_id"])
        if doc_meta:
            enriched.append(
                {
                    "doc_id": r["doc_id"],
                    "filename": doc_meta["filename"],
                    "doc_type": doc_meta["doc_type"],
                    "score": r["score"],
                    "snippet": r.get("snippet"),
                }
            )
    return {"results": enriched}


@app.get("/api/audit-log")
def audit_log(limit: int = 200):
    return {"logs": database.get_audit_log(limit=limit)}


@app.get("/api/stats")
def dashboard_stats():
    document_types = {}
    confidence_by_type = {}
    uploads_per_day = {}

    for doc in DOCS.values():
        doc_type = doc["result"]["classification"]["predicted_type"].title()
        confidence = doc["result"]["classification"]["confidence"]

        document_types[doc_type] = document_types.get(doc_type, 0) + 1

        confidence_by_type.setdefault(doc_type, []).append(confidence)
    
    confidence_percent = {
        k: round(sum(v)/len(v)*100, 1)
        for k, v in confidence_by_type.items()
    }
    return {
        "document_types": document_types,
        "confidence_by_type_percent": confidence_percent,
        "documents_processed": len(DOCS)
    }

@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str):
    print("Before delete:", len(DOCS), DOC_ORDER)
    if doc_id not in DOCS:
        raise HTTPException(status_code=404, detail="Document not found")

    doc = DOCS[doc_id]
    database.delete_document(doc_id)
    path = doc.get("filepath")
    if path and os.path.exists(path):
        os.remove(path)

    DOCS.pop(doc_id)
    if doc_id in DOC_ORDER:
        DOC_ORDER.remove(doc_id)
    print("After delete:", DOCS.keys())
    return {
        "success": True,
        "message": "Document deleted"
    }

@app.post("/api/reset-session")
def reset_session():
    global DOCS, DOC_ORDER

    for doc in DOCS.values():
        path = doc.get("filepath")
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass

    DOCS.clear()
    DOC_ORDER.clear()

    return {
        "success": True,
        "message": "Session reset"
    }

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    return FileResponse(STATIC_DIR / "index.html")