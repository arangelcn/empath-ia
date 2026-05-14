"""Safety domain models."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class SafetyDecision:
    """Outcome of future safety policy evaluation."""

    severity: str = "unknown"
    actions: list[str] = field(default_factory=list)
