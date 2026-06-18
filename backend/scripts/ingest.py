"""CLI entry point: crawl one or all sources and index into Postgres.

Usage:
    python scripts/ingest.py                          # crawl all sources (default limits)
    python scripts/ingest.py --source revenue         # revenue only
    python scripts/ingest.py --source citizensinformation --max-pages 500
    python scripts/ingest.py --source dsp hse rtb     # multiple sources

Available sources: citizensinformation, revenue, dsp, hse, rtb, wrc
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal
from app.ingestion.pipeline import ingest_pages
from app.ingestion.sources import SOURCES
from app.ingestion.web_crawler import crawl

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


async def ingest_source(source_name: str, max_pages: int | None) -> dict:
    config = SOURCES[source_name]
    limit = max_pages or config.get("default_max_pages", 100)

    logger.info("=== Crawling: %s (max %d pages) ===", source_name, limit)
    pages = await crawl(config, max_pages=limit)
    logger.info("[%s] Crawled %d pages — indexing...", source_name, len(pages))

    async with AsyncSessionLocal() as session:
        stats = await ingest_pages(session, pages)

    logger.info(
        "[%s] Done: %d new, %d updated, %d skipped, %d chunks",
        source_name,
        stats["new"], stats["updated"], stats["skipped"], stats["chunks_created"],
    )
    return stats


async def main(sources: list[str], max_pages: int | None) -> None:
    totals = {"new": 0, "updated": 0, "skipped": 0, "chunks_created": 0}

    for source_name in sources:
        if source_name not in SOURCES:
            logger.error("Unknown source '%s'. Available: %s", source_name, ", ".join(SOURCES))
            sys.exit(1)
        stats = await ingest_source(source_name, max_pages)
        for k in totals:
            totals[k] += stats[k]

    if len(sources) > 1:
        logger.info(
            "=== All sources complete: %d new, %d updated, %d skipped, %d chunks ===",
            totals["new"], totals["updated"], totals["skipped"], totals["chunks_created"],
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crawl and index Irish public service sources")
    parser.add_argument(
        "--source",
        nargs="+",
        default=list(SOURCES.keys()),
        metavar="SOURCE",
        help=(
            f"Source(s) to crawl. One or more of: {', '.join(SOURCES.keys())}. "
            "Defaults to all sources."
        ),
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        metavar="N",
        help="Page limit per source (overrides each source's default).",
    )
    args = parser.parse_args()
    asyncio.run(main(args.source, args.max_pages))
