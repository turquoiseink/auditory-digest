"""
finalize.py — last deterministic stage. Reads state/resolved.json (written by
process_selection.py) and, if present, state/deepdive.json (written by the
model), merges them, renders the PDF, appends the reading log, updates canon
progress and the run log. `--fallback` bypasses all of that and renders the
deterministic keyword digest instead (used when process_selection.py exits 2).

Prints OUTPUT_PDF=... and OUTPUT_XLSX=... for the routine to pick up for the
Drive-upload step.
"""
from __future__ import annotations
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import validate_selection
import pipeline_common as pc
import render_pdf
import reading_log

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "state")
ARCHIVE = os.path.join(STATE, "archive")
CANDIDATES = os.path.join(STATE, "candidates.json")
CONTEXT = os.path.join(STATE, "context.json")
RESOLVED = os.path.join(STATE, "resolved.json")
DEEPDIVE = os.path.join(STATE, "deepdive.json")
LOG_XLSX = os.path.join(STATE, "reading_log.xlsx")
CANON_PROGRESS = os.path.join(STATE, "canon_progress.json")
RUN_LOG = os.path.join(STATE, "run_log.json")


def _load(p, default=None):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return default


def _today(context):
    return dt.date.fromisoformat(context["date"]) if context else dt.date.today()


def _write_outputs(editorial, sections, potd, potd_log, log_rows, candidates,
                   context, llm_ok):
    today = _today(context)
    os.makedirs(ARCHIVE, exist_ok=True)
    filename = f"auditory-grouping-daily-{today.isoformat()}.pdf"
    pdf_path = os.path.join(ARCHIVE, filename)
    render_pdf.render_digest(pdf_path, today, editorial, sections, potd,
                             candidates_count=len(candidates),
                             sources_status=(context or {}).get("sources", {}),
                             llm_ok=llm_ok)

    to_append = ([potd_log] if potd_log else []) + log_rows
    seen_run, deduped = set(), []
    for r in to_append:
        k = reading_log._seen_key(r.get("title", ""), r.get("doi", ""))
        if k in seen_run:
            continue
        seen_run.add(k)
        deduped.append(r)
    added = reading_log.append_rows(LOG_XLSX, deduped)

    if potd and potd.get("source") == "canon":
        cp = _load(CANON_PROGRESS, {"served": []})
        cp.setdefault("served", []).append(potd["title"])
        json.dump(cp, open(CANON_PROGRESS, "w", encoding='utf-8'), indent=2)

    hist = _load(RUN_LOG, [])
    hist.append({"date": today.isoformat(), "llm_ok": llm_ok,
                 "rows_appended": added, "path": pdf_path})
    json.dump(hist[-180:], open(RUN_LOG, "w", encoding='utf-8'), indent=2)

    print(f"OUTPUT_PDF={pdf_path}")
    print(f"OUTPUT_XLSX={LOG_XLSX}")
    print(f"rows_appended={added} llm_ok={llm_ok}")


def main():
    candidates = _load(CANDIDATES, [])
    context = _load(CONTEXT, {"date": dt.date.today().isoformat(), "sources": {}})

    if "--fallback" in sys.argv:
        editorial, sections, log_rows = pc.fallback_digest(candidates)
        _write_outputs(editorial, sections, None, None, log_rows, candidates,
                       context, llm_ok=False)
        return 0

    resolved = _load(RESOLVED)
    if resolved is None:
        print("state/resolved.json missing — did process_selection.py succeed? "
              "If not, run: python3 src/finalize.py --fallback")
        return 1

    potd = resolved.get("potd")
    if potd and os.path.exists(DEEPDIVE):
        dd = _load(DEEPDIVE)
        ok, errors = validate_selection.validate_deepdive(dd) if dd else (False, ["missing"])
        if ok:
            potd["bullets"] = dd.get("why_it_matters", potd.get("bullets"))
            potd["reflection_question"] = dd.get("reflection_question",
                                                  potd.get("reflection_question"))
            potd["read_plan"] = dd.get("read_plan", potd.get("read_plan"))
            if dd.get("corresponding_author") or dd.get("university") or dd.get("country"):
                new_credit = pc.credit_line(
                    dd.get("corresponding_author", "") or "",
                    dd.get("university", "") or "",
                    dd.get("country", "") or "",
                )
                if new_credit:  # only overwrite if the deep-dive actually found something
                    potd["credit"] = new_credit
            potd["meta"] = potd.get("meta", "") + (
                " — full text used" if dd.get("full_text_used") else " — abstract only")
        else:
            print("deepdive.json invalid, keeping original selection bullets:", errors)
            potd["meta"] = potd.get("meta", "") + " — abstract only"
    elif potd and potd.get("source") == "new":
        potd["meta"] = potd.get("meta", "") + " — abstract only"

    _write_outputs(resolved.get("editorial"), resolved.get("sections"), potd,
                   resolved.get("potd_log"), resolved.get("log_rows", []),
                   candidates, context, llm_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
