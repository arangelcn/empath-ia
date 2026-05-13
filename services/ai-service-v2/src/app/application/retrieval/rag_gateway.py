"""RAG gateway scaffold."""


class RAGGateway:
    """Future adapter for retrieval requests to the knowledge boundary."""

    def __init__(self, knowledge_service_url: str) -> None:
        self.knowledge_service_url = knowledge_service_url

    def describe(self) -> dict[str, object]:
        """Describe the scaffold retrieval gateway."""
        return {
            "owner": "application.retrieval.rag_gateway",
            "status": "scaffold",
            "knowledge_service_url": self.knowledge_service_url,
        }
