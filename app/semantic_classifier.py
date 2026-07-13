from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
import numpy as np

from app.seed_data import TRAINING_DOCS, TRAINING_LABELS


class SemanticClassifier:

    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        embeddings = self.model.encode(
            TRAINING_DOCS,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        self.classifier = LogisticRegression(max_iter=1000)

        self.classifier.fit(
            embeddings,
            TRAINING_LABELS,
        )

    def classify(self, text: str):

        embedding = self.model.encode(
            [text],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        prediction = self.classifier.predict(embedding)[0]

        probabilities = self.classifier.predict_proba(embedding)[0]

        labels = self.classifier.classes_

        scores = {
            label: round(float(prob), 3)
            for label, prob in zip(labels, probabilities)
        }

        confidence = float(np.max(probabilities))

        return {
            "predicted_type": prediction,
            "confidence": round(confidence, 3),
            "all_scores": scores,
        }