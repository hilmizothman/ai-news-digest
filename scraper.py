"""
scraper.py - Scrapes top AI news articles from reputable RSS feeds.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
    },
    {
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/category/ai/feed/",
    },
    {
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com/feed/",
    },
    {
        "name": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    },
    {
        "name": "ArXiv AI",
        "url": "https://rss.arxiv.org/rss/cs.AI",
    },
]


@dataclass
class Article:
    """Represents a scraped news article."""

    title: str
    url: str
    source: str
    date: str
    summary: str = ""


def fetch_feed(feed_url: str, timeout: int = 10) -> Optional[BeautifulSoup]:
    """
    Fetch and parse an RSS feed URL.

    Args:
        feed_url: The URL of the RSS feed to fetch.
        timeout: Request timeout in seconds.

    Returns:
        A BeautifulSoup object if successful, None otherwise.
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (compatible; AINewsDigest/1.0; "
                "+https://github.com/hilmizothman/ai-news-digest)"
            )
        }
        response = requests.get(feed_url, timeout=timeout, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.content, features="xml")
    except requests.exceptions.Timeout:
        logger.error("Timeout fetching feed: %s", feed_url)
    except requests.exceptions.HTTPError as exc:
        logger.error("HTTP error fetching feed %s: %s", feed_url, exc)
    except requests.exceptions.RequestException as exc:
        logger.error("Error fetching feed %s: %s", feed_url, exc)
    return None


def parse_item_date(item: BeautifulSoup) -> str:
    """
    Extract and normalise the publication date from an RSS item.

    Args:
        item: A BeautifulSoup tag representing an RSS <item>.

    Returns:
        A formatted date string, or today's date if unavailable.
    """
    date_tags = ["pubDate", "published", "updated", "dc:date"]
    for tag in date_tags:
        node = item.find(tag)
        if node and node.get_text(strip=True):
            raw = node.get_text(strip=True)
            # Attempt common formats against the full raw string
            for fmt in (
                "%a, %d %b %Y %H:%M:%S %z",
                "%a, %d %b %Y %H:%M:%S %Z",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d",
            ):
                try:
                    return datetime.strptime(raw.strip(), fmt).strftime("%Y-%m-%d")
                except ValueError:
                    continue
            # Return the raw value if no format matched
            return raw[:20]
    return datetime.today().strftime("%Y-%m-%d")


def extract_articles_from_soup(
    soup: BeautifulSoup, source_name: str, max_items: int = 2
) -> List[Article]:
    """
    Extract article metadata from a parsed RSS feed.

    Args:
        soup: Parsed RSS BeautifulSoup object.
        source_name: Human-readable source label.
        max_items: Maximum number of articles to extract from this feed.

    Returns:
        List of Article dataclass instances.
    """
    articles: List[Article] = []
    items = soup.find_all("item") or soup.find_all("entry")
    for item in items[:max_items]:
        title_tag = item.find("title")
        link_tag = item.find("link")
        desc_tag = item.find("description") or item.find("summary")

        title = title_tag.get_text(strip=True) if title_tag else "No title"

        # <link> can be a tag with text or an href attribute (Atom feeds)
        if link_tag:
            url = link_tag.get("href") or link_tag.get_text(strip=True)
        else:
            url = ""

        # Ensure HTTPS
        if url.startswith("http://"):
            url = "https://" + url[7:]

        raw_summary = ""
        if desc_tag:
            raw_summary = BeautifulSoup(
                desc_tag.get_text(separator=" ", strip=True), "html.parser"
            ).get_text(strip=True)

        date_str = parse_item_date(item)

        articles.append(
            Article(
                title=title,
                url=url,
                source=source_name,
                date=date_str,
                summary=raw_summary[:500],
            )
        )
    return articles


def scrape_top_articles(
    feeds: Optional[List[dict]] = None, total: int = 5
) -> List[Article]:
    """
    Scrape the top *total* AI news articles across all configured RSS feeds.

    Args:
        feeds: List of feed dicts with 'name' and 'url' keys.
               Defaults to the module-level RSS_FEEDS list.
        total: Total number of articles to return.

    Returns:
        List of Article instances (up to *total* items).
    """
    if feeds is None:
        feeds = RSS_FEEDS

    all_articles: List[Article] = []

    for feed in feeds:
        if len(all_articles) >= total:
            break
        logger.info("Fetching feed: %s", feed["url"])
        soup = fetch_feed(feed["url"])
        if soup is None:
            logger.warning("Skipping feed due to fetch failure: %s", feed["name"])
            continue
        articles = extract_articles_from_soup(soup, feed["name"], max_items=2)
        all_articles.extend(articles)
        logger.info("Got %d article(s) from %s", len(articles), feed["name"])

    return all_articles[:total]
