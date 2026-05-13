"""Citation formatting for grounded answers."""


class CitationService:
    """Owner for grounding and citation formatting."""

    def filter_results(self, results: list[dict], min_confidence: float) -> list[dict]:
        """Keep only retrieval hits that satisfy the minimum configured confidence."""
        if min_confidence <= 0:
            return list(results)

        filtered = []
        for item in results:
            score = self._extract_score(item)
            if score is None or score >= min_confidence:
                filtered.append(item)
        return filtered

    def format_results(self, retrieval_result: dict | None) -> list[dict]:
        """Extract normalized citation metadata from retrieval results."""
        if not retrieval_result:
            return []

        citations = []
        for index, item in enumerate(retrieval_result.get("results", []), start=1):
            citation = item.get("citation") or {}
            citations.append(
                {
                    "index": index,
                    "chunk_id": item.get("chunk_id"),
                    "document_id": citation.get("document_id"),
                    "document_version": citation.get("document_version"),
                    "title": citation.get("title"),
                    "section": citation.get("section"),
                    "score": self._extract_score(item),
                    "reason": item.get("retrieval_reason"),
                }
            )
        return citations

    def build_grounding_context(self, retrieval_result: dict | None) -> str:
        """Render retrieved evidence into a compact prompt block."""
        if not retrieval_result:
            return ""

        results = retrieval_result.get("results", [])
        if not results:
            return ""

        lines = ["CONTEXTO RECUPERADO (use apenas se realmente ajudar):"]
        for index, item in enumerate(results, start=1):
            citation = item.get("citation") or {}
            title = citation.get("title") or "Documento sem titulo"
            section = citation.get("section") or "secao nao informada"
            snippet = " ".join(str(item.get("content") or "").split())
            if len(snippet) > 500:
                snippet = f"{snippet[:497].rstrip()}..."
            lines.append(f"[{index}] {title} | {section}")
            lines.append(f"Trecho: {snippet}")
        return "\n".join(lines)

    def build_citation_instruction(self, citations: list[dict], require_citations: bool) -> str:
        """Build a concise instruction for how the model should reference evidence."""
        if not citations:
            return ""

        indexes = ", ".join(f"[{citation['index']}]" for citation in citations)
        if require_citations:
            return (
                "Se usar informacoes do contexto recuperado, cite explicitamente os itens "
                f"{indexes} no corpo da resposta."
            )
        return (
            "Ha contexto recuperado disponivel. Use apenas quando ele aumentar a precisao, "
            "sem inventar fonte."
        )

    def describe(self) -> dict[str, object]:
        """Describe the citation service."""
        return {
            "owner": "application.retrieval.citations",
            "status": "active",
        }

    def _extract_score(self, item: dict) -> float | None:
        scores = item.get("scores") or {}
        for key in ("final", "rerank", "lexical", "vector"):
            raw_score = scores.get(key)
            if raw_score is None:
                continue
            try:
                return float(raw_score)
            except (TypeError, ValueError):
                return None
        return None
