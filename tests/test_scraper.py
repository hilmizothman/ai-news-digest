"""
tests/test_scraper.py - Unit tests for scraper.py
"""

import pytest
import responses as responses_lib

from scraper import (
    Article,
    extract_articles_from_soup,
    fetch_feed,
    scrape_top_articles,
)
from bs4 import BeautifulSoup


SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test AI Feed</title>
    <link>https://example.com</link>
    <item>
      <title>AI Breakthrough 1</title>
      <link>https://example.com/ai-breakthrough-1</link>
      <pubDate>Mon, 01 Jan 2024 10:00:00 +0000</pubDate>
      <description>First article about AI breakthroughs in 2024.</description>
    </item>
    <item>
      <title>AI Breakthrough 2</title>
      <link>https://example.com/ai-breakthrough-2</link>
      <pubDate>Tue, 02 Jan 2024 10:00:00 +0000</pubDate>
      <description>Second article about neural networks.</description>
    </item>
    <item>
      <title>AI Breakthrough 3</title>
      <link>https://example.com/ai-breakthrough-3</link>
      <pubDate>Wed, 03 Jan 2024 10:00:00 +0000</pubDate>
      <description>Third article about large language models.</description>
    </item>
  </channel>
</rss>"""


class TestFetchFeed:
    """Tests for fetch_feed()."""

    @responses_lib.activate
    def test_fetch_feed_success(self):
        """Should return BeautifulSoup when request succeeds."""
        responses_lib.add(
            responses_lib.GET,
            "https://example.com/feed",
            body=SAMPLE_RSS,
            status=200,
            content_type="application/rss+xml",
        )
        result = fetch_feed("https://example.com/feed")
        assert result is not None
        assert result.find("title") is not None

    @responses_lib.activate
    def test_fetch_feed_http_error(self):
        """Should return None on HTTP 404."""
        responses_lib.add(
            responses_lib.GET,
            "https://example.com/feed",
            status=404,
        )
        result = fetch_feed("https://example.com/feed")
        assert result is None

    @responses_lib.activate
    def test_fetch_feed_timeout(self):
        """Should return None on connection timeout."""
        import requests as req
        responses_lib.add(
            responses_lib.GET,
            "https://example.com/feed",
            body=req.exceptions.ConnectTimeout(),
        )
        result = fetch_feed("https://example.com/feed")
        assert result is None

    @responses_lib.activate
    def test_fetch_feed_request_exception(self):
        """Should return None on generic request error."""
        import requests as req
        responses_lib.add(
            responses_lib.GET,
            "https://example.com/feed",
            body=req.exceptions.ConnectionError("Network error"),
        )
        result = fetch_feed("https://example.com/feed")
        assert result is None


class TestExtractArticles:
    """Tests for extract_articles_from_soup()."""

    def test_extracts_correct_number(self):
        """Should respect max_items limit."""
        soup = BeautifulSoup(SAMPLE_RSS, features="xml")
        articles = extract_articles_from_soup(soup, "Test Source", max_items=2)
        assert len(articles) == 2

    def test_article_fields(self):
        """Articles should have correct title, url, source, date."""
        soup = BeautifulSoup(SAMPLE_RSS, features="xml")
        articles = extract_articles_from_soup(soup, "Test Source", max_items=1)
        art = articles[0]
        assert art.title == "AI Breakthrough 1"
        assert art.url == "https://example.com/ai-breakthrough-1"
        assert art.source == "Test Source"
        assert art.date == "2024-01-01"

    def test_https_enforced(self):
        """http:// URLs should be converted to https://."""
        rss = SAMPLE_RSS.replace(
            "https://example.com/ai-breakthrough-1",
            "http://example.com/ai-breakthrough-1",
        )
        soup = BeautifulSoup(rss, features="xml")
        articles = extract_articles_from_soup(soup, "Test Source", max_items=1)
        assert articles[0].url.startswith("https://")

    def test_empty_feed_returns_empty_list(self):
        """Empty RSS feed should return empty list."""
        empty_rss = '<?xml version="1.0"?><rss><channel></channel></rss>'
        soup = BeautifulSoup(empty_rss, features="xml")
        articles = extract_articles_from_soup(soup, "Empty", max_items=5)
        assert articles == []


class TestScrapeTopArticles:
    """Tests for scrape_top_articles()."""

    @responses_lib.activate
    def test_scrape_returns_up_to_total(self):
        """Should return at most `total` articles."""
        responses_lib.add(
            responses_lib.GET,
            "https://example.com/feed",
            body=SAMPLE_RSS,
            status=200,
            content_type="application/rss+xml",
        )
        feeds = [{"name": "Test Feed", "url": "https://example.com/feed"}]
        articles = scrape_top_articles(feeds=feeds, total=2)
        assert len(articles) <= 2

    @responses_lib.activate
    def test_scrape_skips_failed_feed(self):
        """Failed feeds should be skipped gracefully, not raise."""
        responses_lib.add(
            responses_lib.GET,
            "https://example.com/bad-feed",
            status=500,
        )
        feeds = [{"name": "Bad Feed", "url": "https://example.com/bad-feed"}]
        articles = scrape_top_articles(feeds=feeds, total=5)
        assert isinstance(articles, list)

    @responses_lib.activate
    def test_scrape_multiple_feeds(self):
        """Articles should be gathered across multiple feeds."""
        for i in range(1, 3):
            responses_lib.add(
                responses_lib.GET,
                f"https://example.com/feed{i}",
                body=SAMPLE_RSS,
                status=200,
                content_type="application/rss+xml",
            )
        feeds = [
            {"name": f"Feed {i}", "url": f"https://example.com/feed{i}"}
            for i in range(1, 3)
        ]
        articles = scrape_top_articles(feeds=feeds, total=5)
        assert len(articles) == 4  # 2 items per feed × 2 feeds
