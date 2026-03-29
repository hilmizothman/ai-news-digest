# 🤖 AI News Digest

Automatically scrapes the top 5 AI news breakthroughs from reputable sources, summarises each article, and delivers a beautifully formatted HTML email digest to your inbox.

---

## Overview

| Stage | Description |
|-------|-------------|
| **Scrape** | Pulls the latest items from 5 AI-focused RSS feeds |
| **Summarise** | Extracts a concise 2-3 sentence summary per article |
| **Email** | Sends a styled HTML digest via Gmail SMTP |

---

## Sources

| Source | RSS Feed |
|--------|----------|
| TechCrunch AI | `https://techcrunch.com/category/artificial-intelligence/feed/` |
| VentureBeat AI | `https://venturebeat.com/category/ai/feed/` |
| MIT Technology Review | `https://www.technologyreview.com/feed/` |
| The Verge AI | `https://www.theverge.com/rss/ai-artificial-intelligence/index.xml` |
| ArXiv AI | `https://rss.arxiv.org/rss/cs.AI` |

---

## Requirements

- Python 3.10+
- A Gmail account with an **App Password** (not your regular password)

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/hilmizothman/ai-news-digest.git
cd ai-news-digest
```

### 2. Create a virtual environment (optional but recommended)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```dotenv
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_TO=recipient@example.com
```

> **Important:** `GMAIL_APP_PASSWORD` must be a [Gmail App Password](https://support.google.com/accounts/answer/185833), not your regular Google account password.

---

## Usage

Run the digest manually:

```bash
python main.py
```

### Automate with cron (Linux/macOS)

Run daily at 8 AM:

```cron
0 8 * * * cd /path/to/ai-news-digest && /path/to/python main.py >> digest.log 2>&1
```

### Automate with Task Scheduler (Windows)

1. Open Task Scheduler → Create Basic Task
2. Trigger: Daily at desired time
3. Action: `python C:\path\to\ai-news-digest\main.py`

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GMAIL_ADDRESS` | Gmail sender address | ✅ |
| `GMAIL_APP_PASSWORD` | Gmail App Password (spaces allowed) | ✅ |
| `EMAIL_TO` | Recipient email address | ✅ |

---

## Project Structure

```
ai-news-digest/
├── main.py            # Entry point — orchestrates the pipeline
├── scraper.py         # RSS feed scraper
├── summarizer.py      # Article text enrichment & summarisation
├── email_sender.py    # HTML email builder & Gmail SMTP sender
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variable template
├── .gitignore
├── README.md
└── tests/
    ├── test_scraper.py       # Unit tests for scraper
    └── test_email_sender.py  # Unit tests for email sender
```

---

## Running Tests

```bash
pytest tests/ -v
```

All 23 tests should pass covering:
- Successful RSS feed fetching
- HTTP error and timeout handling
- Article field extraction and HTTPS enforcement
- HTML email rendering
- SMTP send flow (mocked)
- Missing environment variable errors

---

## Security Notes

- No credentials are stored in source code — all via environment variables
- `.env` is listed in `.gitignore` and will never be committed
- All outbound HTTP calls use HTTPS only
- No `eval()` or `exec()` calls in the codebase

---

## License

MIT
