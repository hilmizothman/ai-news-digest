"""
tests/test_email_sender.py - Unit tests for email_sender.py
"""

import smtplib
from unittest.mock import MagicMock, patch

import pytest

from email_sender import build_html_email, send_digest
from scraper import Article


SAMPLE_ARTICLES = [
    Article(
        title="GPT-5 Released",
        url="https://example.com/gpt5",
        source="TechCrunch AI",
        date="2024-06-01",
        summary="OpenAI releases GPT-5 with remarkable capabilities. It surpasses all prior benchmarks.",
    ),
    Article(
        title="New AI Chip by Nvidia",
        url="https://example.com/nvidia-chip",
        source="VentureBeat AI",
        date="2024-06-02",
        summary="Nvidia unveils its next-gen AI accelerator chip. Performance gains are significant.",
    ),
]


class TestBuildHtmlEmail:
    """Tests for build_html_email()."""

    def test_returns_string(self):
        html = build_html_email(SAMPLE_ARTICLES, "test@example.com")
        assert isinstance(html, str)

    def test_contains_article_titles(self):
        html = build_html_email(SAMPLE_ARTICLES, "test@example.com")
        assert "GPT-5 Released" in html
        assert "New AI Chip by Nvidia" in html

    def test_contains_urls(self):
        html = build_html_email(SAMPLE_ARTICLES, "test@example.com")
        assert "https://example.com/gpt5" in html
        assert "https://example.com/nvidia-chip" in html

    def test_contains_sources(self):
        html = build_html_email(SAMPLE_ARTICLES, "test@example.com")
        assert "TechCrunch AI" in html
        assert "VentureBeat AI" in html

    def test_contains_recipient(self):
        html = build_html_email(SAMPLE_ARTICLES, "test@example.com")
        assert "test@example.com" in html

    def test_valid_html_structure(self):
        html = build_html_email(SAMPLE_ARTICLES, "test@example.com")
        assert "<html" in html
        assert "</html>" in html
        assert "<!DOCTYPE html>" in html

    def test_empty_articles(self):
        html = build_html_email([], "test@example.com")
        assert isinstance(html, str)
        assert "<html" in html


class TestSendDigest:
    """Tests for send_digest()."""

    def _env(self) -> dict:
        return {
            "GMAIL_ADDRESS": "sender@gmail.com",
            "GMAIL_APP_PASSWORD": "testpassword",
            "EMAIL_TO": "recipient@example.com",
        }

    @patch("email_sender.smtplib.SMTP")
    def test_send_success(self, mock_smtp_cls):
        """Should send email without raising when SMTP succeeds."""
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        with patch.dict("os.environ", self._env()):
            send_digest(SAMPLE_ARTICLES)

        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("sender@gmail.com", "testpassword")
        mock_server.sendmail.assert_called_once()

    def test_missing_env_vars_raises(self):
        """Should raise EnvironmentError when env vars are missing."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(EnvironmentError):
                send_digest(SAMPLE_ARTICLES)

    @patch("email_sender.smtplib.SMTP")
    def test_smtp_auth_error_propagates(self, mock_smtp_cls):
        """SMTPAuthenticationError should propagate to caller."""
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Bad credentials")
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        with patch.dict("os.environ", self._env()):
            with pytest.raises(smtplib.SMTPAuthenticationError):
                send_digest(SAMPLE_ARTICLES)

    @patch("email_sender.smtplib.SMTP")
    def test_smtp_generic_error_propagates(self, mock_smtp_cls):
        """Generic SMTPException should propagate to caller."""
        mock_server = MagicMock()
        mock_server.sendmail.side_effect = smtplib.SMTPException("Server error")
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        with patch.dict("os.environ", self._env()):
            with pytest.raises(smtplib.SMTPException):
                send_digest(SAMPLE_ARTICLES)

    @patch("email_sender.smtplib.SMTP")
    def test_sendmail_called_with_correct_recipient(self, mock_smtp_cls):
        """sendmail should target the EMAIL_TO address."""
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        env = self._env()
        with patch.dict("os.environ", env):
            send_digest(SAMPLE_ARTICLES)

        call_args = mock_server.sendmail.call_args
        assert call_args[0][1] == ["recipient@example.com"]
