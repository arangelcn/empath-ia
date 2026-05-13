"""App lifespan hooks for ai-service-v2."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from .dependencies import build_container
from .settings import get_settings


logger = logging.getLogger(__name__)


def build_lifespan():
    """Create the FastAPI lifespan manager."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        settings = get_settings()
        app.state.container = build_container(settings)
        logger.info(
            "ai-service-v2 inicializado em modo scaffold (env=%s)",
            settings.environment,
        )
        yield
        logger.info("ai-service-v2 finalizado")

    return lifespan
