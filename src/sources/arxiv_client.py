import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict

import requests

from ..config import KEYWORDS, ARXIV_CATEGORIES, MAX_PAPERS_PER_SOURCE

ARXIV_API_URL = "http://export.arxiv.org/api/query"

Paper = Dict

def build_query(keywords: List[str], categories: List[str]) -> str:
    kw_parts = []
    for kw in keywords:
        if kw in ("GPS Solutions", "Journal of Geodesy"):
            continue
        kw_parts.append(f'abs:"{kw}"')
    cat_parts = [f"cat:{c}" for c in categories]
    kw_group = " OR ".join(f"({t})" for t in kw_parts)
    cat_group = " OR ".join(f"({t})" for t in cat_parts)
    return f"({kw_group}) AND ({cat_group})"


def parse_response(xml_text: str) -> List[Paper]:
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }
    root = ET.fromstring(xml_text)
    papers = []
    for entry in root.findall("atom:entry", ns):
        paper_id = entry.find("atom:id", ns).text.strip()
        title = entry.find("atom:title", ns).text.strip().replace("\n", " ").replace("  ", " ")
        summary = entry.find("atom:summary", ns).text.strip().replace("\n", " ").replace("  ", " ")
        published = entry.find("atom:published", ns).text.strip()
        link_el = entry.find("atom:link", ns)
        link = link_el.attrib.get("href", paper_id) if link_el is not None else paper_id
        authors = []
        for author_el in entry.findall("atom:author", ns):
            name_el = author_el.find("atom:name", ns)
            if name_el is not None:
                authors.append(name_el.text.strip())
        categories = []
        for cat_el in entry.findall("arxiv:primary_category", ns):
            categories.append(cat_el.attrib.get("term", ""))
        papers.append({
            "id": paper_id,
            "title": title,
            "abstract": summary,
            "authors": authors,
            "categories": categories,
            "published": published,
            "link": link,
            "source": "arXiv",
        })
    return papers


def search() -> List[Paper]:
    past_day = (datetime.utcnow() - timedelta(days=2)).strftime("%Y%m%d0000")
    query_str = build_query(KEYWORDS, ARXIV_CATEGORIES)
    params = {
        "search_query": query_str,
        "start": 0,
        "max_results": MAX_PAPERS_PER_SOURCE,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API_URL}?{urllib.parse.urlencode(params)}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    papers = parse_response(resp.text)
    for p in papers:
        p["source"] = "arXiv"
    return papers
