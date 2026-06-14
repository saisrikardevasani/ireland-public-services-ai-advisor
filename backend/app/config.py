from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database — two URLs because Alembic uses a sync driver, FastAPI uses async
    database_url: str = "postgresql+asyncpg://advisor:advisor@localhost:5432/advisor"
    database_sync_url: str = "postgresql://advisor:advisor@localhost:5432/advisor"

    # Cache
    redis_url: str = "redis://localhost:6379"

    # LLM provider: "nvidia" (free tier) or "anthropic"
    llm_provider: str = "nvidia"

    # NVIDIA API (OpenAI-compatible) — free at build.nvidia.com
    nvidia_api_key: str = ""
    nvidia_model: str = "meta/llama-3.3-70b-instruct"

    # Anthropic fallback — empty string = disabled
    anthropic_api_key: str = ""

    # Embeddings
    # Local dev default: small model (134 MB, 384-dim, CPU-friendly)
    # Production: BAAI/bge-m3 (2.2 GB, 1024-dim) — change EMBEDDING_DIM too
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384

    # Retrieval — how many candidates each retriever returns before RRF fusion
    bm25_top_k: int = 20
    dense_top_k: int = 20
    # Final chunks sent to the LLM as context
    final_top_k: int = 5

    # Reranker (v0.3) — cross-encoder reranking after RRF fusion
    reranker_model: str = "BAAI/bge-reranker-base"
    reranker_enabled: bool = True

    # App
    debug: bool = False


settings = Settings()
