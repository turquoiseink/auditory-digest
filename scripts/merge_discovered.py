"""
merge_discovered.py — fold verified model-discovered papers into today's
candidates.json, with real sequential candidate_ids, BEFORE selection.json
is written (so the model can reference them like any other candidate).

Run this once after you've added everything you want via
scripts/verify_identifier.py, and before writing selection.json. It's a
no-op (prints and exits 0) if state/model_discovered.json doesn't exist.
"""
from __future__ import annotations
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/src")
import fetch_papers  # for _norm_title

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "state")
CANDIDATES = os.path.join(STATE, "candidates.json")
DISCOVERED = os.path.join(STATE, "model_discovered.json")


def main():
    if not os.path.exists(DISCOVERED):
        print("no state/model_discovered.json found — nothing to merge, proceeding as-is.")
        return 0

    candidates = json.load(open(CANDIDATES, encoding="utf-8")) if os.path.exists(CANDIDATES) else []
    discovered = json.load(open(DISCOVERED, encoding="utf-8"))

    existing_dois = {(c.get("doi") or "").lower().strip() for c in candidates}
    existing_titles = {fetch_papers._norm_title(c.get("title", "")) for c in candidates}

    next_id = max((c.get("candidate_id", -1) for c in candidates), default=-1) + 1
    added = 0
    for d in discovered:
        doi = (d.get("doi") or "").lower().strip()
        tkey = fetch_papers._norm_title(d.get("title", ""))
        if (doi and doi in existing_dois) or tkey in existing_titles:
            continue  # already present via a deterministic tier — skip, no duplicate
        d["candidate_id"] = next_id
        candidates.append(d)
        existing_dois.add(doi)
        existing_titles.add(tkey)
        next_id += 1
        added += 1

    json.dump(candidates, open(CANDIDATES, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    os.remove(DISCOVERED)
    print(f"merged {added} model-discovered paper(s) into candidates.json "
          f"({len(discovered) - added} were already present via a deterministic tier, skipped). "
          f"Total candidates now: {len(candidates)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
