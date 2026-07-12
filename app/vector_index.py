import faiss
import numpy as np


class VectorIndex:
    def __init__(self, embedding_model, dim: int = 384):
        self.embedding_model = embedding_model
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)  # inner product == cosine sim on normalized vectors
        self.doc_ids: list[str] = []
        self.texts: list[str] = []

    def add(self, doc_id: str, text: str):
        self.doc_ids.append(doc_id)
        self.texts.append(text)
        self._rebuild()

    def _rebuild(self):
        if not self.texts:
            return
        vectors = self.embedding_model.encode_corpus(self.texts)
        vectors = np.asarray(vectors, dtype="float32")
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)

    def search(self, query: str, top_k: int = 5):
        if not self.doc_ids:
            return []

        query_vector = self.embedding_model.encode([query])
        query_vector = np.asarray(query_vector, dtype="float32")

        top_k = min(top_k, len(self.doc_ids))
        scores, indices = self.index.search(query_vector, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append({
                "doc_id": self.doc_ids[idx],
                "score": round(float(score), 4),
            })
        return results
