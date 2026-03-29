"""
main.py - Entry point for the AI News Digest application.

Pipeline:
    1. Scrape top 5 AI news articles from RSS feeds.
    2. Enrich/summarize each article.
    3. Send an HTML email digest.
"""

import logging
import os
import sys

from dotenv import load_dotenv

from email_sender import send_digest
from scraper import scrape_top_articles
from summarizer import enrich_articles


def configure_logging() -> None:
    """Configure root logger for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main() -> int:
    """
    Orchestrate the full pipeline: scrape → summarize → email.

    Returns:
        0 on success, 1 on failure.
    """
    configure_logging()
    logger = logging.getLogger(__name__)

    # Load .env file if present (development convenience)
    load_dotenv()

    logger.info("=== AI News Digest starting ===")

    # Stage 1: Scrape
    logger.info("Stage 1/3: Scraping articles...")
    articles = scrape_top_articles(total=5)
    if not articles:
        logger.error("No articles scraped. Aborting.")
        return 1
    logger.info("Scraped %d article(s).", len(articles))

    # Stage 2: Enrich / Summarize
    logger.info("Stage 2/3: Enriching summaries...")
    articles = enrich_articles(articles)

    # Stage 3: Send Email
    logger.info("Stage 3/3: Sending email digest...")
    try:
        send_digest(articles)
    except EnvironmentError as exc:
        logger.error("Configuration error: %s", exc)
        return 1
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to send digest: %s", exc)
        return 1

    logger.info("=== AI News Digest complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
