import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sources import arxiv_client, ieee_client, journal_client
from src.summarizer import summarize
from src.report import generate_daily_report, update_readme_index
from src.notifier import send_notification
from src.config import MAX_TOTAL_PAPERS


def deduplicate(papers_list):
    seen_titles = set()
    deduped = []
    for p in papers_list:
        key = p["title"].lower().strip()[:80]
        if key not in seen_titles:
            seen_titles.add(key)
            deduped.append(p)
    return deduped


def run():
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    print(f"[INFO] Daily digest for {date_str}")

    all_papers = []

    print("[INFO] Searching arXiv...")
    try:
        all_papers.extend(arxiv_client.search())
    except Exception as e:
        print(f"[WARN] arXiv search failed: {e}")

    print("[INFO] Searching IEEE...")
    try:
        all_papers.extend(ieee_client.search())
    except Exception as e:
        print(f"[WARN] IEEE search failed: {e}")

    print("[INFO] Searching journals...")
    try:
        all_papers.extend(journal_client.search())
    except Exception as e:
        print(f"[WARN] Journal search failed: {e}")

    all_papers = deduplicate(all_papers)
    all_papers = sorted(
        all_papers,
        key=lambda p: str(p.get("published", "")),
        reverse=True,
    )

    if len(all_papers) > MAX_TOTAL_PAPERS:
        all_papers = all_papers[:MAX_TOTAL_PAPERS]

    print(f"[INFO] Total papers found: {len(all_papers)}")

    summary_text = ""
    if all_papers:
        print("[INFO] Generating LLM summary...")
        summary_text = summarize(all_papers)

    filepath = generate_daily_report(all_papers, summary_text, date_str)
    print(f"[INFO] Report saved: {filepath}")

    update_readme_index(date_str, filepath)
    print(f"[INFO] Index updated")

    send_notification(summary_text, date_str)
    print(f"[INFO] Done")


if __name__ == "__main__":
    run()
