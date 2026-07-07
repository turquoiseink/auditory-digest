"""
fetch_papers.py — deterministic, no-LLM fetching for Tiers 2 and 3.

  Tier 2 (deep bioRxiv scan): pulls the FULL daily bioRxiv neuroscience
     listing (not keyword-narrowed at the query level), then keeps anything
     matching either a title-keyword stem OR a watch-author name. Full,
     untruncated abstracts always — bioRxiv's API includes them natively.

  Tier 3 (general broad search): keyword-clustered search across OpenAlex,
     PubMed (via efetch — real abstracts + affiliations), and arXiv. The
     widest, lowest-priority net; catches things Tiers 1-2 miss.

Tier 1 (guaranteed flagship-journal coverage) lives in fetch_flagship.py.
Every source function catches its own exceptions and returns [] on failure.
"""
from __future__ import annotations
import datetime as dt
import logging
import re
import time
import requests

import search_config
from fetch_flagship import _parse_pubmed_efetch_xml  # shared XML parser

log = logging.getLogger("fetch")

TIMEOUT = 30
UA = "auditory-grouping-digest/3.0 (personal research tool; mailto:%s)"


def _headers(email: str) -> dict:
    return {"User-Agent": UA % (email or "anonymous@example.com")}


def _get(url, params=None, headers=None):
    r = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return r


def _reconstruct_abstract(inv_index):
    if not inv_index:
        return ""
    try:
        positions = []
        for word, idxs in inv_index.items():
            for i in idxs:
                positions.append((i, word))
        positions.sort()
        return " ".join(w for _, w in positions)
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Tier 3: OpenAlex (keyword-clustered)
# ---------------------------------------------------------------------------
def fetch_openalex(since, until, email="") -> list[dict]:
    out = []
    for q in search_config.QUERY_CLUSTERS:
        try:
            r = _get(
                "https://api.openalex.org/works",
                params={
                    "search": q,
                    "filter": f"from_publication_date:{since.isoformat()},"
                              f"to_publication_date:{until.isoformat()}",
                    "per-page": 12,
                    "sort": "publication_date:desc",
                    "mailto": email or None,
                },
                headers=_headers(email),
            )
            for w in r.json().get("results", []):
                out.append(_openalex_paper(w, pool="A", tag=q))
        except Exception as e:
            log.warning("openalex '%s' failed: %s", q, e)
        time.sleep(0.12)
    return out


def _openalex_paper(w, pool, tag):
    src = (w.get("primary_location") or {}).get("source") or {}
    oa_type = w.get("type") or ""
    affiliation, country = _openalex_affiliation(w)
    return {
        "title": w.get("title") or "",
        "abstract": _reconstruct_abstract(w.get("abstract_inverted_index")),
        "date": w.get("publication_date") or "",
        "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
        "url": w.get("doi") or (w.get("primary_location") or {}).get("landing_page_url") or "",
        "venue": src.get("display_name") or "",
        "authors": [(a.get("author") or {}).get("display_name", "")
                    for a in (w.get("authorships") or [])],
        "type": oa_type,
        "is_preprint": oa_type.lower() == "preprint",
        "affiliation": affiliation,
        "country": country,
        "source_api": "OpenAlex",
        "pool": pool,
        "cluster": tag,
    }


def _openalex_affiliation(w) -> tuple[str, str]:
    """OpenAlex authorships include structured institutions with country
    codes — use the last author's (usually senior/corresponding) first listed
    institution."""
    authorships = w.get("authorships") or []
    if not authorships:
        return "", ""
    last = authorships[-1]
    insts = last.get("institutions") or []
    if not insts:
        return "", ""
    inst = insts[0]
    name = inst.get("display_name") or ""
    country_code = inst.get("country_code") or ""
    country = _COUNTRY_CODE_NAMES.get(country_code, country_code)
    return name, country


_COUNTRY_CODE_NAMES = {
    "US": "USA", "DE": "Germany", "GB": "United Kingdom", "FR": "France",
    "CN": "China", "JP": "Japan", "CA": "Canada", "CH": "Switzerland",
    "NL": "Netherlands", "AT": "Austria", "IT": "Italy", "ES": "Spain",
    "SE": "Sweden", "AU": "Australia", "KR": "South Korea", "IL": "Israel",
    "BE": "Belgium", "DK": "Denmark", "SG": "Singapore", "IN": "India",
    "BR": "Brazil", "PL": "Poland",
}


# ---------------------------------------------------------------------------
# Tier 2: deep bioRxiv scan — full listing, filtered by title stem OR author
# ---------------------------------------------------------------------------
def _title_matches(title: str) -> bool:
    t = (title or "").lower()
    return any(stem.lower() in t for stem in search_config.TITLE_MATCH_STEMS)


def _author_matches(authors: list[str]) -> bool:
    watch = [a.lower() for a in (search_config.WATCH_AUTHORS + search_config.MUNICH_LABS)]
    for a in authors:
        al = a.lower()
        if any(w in al or al in w for w in watch):
            return True
    return False


