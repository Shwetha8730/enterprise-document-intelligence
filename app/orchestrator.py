from app.classifier import DocumentClassifier
from app.metadata_extractor import extract_metadata
from app.agents.summarizer_agent import SummarizerAgent
from app.agents.qa_agent import QAAgent
from app.agents.completeness_agent import CompletenessAgent
from app.agents.search_agent import SearchAgent
from app.embeddings import EmbeddingModel
from app.vector_index import VectorIndex
from app import database


class DocumentOrchestrator:
    def __init__(self):
        database.init_db()

        self.classifier = DocumentClassifier()
        self.summarizer_agent = SummarizerAgent()
        self.qa_agent = QAAgent()
        self.completeness_agent = CompletenessAgent()

        self.embedding_model = EmbeddingModel()
        self.vector_index = VectorIndex(self.embedding_model)
        self.search_agent = SearchAgent(self.vector_index)

    def process(self, doc_id: str, filename: str, text: str) -> dict:
        database.log_action(doc_id, "uploaded", f"filename={filename}")

        classification = self.classifier.classify(text)
        doc_type = classification["predicted_type"]
        database.log_action(doc_id, "classified", f"type={doc_type}, confidence={classification['confidence']}")

        metadata = extract_metadata(text, doc_type=doc_type)
        database.log_action(doc_id, "metadata_extracted",
                             f"fields_found={[k for k, v in metadata.items() if v]}")

        completeness = self.completeness_agent.run(metadata, doc_type)
        database.log_action(doc_id, "completeness_checked", completeness["recommendation"])

        summary = self.summarizer_agent.run(text)
        database.log_action(doc_id, "summarized")

        # persist to DB
        database.save_document(
            doc_id=doc_id, filename=filename, doc_type=doc_type,
            confidence=classification["confidence"], metadata=metadata,
            summary=summary["summary"],
        )

        # index for semantic search
        self.vector_index.add(doc_id, text)
        database.log_action(doc_id, "indexed_for_search", f"embedding_mode={self.embedding_model.mode}")

        return {
            "classification": classification,
            "metadata": metadata,
            "completeness_check": completeness,
            "summary": summary["summary"],
        }

    def answer_question(self, doc_id: str, text: str, question: str) -> dict:
        database.log_action(doc_id, "question_asked", question)
        return self.qa_agent.run(text, question)

    def semantic_search(self, query: str, top_k: int = 5) -> dict:
        return self.search_agent.run(query, top_k=top_k)
