class SearchAgent:
    name = "search_agent"

    def __init__(self, vector_index):
        self.vector_index = vector_index

    def run(self, query: str, top_k: int = 5) -> dict:
        results = self.vector_index.search(query, top_k=top_k)
        return {
            "agent": self.name,
            "query": query,
            "results": results,
        }