def fetch_biorxiv(since, until, email="") -> list[dict]:
    """Pulls the FULL bioRxiv neuroscience/animal-behavior listing for the
    window (not keyword-narrowed at the query level — bioRxiv's API doesn't
    support that anyway), then keeps only entries matching a title stem or a
    watch-author, so volume stays manageable while genuinely widening what
    can be found (an odd-titled paper by a watched author now survives)."""
    out, cursor, total_scanned = [], 0, 0
    try:
        for _ in range(8):  # up to ~1600 recent posts scanned across categories
            url = f"https://api.biorxiv.org/details/biorxiv/{since.isoformat()}/{until.isoformat()}/{cursor}"
            r = _get(url, headers=_headers(email))
            coll = r.json().get("collection", [])
            if not coll:
                break
            total_scanned += len(coll)
            for p in coll:
                if (p.get("category") or "").lower() not in (
                    "neuroscience", "animal behavior and cognition"
                ):
                    continue
                title = p.get("title") or ""
                authors = [a.strip() for a in (p.get("authors") or "").split(";") if a.strip()]
                if not (_title_matches(title) or _author_matches(authors)):
                    continue
                doi = p.get("doi") or ""
                out.append({
                    "title": title,
                    "abstract": p.get("abstract") or "",  # bioRxiv gives full abstract natively
                    "date": p.get("date") or "",
                    "doi": doi,
                    "url": f"https://doi.org/{doi}" if doi else "",
                    "venue": "bioRxiv",
                    "authors": authors,
                    "type": "preprint",
                    "is_preprint": True,
                    "affiliation": "", "country": "",  # not provided by bioRxiv's API
                    "source_api": "bioRxiv",
                    "pool": "A",
                    "cluster": "biorxiv-deep-scan",
                })
            cursor += len(coll)
    except Exception as e:
        log.warning("biorxiv failed at cursor %d: %s", cursor, e)
    log.info("biorxiv: scanned %d posts, %d matched title/author filter", total_scanned, len(out))
    return out


# ---------------------------------------------------------------------------
# Tier 3: PubMed (keyword-clustered, via efetch for real abstracts + affiliation)
# ---------------------------------------------------------------------------
def fetch_pubmed(since, until, email="") -> list[dict]:
    out = []
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    date_filter = f'("{since.strftime("%Y/%m/%d")}"[PDAT] : "{until.strftime("%Y/%m/%d")}"[PDAT])'
    for q in search_config.QUERY_CLUSTERS:
        try:
            r = _get(f"{base}/esearch.fcgi", params={
                "db": "pubmed", "term": f"({q}) AND {date_filter}",
                "retmode": "json", "retmax": 12, "email": email,
            })
            ids = r.json().get("esearchresult", {}).get("idlist", [])
            if not ids:
                continue
            time.sleep(0.34)
            r2 = _get(f"{base}/efetch.fcgi", params={
                "db": "pubmed", "id": ",".join(ids), "retmode": "xml", "email": email,
            })
            records = _parse_pubmed_efetch_xml(r2.text, venue_name="")  # venue read per-record below
            for rec in records:
                rec["pool"] = "A"
                rec["cluster"] = q
            out.extend(records)
        except Exception as e:
            log.warning("pubmed '%s' failed: %s", q, e)
        time.sleep(0.34)
    return out


# ---------------------------------------------------------------------------
# arXiv (q-bio.NC — computational/behavioral modeling side)
# ---------------------------------------------------------------------------
def fetch_arxiv(since, until, email="") -> list[dict]:
    out = []
    try:
        r = _get("http://export.arxiv.org/api/query", params={
            "search_query": "cat:q-bio.NC",
            "sortBy": "submittedDate", "sortOrder": "descending",
            "max_results": 50,
        }, headers=_headers(email))
        for e in re.split(r"<entry>", r.text)[1:]:
            published = _tag(e, "published")[:10]
            if not published:
                continue
            try:
                pub = dt.date.fromisoformat(published)
            except ValueError:
                continue
            if not (since <= pub <= until):
                continue
            out.append({
                "title": " ".join(_tag(e, "title").split()),
                "abstract": " ".join(_tag(e, "summary").split()),
                "date": published,
                "doi": "",
                "url": _tag(e, "id").strip(),
                "venue": "arXiv (q-bio.NC)",
                "authors": re.findall(r"<name>(.*?)</name>", e, re.S),
                "type": "preprint",
                "is_preprint": True,
                "affiliation": "", "country": "",
                "source_api": "arXiv",
                "pool": "A",
                "cluster": "arxiv-qbio",
            })
    except Exception as e:
        log.warning("arxiv failed: %s", e)
    return out


def _tag(block, tag):
    m = re.search(rf"<{tag}.*?>(.*?)</{tag}>", block, re.S)
    return m.group(1).strip() if m else ""


# ---------------------------------------------------------------------------
# Dedupe (title + DOI). Priority order for ties: flagship > A > B, so a paper
# appearing via multiple tiers keeps its richest/most-authoritative record.
# ---------------------------------------------------------------------------
def _norm_title(t):
    return re.sub(r"[^a-z0-9]+", "", (t or "").lower())


_POOL_PRIORITY = {"flagship": 0, "A": 1, "B": 2}


def dedupe(papers) -> list[dict]:
    seen_doi, seen_title, out = set(), set(), []
    papers = sorted(papers, key=lambda p: _POOL_PRIORITY.get(p.get("pool"), 9))
    for p in papers:
        doi = (p.get("doi") or "").lower().strip()
        tkey = _norm_title(p.get("title"))
        if not tkey:
            continue
        if (doi and doi in seen_doi) or tkey in seen_title:
            continue
        if doi:
            seen_doi.add(doi)
        seen_title.add(tkey)
        out.append(p)
    return out
