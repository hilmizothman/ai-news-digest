"""
email_sender.py - Formats and sends the AI news digest HTML email via Gmail SMTP.
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from scraper import Article

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def build_html_email(articles: List[Article], recipient: str) -> str:
    """
    Render a clean HTML email digest from a list of articles.

    Args:
        articles: List of enriched Article instances.
        recipient: Recipient email address (used only for personalisation).

    Returns:
        HTML string ready to be used as email body.
    """
    article_blocks = ""
    for idx, art in enumerate(articles, start=1):
        article_blocks += f"""
        <div class="article">
            <h2>{idx}. <a href="{art.url}">{art.title}</a></h2>
            <p class="meta">
                <span class="source">{art.source}</span> &mdash;
                <span class="date">{art.date}</span>
            </p>
            <p class="summary">{art.summary}</p>
            <p><a href="{art.url}" class="read-more">Read full article &rarr;</a></p>
        </div>
        <hr>
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI News Digest</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                         Helvetica, Arial, sans-serif;
            background: #f5f5f5;
            color: #222;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 680px;
            margin: 32px auto;
            background: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .header {{
            background: #1a1a2e;
            color: #e0e0e0;
            padding: 32px 40px;
        }}
        .header h1 {{
            margin: 0 0 6px;
            font-size: 26px;
            color: #ffffff;
        }}
        .header p {{
            margin: 0;
            font-size: 14px;
            color: #a0a0c0;
        }}
        .content {{
            padding: 32px 40px;
        }}
        .article {{
            margin-bottom: 24px;
        }}
        .article h2 {{
            font-size: 18px;
            margin: 0 0 8px;
        }}
        .article h2 a {{
            color: #1a1a2e;
            text-decoration: none;
        }}
        .article h2 a:hover {{
            text-decoration: underline;
        }}
        .meta {{
            font-size: 13px;
            color: #666;
            margin: 0 0 8px;
        }}
        .source {{
            font-weight: 600;
            color: #444;
        }}
        .summary {{
            font-size: 15px;
            line-height: 1.6;
            margin: 0 0 8px;
        }}
        .read-more {{
            font-size: 13px;
            color: #4a6cf7;
            text-decoration: none;
            font-weight: 600;
        }}
        hr {{
            border: none;
            border-top: 1px solid #ebebeb;
            margin: 24px 0;
        }}
        .footer {{
            background: #f0f0f0;
            padding: 20px 40px;
            font-size: 12px;
            color: #888;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI News Digest</h1>
            <p>Your daily top 5 AI breakthroughs &amp; news</p>
        </div>
        <div class="content">
            {article_blocks}
        </div>
        <div class="footer">
            You are receiving this digest at {recipient}. Powered by AI News Digest.
        </div>
    </div>
</body>
</html>"""
    return html


def send_digest(
    articles: List[Article],
    smtp_host: str = SMTP_HOST,
    smtp_port: int = SMTP_PORT,
) -> None:
    """
    Send the HTML digest email via Gmail SMTP.

    Credentials and recipient are read from environment variables:
        GMAIL_ADDRESS      - sender Gmail address
        GMAIL_APP_PASSWORD - Gmail App Password (not the account password)
        EMAIL_TO           - recipient address

    Args:
        articles: List of enriched Article instances to include in the digest.
        smtp_host: SMTP server hostname.
        smtp_port: SMTP server port (587 for STARTTLS).

    Raises:
        EnvironmentError: If required env vars are missing.
        smtplib.SMTPException: On SMTP-level failures.
    """
    sender = os.environ.get("GMAIL_ADDRESS")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = os.environ.get("EMAIL_TO")

    if not sender or not password or not recipient:
        raise EnvironmentError(
            "Missing required env vars: GMAIL_ADDRESS, GMAIL_APP_PASSWORD, EMAIL_TO"
        )

    html_body = build_html_email(articles, recipient)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🤖 Your Daily AI News Digest"
    msg["From"] = sender
    msg["To"] = recipient

    # Plain-text fallback
    plain_text = "\n\n".join(
        f"{a.title}\n{a.source} | {a.date}\n{a.url}\n{a.summary}" for a in articles
    )
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        logger.info("Connecting to SMTP server %s:%d", smtp_host, smtp_port)
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender, password)
            server.sendmail(sender, [recipient], msg.as_string())
        logger.info("Digest sent successfully to %s", recipient)
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed. Check GMAIL_APP_PASSWORD.")
        raise
    except smtplib.SMTPException as exc:
        logger.error("SMTP error while sending digest: %s", exc)
        raise
