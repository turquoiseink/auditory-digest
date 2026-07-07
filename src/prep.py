"""
prep.py — deterministic fetch across all 3 tiers + dedupe + seen-filter.
Writes state/candidates.json and state/context.json for the model to read.
No LLM here.

Source health is reported by ACTUAL YIELD (candidate count per source), not
just whether the fetch function raised an exception — a rate-limited source
that returns 0 results without erroring used to show as "ok", which is
exactly what happened with a real OpenAlex outage. Now it shows as a real
number, and the PDF footer/editorial can tell a quiet day from a broken one.
"""
from __future__ import annotations
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import fetch_papers
import fetch_flagship
import reading_log

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "state")
LOG_XLSX = os.path.join(STATE, "reading_log.xlsx")
CANON_PROGRESS = os.path.join(STATE, "canon_progress.json")
CANDIDATES = os.path.join(STATE, "candidates.json")
CONTEXT = os.path.join(STATE, "context.json")
ATTEMPT = os.path.join(STATE, "attempt.json")
EMAIL = os.environ.get("CONTACT_EMAIL", "")
LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS", "2"))


def main():
    today = dt.date.today()
    since = today - dt.timedelta(days=LOOKBACK_DAYS)
    seen = reading_log.load_seen(LOG_XLSX)
    try:
        canon_progress = json.load(open(CANON_PROGRESS, encoding="utf-8"))
    except Exception:
        canon_progress = {"served": []}

    sources, candidates = {}, []
    for label, fn in [
        ("Flagship journals (Tier 1)", lambda: fetch_flagship.fetch_all_flagship(since, today, EMAIL)),
        ("bioRxiv deep scan (Tier 2)", lambda: fetch_papers.fetch_biorxiv(since, today, EMAIL)),
        ("OpenAlex (Tier 3)", lambda: fetch_papers.fetch_openalex(since, today, EMAIL)),
        ("PubMed (Tier 3)", lambda: fetch_papers.fetch_pubmed(since, today, EMAIL)),
        ("arXiv (Tier 3)", lambda: fetch_papers.fetch_arxiv(since, today, EMAIL)),
    ]:
        try:
            got = fn()
            sources[label] = {"ok": True, "count": len(got)}
            candidates.extend(got)
        except Exception as e:
            sources[label] = {"ok": False, "count": 0, "error": str(e)[:200]}

    candidates = fetch_papers.dedupe(candidates)
    candidates = [c for c in candidates
                  if reading_log._seen_key(c.get("title", ""), c.get("doi", "")) not in seen]
    for i, c in enumerate(candidates):
        c["candidate_id"] = i

    os.makedirs(STATE, exist_ok=True)
    json.dump(candidates, open(CANDIDATES, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    json.dump({
        "date": today.isoformat(),
        "rotation": "canon" if today.toordinal() % 2 == 1 else "new",
        "canon_served": canon_progress.get("served", []),
        "sources": sources,
        "n_candidates": len(candidates),
    }, open(CONTEXT, "w", encoding="utf-8"), indent=2)
    json.dump({"count": 0}, open(ATTEMPT, "w", encoding="utf-8"))  # fresh cap for today
    print(f"prep: {len(candidates)} candidates after dedupe+seen-filter")
    for label, status in sources.items():
        print(f"  {label}: {status}")


if __name__ == "__main__":
    main()
