"""Retrieval policy normalization."""

from typing import Any


class RetrievalPolicy:
    """Owner for retrieval policy normalization."""

    def normalize(self, rag_policy: dict[str, Any] | None) -> dict[str, Any]:
        """Normalize the raw request policy into a stable internal shape."""
        raw = rag_policy or {}
        enabled = bool(raw.get("enabled")) if "enabled" in raw else bool(raw)
        allowed_scopes = [
            str(scope).strip()
            for scope in raw.get("allowed_scopes", raw.get("scopes", []))
            if str(scope).strip()
        ]
        try:
            top_k = int(raw.get("top_k", 6))
        except (TypeError, ValueError):
            top_k = 6
        top_k = max(1, min(top_k, 20))

        try:
            min_confidence = float(raw.get("min_confidence", 0.0))
        except (TypeError, ValueError):
            min_confidence = 0.0

        fallback_behavior = str(raw.get("fallback_behavior", "answer_without_sources")).strip()
        if fallback_behavior not in {
            "answer_without_sources",
            "refuse_if_unavailable",
            "warn_if_unavailable",
        }:
            fallback_behavior = "answer_without_sources"

        return {
            "enabled": enabled,
            "allowed_scopes": allowed_scopes,
            "top_k": top_k,
            "min_confidence": max(0.0, min(min_confidence, 1.0)),
            "require_citations": bool(raw.get("require_citations", True)),
            "fallback_behavior": fallback_behavior,
            "language": str(raw.get("language", "pt-BR")).strip() or "pt-BR",
        }

    def describe(self, rag_policy: dict[str, Any]) -> dict[str, Any]:
        """Return the normalized policy used by the orchestration flow."""
        normalized = self.normalize(rag_policy)
        return {
            "owner": "application.retrieval.retrieval_policy",
            "enabled": normalized["enabled"],
            "allowed_scopes": normalized["allowed_scopes"],
            "top_k": normalized["top_k"],
            "min_confidence": normalized["min_confidence"],
            "require_citations": normalized["require_citations"],
            "fallback_behavior": normalized["fallback_behavior"],
            "language": normalized["language"],
            "raw_policy": rag_policy,
        }
