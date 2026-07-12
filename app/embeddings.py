import numpy as np

class EmbeddingModel:
    def __init__(self):
        self.mode = None
        self._st_model = None
        self._tfidf_vectorizer = None
        self._tfidf_fitted = False
        self._try_load_sentence_transformer()

    def _try_load_sentence_transformer(self):
        try:
            from sentence_transformers import SentenceTransformer
            self._st_model = SentenceTransformer("all-MiniLM-L6-v2")
            self.mode = "sentence-transformers (all-MiniLM-L6-v2)"
        except Exception as e:
            self.mode = f"tfidf-fallback (sentence-transformers unavailable: {type(e).__name__})"
            from sklearn.feature_extraction.text import TfidfVectorizer
            self._tfidf_vectorizer = TfidfVectorizer(stop_words="english", max_features=384)

    def encode(self, texts: list[str]) -> np.ndarray:
        """Encode a query or a one-off batch using the already-fitted
        vector space. For sentence-transformers this is stateless. For
        the TF-IDF fallback, call encode_corpus() first to fit the
        vector space on the full document set."""
        if self._st_model is not None:
            return self._st_model.encode(texts, normalize_embeddings=True)
        return self._encode_tfidf(texts, fit=False)

    def encode_corpus(self, texts: list[str]) -> np.ndarray:
        """Encode the full document corpus, (re)fitting the vector
        space if using the TF-IDF fallback. Always call this - not
        encode() - when (re)building an index over multiple documents,
        so the fallback vocabulary reflects every document, not just
        the first one indexed."""
        if self._st_model is not None:
            return self._st_model.encode(texts, normalize_embeddings=True)
        return self._encode_tfidf(texts, fit=True)

    def _encode_tfidf(self, texts: list[str], fit: bool) -> np.ndarray:
        if fit or not self._tfidf_fitted:
            vectors = self._tfidf_vectorizer.fit_transform(texts).toarray()
            self._tfidf_fitted = True
        else:
            vectors = self._tfidf_vectorizer.transform(texts).toarray()

        # pad/truncate to a fixed 384-dim space so FAISS index dimension
        # stays consistent even as vocabulary grows
        dim = 384
        if vectors.shape[1] < dim:
            pad = np.zeros((vectors.shape[0], dim - vectors.shape[1]))
            vectors = np.hstack([vectors, pad])
        else:
            vectors = vectors[:, :dim]

        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return (vectors / norms).astype("float32")
