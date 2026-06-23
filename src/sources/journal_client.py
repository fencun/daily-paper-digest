from datetime import datetime, timedelta
from typing import List, Dict

import feedparser
import requests

from ..config import JOURNAL_FEEDS, MAX_PAPERS_PER_SOURCE

Paper = Dict


def fetch_rss(url: str, journal_name: str) -> List[Paper]:
    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception:
        return []

    papers = []
    past_day = datetime.utcnow() - timedelta(days=7)

    for entry in feed.entries[:MAX_PAPERS_PER_SOURCE]:
        published_parsed = entry.get("published_parsed")
        published_str = entry.get("published", "")
        if published_parsed:
            pub_date = datetime(*published_parsed[:6])
            if pub_date < past_day:
                continue
            published_str = pub_date.strftime("%Y-%m-%d")

        title = entry.get("title", "").strip()
        if not title:
            continue

        summary_text = entry.get("summary", entry.get("description", "")).strip()
        link = entry.get("link", "")
        authors = []
        if hasattr(entry, "authors"):
            authors = [a.get("name", "") for a in entry.authors]

        papers.append({
            "id": f"{journal_name.replace(' ', '_')}-{title[:50]}",
            "title": title,
            "abstract": summary_text,
            "authors": authors,
            "categories": [journal_name],
            "published": published_str,
            "link": link,
            "source": journal_name,
        })

    return papers


def search() -> List[Paper]:
    all_papers = []
    for name, url in JOURNAL_FEEDS.items():
        papers = fetch_rss(url, name)
        all_papers.extend(papers)
    return all_papers
