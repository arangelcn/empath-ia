"""Service client descriptors for external boundaries kept outside the monolith."""

from dataclasses import dataclass


@dataclass(slots=True)
class ExternalServiceClient:
    """Reference to an external service kept beyond this migration step."""

    name: str
    base_url: str
