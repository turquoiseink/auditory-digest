"""
validate_selection.py — the deterministic judge between LLM output and the PDF.

Given the parsed selection JSON and the list of candidate papers, returns
(ok: bool, errors: list[str]). main.py uses the errors to (a) feed a targeted
retry to the LLM, or (b) after max attempts, fall back to a no-LLM digest.

This is the single most important guardrail against the "day 2 broke" failure:
nothing the LLM emits reaches the PDF unless it passes here.
"""
from __future__ import annotations

ALLOWED_SECTIONS = {
    "Chunking & sequence processing",
    "Auditory & prefrontal electrophysiology",
    "Behavioral & computational modeling",
    "Statistical learning & oddball",
    "Language, stroke & BCI",
    "Circuits, methods & population analysis",
    "Serendipity (outside my paradigm)",
    "Other notable",
}

MAX_TOTAL_PAPERS = 14
MAX_BULLETS = 5
MIN_BULLETS = 2


def validate(selection: dict, candidates: list[dict]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    n = len(candidates)

    if not isinstance(selection, dict):
        return False, ["top-level JSON is not an object"]

    # --- editorial ---
    ed = selection.get("editorial")
    if not isinstance(ed, str) or not ed.strip():
        errors.append("editorial missing or empty (need a non-empty string)")
    elif len(ed) > 1200:
        errors.append("editorial too long (keep it to 3-5 sentences, <1200 chars)")

    # --- sections ---
    sections = selection.get("sections")
    total = 0
    used_ids = set()
    if not isinstance(sections, dict):
        errors.append("sections missing or not an object")
    else:
        for name, items in sections.items():
            if name not in ALLOWED_SECTIONS:
                errors.append(
                    f"section name '{name}' not allowed; must be one of: "
                    f"{sorted(ALLOWED_SECTIONS)}"
                )
            if not isinstance(items, list):
                errors.append(f"section '{name}' value is not a list")
                continue
            for it in items:
                if not isinstance(it, dict):
                    errors.append(f"item in '{name}' is not an object")
                    continue
                cid = it.get("candidate_id")
                if not isinstance(cid, int) or not (0 <= cid < n):
                    errors.append(
                        f"candidate_id {cid!r} in '{name}' is out of range "
                        f"(valid 0..{n-1})"
                    )
                else:
                    used_ids.add(cid)
                note = it.get("relevance_note")
                if not isinstance(note, str) or not note.strip():
                    errors.append(f"relevance_note for candidate {cid} missing/empty")
                total += 1
    if total > MAX_TOTAL_PAPERS:
        errors.append(f"too many papers selected ({total}); max {MAX_TOTAL_PAPERS}")

    # --- paper of the day ---
    potd = selection.get("paper_of_the_day")
    if not isinstance(potd, dict):
        errors.append("paper_of_the_day missing or not an object")
    else:
        src = potd.get("source")
        if src not in ("new", "canon"):
            errors.append("paper_of_the_day.source must be 'new' or 'canon'")
        if src == "new":
            cid = potd.get("candidate_id")
            if not isinstance(cid, int) or not (0 <= cid < n):
                errors.append(
                    f"paper_of_the_day.candidate_id {cid!r} out of range "
                    f"(valid 0..{n-1}) for source=new"
                )
            elif candidates[cid].get("is_preprint"):
                errors.append(
                    f"paper_of_the_day.candidate_id {cid} is a preprint "
                    f"({candidates[cid].get('source_api')}, venue="
                    f"{candidates[cid].get('venue')!r}) — Paper of the Day must be a "
                    f"peer-reviewed published paper. Pick a different, non-preprint "
                    f"candidate, or if none of today's candidates qualify, set "
                    f"source='canon' instead and use the next unserved canon entry."
                )
        elif src == "canon":
            ce = potd.get("canon_entry")
            if not isinstance(ce, str) or not ce.strip():
                errors.append("paper_of_the_day.canon_entry required when source=canon")

        bullets = potd.get("why_it_matters")
        if not isinstance(bullets, list) or not (MIN_BULLETS <= len(bullets) <= MAX_BULLETS):
            errors.append(
                f"paper_of_the_day.why_it_matters must be a list of "
                f"{MIN_BULLETS}-{MAX_BULLETS} bullets"
            )
        elif any(not isinstance(b, str) or not b.strip() for b in bullets):
            errors.append("paper_of_the_day.why_it_matters has an empty bullet")

        rq = potd.get("reflection_question")
        if not isinstance(rq, str) or not rq.strip():
            errors.append("paper_of_the_day.reflection_question missing or empty")
        elif "?" not in rq:
            errors.append("paper_of_the_day.reflection_question should be a question")
        elif len(rq.strip()) < 60:
            errors.append(
                "paper_of_the_day.reflection_question is too short/trivial "
                "(<60 chars) — it should require real engagement with the paper's "
                "method or finding, ideally as a two-part question building toward "
                "an experimental-design decision, not a single-clause comprehension check"
            )

        read_plan = potd.get("read_plan")
        if not isinstance(read_plan, str) or not read_plan.strip():
            errors.append(
                "paper_of_the_day.read_plan missing or empty — give a concrete "
                "20-minute reading plan (which sections to read in full, which to "
                "skim, what to focus on in each)"
            )

    return (len(errors) == 0), errors


def validate_deepdive(deepdive: dict) -> tuple[bool, list[str]]:
    """Validates the deep-dive refinement JSON (why_it_matters, read_plan,
    reflection_question). Same rules as the Paper of the Day fields above,
    applied standalone."""
    errors: list[str] = []
    if not isinstance(deepdive, dict):
        return False, ["deepdive.json is not an object"]

    bullets = deepdive.get("why_it_matters")
    if not isinstance(bullets, list) or not (MIN_BULLETS <= len(bullets) <= MAX_BULLETS):
        errors.append(f"why_it_matters must be a list of {MIN_BULLETS}-{MAX_BULLETS} bullets")
    elif any(not isinstance(b, str) or not b.strip() for b in bullets):
        errors.append("why_it_matters has an empty bullet")

    rq = deepdive.get("reflection_question")
    if not isinstance(rq, str) or not rq.strip():
        errors.append("reflection_question missing or empty")
    elif "?" not in rq:
        errors.append("reflection_question should be a question")
    elif len(rq.strip()) < 60:
        errors.append("reflection_question is too short/trivial (<60 chars)")

    read_plan = deepdive.get("read_plan")
    if not isinstance(read_plan, str) or not read_plan.strip():
        errors.append("read_plan missing or empty")

    return (len(errors) == 0), errors
