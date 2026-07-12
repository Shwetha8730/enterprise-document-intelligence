from sklearn.feature_extraction.text import TfidfVectorizer
from app.text_utils import split_sentences


class SummarizerAgent:
    name = "summarizer_agent"

    def run(self, text: str, num_sentences: int = 3) -> dict:
        sentences = split_sentences(text)
        if len(sentences) <= num_sentences:
            summary = " ".join(sentences)
        else:
            summary = self._extractive_summary(sentences, num_sentences)

        return {
            "agent": self.name,
            "summary": summary,
            "original_sentence_count": len(sentences),
        }

    @staticmethod
    def _extractive_summary(sentences, num_sentences):
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf = vectorizer.fit_transform(sentences)
        scores = tfidf.sum(axis=1).A1  # sum of tfidf weights per sentence
        top_idx = sorted(scores.argsort()[-num_sentences:])  # keep original order
        return " ".join(sentences[i] for i in top_idx)
