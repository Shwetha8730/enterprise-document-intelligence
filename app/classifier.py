from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from app.seed_data import TRAINING_DOCS, TRAINING_LABELS

KEYWORD_HINTS = {
    "invoice": ["invoice", "total due", "amount due", "bill to", "invoice number", "subtotal"],
    "resume": ["objective", "work experience", "education", "skills", "curriculum vitae", "references"],
    "contract": ["agreement", "party", "whereas", "hereby", "terms and conditions", "effective date"],
    "email": ["subject:", "dear", "regards", "best regards", "from:", "to:", "sent:"],
    "spreadsheet": ["employee id", "sales report", "inventory", "designation", "department", "quantity", "price", "stock", "location",],
    "presentation":["project proposal", "presentation", "slide", "agenda", "objectives", "overview", "thank you", "conclusion", "architecture", "implementation"],
    "letter":["dear sir", "subject", "offer letter", "recommendation", "leave application", "sincerely"]
}

class DocumentClassifier:
    def __init__(self):
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(stop_words="english", ngram_range=(1, 2))),
            ("clf", MultinomialNB()),
        ])
        self.pipeline.fit(TRAINING_DOCS, TRAINING_LABELS)
        self.labels = sorted(set(TRAINING_LABELS))

    def classify(self, text: str) -> dict:
        text_lower = text.lower()
        proba = self.pipeline.predict_proba([text])[0]
        label_conf = dict(zip(self.pipeline.classes_, proba))
        best_label = max(label_conf, key=label_conf.get)
        confidence = label_conf[best_label]

        # Low-confidence fallback: keyword scoring
        if confidence < 0.45:
            scores = {
                label: sum(1 for kw in kws if kw in text_lower)
                for label, kws in KEYWORD_HINTS.items()
            }
            if max(scores.values()) > 0:
                best_label = max(scores, key=scores.get)
                confidence = min(0.95, 0.5 + 0.1 * scores[best_label])

        return {
            "predicted_type": best_label,
            "confidence": round(float(confidence), 3),
            "all_scores": {k: round(float(v), 3) for k, v in label_conf.items()},
        }
