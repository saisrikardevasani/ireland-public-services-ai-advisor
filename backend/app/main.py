import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api import chat, feedback, health

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Pre-warm both models into memory so the first real request isn't slow.
    # Health check only returns 200 after this block completes.
    logger.info("Pre-warming embedding model...")
    from app.ingestion.embedder import embed_query
    embed_query("warmup")

    logger.info("Pre-warming reranker model...")
    from app.pipeline.reranker import _get_reranker
    _get_reranker()

    logger.info("Models ready.")
    yield


limiter = Limiter(key_func=get_remote_address, default_limits=["20/minute"])

app = FastAPI(
    title="Ireland Public Services AI Advisor",
    version="0.6.0",
    description="RAG system over Irish government and EU legislative sources.",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

_raw = os.getenv("CORS_ORIGINS", "http://localhost:3000")
_origins = [o.strip() for o in _raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(feedback.router)
