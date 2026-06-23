import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict

import requests

from ..config import KEYWORDS, ARXIV_CATEGORIES, MAX_PAPERS_PER_SOURCE

ARXIV_API_URL = "http://export.arxiv.org/api/query"

Paper = Dict

KEYWORD_SET = {kw.lower() for kw in KEYWORDS if kw not in ("GPS Solutions", "Journal of Geodesy")}


def is_relevant(paper: Paper) -> bool:
    text = (paper["title"] + " " + paper.get("abstract", "")).lower()
    return any(kw in text for kw in KEYWORD_SET)


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


def search_category(category: str) -> List[Paper]:
    query = f"cat:{category}"
    params = {
        "search_query": query,
        "start": 0,
        "max_results": MAX_PAPERS_PER_SOURCE,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API_URL}?{urllib.parse.urlencode(params)}"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return parse_response(resp.text)


def search() -> List[Paper]:
    all_papers = []
    for cat in ARXIV_CATEGORIES:
        try:
            papers = search_category(cat)
            all_papers.extend(papers)
        except Exception:
            continue

    relevant = [p for p in all_papers if is_relevant(p)]

    seen = set()
    deduped = []
    for p in relevant:
        key = p["id"]
        if key not in seen:
            seen.add(key)
            deduped.append(p)

    return deduped[:MAX_PAPERS_PER_SOURCE]
