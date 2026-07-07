"""
fetch_flagship.py — Tier 1: "no miss" flagship-journal coverage.

Design: for each journal in search_config.FLAGSHIP_JOURNALS, pull from TWO
independent sources and union the results:
  (a) the journal's own RSS/Atom feed (fast, has real content, but any single
      feed can go stale/change format/rate-limit)
  (b) a PubMed query scoped to that journal's ISSN for the same date window
      (slower, but PubMed's uptime is independent of any one publisher's feed)

If either source lists an article the other missed, it's still caught. If a
journal's feed is entirely down, the PubMed side alone still covers it (and
vice versa) — this is fault-isolation applied to COMPLETENESS, not just
uptime. Every source function still catches its own exceptions.
"""
from __future__ import annotations
import datetime as dt
import logging
import re
import time
import requests
import xml.etree.ElementTree as ET

import search_config

log = logging.getLogger("fetch_flagship")
TIMEOUT = 30
UA = "auditory-grouping-digest/3.0 (personal research tool; mailto:%s)"

def _headers(email: str) -> dict:
    return {"User-Agent": UA % (email or "anonymous@example.com")}


def _get(url, params=None, headers=None):
    r = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return r


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"&[a-z#0-9]+;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_date(s: str) -> str:
    """Best-effort: normalize common RSS/Atom date formats to YYYY-MM-DD."""
    if not s:
        return ""
    s = s.strip()
    formats = [
        "%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    m = re.search(r"(\d{4}-\d{2}-\d{2})", s)
    return m.group(1) if m else ""


def _strip_namespaces(root):
    """Atom feeds use a default xmlns that namespaces every element
    ({http://www.w3.org/2005/Atom}entry, ...title, etc). Stripping it right
    after parsing means all downstream find()/findall() calls can use plain
    tag names regardless of whether the feed was RSS or Atom, instead of
    juggling namespace prefixes at every lookup site."""
    for el in root.iter():
        if "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]
    return root


def fetch_journal_feed(journal: dict, since: dt.date, until: dt.date, email: str) -> list[dict]:
    """Parses one journal's RSS/Atom feed. Handles both formats via ElementTree,
    falling back to a regex scrape if the XML doesn't parse cleanly (some
    publisher feeds are slightly malformed)."""
    url = journal.get("rss")
    if not url:
        return []
    out = []
    try:
        r = _get(url, headers=_headers(email))
        try:
            root = _strip_namespaces(ET.fromstring(r.content))
        except ET.ParseError:
            return _regex_fallback_parse(r.text, journal, since, until)

        items = root.findall(".//item") or root.findall(".//entry")
        for item in items:
            title = _find_text(item, ["title"])
            link = _find_text(item, ["link"]) or _find_attr(item, ["link"], "href")
            desc = _find_text(item, ["description", "summary", "encoded", "content"])
            date_raw = _find_text(item, ["pubDate", "published", "updated", "date"])
            date = _parse_date(date_raw)
            if date and not (since.isoformat() <= date <= until.isoformat()):
                continue
            doi = _extract_doi(link) or _extract_doi(desc)
            out.append({
                "title": _clean(title),
                "abstract": _clean(desc),
                "date": date,
                "doi": doi,
                "url": link or "",
                "venue": journal["name"],
                "authors": [],  # feeds rarely include structured author lists
                "type": "article",
                "is_preprint": False,
                "source_api": f"RSS:{journal['name']}",
                "pool": "flagship",
                "cluster": "flagship-feed",
            })
    except Exception as e:
        log.warning("feed fetch failed for %s: %s", journal["name"], e)
    return out


def _find_text(item, tags):
    for tag in tags:
        el = item.find(tag)
        if el is not None and el.text:
            return el.text
    return ""


def _find_attr(item, tags, attr):
    for tag in tags:
        el = item.find(tag)
        if el is not None and el.get(attr):
            return el.get(attr)
    return ""


def _extract_doi(text: str) -> str:
    if not text:
        return ""
    m = re.search(r"10\.\d{4,9}/[^\s\"'<>]+", text)
    return m.group(0).rstrip(".,;)") if m else ""


def _regex_fallback_parse(raw_xml: str, journal: dict, since: dt.date, until: dt.date) -> list[dict]:
    """Some publisher feeds are technically malformed XML; scrape with regex
    as a last resort rather than lose the whole journal for one bad feed."""
    out = []
    for block in re.split(r"<item>|<entry>", raw_xml)[1:]:
        title_m = re.search(r"<title.*?>(.*?)</title>", block, re.S)
        title = _clean(title_m.group(1)) if title_m else ""
        desc_m = re.search(r"<(description|summary)>(.*?)</\1>", block, re.S)
        desc = _clean(desc_m.group(2)) if desc_m else ""
        date_m = re.search(r"<(pubDate|published|updated)>(.*?)</\1>", block, re.S)
        date = _parse_date(date_m.group(2)) if date_m else ""
        if date and not (since.isoformat() <= date <= until.isoformat()):
            continue
        if not title:
            continue
        out.append({
            "title": title, "abstract": desc, "date": date, "doi": _extract_doi(block),
            "url": "", "venue": journal["name"], "authors": [], "type": "article",
            "is_preprint": False, "source_api": f"RSS:{journal['name']}",
            "pool": "flagship", "cluster": "flagship-feed",
        })
    return out


def fetch_journal_pubmed(journal: dict, since: dt.date, until: dt.date, email: str) -> list[dict]:
    """The independent second source: PubMed scoped to this journal's ISSN,
    using efetch (not esummary) so we get real abstracts and affiliations in
    one call."""
    if not journal.get("issn"):
        return []
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    date_filter = f'("{since.strftime("%Y/%m/%d")}"[PDAT] : "{until.strftime("%Y/%m/%d")}"[PDAT])'
    term = f'{journal["issn"]}[ISSN] AND {date_filter}'
    try:
        r = _get(f"{base}/esearch.fcgi", params={
            "db": "pubmed", "term": term, "retmode": "json", "retmax": 40, "email": email,
        })
        ids = r.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []
        time.sleep(0.34)
        r2 = _get(f"{base}/efetch.fcgi", params={
            "db": "pubmed", "id": ",".join(ids), "retmode": "xml", "email": email,
        })
        return _parse_pubmed_efetch_xml(r2.text, journal["name"])
    except Exception as e:
        log.warning("pubmed-ISSN fetch failed for %s: %s", journal["name"], e)
        return []


def _parse_pubmed_efetch_xml(xml_text: str, venue_name: str = "") -> list[dict]:
    """Shared by fetch_flagship (ISSN-scoped, venue already known) and
    fetch_papers (general search, venue not known ahead of time — extracted
    from the record itself). Extracts title, full abstract, authors, DOI,
    PMID, publication date, and corresponding-author affiliation/country."""
    out = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        log.warning("efetch XML parse failed: %s", e)
        return out

    for article in root.findall(".//PubmedArticle"):
        try:
            title_el = article.find(".//ArticleTitle")
            title = _clean(ET.tostring(title_el, encoding="unicode", method="text")) if title_el is not None else ""

            abstract_parts = [
                _clean(ET.tostring(ab, encoding="unicode", method="text"))
                for ab in article.findall(".//AbstractText")
            ]
            abstract = " ".join(p for p in abstract_parts if p)

            pmid_el = article.find(".//PMID")
            pmid = pmid_el.text if pmid_el is not None else ""

            doi = ""
            for aid in article.findall(".//ArticleId"):
                if aid.get("IdType") == "doi":
                    doi = aid.text or ""

            journal_title = venue_name or (article.findtext(".//Journal/Title") or "")

            year_el = article.find(".//PubDate/Year")
            if year_el is None:
                year_el = article.find(".//PubDate/MedlineDate")
            date = year_el.text[:4] if year_el is not None and year_el.text else ""

            authors, affiliation, country = [], "", ""
            author_els = article.findall(".//Author")
            for i, a in enumerate(author_els):
                last = a.findtext("LastName", "")
                fore = a.findtext("ForeName", "")
                if last:
                    authors.append(f"{fore} {last}".strip())
                if i == len(author_els) - 1:  # last author, usually corresponding/senior
                    aff_el = a.find(".//AffiliationInfo/Affiliation")
                    if aff_el is not None and aff_el.text:
                        affiliation = aff_el.text
                        country = _guess_country(affiliation)

            out.append({
                "title": title, "abstract": abstract, "date": date, "doi": doi,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                "venue": journal_title, "authors": authors, "type": "article",
                "is_preprint": False, "source_api": "PubMed",
                "affiliation": affiliation, "country": country,
                "pool": "flagship", "cluster": "flagship-pubmed",
            })
        except Exception as e:
            log.info("skipping one malformed PubMed record: %s", e)
    return out


_COUNTRY_HINTS = [
    "USA", "United States", "U.S.A", "Germany", "United Kingdom", "UK", "England",
    "France", "China", "Japan", "Canada", "Switzerland", "Netherlands", "Austria",
    "Italy", "Spain", "Sweden", "Australia", "South Korea", "Republic of Korea",
    "Israel", "Belgium", "Denmark", "Singapore", "India", "Brazil", "Poland",
]


def _guess_country(affiliation: str) -> str:
    """Affiliation strings don't have a structured country field in PubMed
    XML — best-effort tail match against a common-country list. Imperfect but
    good enough for a meta-line credit, not used for any decision logic."""
    for c in _COUNTRY_HINTS:
        if re.search(rf"\b{re.escape(c)}\b", affiliation, re.I):
            return c
    return ""


def fetch_all_flagship(since: dt.date, until: dt.date, email: str = "") -> list[dict]:
    papers = []
    for journal in search_config.FLAGSHIP_JOURNALS:
        feed_papers = fetch_journal_feed(journal, since, until, email)
        pubmed_papers = fetch_journal_pubmed(journal, since, until, email)
        log.info("%s: %d via feed, %d via PubMed", journal["name"], len(feed_papers), len(pubmed_papers))
        papers.extend(feed_papers)
        papers.extend(pubmed_papers)
        time.sleep(0.1)
    return papers
