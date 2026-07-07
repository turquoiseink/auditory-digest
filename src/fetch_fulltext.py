"""
fetch_fulltext.py — best-effort OPEN-ACCESS full text for the Paper of the Day.

Order: PMC (PubMed Central) -> bioRxiv full text -> Unpaywall -> Semantic
Scholar open PDF -> give up (abstract only). Only legal open sources; no
Sci-Hub, no automated institutional login. Returns (text, used_full_text).

If nothing is fetchable, returns ("", False) and the caller works from the
abstract and marks the digest honestly.
"""
from __future__ import annotations
import logging
import re
import requests

log = logging.getLogger("fulltext")
TIMEOUT = 30
MAX_CHARS = 45000  # keep the LLM prompt bounded


def _get(url, params=None, headers=None):
    r = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return r


def fetch_fulltext(doi: str = "", title: str = "", email: str = "") -> tuple[str, bool]:
    doi = (doi or "").strip().lower()
    for fn in (_try_pmc, _try_unpaywall, _try_core, _try_semantic_scholar):
        try:
            text = fn(doi, title, email)
            if text and len(text) > 800:
                return text[:MAX_CHARS], True
        except Exception as e:
            log.info("%s failed: %s", fn.__name__, e)
    return "", False


def _try_pmc(doi, title, email):
    """DOI -> PMCID via NCBI idconv -> full text via PMC OA."""
    if not doi:
        return ""
    r = _get("https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/",
             params={"ids": doi, "format": "json", "email": email})
    recs = r.json().get("records", [])
    pmcid = recs[0].get("pmcid") if recs else None
    if not pmcid:
        return ""
    r2 = _get(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/",
              headers={"User-Agent": "auditory-digest/2.0"})
    return _strip_html(r2.text)


def _try_unpaywall(doi, title, email):
    if not doi:
        return ""
    r = _get(f"https://api.unpaywall.org/v2/{doi}", params={"email": email or "test@example.com"})
    loc = (r.json() or {}).get("best_oa_location") or {}
    pdf_url = loc.get("url_for_pdf") or loc.get("url")
    if not pdf_url:
        return ""
    r2 = _get(pdf_url, headers={"User-Agent": "auditory-digest/2.0"})
    ct = r2.headers.get("content-type", "")
    if "pdf" in ct.lower():
        return _pdf_to_text(r2.content)
    return _strip_html(r2.text)


def _try_core(doi, title, email):
    """CORE aggregates open-access full text from repositories worldwide —
    broader coverage than Unpaywall for some institutional repositories.
    Works unauthenticated but rate-limited; set CORE_API_KEY (free academic
    registration at core.ac.uk, not a paid service) for better reliability.
    Best-effort — silently contributes nothing if unavailable."""
    import os
    headers = {"User-Agent": "auditory-digest/2.0"}
    api_key = os.environ.get("CORE_API_KEY", "")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    query = f'doi:"{doi}"' if doi else f'title:"{title}"'
    r = _get("https://api.core.ac.uk/v3/search/works/",
             params={"q": query, "limit": 3}, headers=headers)
    results = (r.json() or {}).get("results", [])
    for item in results:
        pdf_url = item.get("downloadUrl") or (item.get("sourceFulltextUrls") or [None])[0]
        if not pdf_url:
            continue
        r2 = _get(pdf_url, headers={"User-Agent": "auditory-digest/2.0"})
        ct = r2.headers.get("content-type", "")
        if "pdf" in ct.lower():
            return _pdf_to_text(r2.content)
        return _strip_html(r2.text)
    return ""


def _try_semantic_scholar(doi, title, email):
    ident = f"DOI:{doi}" if doi else None
    if not ident:
        return ""
    r = _get(f"https://api.semanticscholar.org/graph/v1/paper/{ident}",
             params={"fields": "openAccessPdf,abstract"})
    data = r.json() or {}
    pdf = (data.get("openAccessPdf") or {}).get("url")
    if pdf:
        r2 = _get(pdf, headers={"User-Agent": "auditory-digest/2.0"})
        if "pdf" in r2.headers.get("content-type", "").lower():
            return _pdf_to_text(r2.content)
    return data.get("abstract") or ""


def _strip_html(html: str) -> str:
    html = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style.*?</style>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&[a-z]+;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _pdf_to_text(content: bytes) -> str:
    try:
        import io
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(content))
        return " ".join((pg.extract_text() or "") for pg in reader.pages)
    except Exception as e:
        log.info("pdf extract failed: %s", e)
        return ""
