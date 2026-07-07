"""
process_selection.py — the deterministic gate the routine calls after writing
state/selection.json. This is where drift gets stopped, structurally:

  - The retry cap (3) is enforced HERE, by a counter file, not by trusting the
    model to stop asking. Even a model that ignores instructions and keeps
    retrying forever cannot exceed 3 attempts, because this script refuses to
    validate past that point and forces the fallback path itself.
  - Validation is the SAME schema check every day (validate_selection.py) —
    no judgment calls, just a fixed contract.

Exit codes (the routine reacts to these, but the CAP is enforced regardless
of whether the routine reads them correctly):
  0  -> valid. Resolved data + deep-dive input written. Proceed to the
        deep-dive step (write state/deepdive.json), then finalize.py.
  1  -> invalid, attempts remain. Errors printed. Fix state/selection.json
        and run this script again.
  2  -> attempts exhausted (or any other unrecoverable state). Run
        `python3 src/finalize.py --fallback` instead.
"""
from __future__ import annotations
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import validate_selection
import pipeline_common as pc
import fetch_fulltext

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "state")
CANDIDATES = os.path.join(STATE, "candidates.json")
CONTEXT = os.path.join(STATE, "context.json")
SELECTION = os.path.join(STATE, "selection.json")
ATTEMPT = os.path.join(STATE, "attempt.json")
RESOLVED = os.path.join(STATE, "resolved.json")
DEEPDIVE_INPUT = os.path.join(STATE, "deepdive_input.json")

MAX_ATTEMPTS = 3
EMAIL = os.environ.get("CONTACT_EMAIL", "")


def _load(p, default=None):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return default


def main():
    attempt = _load(ATTEMPT, {"count": 0})
    attempt["count"] = attempt.get("count", 0) + 1
    json.dump(attempt, open(ATTEMPT, "w", encoding='utf-8'))

    if attempt["count"] > MAX_ATTEMPTS:
        print(f"MAX_ATTEMPTS_EXCEEDED ({attempt['count']-1} attempts used)")
        print("Run: python3 src/finalize.py --fallback")
        return 2

    candidates = _load(CANDIDATES, [])
    selection = _load(SELECTION)
    if selection is None:
        print("selection.json missing or not valid JSON")
        return 1

    ok, errors = validate_selection.validate(selection, candidates)
    if not ok:
        print(f"INVALID (attempt {attempt['count']}/{MAX_ATTEMPTS})")
        for e in errors:
            print("  -", e)
        if attempt["count"] >= MAX_ATTEMPTS:
            print("No attempts remain.")
            print("Run: python3 src/finalize.py --fallback")
            return 2
        print("Fix state/selection.json and run this script again.")
        return 1

    # Valid: resolve, fetch full text for the Paper of the Day, write inputs
    # for the (optional, single) deep-dive step.
    sections, potd, potd_log, log_rows = pc.resolve_selection(selection, candidates)
    json.dump({
        "editorial": selection.get("editorial"),
        "sections": sections,
        "potd": {k: v for k, v in (potd or {}).items() if k != "_paper"},
        "potd_log": potd_log,
        "log_rows": log_rows,
    }, open(RESOLVED, "w", encoding='utf-8'), indent=2, ensure_ascii=False)

    if potd and potd.get("source") == "new" and potd.get("_paper"):
        p = potd["_paper"]
        full_text, used = fetch_fulltext.fetch_fulltext(
            p.get("doi", ""), p.get("title", ""), EMAIL)
        json.dump({
            "title": p.get("title", ""), "abstract": p.get("abstract", ""),
            "full_text_available": used, "full_text": full_text,
            "current_bullets": potd.get("bullets", []),
            "current_reflection_question": potd.get("reflection_question", ""),
        }, open(DEEPDIVE_INPUT, "w", encoding='utf-8'), indent=2, ensure_ascii=False)
        print("VALID — deep-dive input ready (state/deepdive_input.json)")
        print("Next: read it + DEEPDIVE_SCHEMA.md, write state/deepdive.json, "
              "then run python3 src/finalize.py")
    else:
        # canon day: no full-text deep dive needed, finalize can run directly
        if os.path.exists(DEEPDIVE_INPUT):
            os.remove(DEEPDIVE_INPUT)
        print("VALID — canon day, no deep-dive needed. Run python3 src/finalize.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
