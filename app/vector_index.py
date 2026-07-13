import faiss
import numpy as np

from app.text_utils import chunk_text


class VectorIndex:
    def __init__(self, embedding_model, dim: int = 384):
        self.embedding_model = embedding_model
        self.dim = dim

        self.index = faiss.IndexFlatIP(dim)

        self.chunk_doc_ids = []
        self.chunk_texts = []

        # Track processed documents
        self.indexed_docs = set()

    def add(self, doc_id: str, text: str):
        # Prevent duplicate indexing
        if doc_id in self.indexed_docs:
            return

        chunks = chunk_text(text)

        if not chunks:
            return

        vectors = self.embedding_model.encode_corpus(chunks)
        vectors = np.asarray(vectors, dtype="float32")

        self.index.add(vectors)

        self.chunk_doc_ids.extend([doc_id] * len(chunks))
        self.chunk_texts.extend(chunks)

        self.indexed_docs.add(doc_id)

    def search(self, query: str, top_k: int = 5):

        if not self.chunk_doc_ids:
            return []

        query_vector = self.embedding_model.encode([query])
        query_vector = np.asarray(query_vector, dtype="float32")

        # Retrieve extra candidates before deduplicating by document
        search_size = min(top_k * 5, len(self.chunk_doc_ids))

        scores, indices = self.index.search(query_vector, search_size)

        best_docs = {}

        for score, idx in zip(scores[0], indices[0]):

            if idx == -1:
                continue
            
            if score < 0.30:
                continue

            doc_id = self.chunk_doc_ids[idx]

            if (
                doc_id not in best_docs
                or score > best_docs[doc_id]["score"]
            ):
                best_docs[doc_id] = {
                    "doc_id": doc_id,
                    "score": round(float(score), 4),
                    "snippet": self.chunk_texts[idx],
                }

        results = sorted(
            best_docs.values(),
            key=lambda x: x["score"],
            reverse=True,
        )

        return results[:top_k]