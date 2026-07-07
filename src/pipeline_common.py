"""
pipeline_common.py — deterministic logic shared by prep.py, process_selection.py,
and finalize.py. No LLM, no network (fetch_fulltext is called separately).
"""
from __future__ import annotations

SECTION_ORDER = [
    "Chunking & sequence processing",
    "Auditory & prefrontal electrophysiology",
    "Behavioral & computational modeling",
    "Statistical learning & oddball",
    "Language, stroke & BCI",
    "Circuits, methods & population analysis",
    "Field pulse (outside my paradigm)",
    "Other notable",
]

FALLBACK_KEYWORDS = [
    "auditory", "sequence", "chunk", "prefrontal", "prelimbic", "neuropixels",
    "utah array", "intracranial", "ecog", "single unit", "spike", "decoding",
    "population", "streaming", "statistical learning", "oddball", "mismatch",
    "aphasia", "stroke", "dopamine", "drift diffusion", "optogenetic",
]


def meta(p: dict) -> str:
    authors = p.get("authors") or []
    a = authors[0] + " et al." if len(authors) > 1 else (authors[0] if authors else "")
    parts = [x for x in [a, p.get("venue", ""), p.get("date", "")] if x]
    lab = (p.get("affiliation") or "").strip()
    country = p.get("country") or ""
    if len(lab) > 70:  # PubMed's raw affiliation strings can be a full department+address
        lab = lab[:67].rsplit(" ", 1)[0] + "…"
    if lab or country:
        tail = " — ".join(x for x in [lab, country] if x)
        parts.append(tail)
    return " — ".join(parts)


def fallback_digest(candidates: list[dict]):
    """No-LLM digest: keyword-scored, clearly marked. Used when the model
    exhausts its attempts. Returns (editorial, sections_dict, log_rows)."""
    scored = []
    for p in candidates:
        text = f"{p.get('title','')} {p.get('abstract','')}".lower()
        s = sum(1 for k in FALLBACK_KEYWORDS if k in text)
        if s:
            scored.append((s, p))
    scored.sort(key=lambda t: t[0], reverse=True)
    top = [p for _, p in scored[:10]]

    sections = {name: [] for name in SECTION_ORDER}
    log_rows = []
    for p in top:
        sections["Other notable"].append({
            "title": p.get("title", ""), "meta": meta(p),
            "pool": p.get("pool", "A"), "source_api": p.get("source_api", ""),
            "note": "(Fallback: model selection unavailable — keyword-matched, unranked.)",
        })
        log_rows.append({**p, "section": "Other notable",
                         "note": "keyword-matched fallback (model selection unavailable)",
                         "is_potd": False, "full_text_used": False})

    editorial = ("Model selection was unavailable for this issue after 3 attempts, so "
                 "today's digest is an unranked keyword-matched fallback rather than a "
                 "curated one. Check state/run_log.json for what happened.")
    return editorial, sections, log_rows


def resolve_selection(selection: dict, candidates: list[dict]):
    """Turn a VALIDATED selection JSON into render-ready sections + a
    provisional Paper-of-the-Day (bullets/reflection question may still be
    refined by the deep-dive step) + reading-log rows.
    Returns (sections, potd, potd_log_row, log_rows)."""
    sections = {name: [] for name in SECTION_ORDER}
    log_rows = []
    for sec_name, items in (selection.get("sections") or {}).items():
        target = sec_name if sec_name in sections else "Other notable"
        for it in items:
            p = candidates[it["candidate_id"]]
            note = it.get("relevance_note", "")
            sections[target].append({
                "title": p.get("title", ""), "meta": meta(p),
                "pool": p.get("pool", "A"), "source_api": p.get("source_api", ""),
                "note": note,
            })
            log_rows.append({**p, "section": target, "note": note,
                             "is_potd": False, "full_text_used": False})

    potd, potd_log = None, None
    raw = selection.get("paper_of_the_day") or {}
    if raw.get("source") == "new" and isinstance(raw.get("candidate_id"), int):
        p = candidates[raw["candidate_id"]]
        potd = {
            "title": p.get("title", ""), "meta": meta(p) + " — new pick",
            "source": "new", "bullets": raw.get("why_it_matters", []),
            "reflection_question": raw.get("reflection_question", ""),
            "read_plan": raw.get("read_plan", ""),
            "_paper": p,
        }
        potd_log = {**p, "section": "\u2605 Paper of the Day", "is_potd": True,
                    "note": " ".join(raw.get("why_it_matters", []))}
    elif raw.get("source") == "canon":
        potd = {
            "title": raw.get("canon_entry", ""), "meta": "Foundations pick",
            "source": "canon", "bullets": raw.get("why_it_matters", []),
            "reflection_question": raw.get("reflection_question", ""),
            "read_plan": raw.get("read_plan", ""),
            "_paper": None,
        }
    return sections, potd, potd_log, log_rows
