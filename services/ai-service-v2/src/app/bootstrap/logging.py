"""Logging bootstrap for ai-service-v2."""

import logging


def configure_logging() -> None:
    """Configure a small, predictable logging setup once per process."""
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
