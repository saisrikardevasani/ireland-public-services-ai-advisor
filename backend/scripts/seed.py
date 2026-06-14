"""Load fixture documents into the database for local development.

Loads both Citizens Information and Revenue.ie fixture files.
Idempotent — rerun safely; unchanged documents are skipped.

Usage:
    python scripts/seed.py
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.ingestion.pipeline import ingest_pages

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

FIXTURE_FILES = [
    FIXTURES_DIR / "citizens_information.json",
    FIXTURES_DIR / "revenue_ie.json",
]


async def main() -> None:
    all_pages = []
    for path in FIXTURE_FILES:
        pages = json.loads(path.read_text())
        logger.info("Loaded %d pages from %s", len(pages), path.name)
        all_pages.extend(pages)

    logger.info("Total: %d documents to ingest", len(all_pages))
    logger.info("Embedding and indexing (first run downloads models)...")

    async with AsyncSessionLocal() as session:
        stats = await ingest_pages(session, all_pages)

    logger.info(
        "Done: %d new, %d updated, %d skipped, %d chunks created",
        stats["new"], stats["updated"], stats["skipped"], stats["chunks_created"],
    )
    logger.info("Database ready. Start the backend with: make backend")


if __name__ == "__main__":
    asyncio.run(main())
