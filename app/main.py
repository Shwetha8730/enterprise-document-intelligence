import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from pydantic import BaseModel

from app.extractor import extract_text
from app.orchestrator import DocumentOrchestrator
from app import database

app = FastAPI(
    title="Enterprise AI Document Intelligence Platform",
    description="Multi-agent document classification, metadata extraction, "
                 "RAG-based semantic search, and Q&A - built as a project "
                 "inspired by OpenText's EIM / AI Engineering internship role.",
    version="2.0.0",
)

orchestrator = DocumentOrchestrator()

UPLOAD_DIR = Path("uploaded_docs")
UPLOAD_DIR.mkdir(exist_ok=True)

# raw extracted text is kept in memory for Q&A (only metadata/summary
# persist to the DB) - fine for a prototype; a production version would
# store raw text in object storage (e.g. S3) keyed by doc_id
TEXT_CACHE: dict[str, str] = {}


class QuestionRequest(BaseModel):
    doc_id: str
    question: str


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


@app.get("/")
def root():
    return {
        "message": "Enterprise AI Document Intelligence Platform API is running.",
        "embedding_mode": orchestrator.embedding_model.mode,
        "endpoints": [
            "/analyze (POST)", "/ask (POST)", "/search (POST)",
            "/documents (GET)", "/audit-log (GET)",
        ],
    }


@app.post("/analyze")
async def analyze_document(file: UploadFile = File(...)):
    doc_id = str(uuid.uuid4())[:8]
    save_path = UPLOAD_DIR / f"{doc_id}_{file.filename}"

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        text = extract_text(str(save_path))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not text.strip():
        raise HTTPException(status_code=422, detail="No extractable text found in document.")

    result = orchestrator.process(doc_id=doc_id, filename=file.filename, text=text)
    TEXT_CACHE[doc_id] = text

    return {"doc_id": doc_id, "filename": file.filename, **result}


@app.post("/ask")
async def ask_question(req: QuestionRequest):
    if req.doc_id not in TEXT_CACHE:
        raise HTTPException(status_code=404, detail="Document not found in this session. Upload it first via /analyze.")

    answer = orchestrator.answer_question(req.doc_id, TEXT_CACHE[req.doc_id], req.question)
    return {"doc_id": req.doc_id, **answer}


@app.post("/search")
async def semantic_search(req: SearchRequest):
    """Semantic search across all processed documents - matches on
    meaning, not just exact keyword overlap (e.g. 'invoices from
    Microsoft' can match a doc that says 'Redmond-based vendor')."""
    result = orchestrator.semantic_search(req.query, top_k=req.top_k)

    # enrich results with filename/doc_type from the DB
    enriched = []
    for r in result["results"]:
        doc = database.get_document(r["doc_id"])
        if doc:
            enriched.append({**r, "filename": doc["filename"], "doc_type": doc["doc_type"]})
    result["results"] = enriched
    return result


@app.get("/documents")
def list_documents():
    return database.list_documents()


@app.get("/audit-log")
def audit_log(doc_id: str = Query(None, description="Filter audit log to a single document")):
    return database.get_audit_log(doc_id=doc_id)
