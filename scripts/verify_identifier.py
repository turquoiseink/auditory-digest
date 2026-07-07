"""
verify_identifier.py — safely add a paper the model found via its own search.

Usage:
    python3 scripts/verify_identifier.py <doi-or-pmid>

This is the verification gate: the model NEVER types a paper's title,
authors, or abstract by hand when adding something from its own search
(browsing, watch-author follow-up, checking a specific journal). Instead it
gives ONLY an identifier, and this script fetches the canonical record from
CrossRef (for a DOI) or PubMed (for a PMID) and appends that — and only
that — to state/model_discovered.json.

Why this matters: the misattribution bug (writing detailed bullets about the
wrong paper under a correct-sounding title) happened because content was
written from memory instead of a verified fetch. This script makes "trust
memory" structurally impossible for anything added this way — if the
identifier doesn't resolve, nothing is added, and the script says so plainly.

After running this for each paper you want to add, run
scripts/merge_discovered.py once to fold them into today's candidate list
with real candidate_ids, before writing selection.json.
"""
from __future__ import annotations
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/src")
import requests

STATE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "state")
DISCOVERED = os.path.join(STATE, "model_discovered.json")
TIMEOUT = 20
UA = "auditory-grouping-digest/3.0 (personal research tool)"


def _looks_like_pmid(s: str) -> bool:
    return bool(re.fullmatch(r"\d{5,9}", s.strip()))


def _from_crossref(doi: str) -> dict | None:
    doi = doi.strip().lower().replace("https://doi.org/", "")
    try:
        r = requests.get(f"https://api.crossref.org/works/{doi}",
                          headers={"User-Agent": UA}, timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        msg = r.json().get("message", {})
        title = (msg.get("title") or [""])[0]
        abstract = re.sub(r"<[^>]+>", "", msg.get("abstract") or "")
        authors = [f'{a.get("given","")} {a.get("family","")}'.strip()
                   for a in msg.get("author", [])]
        venue = (msg.get("container-title") or [""])[0]
        date_parts = (msg.get("published") or msg.get("published-print") or
                      msg.get("published-online") or {}).get("date-parts", [[None]])[0]
        date = "-".join(f"{p:02d}" if i > 0 else str(p)
                        for i, p in enumerate(date_parts) if p) if date_parts and date_parts[0] else ""
        work_type = msg.get("type", "")
        return {
            "title": title, "abstract": abstract, "date": date, "doi": doi,
            "url": f"https://doi.org/{doi}", "venue": venue, "authors": authors,
            "type": work_type, "is_preprint": "preprint" in work_type.lower(),
            "affiliation": "", "country": "",
            "source_api": "CrossRef (model-discovered)", "pool": "model-search",
            "cluster": "model-discovered",
        }
    except Exception as e:
        print(f"CrossRef lookup failed: {e}", file=sys.stderr)
        return None


def _from_pubmed(pmid: str) -> dict | None:
    try:
        r = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params={"db": "pubmed", "id": pmid, "retmode": "xml"},
            headers={"User-Agent": UA}, timeout=TIMEOUT,
        )
        if r.status_code != 200:
            return None
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/src")
        import fetch_flagship
        records = fetch_flagship._parse_pubmed_efetch_xml(r.text)
        if not records:
            return None
        rec = records[0]
        rec["source_api"] = "PubMed (model-discovered)"
        rec["pool"] = "model-search"
        rec["cluster"] = "model-discovered"
        return rec
    except Exception as e:
        print(f"PubMed lookup failed: {e}", file=sys.stderr)
        return None


def main():
    if len(sys.argv) != 2:
        print("usage: python3 scripts/verify_identifier.py <doi-or-pmid>", file=sys.stderr)
        return 1
    ident = sys.argv[1].strip()

    record = _from_pubmed(ident) if _looks_like_pmid(ident) else _from_crossref(ident)
    if not record or not record.get("title"):
        print(f"COULD NOT VERIFY: '{ident}' did not resolve to a real record. "
              f"Nothing was added. Do not write about this paper from memory instead — "
              f"either find its correct identifier or drop it.")
        return 1

    os.makedirs(STATE, exist_ok=True)
    existing = []
    if os.path.exists(DISCOVERED):
        try:
            existing = json.load(open(DISCOVERED, encoding="utf-8"))
        except Exception:
            existing = []
    existing.append(record)
    json.dump(existing, open(DISCOVERED, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    print(f"VERIFIED and added to state/model_discovered.json:")
    print(f"  Title: {record['title']}")
    print(f"  Venue: {record['venue']}  Date: {record['date']}")
    print(f"  Abstract available: {'yes' if record['abstract'] else 'NO — title-only match'}")
    print(f"Run scripts/merge_discovered.py once you've added everything you want, "
          f"before writing selection.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
