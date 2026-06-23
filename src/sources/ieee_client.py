from datetime import datetime, timedelta
from typing import List, Dict

import requests

from ..config import IEEE_API_KEY, IEEE_KEYWORDS, MAX_PAPERS_PER_SOURCE

IEEE_API_URL = "https://ieeexploreapi.ieee.org/api/v1/search/articles"

Paper = Dict


def search() -> List[Paper]:
    if not IEEE_API_KEY:
        return []

    past_day = (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%d")
    query = " OR ".join(f'({k})' for k in IEEE_KEYWORDS)

    params = {
        "apikey": IEEE_API_KEY,
        "querytext": query,
        "max_records": MAX_PAPERS_PER_SOURCE,
        "sort_field": "article_number",
        "sort_order": "desc",
    }

    try:
        resp = requests.get(IEEE_API_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if "articles" not in data or not data["articles"]:
            print(f"[WARN] IEEE returned no articles. Response keys: {list(data.keys())}")
            print(f"[WARN] IEEE total_records: {data.get('total_records', 'N/A')}")
            return []
    except Exception as e:
        print(f"[WARN] IEEE search failed: {e}")
        return []

    papers = []
    for article in data.get("articles", []):
        title = article.get("title", "")
        if not title:
            continue
        abstract = article.get("abstract", "")
        authors = [a.get("full_name", "") for a in article.get("authors", {}).get("authors", [])]
        doi = article.get("doi", "")
        link = f"https://doi.org/{doi}" if doi else article.get("html_link", "")
        papers.append({
            "id": f"ieee-{article.get('article_number', title[:40])}",
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "categories": [article.get("publication_title", "IEEE")],
            "published": article.get("publication_date", ""),
            "link": link,
            "source": "IEEE",
        })

    return papers
