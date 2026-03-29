"""
summarizer.py - Enriches articles with fetched full-text summaries.
"""

import logging
import re
from typing import List

import requests
from bs4 import BeautifulSoup

from scraper import Article

logger = logging.getLogger(__name__)


def fetch_article_text(url: str, timeout: int = 10) -> str:
    """
    Fetch the main body text of an article page.

    Args:
        url: The article URL to fetch.
        timeout: Request timeout in seconds.

    Returns:
        Extracted plain text (up to ~2 000 chars), or empty string on failure.
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (compatible; AINewsDigest/1.0; "
                "+https://github.com/hilmizothman/ai-news-digest)"
            )
        }
        response = requests.get(url, timeout=timeout, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Remove boilerplate tags
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # Prefer <article> content, fall back to <main>, then <body>
        container = soup.find("article") or soup.find("main") or soup.find("body")
        if container is None:
            return ""

        paragraphs = container.find_all("p")
        text = " ".join(p.get_text(separator=" ", strip=True) for p in paragraphs)
        return text[:2000]
    except requests.exceptions.Timeout:
        logger.warning("Timeout fetching article: %s", url)
    except requests.exceptions.HTTPError as exc:
        logger.warning("HTTP error for %s: %s", url, exc)
    except requests.exceptions.RequestException as exc:
        logger.warning("Request error for %s: %s", url, exc)
    return ""


def build_summary(text: str, max_sentences: int = 3) -> str:
    """
    Build a 2-3 sentence summary from plain text.

    Splits on sentence boundaries and returns the first *max_sentences*.

    Args:
        text: Source plain text.
        max_sentences: Maximum number of sentences to include.

    Returns:
        A short summary string.
    """
    if not text:
        return "No summary available."

    # Split on sentence-ending punctuation followed by whitespace
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    # Filter out very short fragments
    sentences = [s for s in sentences if len(s) > 20]
    selected = sentences[:max_sentences]
    return " ".join(selected) if selected else text[:300]


def enrich_articles(articles: List[Article]) -> List[Article]:
    """
    Enrich each article's summary by fetching full article text when the
    RSS description is absent or very short.

    Args:
        articles: List of Article instances to enrich in-place.

    Returns:
        The same list with updated summaries.
    """
    for article in articles:
        if len(article.summary) < 100 and article.url:
            logger.info("Fetching full text for: %s", article.title)
            full_text = fetch_article_text(article.url)
            if full_text:
                article.summary = build_summary(full_text)
        else:
            # Still clean up the existing RSS description
            article.summary = build_summary(article.summary)
    return articles
