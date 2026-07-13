import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

DB_PATH = Path(__file__).parent.parent / "doc_intelligence.db"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                doc_type TEXT,
                confidence REAL,
                status TEXT DEFAULT 'processing',
                metadata_json TEXT,
                summary TEXT,
                uploaded_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id TEXT,
                action TEXT NOT NULL,
                details TEXT,
                timestamp TEXT NOT NULL
            )
        """)


def log_action(doc_id: str, action: str, details: str = ""):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO audit_log (doc_id, action, details, timestamp) VALUES (?, ?, ?, ?)",
            (doc_id, action, details, _now()),
        )


def save_document(doc_id: str, filename: str, doc_type: str, confidence: float,
                   metadata: dict, summary: str, status: str = "processed"):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO documents (doc_id, filename, doc_type, confidence, status, metadata_json, summary, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(doc_id) DO UPDATE SET
                doc_type=excluded.doc_type, confidence=excluded.confidence,
                status=excluded.status, metadata_json=excluded.metadata_json,
                summary=excluded.summary
        """, (doc_id, filename, doc_type, confidence, status, json.dumps(metadata), summary, _now()))
    log_action(doc_id, "document_processed", f"type={doc_type}, confidence={confidence}")


def get_document(doc_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM documents WHERE doc_id = ?", (doc_id,)).fetchone()
        if row is None:
            return None
        d = dict(row)
        d["metadata_json"] = json.loads(d["metadata_json"]) if d["metadata_json"] else {}
        return d


def list_documents() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT doc_id, filename, doc_type, confidence, status, uploaded_at FROM documents ORDER BY uploaded_at DESC").fetchall()
        return [dict(r) for r in rows]


def get_audit_log(doc_id: str = None, limit: int = 100):
    with get_connection() as conn:
        if doc_id:
            rows = conn.execute(
                "SELECT * FROM audit_log WHERE doc_id = ? ORDER BY timestamp DESC LIMIT ?",
                (doc_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]
