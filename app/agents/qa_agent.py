from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.text_utils import split_sentences

class QAAgent:
    name = "qa_agent"

    def run(self, text: str, question: str, top_k: int = 2) -> dict:
        sentences = split_sentences(text)
        if not sentences:
            return {"agent": self.name, "answer": None, "supporting_sentences": []}

        vectorizer = TfidfVectorizer(stop_words="english")
        corpus = sentences + [question]
        tfidf = vectorizer.fit_transform(corpus)

        doc_vectors = tfidf[:-1]
        question_vector = tfidf[-1]

        similarities = cosine_similarity(question_vector, doc_vectors).flatten()
        top_indices = similarities.argsort()[::-1][:top_k]
        top_indices = [i for i in top_indices if similarities[i] > 0]

        supporting = [sentences[i] for i in sorted(top_indices)]

        return {
            "agent": self.name,
            "question": question,
            "answer": " ".join(supporting) if supporting else "No relevant information found in the document.",
            "supporting_sentences": supporting,
            "confidence": round(float(similarities[top_indices[0]]), 3) if top_indices else 0.0,
        }
