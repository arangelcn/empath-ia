"""Safety node."""

from __future__ import annotations

import unicodedata

from ...llm.structured_outputs import SafetyOutput


class SafetyNode:
    """Evaluate the generated answer against safety policies."""

    def __call__(self, state):
        state.node_trace.append("safety")
        generation = state.generation_result or {}
        response_text = self._normalize((generation.get("text") or ""))
        user_text = self._normalize((state.user_message or ""))

        severity = "low"
        actions: list[str] = []
        allow_response = True

        high_risk_markers = [
            "suic",
            "me matar",
            "acabar com tudo",
            "autoagress",
            "não aguento mais",
            "quero morrer",
        ]
        medium_risk_markers = [
            "crise",
            "pânico",
            "panico",
            "desesperado",
            "não consigo continuar",
            "nao consigo continuar",
            "sem saída",
            "sem saida",
            "ataque de ansiedade",
        ]
        risky_response_markers = [
            "como se matar",
            "forma mais rapida",
            "dose letal",
            "machucar outra pessoa",
        ]

        if any(marker in user_text for marker in high_risk_markers):
            severity = "high"
            actions = ["crisis_protocol", "urgent_support_guidance"]
        elif any(marker in user_text for marker in medium_risk_markers):
            severity = "medium"
            actions = ["supportive_grounding", "monitor_risk"]

        if any(marker in response_text for marker in risky_response_markers):
            severity = "high"
            actions = ["review_generated_content", "restrict_harmful_specificity"]
            allow_response = False
            state.warnings.append("generated_response_flagged_for_harmful_specificity")

        if state.retrieval_result and not state.retrieval_result.get("success", True):
            state.warnings.append("retrieval_unavailable")

        if state.citations and not any(token in response_text for token in ("fonte", "segundo", "refer", "[1]", "[2]", "[3]")):
            state.warnings.append("response_has_retrieval_but_no_explicit_grounding_language")

        state.safety_result = SafetyOutput(
            severity=severity,
            allow_response=allow_response,
            actions=actions,
        ).model_dump()
        return state

    def _normalize(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value.lower())
        return "".join(char for char in normalized if not unicodedata.combining(char))
