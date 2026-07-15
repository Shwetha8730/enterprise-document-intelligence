# 📄 Enterprise AI Document Intelligence Platform

Enterprise AI Document Intelligence Platform is an AI-powered application designed to simplify document analysis using Natural Language Processing (NLP), Optical Character Recognition (OCR), semantic search, and a multi-agent workflow.

The platform enables users to upload PDF and text documents, automatically classify them, extract important metadata, validate document completeness, generate summaries, answer questions based on document content, perform semantic search, and export detailed PDF analysis reports.

The application demonstrates how machine learning, natural language processing, optical character recognition, and semantic search techniques can be integrated into a single intelligent document processing system through an interactive Streamlit interface.

---

## ✨ Features

- 📤 Upload and process **PDF** and **TXT** documents
- 🔍 OCR support for scanned PDF documents
- 🏷️ AI-powered document classification
- 📑 Metadata extraction using spaCy 
- ✅ Document completeness validation
- 📝 Extractive document summarization 
- ❓ Question answering over uploaded documents
- 🔎 Semantic search using FAISS
- 📊 Analytics dashboard
- 🧾 Audit logging for document processing
- 📄 Export document analysis reports as PDF
- 🚫 Prevent duplicate document processing using SHA-256 hashing

---

## 📷 Screenshots

### 🏠 Home Dashboard

![Home Dashboard](screenshots/home_dashboard.png)

### 📄 Document Analysis

![Document Analysis](screenshots/document_analysis.png)

### 🔍 Semantic Search

![Semantic Search](screenshots/semantic_search.png)

### 📊 Analytics Dashboard

![Analytics Dashboard](screenshots/analytics_dashboard.png)

---

## 🧠 How It Works


1. Upload a PDF or TXT document.
2. Extract text using pdfplumber or EasyOCR for scanned PDFs.
3. Classify the document using AI models.
4. Extract metadata using spaCy.
5. Validate document completeness.
6. Generate a document summary.
7. Create embeddings for semantic search.
8. Search documents or ask questions.
9. Export the analysis report as a PDF.

---

## 🛠️ Tech Stack

| Layer | Tools |
|---|---|
| Language | Python |
| API | FastAPI, Pydantic, Uvicorn |
| UI / Dashboard | Streamlit |
| NLP | spaCy, Sentence-Transformers |
| Classical ML | scikit-learn (TF-IDF, Naive Bayes, Logistic Regression, cosine similarity) |
| OCR | EasyOCR, pdf2image, Pillow |
| PDF Parsing | pdfplumber |
| Semantic Search | FAISS |
| Database | SQLite |
| Report Generation | ReportLab |
| Numerical Computing | NumPy |

---

## 📂 Project Structure

```text
enterprise-document-intelligence/
│
├── app/
│   ├── agents/
│   │   ├── summarizer_agent.py       # TF-IDF extractive summarization
│   │   ├── qa_agent.py               # TF-IDF similarity-based Q&A
│   │   ├── completeness_agent.py     # Required-field validation per doc type
│   │   └── search_agent.py           # Wraps the FAISS vector index for search
│   │
│   ├── classifier.py                 # TF-IDF + Naive Bayes classifier (+ keyword fallback)
│   ├── semantic_classifier.py        # Sentence-Transformers + Logistic Regression classifier
│   ├── extractor.py                  # Text extraction (pdfplumber) + OCR fallback (EasyOCR)
│   ├── metadata_extractor.py         # spaCy-based entity & field extraction
│   ├── embeddings.py                 # Embedding model wrapper (Sentence-Transformers / TF-IDF)
│   ├── vector_index.py               # FAISS index build/search over chunked documents
│   ├── text_utils.py                 # Sentence splitting & chunking utilities
│   ├── orchestrator.py               # Coordinates the full multi-agent pipeline
│   ├── database.py                   # SQLite persistence, audit log, dashboard stats
│   ├── report_generator.py           # ReportLab PDF report export
│   ├── seed_data.py                  # Training data for the classifiers
│   └── main.py                       # FastAPI app & REST endpoints
│
├── demo_ui.py                        # Streamlit dashboard (Upload, Search, Audit Log, Analytics)
├── requirements.txt
└── README.md
```

---


## 📊 Dashboard Features

- Document type distribution (bar chart)
- Classification confidence by document type
- Upload activity over time
- Per-document classification, metadata, summary, completeness check, and Q&A — all in one view
- Full audit trail table
- One-click PDF report export and original document download

---

## ⚙️ Installation

```bash
pip install -r requirements.txt
streamlit run demo_ui.py
```
---
 
## 📈 Future Enhancements

- Support for Word (`.docx`) and Excel (`.xlsx`) documents
- Cloud object storage for raw document text (currently held in memory per session)
- Fine-tuned transformer models for enterprise-specific document classification
- Multi-user authentication and role-based access control
- Persistent, cross-session FAISS index (currently rebuilt per app session)

---

## 🎯 Learning Outcomes

Through this project, I gained practical experience in:

- Natural Language Processing
- Optical Character Recognition (OCR)
- Semantic Search
- Multi-Agent AI Systems
- FastAPI Development
- Streamlit Dashboard Development
- SQLite Database Design
- Enterprise Document Processing

---

## 👩‍💻 Author

**Shwethashree S**

B.Tech – Information Science & Engineering (AI & Robotics)

Presidency University, Bengaluru.

---
